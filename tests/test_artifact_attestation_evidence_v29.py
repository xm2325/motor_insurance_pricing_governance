from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "action_results/v29/artifact_attestation_result.json"
VERIFY_PATH = ROOT / "action_results/v29/attestation_verification.json"


class TestArtifactAttestationEvidenceV29(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        cls.verification = json.loads(VERIFY_PATH.read_text(encoding="utf-8"))
        cls.verification_text = json.dumps(cls.verification, sort_keys=True)

    def test_attestation_status_and_subject(self) -> None:
        self.assertEqual(self.result["status"], "V29_GITHUB_ARTIFACT_ATTESTATION_PASS")
        self.assertEqual(
            self.result["subject"], "dist/motor-pricing-shadow-bundle-v29.tar.gz"
        )
        self.assertEqual(self.result["subject_bytes"], 386598)
        self.assertEqual(len(self.result["subject_sha256"]), 64)
        self.assertEqual(
            self.result["subject_sha256"],
            "14866b170f3737193f7e46c9997a532d3d2a0fdd9e1223f9dbd240617548bfbf",
        )

    def test_github_cli_verification_succeeded(self) -> None:
        self.assertTrue(self.result["gh_attestation_verify_success"])
        self.assertEqual(self.result["verification_records"], 1)
        self.assertIsInstance(self.verification, list)
        self.assertGreater(len(self.verification), 0)

    def test_verification_material_binds_subject_repo_workflow_and_commit(self) -> None:
        self.assertIn(self.result["subject_sha256"], self.verification_text)
        self.assertIn("xm2325/motor_insurance_pricing_governance", self.verification_text)
        self.assertIn("v29-attestation.yml", self.verification_text)
        self.assertIn(self.result["commit_sha"], self.verification_text)

    def test_attestation_identity_and_governance(self) -> None:
        self.assertEqual(self.result["attestation_id"], "42232000")
        self.assertEqual(
            self.result["attestation_url"],
            "https://github.com/xm2325/motor_insurance_pricing_governance/attestations/42232000",
        )
        self.assertEqual(self.result["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(self.result["repository"], "xm2325/motor_insurance_pricing_governance")

    def test_boundary_does_not_claim_model_safety_or_pricing_approval(self) -> None:
        boundary = self.result["provenance_boundary"].lower()
        self.assertIn("build provenance", boundary)
        self.assertIn("does not prove", boundary)
        self.assertIn("approved for customer pricing", boundary)
        self.assertIn("first central", boundary)


if __name__ == "__main__":
    unittest.main()
