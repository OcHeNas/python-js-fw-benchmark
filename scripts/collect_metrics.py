#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path


FIELDNAMES = [
    "run_id",
    "framework",
    "test",
    "rps",
    "http_reqs",
    "latency_avg_ms",
    "latency_p95_ms",
    "cpu_avg_percent",
    "cpu_max_percent",
    "ram_avg_mb",
    "ram_max_mb",
    "k6_summary",
    "monitor_csv",
]


SIZE_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([A-Za-z]+)\s*$")
SIZE_MULTIPLIERS = {
    "b": 1,
    "kb": 1000,
    "kib": 1024,
    "mb": 1000**2,
    "mib": 1024**2,
    "gb": 1000**3,
    "gib": 1024**3,
}


def parse_float(value):
    if value in (None, ""):
        return None
    return float(str(value).strip().replace("%", ""))


def parse_size_bytes(value):
    if not value:
        return None
    usage = str(value).split("/")[0].strip()
    match = SIZE_RE.match(usage)
    if not match:
        return None
    amount, unit = match.groups()
    multiplier = SIZE_MULTIPLIERS.get(unit.lower())
    if multiplier is None:
        return None
    return float(amount) * multiplier


def read_k6_summary(path):
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    metrics = data.get("metrics", {})
    duration = metrics.get("http_req_duration", {})
    requests = metrics.get("http_reqs", {})

    return {
        "rps": requests.get("rate"),
        "http_reqs": requests.get("count"),
        "latency_avg_ms": duration.get("avg"),
        "latency_p95_ms": duration.get("p(95)"),
    }


def read_monitor(path):
    if not path.exists():
        return {
            "cpu_avg_percent": None,
            "cpu_max_percent": None,
            "ram_avg_mb": None,
            "ram_max_mb": None,
        }

    cpu_values = []
    ram_values_mb = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cpu = parse_float(row.get("cpu_percent"))
            ram_bytes = parse_size_bytes(row.get("mem_usage"))
            if cpu is not None:
                cpu_values.append(cpu)
            if ram_bytes is not None:
                ram_values_mb.append(ram_bytes / (1024**2))

    return {
        "cpu_avg_percent": sum(cpu_values) / len(cpu_values) if cpu_values else None,
        "cpu_max_percent": max(cpu_values) if cpu_values else None,
        "ram_avg_mb": sum(ram_values_mb) / len(ram_values_mb) if ram_values_mb else None,
        "ram_max_mb": max(ram_values_mb) if ram_values_mb else None,
    }


def identify_result(summary_path, raw_dir):
    relative = summary_path.relative_to(raw_dir)
    parts = relative.parts

    if len(parts) >= 4:
        return parts[0], parts[1], parts[2]
    if len(parts) >= 3:
        return "legacy", parts[0], parts[1]

    raise ValueError(f"Unsupported result path: {summary_path}")


def collect(raw_dir, run_id=None):
    rows = []
    summary_files = sorted(raw_dir.rglob("k6-summary.json")) + sorted(raw_dir.rglob("result.json"))

    for summary_path in summary_files:
        current_run_id, framework, test_name = identify_result(summary_path, raw_dir)
        if run_id and current_run_id != run_id:
            continue

        try:
            k6_metrics = read_k6_summary(summary_path)
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

        monitor_path = summary_path.parent / "docker-stats.csv"
        monitor_metrics = read_monitor(monitor_path)
        rows.append(
            {
                "run_id": current_run_id,
                "framework": framework,
                "test": test_name,
                **k6_metrics,
                **monitor_metrics,
                "k6_summary": str(summary_path),
                "monitor_csv": str(monitor_path) if monitor_path.exists() else "",
            }
        )

    return rows


def write_outputs(rows, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "metrics.csv"
    json_path = output_dir / "metrics.json"

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    return csv_path, json_path


def main():
    parser = argparse.ArgumentParser(description="Collect k6 and docker stats metrics.")
    parser.add_argument("--raw-dir", default="results/raw")
    parser.add_argument("--output-dir", default="results/processed")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    rows = collect(Path(args.raw_dir), args.run_id)
    csv_path, json_path = write_outputs(rows, Path(args.output_dir))
    print(f"Collected {len(rows)} result rows into {csv_path} and {json_path}")


if __name__ == "__main__":
    main()
