#!/usr/bin/env python3
"""Display the model-by-question status pivot from the long comparison CSV.

    python display-comparison-matrix.py
    python display-comparison-matrix.py path/to/model-question-comparison-en.csv
"""
import argparse
import csv
from pathlib import Path


REQUIRED_COLUMNS = {"case_id", "model_id", "status"}


def case_sort_key(case_id: str) -> tuple[str, int | str]:
    prefix = case_id.rstrip("0123456789")
    suffix = case_id[len(prefix):]
    return (prefix, int(suffix)) if suffix else (case_id, case_id)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a Markdown models-by-questions status matrix."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("model-question-comparison-en.csv"),
        help="long comparison CSV (defaults to the file beside this script)",
    )
    args = parser.parse_args()

    try:
        with args.csv_file.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            columns = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - columns
            if missing:
                parser.error(f"{args.csv_file}: missing columns: {', '.join(sorted(missing))}")

            matrix: dict[tuple[str, str], str] = {}
            models: set[str] = set()
            cases: set[str] = set()
            for line_number, row in enumerate(reader, start=2):
                model_id = (row.get("model_id") or "").strip()
                case_id = (row.get("case_id") or "").strip()
                status = (row.get("status") or "").strip()
                if not model_id or not case_id or not status:
                    parser.error(
                        f"{args.csv_file}:{line_number}: model_id, case_id, and status "
                        "must not be empty"
                    )
                key = (model_id, case_id)
                if key in matrix:
                    parser.error(
                        f"{args.csv_file}:{line_number}: duplicate model/question "
                        f"pair {model_id!r}, {case_id!r}"
                    )
                matrix[key] = status
                models.add(model_id)
                cases.add(case_id)
    except OSError as error:
        parser.error(f"cannot read {args.csv_file}: {error}")

    if not matrix:
        parser.error(f"{args.csv_file}: no comparison rows found")

    case_columns = sorted(cases, key=case_sort_key)
    print("| Model | " + " | ".join(case_columns) + " |")
    print("|" + "|".join(["---"] * (len(case_columns) + 1)) + "|")
    for model_id in sorted(models):
        statuses = [
            matrix.get((model_id, case_id), "—").replace("|", "\\|")
            for case_id in case_columns
        ]
        print("| " + model_id.replace("|", "\\|") + " | " + " | ".join(statuses) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
