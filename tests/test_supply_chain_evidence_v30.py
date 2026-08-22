from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "action_results/v30/runtime_supply_chain_result.json"
POLICY = ROOT / "action_results/v30/supply_chain_policy_result.json"
PARITY = ROOT / "action_results/v30/runtime_http_parity.json"
VEX = ROOT / "action_results/v30/vex_v30.json"
STATUS = ROOT / "action_results/v30/ACTION_V30_STATUS.json"


class TestSupplyChainEvidenceV30(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.parity = json.loads(PARITY.read_text(encoding="utf-8"))
        cls.vex = json.loads(VEX.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS.read_text(encoding="utf-8"))

    def test_action_and_governance_status(self) -> None:
        self.assertEqual(self.status["status"], "success")
        self.assertEqual(self.result["status"], "V30_RUNTIME_SBOM_SECURITY_PASS")
        self.assertEqual(self.result["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(self.result["security_policy_status"], "V30_SUPPLY_CHAIN_POLICY_PASS")

    def test_runtime_sbom_and_cpu_boundary(self) -> None:
        self.assertEqual(self.result["runtime_image_architecture"], "amd64")
        self.assertEqual(self.result["sbom_component_count"], 112)
        self.assertGreater(self.result["runtime_image_bytes"], 0)
        self.assertEqual(self.policy["sbom"]["xgboost_components"], ["xgboost-cpu"])
        self.assertEqual(self.policy["sbom"]["forbidden_packages_present"], [])

    def test_vulnerability_gate(self) -> None:
        self.assertEqual(self.result["high_total"], 14)
        self.assertEqual(self.result["high_fixable"], 0)
        self.assertEqual(self.result["critical_total"], 3)
        self.assertEqual(self.result["critical_fixable"], 0)
        self.assertEqual(self.result["critical_vex_covered"], 3)
        self.assertEqual(self.result["critical_unreviewed"], 0)
        self.assertEqual(self.result["high_unfixed"], 14)
        self.assertEqual(self.result["vex_expires_on"], "2026-09-30")

    def test_vex_is_exact_and_time_limited(self) -> None:
        self.assertEqual(self.vex["format"], "project-vex-v1")
        self.assertEqual(self.vex["expires_on"], "2026-09-30")
        statements = {(s["vulnerability"], s["package"]) for s in self.vex["statements"]}
        self.assertEqual(
            statements,
            {
                ("CVE-2026-13221", "perl-base"),
                ("CVE-2026-42496", "perl-base"),
                ("CVE-2026-8376", "perl-base"),
            },
        )
        self.assertTrue(all(s["status"] == "not_affected" for s in self.vex["statements"]))

    def test_shadow_scoring_parity_survives_security_remediation(self) -> None:
        self.assertEqual(self.parity["status"], "V30_RUNTIME_HTTP_PARITY_PASS")
        self.assertEqual(self.parity["comparisons"], 100)
        self.assertEqual(self.parity["max_absolute_error"], 0.0)
        self.assertEqual(self.parity["bundle_integrity"], "CONTENT_ADDRESSED_BUNDLE_VERIFIED")

    def test_sbom_attestation_verified(self) -> None:
        self.assertTrue(self.result["sbom_attestation_verify_success"])
        self.assertTrue(str(self.result["sbom_attestation_id"]).strip())
        self.assertEqual(len(self.result["runtime_archive_sha256"]), 64)
        self.assertEqual(len(self.result["sbom_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
