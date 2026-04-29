# Бенчмарк backend-фреймворков Python/JavaScript

Воспроизводимый тестовый стенд на основе Docker для сравнительного анализа backend-фреймворков:
FastAPI, Sanic, aiohttp, Express.js, NestJS и Fastify.

Стенд запускает по одному backend-сервису, выполняет его прогрев, затем запускает нагрузочные сценарии k6, собирает метрики CPU/RAM через Docker, извлекает показатели производительности, нормализует их с использованием весов и формирует итоговый отчёт в формате Markdown.

## Стек технологий

* Backend-сервисы: `GET /ping`, `GET /items`, `GET /io`
* Генератор нагрузки: k6
* Мониторинг: `docker stats`
* Метрики: RPS, средняя задержка, p95 задержки, CPU, RAM
* Результаты:

  * сырые данные: JSON / NDJSON / CSV
  * обработанные данные: CSV / JSON
  * отчёт: Markdown
* CI/CD: GitHub Actions (`.github/workflows/benchmark.yml`)

## Сценарии тестирования

| Тест     | Назначение                                                | Нагрузка по умолчанию |
| -------- | --------------------------------------------------------- | --------------------- |
| warmup   | Прогрев среды выполнения и кэшей                          | 10 VUs, 30s           |
| baseline | Базовая (нормальная) нагрузка                             | 100 VUs, 60s          |
| work     | Смешанная реалистичная нагрузка: `/ping`, `/items`, `/io` | 100 VUs, 60s          |
| stress   | Тест на предельную нагрузку                               | 500 VUs, 60s          |
| soak     | Длительный тест стабильности                              | 100 VUs, 10m          |

Профиль CI использует тот же pipeline, но с сокращённой длительностью тестов, чтобы проверять воспроизводимость без длительного выполнения на каждый push.

## Запуск

```bash
docker compose build
bash scripts/run_benchmarks.sh
```

Полезные альтернативы:

```bash
BENCH_PROFILE=ci bash scripts/run_benchmarks.sh
BENCH_BUILD=0 BENCH_RUN_ID=my-run bash scripts/run_benchmarks.sh

python scripts/collect_metrics.py --run-id my-run
python scripts/normalize.py --run-id my-run
python scripts/generate_report.py --run-id my-run
```

## Результаты

Результаты сохраняются в следующие директории:

* `results/raw/<run_id>/<framework>/<test>/k6-summary.json`
* `results/raw/<run_id>/<framework>/<test>/k6-samples.ndjson`
* `results/raw/<run_id>/<framework>/<test>/docker-stats.csv`
* `results/processed/metrics.csv`
* `results/processed/scores.csv`
* `results/processed/overall_scores.csv`
* `results/reports/<run_id>/report.md`

## Конфигурация

Основной конфигурационный файл: `config/test_config.yaml`.

Он намеренно записан в формате JSON-совместимого YAML, чтобы его можно было обрабатывать средствами стандартной библиотеки Python без дополнительных зависимостей.

Весовые коэффициенты для научной части (нормализации) находятся в `config/weights.json`.

* `rps` — максимизируется
* `latency`, `CPU`, `RAM` — минимизируются

## Pipeline

1. Сборка Docker-контейнеров backend-сервисов.
2. Запуск одного тестируемого сервиса.
3. Ожидание готовности (`/ping`).
4. Выполнение этапа `warmup`.
5. Последовательный запуск тестов:

   * `baseline`
   * `work`
   * `stress`
   * `soak`
6. Сбор метрик:

   * latency и RPS (k6)
   * CPU и RAM (docker stats)
7. Остановка сервиса.
8. Повтор шагов для следующего фреймворка.
9. Нормализация метрик и генерация итогового отчёта.

---

