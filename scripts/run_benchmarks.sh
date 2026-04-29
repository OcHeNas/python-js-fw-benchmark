#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CONFIG_FILE="${CONFIG_FILE:-config/test_config.yaml}"
BENCH_PROFILE="${BENCH_PROFILE:-default}"
BENCH_BUILD="${BENCH_BUILD:-1}"
BENCH_PROCESS="${BENCH_PROCESS:-1}"
BENCH_RUN_ID="${BENCH_RUN_ID:-$(date -u +"%Y%m%dT%H%M%SZ")}"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python3}"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python}"
else
  echo "Python is required to read benchmark config and process metrics." >&2
  exit 1
fi

eval "$("$PYTHON_BIN" scripts/config_query.py shell --config "$CONFIG_FILE" --profile "$BENCH_PROFILE")"

read -r -a SERVICES <<< "$FRAMEWORKS"
read -r -a TEST_NAMES <<< "$TESTS"

RUN_DIR="results/raw/$BENCH_RUN_ID"
FAILURES=()
MONITOR_PID=""

stop_monitor() {
  if [[ -n "${MONITOR_PID:-}" ]]; then
    kill "$MONITOR_PID" >/dev/null 2>&1 || true
    wait "$MONITOR_PID" >/dev/null 2>&1 || true
    MONITOR_PID=""
  fi
}

stop_backends() {
  docker compose stop "${SERVICES[@]}" >/dev/null 2>&1 || true
}

cleanup() {
  stop_monitor
  stop_backends
}

trap cleanup EXIT INT TERM

wait_for_service() {
  local service="$1"
  local target="http://${service}:${SERVICE_PORT}"
  local attempts=$((STARTUP_TIMEOUT_SECONDS / 2))

  if [[ "$attempts" -lt 1 ]]; then
    attempts=1
  fi

  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if docker compose run --rm k6 run -q -e TARGET="$target" /scripts/healthcheck.js >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "Service $service did not become ready at $target within ${STARTUP_TIMEOUT_SECONDS}s." >&2
  return 1
}

test_var() {
  local test_name="$1"
  local field="$2"
  local var_name="TEST_${test_name^^}_${field}"
  printf "%s" "${!var_name}"
}

mkdir -p "$RUN_DIR"
cp "$CONFIG_FILE" "$RUN_DIR/test_config.yaml"
cp config/weights.json "$RUN_DIR/weights.json"
cat > "$RUN_DIR/manifest.json" <<EOF
{
  "run_id": "$BENCH_RUN_ID",
  "profile": "$BENCH_PROFILE",
  "created_at_utc": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "service_port": "$SERVICE_PORT",
  "frameworks": "$FRAMEWORKS",
  "tests": "$TESTS"
}
EOF

echo "Benchmark run: $BENCH_RUN_ID (profile: $BENCH_PROFILE)"

if [[ "$BENCH_BUILD" == "1" ]]; then
  echo "Building backend containers..."
  docker compose build "${SERVICES[@]}"
fi

for service in "${SERVICES[@]}"; do
  echo "Starting $service..."
  stop_backends
  docker compose up -d "$service"
  wait_for_service "$service"

  for test_name in "${TEST_NAMES[@]}"; do
    script="$(test_var "$test_name" SCRIPT)"
    vus="$(test_var "$test_name" VUS)"
    duration="$(test_var "$test_name" DURATION)"
    output_dir="$RUN_DIR/$service/$test_name"
    monitor_csv="$output_dir/docker-stats.csv"
    target="http://${service}:${SERVICE_PORT}"

    mkdir -p "$output_dir"
    echo "Running $service / $test_name: VUs=$vus, duration=$duration"

    bash scripts/monitor.sh "$service" "$monitor_csv" "$MONITOR_INTERVAL_SECONDS" &
    MONITOR_PID="$!"

    set +e
    docker compose run --rm k6 run \
      -e TARGET="$target" \
      -e VUS="$vus" \
      -e DURATION="$duration" \
      -e TEST_NAME="$test_name" \
      --summary-export "/results/raw/$BENCH_RUN_ID/$service/$test_name/k6-summary.json" \
      --out "json=/results/raw/$BENCH_RUN_ID/$service/$test_name/k6-samples.ndjson" \
      "/scripts/$script"
    status=$?
    set -e

    stop_monitor
    echo "$status" > "$output_dir/k6-exit-code.txt"

    if [[ "$status" -ne 0 ]]; then
      FAILURES+=("$service/$test_name")
      echo "Test failed: $service/$test_name (exit code $status)" >&2
    fi
  done

  echo "Stopping $service..."
  docker compose stop "$service" >/dev/null
done

if [[ "$BENCH_PROCESS" == "1" ]]; then
  "$PYTHON_BIN" scripts/collect_metrics.py --run-id "$BENCH_RUN_ID"
  "$PYTHON_BIN" scripts/normalize.py --run-id "$BENCH_RUN_ID"
  "$PYTHON_BIN" scripts/generate_report.py --run-id "$BENCH_RUN_ID"
fi

if [[ "${#FAILURES[@]}" -gt 0 ]]; then
  echo "Benchmark completed with failures: ${FAILURES[*]}" >&2
  exit 1
fi

echo "Benchmark completed successfully. Results: $RUN_DIR"
