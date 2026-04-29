# Python/JavaScript Backend Framework Benchmark

Reproducible Docker-based benchmark stand for comparing backend frameworks:
FastAPI, Sanic, aiohttp, Express.js, NestJS, and Fastify.

The stand runs one backend service at a time, warms it up, executes k6 load
scenarios, records Docker CPU/RAM usage, extracts metrics, normalizes them with
weights, and generates a Markdown report.

## Stack

- Backend services: `GET /ping`, `GET /items`, `GET /io`
- Load generator: k6
- Monitoring: `docker stats`
- Metrics: RPS, average latency, p95 latency, CPU, RAM
- Output: raw JSON/NDJSON/CSV, processed CSV/JSON, Markdown report
- CI/CD: GitHub Actions workflow in `.github/workflows/benchmark.yml`

## Test scenarios

| Test | Purpose | Default load |
| --- | --- | --- |
| warmup | Warm up runtime and caches | 10 VUs, 30s |
| baseline | Normal baseline load | 100 VUs, 60s |
| work | Mixed realistic traffic: `/ping`, `/items`, `/io` | 100 VUs, 60s |
| stress | Overload boundary | 500 VUs, 60s |
| soak | Long-running stability check | 100 VUs, 10m |

The CI profile keeps the same pipeline but shortens durations so the workflow
validates reproducibility without spending an hour on every push.

## Run

```bash
docker compose build
bash scripts/run_benchmarks.sh
```

Useful alternatives:

```bash
BENCH_PROFILE=ci bash scripts/run_benchmarks.sh
BENCH_BUILD=0 BENCH_RUN_ID=my-run bash scripts/run_benchmarks.sh
python scripts/collect_metrics.py --run-id my-run
python scripts/normalize.py --run-id my-run
python scripts/generate_report.py --run-id my-run
```

Results are written to:

- `results/raw/<run_id>/<framework>/<test>/k6-summary.json`
- `results/raw/<run_id>/<framework>/<test>/k6-samples.ndjson`
- `results/raw/<run_id>/<framework>/<test>/docker-stats.csv`
- `results/processed/metrics.csv`
- `results/processed/scores.csv`
- `results/processed/overall_scores.csv`
- `results/reports/<run_id>/report.md`

## Configuration

The single benchmark config is `config/test_config.yaml`. It is intentionally
JSON-compatible YAML, so scripts can read it with Python standard library only.

Weights for the scientific normalization step are in `config/weights.json`.
`rps` is maximized; latency, CPU, and RAM are minimized.

## Pipeline

1. Build backend containers.
2. Start exactly one framework service.
3. Wait for `/ping`.
4. Run `warmup`.
5. Run `baseline`, `work`, `stress`, and `soak`.
6. Collect k6 latency/RPS and Docker CPU/RAM metrics.
7. Stop the service.
8. Repeat for the next framework.
9. Normalize metrics and generate a report.
