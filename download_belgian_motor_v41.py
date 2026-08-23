from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from pathlib import Path

import pyreadr

PREREG = Path("governance/external_validation_prereg_v40.json")
OUTDIR = Path("data_external_v41")
AUDIT_DIR = Path("results_v41")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    source = prereg["source"]
    commit = source["upstream_commit"]
    upstream_path = source["upstream_path"]
    url = f"https://raw.githubusercontent.com/{source['upstream_repository']}/{commit}/{upstream_path}"

    OUTDIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTDIR / "beMTPL97.rda"
    urllib.request.urlretrieve(url, destination)

    payload = pyreadr.read_r(str(destination))
    if "beMTPL97" not in payload:
        raise RuntimeError(f"Expected beMTPL97 object; found {sorted(payload)}")
    frame = payload["beMTPL97"]

    expected_columns = source["known_from_public_documentation_before_row_level_access"]["column_names"]
    if list(frame.columns) != expected_columns:
        raise RuntimeError(f"Unexpected columns/order: {list(frame.columns)}")
    contract = prereg["data_contract"]
    if len(frame) != int(contract["required_rows"]):
        raise RuntimeError(f"Unexpected row count: {len(frame)}")
    required_nonmissing = contract["required_nonmissing_for_model"]
    if frame[required_nonmissing].isna().any().any():
        raise RuntimeError("Pinned Belgian source contains missing values in preregistered modelling fields")
    if frame["id"].duplicated().any():
        raise RuntimeError("Pinned Belgian source contains duplicate policy ids")

    exposure = frame["expo"].astype(float)
    claim_nb = frame["nclaims"].astype(float)
    claim_amount = frame["amount"].astype(float)
    numeric_model_fields = ["expo", "nclaims", "amount", *prereg["features"]["numeric"]]
    for column in numeric_model_fields:
        values = frame[column].astype(float)
        if not values.map(math.isfinite).all():
            raise RuntimeError(f"Pinned Belgian source contains non-finite {column}")
    if (exposure <= 0).any() or (exposure > 1).any():
        raise RuntimeError("Pinned Belgian source exposure violates registered (0, 1] contract")
    if (claim_nb < 0).any() or ((claim_nb - claim_nb.round()).abs() > 1e-12).any():
        raise RuntimeError("Pinned Belgian source claim count violates registered contract")
    if (claim_amount < 0).any():
        raise RuntimeError("Pinned Belgian source contains negative aggregate claim amount")

    audit = {
        "status": "V41_PINNED_BELGIAN_SOURCE_VERIFIED",
        "source_repository": source["upstream_repository"],
        "source_commit": commit,
        "source_path": upstream_path,
        "download_url": url,
        "file_name": destination.name,
        "file_bytes": destination.stat().st_size,
        "file_sha256": sha256_file(destination),
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "unique_policy_ids": int(frame["id"].nunique()),
        "raw_data_persisted_to_repository": False,
    }
    (AUDIT_DIR / "belgian_source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
