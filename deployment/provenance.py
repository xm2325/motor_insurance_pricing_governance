from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOCK_VERSION = "0.27"
LOCK_FILENAME = "bundle.lock.json"


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or value.strip() == "":
        raise RuntimeError(f"Unsafe bundle artifact path: {value!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"Unsafe bundle artifact path: {value!r}")
    return path


def model_artifact_paths(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    artifacts: list[tuple[str, str]] = []
    for model_name, metadata in manifest.get("models", {}).items():
        mode = metadata.get("serialization", "joblib_pipeline")
        if mode == "joblib_pipeline":
            artifacts.append((metadata["artifact"], f"model:{model_name}:joblib_pipeline"))
            continue
        if mode == "sklearn_preprocessor_plus_xgboost_ubj":
            artifacts.append(
                (
                    metadata["preprocessor_artifact"],
                    f"model:{model_name}:sklearn_preprocessor",
                )
            )
            artifacts.append(
                (
                    metadata["native_model_artifact"],
                    f"model:{model_name}:xgboost_ubjson",
                )
            )
            continue
        raise RuntimeError(f"Unsupported serialization mode in provenance builder: {mode}")
    return artifacts


def build_bundle_lock_payload(
    root: Path,
    manifest: dict[str, Any],
    *,
    source_provenance: dict[str, Any],
    build_provenance: dict[str, Any],
) -> dict[str, Any]:
    requested: list[tuple[str, str]] = [
        ("manifest.json", "bundle_manifest"),
        ("parity_reference.json", "same_fit_parity_reference"),
        ("serialization_parity_summary.json", "same_fit_serialization_evidence"),
        *model_artifact_paths(manifest),
    ]
    seen: set[str] = set()
    artifacts: list[dict[str, Any]] = []
    for relative, kind in requested:
        safe = _safe_relative_path(relative)
        key = safe.as_posix()
        if key in seen:
            continue
        seen.add(key)
        path = root / safe
        if not path.is_file():
            raise FileNotFoundError(f"Cannot lock missing bundle artifact: {path}")
        artifacts.append(
            {
                "path": key,
                "kind": kind,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    return {
        "lock_version": LOCK_VERSION,
        "bundle_contract_version": str(manifest.get("bundle_contract_version")),
        "model_version": manifest.get("model_version"),
        "governance_status": manifest.get("governance_status"),
        "feature_contract_hash": manifest.get("feature_contract_hash"),
        "source_provenance": source_provenance,
        "build_provenance": build_provenance,
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "integrity_boundary": (
            "Content-addressed integrity contract. Detects missing or modified locked files when "
            "this lockfile digest is trusted; it is not a cryptographic signature and does not "
            "claim resistance to an attacker who can replace both artifacts and lockfile."
        ),
    }


def write_bundle_lock(
    root: Path,
    manifest: dict[str, Any],
    *,
    source_provenance: dict[str, Any],
    build_provenance: dict[str, Any],
) -> dict[str, Any]:
    payload = build_bundle_lock_payload(
        root,
        manifest,
        source_provenance=source_provenance,
        build_provenance=build_provenance,
    )
    lock_digest = sha256_bytes(canonical_json_bytes(payload))
    document = {**payload, "lock_digest_sha256": lock_digest}
    (root / LOCK_FILENAME).write_text(json.dumps(document, indent=2), encoding="utf-8")
    return document


@dataclass(frozen=True)
class BundleIntegrityReport:
    status: str
    lock_digest_sha256: str
    artifact_count: int
    total_locked_bytes: int
    verified_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "lock_digest_sha256": self.lock_digest_sha256,
            "artifact_count": self.artifact_count,
            "total_locked_bytes": self.total_locked_bytes,
            "verified_paths": list(self.verified_paths),
        }


def verify_bundle_lock(root: str | Path) -> BundleIntegrityReport:
    root = Path(root)
    lock_path = root / LOCK_FILENAME
    if not lock_path.is_file():
        raise RuntimeError(f"Missing required content-addressed bundle lock: {lock_path}")
    document = json.loads(lock_path.read_text(encoding="utf-8"))
    expected_digest = document.get("lock_digest_sha256")
    if not isinstance(expected_digest, str):
        raise RuntimeError("Bundle lock is missing lock_digest_sha256")
    payload = {key: value for key, value in document.items() if key != "lock_digest_sha256"}
    observed_digest = sha256_bytes(canonical_json_bytes(payload))
    if observed_digest != expected_digest:
        raise RuntimeError(
            f"Bundle lock self-digest mismatch: {observed_digest} != {expected_digest}"
        )
    if document.get("lock_version") != LOCK_VERSION:
        raise RuntimeError(
            f"Unsupported bundle lock version: {document.get('lock_version')} != {LOCK_VERSION}"
        )

    verified: list[str] = []
    total_bytes = 0
    for artifact in document.get("artifacts", []):
        if not isinstance(artifact, dict):
            raise RuntimeError("Malformed artifact entry in bundle lock")
        relative = _safe_relative_path(str(artifact.get("path", "")))
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"Locked bundle artifact is missing: {relative.as_posix()}")
        observed_bytes = path.stat().st_size
        expected_bytes = int(artifact.get("bytes", -1))
        if observed_bytes != expected_bytes:
            raise RuntimeError(
                f"Locked artifact size mismatch for {relative.as_posix()}: "
                f"{observed_bytes} != {expected_bytes}"
            )
        observed_hash = sha256_file(path)
        expected_hash = str(artifact.get("sha256", ""))
        if observed_hash != expected_hash:
            raise RuntimeError(
                f"Locked artifact hash mismatch for {relative.as_posix()}: "
                f"{observed_hash} != {expected_hash}"
            )
        verified.append(relative.as_posix())
        total_bytes += observed_bytes

    if not verified:
        raise RuntimeError("Bundle lock contains no artifacts")
    return BundleIntegrityReport(
        status="CONTENT_ADDRESSED_BUNDLE_VERIFIED",
        lock_digest_sha256=expected_digest,
        artifact_count=len(verified),
        total_locked_bytes=total_bytes,
        verified_paths=tuple(sorted(verified)),
    )
