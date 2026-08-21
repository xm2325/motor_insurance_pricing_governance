from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

DATA_PATH = Path("data_spanish_2022_2024/Dataset_of_motor_insurance_portfolio.csv")
OUT_PATH = Path("results_oot_2024/schema_data_audit.json")


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    year_counts: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    sample_rows = []
    n = 0
    header: list[str] = []

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        header = list(reader.fieldnames or [])
        for row in reader:
            n += 1
            year_counts[str(row.get("year", ""))] += 1
            for col in header:
                value = row.get(col)
                if value is None or value.strip() in {"", "NA", "NaN", "nan", "NULL", "null"}:
                    missing[col] += 1
            if len(sample_rows) < 3:
                sample_rows.append({k: row.get(k) for k in header})

    payload = {
        "status": "SCHEMA_DATA_AUDIT_OK",
        "rows": n,
        "columns": len(header),
        "header": header,
        "year_counts": dict(sorted(year_counts.items())),
        "missing_counts": {col: int(missing[col]) for col in header},
        "missing_rates": {col: (missing[col] / n if n else None) for col in header},
        "sample_rows": sample_rows,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
