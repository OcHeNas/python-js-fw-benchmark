#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <compose-service-or-container-id> <output.csv> [interval_seconds]" >&2
  exit 2
fi

target="$1"
output="$2"
interval="${3:-2}"
container="$target"

if ! docker inspect "$target" >/dev/null 2>&1; then
  resolved="$(docker compose ps -q "$target" 2>/dev/null || true)"
  if [[ -n "$resolved" ]]; then
    container="$resolved"
  fi
fi

mkdir -p "$(dirname "$output")"
echo "timestamp,cpu_percent,mem_usage,mem_percent" > "$output"

while true; do
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  stats="$(docker stats "$container" --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}" 2>/dev/null || true)"

  if [[ -n "$stats" ]]; then
    echo "${timestamp},${stats}" >> "$output"
  else
    echo "${timestamp},,," >> "$output"
  fi

  sleep "$interval"
done
