from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

URL = "https://raw.githubusercontent.com/Niekrenz82/IntML_Pro1/main/data/Motor%20vehicle%20insurance%20data.csv"
REQUIRED = {
    "ID", "Date_start_contract", "Date_last_renewal", "Date_next_renewal",
    "Premium", "Cost_claims_year", "N_claims_year", "N_claims_history",
    "Type_risk", "Area", "Second_driver", "Value_vehicle", "Type_fuel",
    "Length", "Weight",
}


def download_with_retries(url: str, out: Path, attempts: int = 3, timeout: int = 90) -> None:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = Request(url, headers={"User-Agent": "motor-insurance-pricing-governance/0.11"})
            with urlopen(req, timeout=timeout) as response, out.open("wb") as fh:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    fh.write(chunk)
            if out.stat().st_size < 1_000_000:
                raise RuntimeError(f"Downloaded file is unexpectedly small: {out.stat().st_size} bytes")
            return
        except Exception as exc:
            last_error = exc
            if out.exists():
                out.unlink()
            if attempt < attempts:
                time.sleep(5 * attempt)
    raise RuntimeError(f"Download failed after {attempts} attempts: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data_spanish/Motor_vehicle_insurance_data.csv")
    parser.add_argument("--audit", default="results_oot/spanish_data_audit.json")
    args = parser.parse_args()

    out = Path(args.output)
    audit_path = Path(args.audit)
    out.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        download_with_retries(URL, out)
        raw = out.read_bytes()
        df = pd.read_csv(out, sep=";", low_memory=False)
        missing = sorted(REQUIRED - set(df.columns))
        if missing:
            raise RuntimeError(f"Missing required columns: {missing}")
        if len(df) < 100_000:
            raise RuntimeError(f"Unexpectedly small row count: {len(df)}")

        dates = pd.to_datetime(df["Date_last_renewal"], dayfirst=True, errors="coerce")
        if dates.notna().sum() == 0:
            raise RuntimeError("Date_last_renewal could not be parsed")

        audit = {
            "status": "DOWNLOAD_AND_AUDIT_OK",
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
    except Exception as exc:
        audit = {
            "status": "DOWNLOAD_OR_AUDIT_FAILED",
            "source_url": URL,
            "error": repr(exc),
        }
        audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
        print(json.dumps(audit, indent=2))
        raise


if __name__ == "__main__":
    main()
