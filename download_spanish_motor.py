from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

URL = "https://raw.githubusercontent.com/Niekrenz82/IntML_Pro1/main/data/Motor%20vehicle%20insurance%20data.csv"
REQUIRED = {
    "ID", "Date_start_contract", "Date_last_renewal", "Date_next_renewal",
    "Premium", "Cost_claims_year", "N_claims_year", "N_claims_history",
    "Type_risk", "Area", "Second_driver", "Value_vehicle", "Type_fuel",
    "Length", "Weight",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data_spanish/Motor_vehicle_insurance_data.csv")
    parser.add_argument("--audit", default="results_oot/spanish_data_audit.json")
    args = parser.parse_args()

    out = Path(args.output)
    audit_path = Path(args.audit)
    out.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    urlretrieve(URL, out)
    raw = out.read_bytes()
    df = pd.read_csv(out, sep=";", low_memory=False)
    missing = sorted(REQUIRED - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    dates = pd.to_datetime(df["Date_last_renewal"], dayfirst=True, errors="coerce")
    if dates.notna().sum() == 0:
        raise SystemExit("Date_last_renewal could not be parsed")

    audit = {
        "source_url": URL,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "date_last_renewal_min": str(dates.min().date()),
        "date_last_renewal_max": str(dates.max().date()),
        "unique_renewal_years": sorted(int(x) for x in dates.dt.year.dropna().unique()),
        "missing_required_columns": missing,
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
