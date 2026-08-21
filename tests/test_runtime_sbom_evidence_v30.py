from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "action_results/v30/runtime_sbom_result.json"
SECURITY = ROOT / "action_results/v30/runtime_security_summary.json"
LOCK = ROOT / "action_results/v30/runtime-lock-v30.txt"
AUDIT = ROOT / "action_results/v30/pip_audit.json"
SBOM = ROOT / "action_results/v30/runtime_sbom.cdx.json"
SBOM_VERIFY = ROOT / "action_results/v30/sbom_attestation_verification.json"


class TestRuntimeSbomEvidenceV30(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))
        cls.security = json.loads(SECURITY.read_text(encoding="utf-8"))
        cls.audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        cls.sbom = json.loads(SBOM.read_text(encoding="utf-8"))
        cls.sbom_verification = json.loads(SBOM_VERIFY.read_text(encoding="utf-8"))
        cls.lock_lines = [line.strip() for line in LOCK.read_text().splitlines() if line.strip()]

    def test_runtime_inventory_counts_align(self) -> None:
        self.assertEqual(len(self.lock_lines), 23)
        self.assertEqual(self.result["runtime_lock_distribution_count"], 23)
        self.assertEqual(self.result["audited_dependency_count"], 23)
        self.assertEqual(self.result["cyclonedx_component_count"], 23)
        self.assertEqual(self.security["runtime_lock_distribution_count"], 23)
        self.assertEqual(self.security["dependency_records"], 23)
        self.assertEqual(self.security["cyclonedx_component_count"], 23)
        self.assertEqual(len(self.audit["dependencies"]), 23)
        self.assertEqual(len(self.sbom["components"]), 23)
        self.assertFalse(any(line.lower().startswith("pip==") for line in self.lock_lines))

    def test_zero_known_vulnerability_gate(self) -> None:
        self.assertEqual(self.result["status"], "V30_RUNTIME_SBOM_AND_VULNERABILITY_GATE_PASS")
        self.assertEqual(self.result["known_vulnerability_count"], 0)
        self.assertEqual(self.security["known_vulnerability_count"], 0)
        self.assertEqual(self.security["vulnerabilities"], [])
        self.assertTrue(all(dep.get("vulns") == [] for dep in self.audit["dependencies"]))
        self.assertEqual(self.result["audit_tool"], "pip-audit 2.10.1")

    def test_cyclonedx_sbom_and_attestation(self) -> None:
        self.assertEqual(self.sbom["bomFormat"], "CycloneDX")
        self.assertEqual(self.result["cyclonedx_spec_version"], "1.4")
        self.assertEqual(self.sbom["specVersion"], "1.4")
        self.assertEqual(self.result["sbom_predicate_type"], "https://cyclonedx.org/bom")
        self.assertEqual(self.result["sbom_verification_records"], 1)
        self.assertGreater(len(self.sbom_verification), 0)
        verification_text = json.dumps(self.sbom_verification, sort_keys=True)
        self.assertIn("https://cyclonedx.org/bom", verification_text)
        self.assertIn(self.result["release_archive_sha256"], verification_text)

    def test_attested_release_identity_and_governance(self) -> None:
        self.assertEqual(
            self.result["release_archive_sha256"],
            "bbc7fd49dcd1ef05080afcfbb70e830dd9eb67ac66de4a3f9f2a9e311e194f45",
        )
        self.assertEqual(self.result["release_archive_bytes"], 386607)
        self.assertEqual(self.result["build_provenance_attestation_id"], "42234539")
        self.assertEqual(self.result["sbom_attestation_id"], "42234544")
        self.assertEqual(self.result["provenance_verification_records"], 1)
        self.assertEqual(self.result["governance_status"], "HOLD_SHADOW_ONLY")

    def test_security_boundary_is_not_overclaimed(self) -> None:
        boundary = self.result["security_boundary"].lower()
        self.assertIn("known vulnerability", boundary)
        self.assertIn("neither is static code analysis", boundary)
        self.assertIn("malicious-package detection", boundary)
        self.assertIn("pricing model", boundary)


if __name__ == "__main__":
    unittest.main()
