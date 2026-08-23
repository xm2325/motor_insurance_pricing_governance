from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import pyreadr


PREREG = Path("governance/external_validation_prereg_v36.json")
OUTDIR = Path("data_external_v37")
AUDIT_DIR = Path("results_v37")


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
    destination = OUTDIR / "ausprivauto0405.rda"
    urllib.request.urlretrieve(url, destination)

    payload = pyreadr.read_r(str(destination))
    if "ausprivauto0405" not in payload:
        raise RuntimeError(f"Expected ausprivauto0405 object; found {sorted(payload)}")
    frame = payload["ausprivauto0405"]

    expected_columns = source["known_from_public_documentation_before_row_level_access"]["column_names"]
    if list(frame.columns) != expected_columns:
        raise RuntimeError(f"Unexpected columns/order: {list(frame.columns)}")
    if len(frame) != int(prereg["data_contract"]["required_rows"]):
        raise RuntimeError(f"Unexpected row count: {len(frame)}")

    required = prereg["data_contract"]["required_columns"]
    if frame[required].isna().any().any():
        raise RuntimeError("Pinned external source contains missing required values")
    exposure = frame["Exposure"].astype(float)
    claim_nb = frame["ClaimNb"].astype(float)
    claim_amount = frame["ClaimAmount"].astype(float)
    if (exposure <= 0).any():
        raise RuntimeError("Pinned external source contains non-positive Exposure")
    if (claim_nb < 0).any():
        raise RuntimeError("Pinned external source contains negative ClaimNb")
    if ((claim_nb - claim_nb.round()).abs() > 1e-12).any():
        raise RuntimeError("Pinned external source contains non-integer ClaimNb")
    if (claim_amount < 0).any():
        raise RuntimeError("Pinned external source contains negative ClaimAmount")

    claim_policy_count = int((claim_nb > 0).sum())
    expected_claim_policy_count = int(
        source["known_from_public_documentation_before_row_level_access"]["policies_with_at_least_one_claim"]
    )
    if claim_policy_count != expected_claim_policy_count:
        raise RuntimeError(
            f"Documented claim-policy count mismatch: {claim_policy_count} != {expected_claim_policy_count}"
        )

    audit = {
        "status": "V37_PINNED_AUSTRALIAN_SOURCE_VERIFIED",
        "source_repository": source["upstream_repository"],
        "source_commit": commit,
        "source_path": upstream_path,
        "download_url": url,
        "file_name": destination.name,
        "file_bytes": destination.stat().st_size,
        "file_sha256": sha256_file(destination),
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "policies_with_at_least_one_claim": claim_policy_count,
        "raw_data_persisted_to_repository": False,
    }
    (AUDIT_DIR / "australian_source_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
