from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "action_results/v30/attested_release_admission_summary.json"
STATUS_PATH = ROOT / "action_results/v30/ACTION_V30_STATUS.json"


class TestReleaseAdmissionEvidenceV30(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))

    def test_workflow_persisted_success(self) -> None:
        self.assertEqual(self.status["status"], "success")
        self.assertEqual(
            self.status["workflow"],
            "Motor pricing attested release admission v0.30",
        )

    def test_admission_is_shadow_registry_only(self) -> None:
        self.assertEqual(
            self.summary["status"],
            "V30_ATTESTED_RELEASE_ADMISSION_POLICY_PASS",
        )
        admission = self.summary["admission"]
        self.assertEqual(admission["status"], "V30_ATTESTED_RELEASE_ADMISSION_PASS")
        self.assertEqual(admission["decision"], "ADMIT_TO_SHADOW_REGISTRY_ONLY")
        self.assertEqual(admission["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(
            self.summary["governance_boundary"],
            "HOLD / HOLD_SHADOW_ONLY remains unchanged",
        )

    def test_attestation_identity_is_bound_to_expected_build_policy(self) -> None:
        identity = self.summary["admission"]["attestation_identity"]
        archive = self.summary["admission"]["archive"]
        self.assertEqual(identity["subject_sha256"], archive["sha256"])
        self.assertEqual(identity["repository"], "xm2325/motor_insurance_pricing_governance")
        self.assertEqual(
            identity["workflow_name"],
            "Motor pricing attested release admission v0.30",
        )
        self.assertEqual(identity["workflow_path"], ".github/workflows/v30-admission.yml")
        self.assertEqual(identity["predicate_type"], "https://slsa.dev/provenance/v1")
        self.assertEqual(
            identity["build_type"],
            "https://actions.github.io/buildtypes/workflow/v1",
        )
        self.assertGreaterEqual(identity["verified_timestamp_count"], 1)
        self.assertEqual(len(identity["source_commit_sha"]), 40)

    def test_archive_and_inner_bundle_boundaries(self) -> None:
        admission = self.summary["admission"]
        archive = admission["archive"]
        inner = admission["inner_bundle"]
        self.assertEqual(archive["raw_source_data_members"], 0)
        self.assertGreaterEqual(archive["member_count"], 3)
        self.assertEqual(inner["integrity_status"], "CONTENT_ADDRESSED_BUNDLE_VERIFIED")
        self.assertEqual(inner["artifact_count"], 9)
        self.assertGreater(inner["total_locked_bytes"], 0)
        self.assertEqual(inner["bundle_contract_version"], "0.27")
        self.assertEqual(inner["dataset_id"], "sw4jmdb2sm")
        self.assertEqual(inner["dataset_version"], 1)

    def test_negative_admission_cases_all_fail_closed(self) -> None:
        negative = self.summary["negative_tests"]
        self.assertEqual(negative["status"], "V30_NEGATIVE_ADMISSION_TESTS_PASS")
        self.assertEqual(negative["negative_case_count"], 3)
        self.assertTrue(negative["tampered_archive_attestation_rejected"])
        self.assertTrue(negative["wrong_repository_attestation_rejected"])
        self.assertTrue(negative["wrong_workflow_identity_rejected"])


if __name__ == "__main__":
    unittest.main()
