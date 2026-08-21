from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "action_results/v27/bundle_integrity_result.json"
EXPECTED_SOURCE_SHA256 = "6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4"


class TestBundleIntegrityEvidenceV27(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_status_and_governance_boundary(self) -> None:
        self.assertEqual(self.result["status"], "V27_CONTENT_ADDRESSED_BUNDLE_PASS")
        self.assertEqual(
            self.result["container"]["governance_status"], "HOLD_SHADOW_ONLY"
        )
        self.assertIn("HOLD_SHADOW_ONLY", self.result["governance_boundary"])

    def test_lock_covers_expected_artifacts_and_source(self) -> None:
        lock = self.result["bundle_lock"]
        self.assertEqual(lock["lock_version"], "0.27")
        self.assertEqual(lock["artifact_count"], 9)
        self.assertGreater(lock["total_locked_bytes"], 1_000_000)
        self.assertEqual(
            lock["source_provenance"]["portfolio_file_sha256"],
            EXPECTED_SOURCE_SHA256,
        )
        self.assertEqual(lock["source_provenance"]["dataset_id"], "sw4jmdb2sm")
        self.assertEqual(lock["source_provenance"]["dataset_version"], 1)
        self.assertEqual(len(lock["lock_digest_sha256"]), 64)

    def test_container_same_fit_parity_is_exact(self) -> None:
        container = self.result["container"]
        self.assertEqual(
            container["status"], "V27_CONTAINER_INTEGRITY_AND_HTTP_PARITY_PASS"
        )
        self.assertEqual(container["bundle_integrity"], "CONTENT_ADDRESSED_BUNDLE_VERIFIED")
        self.assertEqual(container["environment_compatibility"], "HYBRID_MODEL_IO_COMPATIBLE")
        self.assertEqual(container["records_tested"], 25)
        self.assertEqual(container["fields_per_record"], 4)
        self.assertEqual(container["comparisons"], 100)
        self.assertEqual(container["max_absolute_error"], 0.0)

    def test_three_deliberate_tamper_cases_fail_closed(self) -> None:
        tamper = self.result["tamper_tests"]
        self.assertEqual(tamper["status"], "V27_TAMPER_TESTS_PASS")
        self.assertEqual(tamper["case_count"], 3)
        self.assertEqual(
            set(tamper["cases"]),
            {
                "model_artifact_byte_tamper",
                "missing_locked_artifact",
                "lock_self_tamper",
            },
        )
        for case in tamper["cases"].values():
            self.assertEqual(case["status"], "FAIL_CLOSED_AS_EXPECTED")

    def test_integrity_boundary_does_not_claim_signature(self) -> None:
        boundary = self.result["integrity_boundary"].lower()
        self.assertIn("not a cryptographic signature", boundary)
        self.assertIn("replace both artifacts and lockfile", boundary)


if __name__ == "__main__":
    unittest.main()
