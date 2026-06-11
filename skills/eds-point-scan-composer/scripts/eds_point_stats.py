from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize EDS point-scan C percentage values by sample group."
    )
    parser.add_argument("input", type=Path, help="CSV with columns group,value or sample,value.")
    parser.add_argument("--group-column", default="group", help="Group column name. Default: group.")
    parser.add_argument("--value-column", default="value", help="Numeric C percent column. Default: value.")
    parser.add_argument("--output-csv", type=Path, help="Optional output summary CSV path.")
    parser.add_argument("--output-json", type=Path, help="Optional output summary JSON path.")
    return parser.parse_args()


def load_values(path: Path, group_col: str, value_col: str) -> dict[str, list[float]]:
    values: dict[str, list[float]] = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if group_col not in reader.fieldnames and group_col == "group" and "sample" in (reader.fieldnames or []):
            group_col = "sample"
        if group_col not in (reader.fieldnames or []):
            raise ValueError(f"Missing group column: {group_col}")
        if value_col not in (reader.fieldnames or []):
            raise ValueError(f"Missing value column: {value_col}")
        for row in reader:
            group = (row.get(group_col) or "").strip()
            raw = (row.get(value_col) or "").strip().rstrip("%")
            if not group or not raw:
                continue
            values[group].append(float(raw))
    return dict(values)


def summarize(values: dict[str, list[float]]) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for group, nums in values.items():
        n = len(nums)
        mean = statistics.fmean(nums)
        sd = statistics.stdev(nums) if n > 1 else 0.0
        rsd = sd / mean * 100 if mean else 0.0
        rows.append(
            {
                "group": group,
                "n": n,
                "mean": mean,
                "sd": sd,
                "min": min(nums),
                "max": max(nums),
                "rsd_percent": rsd,
            }
        )
    return sorted(rows, key=lambda row: str(row["group"]))


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["group", "n", "mean", "sd", "min", "max", "rsd_percent"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    rows = summarize(load_values(args.input, args.group_column, args.value_column))
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    if args.output_csv:
        write_csv(args.output_csv, rows)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
