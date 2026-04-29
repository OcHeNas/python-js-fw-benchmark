.PHONY: build benchmark benchmark-ci collect normalize report down all

build:
	docker compose build

benchmark:
	bash scripts/run_benchmarks.sh

benchmark-ci:
	BENCH_PROFILE=ci bash scripts/run_benchmarks.sh

collect:
	python scripts/collect_metrics.py

normalize:
	python scripts/normalize.py

report:
	python scripts/generate_report.py

down:
	docker compose down --remove-orphans

all: benchmark
