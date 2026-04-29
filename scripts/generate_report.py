#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def read_csv(path):
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def choose_run_id(metrics, requested):
    if requested:
        return requested
    run_ids = sorted({row["run_id"] for row in metrics})
    if not run_ids:
        raise SystemExit("No metrics found. Run collect_metrics.py first.")
    return run_ids[-1]


def table(headers, rows):
    output = []
    output.append("| " + " | ".join(headers) + " |")
    output.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        output.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(output)


def fmt(value, digits=3):
    if value in (None, ""):
        return ""
    return f"{float(value):.{digits}f}"


def build_report(run_id, metrics, scores, overall):
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    metrics = [row for row in metrics if row["run_id"] == run_id]
    scores = [row for row in scores if row["run_id"] == run_id]
    overall = [row for row in overall if row["run_id"] == run_id]

    score_by_key = {(row["framework"], row["test"]): row for row in scores}
    by_test = defaultdict(list)
    for row in metrics:
        by_test[row["test"]].append(row)

    lines = [
        f"# Benchmark report: {run_id}",
        "",
        f"Generated: {generated}",
        "",
        "## Overall score",
        "",
    ]

    lines.append(
        table(
            ["Rank", "Framework", "Score", "Tests"],
            [
                [row["rank"], row["framework"], fmt(row["score"], 6), row["tests_count"]]
                for row in overall
            ],
        )
    )

    for test_name in sorted(by_test):
        rows = sorted(
            by_test[test_name],
            key=lambda item: int(score_by_key.get((item["framework"], test_name), {}).get("rank", 9999)),
        )
        lines.extend(["", f"## {test_name}", ""])
        lines.append(
            table(
                ["Rank", "Framework", "RPS", "Avg latency ms", "P95 latency ms", "CPU avg %", "RAM avg MB", "Score"],
                [
                    [
                        score_by_key.get((row["framework"], test_name), {}).get("rank", ""),
                        row["framework"],
                        fmt(row["rps"]),
                        fmt(row["latency_avg_ms"]),
                        fmt(row["latency_p95_ms"]),
                        fmt(row["cpu_avg_percent"]),
                        fmt(row["ram_avg_mb"]),
                        fmt(score_by_key.get((row["framework"], test_name), {}).get("score", ""), 6),
                    ]
                    for row in rows
                ],
            )
        )

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate a Markdown benchmark report.")
    parser.add_argument("--run-id")
    parser.add_argument("--processed-dir", default="results/processed")
    parser.add_argument("--reports-dir", default="results/reports")
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    metrics = read_csv(processed_dir / "metrics.csv")
    scores = read_csv(processed_dir / "scores.csv")
    overall = read_csv(processed_dir / "overall_scores.csv")
    run_id = choose_run_id(metrics, args.run_id)

    report_dir = Path(args.reports_dir) / run_id
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.md"
    report_path.write_text(build_report(run_id, metrics, scores, overall), encoding="utf-8")

    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
