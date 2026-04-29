#!/usr/bin/env python3
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


SCORE_FIELDS = [
    "run_id",
    "framework",
    "test",
    "score",
    "rank",
]


OVERALL_FIELDS = [
    "run_id",
    "framework",
    "score",
    "rank",
    "tests_count",
]


def as_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_metrics(path, run_id=None):
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if run_id:
        rows = [row for row in rows if row["run_id"] == run_id]
    return rows


def load_weights(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        weights = json.load(handle)

    total = sum(float(spec["weight"]) for spec in weights.values())
    if total <= 0:
        raise ValueError("Metric weights must have a positive sum.")

    for spec in weights.values():
        spec["weight"] = float(spec["weight"]) / total
        if spec.get("direction") not in {"min", "max"}:
            raise ValueError("Metric direction must be either 'min' or 'max'.")

    return weights


def normalize_value(value, values, direction):
    if value is None:
        return 0.0

    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        return 1.0

    if direction == "max":
        return (value - minimum) / (maximum - minimum)
    return (maximum - value) / (maximum - minimum)


def score_rows(rows, weights):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["run_id"], row["test"])].append(row)

    scored = []
    for (_run_id, _test_name), group in grouped.items():
        metric_values = {}
        for metric in weights:
            values = [as_float(row.get(metric)) for row in group]
            metric_values[metric] = [value for value in values if value is not None]

        group_scores = []
        for row in group:
            score = 0.0
            for metric, spec in weights.items():
                values = metric_values[metric]
                value = as_float(row.get(metric))
                if values:
                    score += spec["weight"] * normalize_value(value, values, spec["direction"])
            score_row = {
                "run_id": row["run_id"],
                "framework": row["framework"],
                "test": row["test"],
                "score": round(score, 6),
            }
            group_scores.append(score_row)

        group_scores.sort(key=lambda item: item["score"], reverse=True)
        for rank, row in enumerate(group_scores, start=1):
            row["rank"] = rank
            scored.append(row)

    scored.sort(key=lambda item: (item["run_id"], item["test"], item["rank"]))
    return scored


def overall_scores(scored_rows, include_warmup=False):
    grouped = defaultdict(list)
    for row in scored_rows:
        if not include_warmup and row["test"] == "warmup":
            continue
        grouped[(row["run_id"], row["framework"])].append(float(row["score"]))

    rows = []
    for (run_id, framework), values in grouped.items():
        rows.append(
            {
                "run_id": run_id,
                "framework": framework,
                "score": round(sum(values) / len(values), 6),
                "tests_count": len(values),
            }
        )

    by_run = defaultdict(list)
    for row in rows:
        by_run[row["run_id"]].append(row)

    ranked = []
    for run_id, group in by_run.items():
        group.sort(key=lambda item: item["score"], reverse=True)
        for rank, row in enumerate(group, start=1):
            row["rank"] = rank
            ranked.append(row)

    ranked.sort(key=lambda item: (item["run_id"], item["rank"]))
    return ranked


def write_csv(path, rows, fieldnames):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Normalize metrics and calculate weighted scores.")
    parser.add_argument("--metrics", default="results/processed/metrics.csv")
    parser.add_argument("--weights", default="config/weights.json")
    parser.add_argument("--output-dir", default="results/processed")
    parser.add_argument("--run-id")
    parser.add_argument("--include-warmup", action="store_true")
    args = parser.parse_args()

    rows = load_metrics(args.metrics, args.run_id)
    weights = load_weights(args.weights)
    scored = score_rows(rows, weights)
    overall = overall_scores(scored, include_warmup=args.include_warmup)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scores_csv = output_dir / "scores.csv"
    overall_csv = output_dir / "overall_scores.csv"
    scores_json = output_dir / "scores.json"

    write_csv(scores_csv, scored, SCORE_FIELDS)
    write_csv(overall_csv, overall, OVERALL_FIELDS)
    with scores_json.open("w", encoding="utf-8") as handle:
        json.dump({"scores": scored, "overall": overall}, handle, indent=2)

    print(f"Calculated {len(scored)} test scores and {len(overall)} overall scores.")


if __name__ == "__main__":
    main()
