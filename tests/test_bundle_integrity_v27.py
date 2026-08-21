from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deployment.bundle import ShadowModelBundle
from deployment.contracts import feature_contract_hash
from deployment.environment import capture_model_environment
from deployment.provenance import (
    LOCK_FILENAME,
    build_bundle_lock_payload,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
    verify_bundle_lock,
    write_bundle_lock,
)


class TestBundleIntegrityV27(unittest.TestCase):
    def _minimal_root(self, directory: str, with_model: bool = False) -> tuple[Path, dict]:
        root = Path(directory)
        manifest = {
            "bundle_contract_version": "0.27",
            "model_version": "test-shadow",
            "governance_status": "HOLD_SHADOW_ONLY",
            "feature_contract_hash": feature_contract_hash(),
            "training_environment": capture_model_environment(),
            "models": {},
        }
        if with_model:
            artifact = root / "dummy.joblib"
            artifact.write_bytes(b"not-a-real-joblib-object")
            manifest["models"] = {
                "dummy": {
                    "serialization": "joblib_pipeline",
                    "artifact": artifact.name,
                    "sha256": sha256_file(artifact),
                }
            }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (root / "parity_reference.json").write_text(
            json.dumps({"records": [], "scores": []}, indent=2), encoding="utf-8"
        )
        (root / "serialization_parity_summary.json").write_text(
            json.dumps({"status": "TEST"}, indent=2), encoding="utf-8"
        )
        write_bundle_lock(
            root,
            manifest,
            source_provenance={"dataset_id": "test", "sha256": "0" * 64},
            build_provenance={"code_sha": "test"},
        )
        return root, manifest

    def test_clean_lock_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self._minimal_root(directory)
            report = verify_bundle_lock(root)
            self.assertEqual(report.status, "CONTENT_ADDRESSED_BUNDLE_VERIFIED")
            self.assertEqual(report.artifact_count, 3)
            self.assertIn("manifest.json", report.verified_paths)

    def test_artifact_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self._minimal_root(directory)
            path = root / "parity_reference.json"
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaisesRegex(RuntimeError, "size mismatch|hash mismatch"):
                verify_bundle_lock(root)

    def test_missing_locked_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self._minimal_root(directory)
            (root / "serialization_parity_summary.json").unlink()
            with self.assertRaisesRegex(RuntimeError, "artifact is missing"):
                verify_bundle_lock(root)

    def test_lock_self_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self._minimal_root(directory)
            path = root / LOCK_FILENAME
            document = json.loads(path.read_text(encoding="utf-8"))
            document["governance_status"] = "PROMOTE"
            path.write_text(json.dumps(document, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "self-digest mismatch"):
                verify_bundle_lock(root)

    def test_path_traversal_is_rejected_even_with_valid_self_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = {
                "lock_version": "0.27",
                "bundle_contract_version": "0.27",
                "model_version": "test",
                "governance_status": "HOLD_SHADOW_ONLY",
                "feature_contract_hash": feature_contract_hash(),
                "source_provenance": {},
                "build_provenance": {},
                "artifacts": [
                    {"path": "../outside", "kind": "bad", "bytes": 1, "sha256": "0" * 64}
                ],
                "integrity_boundary": "test",
            }
            document = {
                **payload,
                "lock_digest_sha256": sha256_bytes(canonical_json_bytes(payload)),
            }
            (root / LOCK_FILENAME).write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Unsafe bundle artifact path"):
                verify_bundle_lock(root)

    def test_loader_rejects_tamper_before_joblib_deserialization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self._minimal_root(directory, with_model=True)
            artifact = root / "dummy.joblib"
            artifact.write_bytes(artifact.read_bytes() + b"tamper")
            with patch("deployment.bundle.joblib.load") as mocked_load:
                with self.assertRaisesRegex(RuntimeError, "size mismatch|hash mismatch"):
                    ShadowModelBundle.load(root)
                mocked_load.assert_not_called()

    def test_builder_rejects_missing_core_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._minimal_root(directory)
            (root / "parity_reference.json").unlink()
            with self.assertRaises(FileNotFoundError):
                build_bundle_lock_payload(
                    root,
                    manifest,
                    source_provenance={},
                    build_provenance={},
                )


if __name__ == "__main__":
    unittest.main()
