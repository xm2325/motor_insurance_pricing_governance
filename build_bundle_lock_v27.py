from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from deployment.provenance import sha256_file, verify_bundle_lock, write_bundle_lock
from run_spanish_oot_2024 import DATA_PATH


ROOT = Path("deployment_artifacts")
MANIFEST_PATH = ROOT / "manifest.json"
DATASET_ID = "sw4jmdb2sm"
DATASET_VERSION = 1


def git_sha() -> str:
    github_sha = os.environ.get("GITHUB_SHA")
    if github_sha:
        return github_sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def main() -> None:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(
            "Build the v0.26 hybrid deployment bundle before creating the v0.27 lock"
        )
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Missing audited source dataset: {DATA_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("governance_status") != "HOLD_SHADOW_ONLY":
        raise RuntimeError("v0.27 must not change the shadow-only governance decision")
    if manifest.get("serialization", {}).get("format") != (
        "hybrid_sklearn_joblib_plus_xgboost_native_ubj"
    ):
        raise RuntimeError("v0.27 expects the validated v0.26 hybrid model-IO bundle")

    manifest["bundle_contract_version"] = "0.27"
    manifest["integrity"] = {
        "lockfile": "bundle.lock.json",
        "lock_version": "0.27",
        "verification_before_model_deserialization": True,
        "scope": "content_addressed_integrity_not_cryptographic_signature",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    source_provenance = {
        "provider": "Mendeley Data",
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "portfolio_file": DATA_PATH.name,
        "portfolio_file_bytes": DATA_PATH.stat().st_size,
        "portfolio_file_sha256": sha256_file(DATA_PATH),
    }
    build_provenance = {
        "repository": "xm2325/motor_insurance_pricing_governance",
        "code_sha": git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_workflow": os.environ.get("GITHUB_WORKFLOW"),
        "builder": "build_deployment_bundle_v21.py + build_bundle_lock_v27.py",
    }

    lock = write_bundle_lock(
        ROOT,
        manifest,
        source_provenance=source_provenance,
        build_provenance=build_provenance,
    )
    report = verify_bundle_lock(ROOT)
    summary = {
        "status": "V27_CONTENT_ADDRESSED_LOCK_CREATED",
        "governance_status": manifest["governance_status"],
        "bundle_contract_version": manifest["bundle_contract_version"],
        "lock_digest_sha256": lock["lock_digest_sha256"],
        "artifact_count": report.artifact_count,
        "total_locked_bytes": report.total_locked_bytes,
        "source_provenance": source_provenance,
        "build_provenance": build_provenance,
        "integrity_boundary": lock["integrity_boundary"],
    }
    (ROOT / "bundle_integrity_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
