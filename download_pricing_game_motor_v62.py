from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

from validate_prospective_request_registration_v61 import canonical_sha256, validate

REGISTRATION = Path("governance/prospective_request_registration_v61.json")
IMPLEMENTATION = Path("governance/s1_execution_implementation_v62.json")
V61_STATUS = Path("action_results/v61/origin/32793349122/ACTION_V61_STATUS.json")
OUTDIR = Path("data_external_v62")
AUDIT_DIR = Path("results_v62")
DATA_PATH = OUTDIR / "pg15training.rda"
EXPECTED_PROTOCOL_SHA256 = "80533141f88b042a02618d609f77d355f32c9d81ce53569aece27aab207a58c9"
EXPECTED_V61_EVIDENCE_COMMIT = "9a4520d9647eb7a1c51ff1d8e49345fd783def10"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_locked_s1() -> tuple[dict, dict, dict]:
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    validate(registration)
    digest = canonical_sha256(registration)
    if digest != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError(f"v0.61 canonical protocol digest changed: {digest}")
    implementation = json.loads(IMPLEMENTATION.read_text(encoding="utf-8"))
    parent = implementation["parent_registration"]
    if parent["canonical_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.62 implementation seal is not tied to the registered v0.61 protocol")
    if parent["main_evidence_commit"] != EXPECTED_V61_EVIDENCE_COMMIT:
        raise RuntimeError("v0.62 implementation seal points to an unexpected v0.61 evidence commit")
    status = json.loads(V61_STATUS.read_text(encoding="utf-8"))
    if status["status"] != "success":
        raise RuntimeError("v0.61 immutable registration status is not successful")
    if status["protocol_canonical_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.61 immutable registration digest changed")
    if status["request_id"] != "MCR-XGB-MOTOR-002" or status["request_lifecycle"] != "REGISTERED_SEALED_BEFORE_S1":
        raise RuntimeError("v0.61 immutable lifecycle does not authorise first S1 execution")
    for key in ("s1_open", "s2_open", "s3_open", "new_rda_downloaded", "new_rda_decoded", "row_level_new_source_accessed", "new_outcome_values_accessed", "model_fit_executed", "performance_metrics_computed"):
        if status[key] is not False:
            raise RuntimeError(f"v0.61 pre-access boundary changed: {key}")
    if status["s3_reserve_sealed"] is not True:
        raise RuntimeError("v0.61 reserve is no longer sealed")
    return registration, implementation, status


def main() -> None:
    registration, implementation, v61_status = _load_locked_s1()
    source = registration["sources"]["S1_TEMPORAL_QUALIFICATION"]
    file_spec = source["rda_files"][0]
    commit = registration["distribution_channel"]["pinned_commit"]
    repository = registration["distribution_channel"]["repository"]
    upstream_path = file_spec["path"]
    url = f"https://raw.githubusercontent.com/{repository}/{commit}/{upstream_path}"

    OUTDIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, DATA_PATH)

    actual_size = DATA_PATH.stat().st_size
    actual_git_blob = git_blob_sha1(DATA_PATH)
    if actual_size != int(file_spec["bytes"]):
        raise RuntimeError(f"S1 source byte-size identity changed: {actual_size}")
    if actual_git_blob != file_spec["git_blob_sha1"]:
        raise RuntimeError(f"S1 source Git-blob identity changed: {actual_git_blob}")

    audit = {
        "status": "V62_PINNED_PG15TRAINING_BINARY_VERIFIED_BEFORE_DECODE",
        "request_id": registration["request_id"],
        "stage": "S1_TEMPORAL_QUALIFICATION",
        "v61_protocol_canonical_sha256": EXPECTED_PROTOCOL_SHA256,
        "v61_main_evidence_commit": EXPECTED_V61_EVIDENCE_COMMIT,
        "v61_main_run_id": v61_status["run_id"],
        "source_repository": repository,
        "source_commit": commit,
        "source_path": upstream_path,
        "download_url": url,
        "file_name": DATA_PATH.name,
        "file_bytes": actual_size,
        "git_blob_sha1": actual_git_blob,
        "file_sha256": sha256_file(DATA_PATH),
        "binary_downloaded": True,
        "decoded_in_downloader": False,
        "row_values_inspected_in_downloader": False,
        "outcome_values_inspected_in_downloader": False,
        "s2_accessed": False,
        "s3_accessed": False,
        "raw_data_persisted_to_repository": False,
        "implementation_seal_access_state_was_pre_download": implementation["access_state_at_seal"]["pg15training_downloaded"] is False,
    }
    (AUDIT_DIR / "pricing_game_source_binary_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
