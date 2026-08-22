from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from deployment.provenance import verify_bundle_lock


EXPECTED_REPOSITORY = "xm2325/motor_insurance_pricing_governance"
EXPECTED_WORKFLOW_NAME = "Motor pricing attested release admission v0.30"
EXPECTED_WORKFLOW_PATH = ".github/workflows/v30-admission.yml"
EXPECTED_GOVERNANCE = "HOLD_SHADOW_ONLY"
FORBIDDEN_ARCHIVE_TOKENS = (
    "Dataset_of_motor_insurance_portfolio.csv",
    "data_spanish_2022_2024",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _attestation_identity(
    verification: list[dict[str, Any]],
    *,
    archive_name: str,
    archive_sha256: str,
    expected_repository: str,
    expected_workflow_name: str,
    expected_workflow_path: str,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for record in verification:
        result = record.get("verificationResult", {})
        statement = result.get("statement", {})
        subjects = statement.get("subject", [])
        certificate = result.get("signature", {}).get("certificate", {})
        predicate = statement.get("predicate", {})
        workflow = (
            predicate.get("buildDefinition", {})
            .get("externalParameters", {})
            .get("workflow", {})
        )
        subject_match = any(
            str(subject.get("name")) == archive_name
            and str(subject.get("digest", {}).get("sha256")) == archive_sha256
            for subject in subjects
            if isinstance(subject, dict)
        )
        if not subject_match:
            continue
        if certificate.get("githubWorkflowRepository") != expected_repository:
            continue
        if certificate.get("githubWorkflowName") != expected_workflow_name:
            continue
        if workflow.get("path") != expected_workflow_path:
            continue
        repository_url = f"https://github.com/{expected_repository}"
        if workflow.get("repository") != repository_url:
            continue
        source_commit = certificate.get("sourceRepositoryDigest")
        if not isinstance(source_commit, str) or len(source_commit) != 40:
            continue
        matches.append(
            {
                "subject_sha256": archive_sha256,
                "repository": expected_repository,
                "workflow_name": expected_workflow_name,
                "workflow_path": expected_workflow_path,
                "workflow_ref": certificate.get("githubWorkflowRef"),
                "source_commit_sha": source_commit,
                "source_repository_visibility": certificate.get(
                    "sourceRepositoryVisibilityAtSigning"
                ),
                "runner_environment": certificate.get("runnerEnvironment"),
                "verified_timestamp_count": len(result.get("verifiedTimestamps", [])),
                "predicate_type": statement.get("predicateType"),
                "build_type": predicate.get("buildDefinition", {}).get("buildType"),
            }
        )
    if not matches:
        raise RuntimeError(
            "No verified attestation record binds the exact archive digest to the expected "
            "repository and v0.30 workflow identity"
        )
    if len(matches) != 1:
        raise RuntimeError(f"Expected one admission attestation match, found {len(matches)}")
    return matches[0]


def _validate_archive_members(path: Path) -> list[str]:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names: list[str] = []
        for member in members:
            member_path = Path(member.name)
            if member_path.is_absolute() or any(part in {"", ".", ".."} for part in member_path.parts):
                raise RuntimeError(f"Unsafe archive member path: {member.name!r}")
            if member.issym() or member.islnk():
                raise RuntimeError(f"Archive links are not allowed: {member.name!r}")
            if any(token in member.name for token in FORBIDDEN_ARCHIVE_TOKENS):
                raise RuntimeError(f"Raw source data token found in release archive: {member.name}")
            names.append(member.name)
    required = {
        "deployment_artifacts/bundle.lock.json",
        "deployment_artifacts/manifest.json",
        "deployment_artifacts/parity_reference.json",
    }
    missing = required.difference(names)
    if missing:
        raise RuntimeError(f"Release archive is missing required members: {sorted(missing)}")
    return names


def verify_release_admission(
    archive_path: str | Path,
    verification_path: str | Path,
    *,
    expected_repository: str = EXPECTED_REPOSITORY,
    expected_workflow_name: str = EXPECTED_WORKFLOW_NAME,
    expected_workflow_path: str = EXPECTED_WORKFLOW_PATH,
) -> dict[str, Any]:
    archive_path = Path(archive_path)
    verification_path = Path(verification_path)
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    if not isinstance(verification, list) or not verification:
        raise RuntimeError("Attestation verification output is empty or malformed")

    archive_sha = sha256_file(archive_path)
    identity = _attestation_identity(
        verification,
        archive_name=archive_path.name,
        archive_sha256=archive_sha,
        expected_repository=expected_repository,
        expected_workflow_name=expected_workflow_name,
        expected_workflow_path=expected_workflow_path,
    )
    members = _validate_archive_members(archive_path)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(root, filter="data")
        bundle = root / "deployment_artifacts"
        integrity = verify_bundle_lock(bundle)
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        lock = json.loads((bundle / "bundle.lock.json").read_text(encoding="utf-8"))
        if manifest.get("governance_status") != EXPECTED_GOVERNANCE:
            raise RuntimeError(
                f"Attested release governance is not shadow-only: {manifest.get('governance_status')}"
            )
        if lock.get("governance_status") != EXPECTED_GOVERNANCE:
            raise RuntimeError("Inner bundle lock governance does not remain HOLD_SHADOW_ONLY")
        source = lock.get("source_provenance", {})
        if source.get("dataset_id") != "sw4jmdb2sm" or source.get("dataset_version") != 1:
            raise RuntimeError("Unexpected source-data provenance inside attested release")

        result = {
            "status": "V30_ATTESTED_RELEASE_ADMISSION_PASS",
            "decision": "ADMIT_TO_SHADOW_REGISTRY_ONLY",
            "governance_status": EXPECTED_GOVERNANCE,
            "archive": {
                "name": archive_path.name,
                "bytes": archive_path.stat().st_size,
                "sha256": archive_sha,
                "member_count": len(members),
                "raw_source_data_members": 0,
            },
            "attestation_identity": identity,
            "inner_bundle": {
                "integrity_status": integrity.status,
                "lock_digest_sha256": integrity.lock_digest_sha256,
                "artifact_count": integrity.artifact_count,
                "total_locked_bytes": integrity.total_locked_bytes,
                "model_version": manifest.get("model_version"),
                "bundle_contract_version": manifest.get("bundle_contract_version"),
                "dataset_id": source.get("dataset_id"),
                "dataset_version": source.get("dataset_version"),
            },
            "admission_boundary": (
                "Admission authorises only entry to the shadow release registry. It does not "
                "promote the model family, change customer pricing, or establish production safety."
            ),
        }
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("verification_json")
    parser.add_argument("--out", default="results_v30/release_admission_result.json")
    args = parser.parse_args()
    result = verify_release_admission(args.archive, args.verification_json)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
