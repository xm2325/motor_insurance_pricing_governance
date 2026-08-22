from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from evaluate_supply_chain_v30 import evaluate


TODAY = date(2026, 8, 22)
ROOT = Path(__file__).resolve().parents[1]
TRIVY_ACTION_SHA = "ed142fd0673e97e23eac54620cfb913e5ce36c25"
ATTEST_ACTION_SHA = "508db95dd578ae2727ebd6217d5ba78e4fbda05d"


class TestSupplyChainV30(unittest.TestCase):
    def _sbom(self):
        packages = {
            "numpy": "2.5.2",
            "pandas": "3.0.5",
            "scipy": "1.18.0",
            "scikit-learn": "1.9.0",
            "joblib": "1.5.3",
            "xgboost-cpu": "3.4.0",
            "fastapi": "0.116.1",
            "uvicorn": "0.35.0",
            "pydantic": "2.11.0",
            "starlette": "0.47.0",
            "typing-extensions": "4.14.0",
        }
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "version": 1,
            "components": [
                {"type": "library", "name": name, "version": version}
                for name, version in packages.items()
            ],
        }

    def _vex(self, statements=None, expires_on="2026-09-30"):
        return {
            "format": "project-vex-v1",
            "expires_on": expires_on,
            "statements": statements or [],
        }

    def test_clean_runtime_passes(self):
        result = evaluate(self._sbom(), {"Results": []}, self._vex(), today=TODAY)
        self.assertEqual(result["status"], "V30_SUPPLY_CHAIN_POLICY_PASS")
        self.assertEqual(result["vulnerability_policy"]["critical_total"], 0)

    def test_forbidden_dev_package_rejects(self):
        sbom = self._sbom()
        sbom["components"].append({"type": "library", "name": "pytest", "version": "9.0"})
        with self.assertRaisesRegex(AssertionError, "Forbidden"):
            evaluate(sbom, {"Results": []}, self._vex(), today=TODAY)

    def test_unreviewed_critical_rejects(self):
        scan = {
            "Results": [{"Vulnerabilities": [{
                "VulnerabilityID": "CVE-TEST-CRITICAL",
                "PkgName": "demo",
                "InstalledVersion": "1.0",
                "FixedVersion": "",
                "Severity": "CRITICAL",
            }]}]
        }
        with self.assertRaises(RuntimeError):
            evaluate(self._sbom(), scan, self._vex(), today=TODAY)

    def test_unpatched_critical_with_specific_nonexpired_vex_passes(self):
        scan = {
            "Results": [{"Vulnerabilities": [{
                "VulnerabilityID": "CVE-TEST-CRITICAL",
                "PkgName": "demo",
                "InstalledVersion": "1.0",
                "FixedVersion": "",
                "Severity": "CRITICAL",
            }]}]
        }
        vex = self._vex([{
            "vulnerability": "CVE-TEST-CRITICAL",
            "package": "demo",
            "status": "not_affected",
            "justification": "vulnerable_code_not_in_execute_path",
            "impact_statement": (
                "This synthetic unit-test finding is not reachable from the validated service execution "
                "path; the statement is intentionally long enough to require a substantive rationale."
            ),
        }])
        result = evaluate(self._sbom(), scan, vex, today=TODAY)
        self.assertEqual(result["vulnerability_policy"]["critical_vex_covered"], 1)
        self.assertEqual(result["vulnerability_policy"]["critical_unreviewed"], 0)

    def test_critical_with_published_fix_rejects_even_if_vex_exists(self):
        scan = {
            "Results": [{"Vulnerabilities": [{
                "VulnerabilityID": "CVE-TEST-CRITICAL",
                "PkgName": "demo",
                "InstalledVersion": "1.0",
                "FixedVersion": "1.1",
                "Severity": "CRITICAL",
            }]}]
        }
        vex = self._vex([{
            "vulnerability": "CVE-TEST-CRITICAL",
            "package": "demo",
            "status": "not_affected",
            "justification": "vulnerable_code_not_in_execute_path",
            "impact_statement": (
                "A fix exists, so this statement must not be sufficient to pass the policy even with "
                "a long rationale. The runtime should update instead of relying on VEX."
            ),
        }])
        with self.assertRaises(RuntimeError):
            evaluate(self._sbom(), scan, vex, today=TODAY)

    def test_expired_vex_rejects(self):
        with self.assertRaisesRegex(AssertionError, "VEX expired"):
            evaluate(self._sbom(), {"Results": []}, self._vex(expires_on="2026-08-21"), today=TODAY)

    def test_fixable_high_rejects(self):
        scan = {
            "Results": [{"Vulnerabilities": [{
                "VulnerabilityID": "CVE-TEST-HIGH",
                "PkgName": "demo",
                "InstalledVersion": "1.0",
                "FixedVersion": "1.1",
                "Severity": "HIGH",
            }]}]
        }
        with self.assertRaises(RuntimeError):
            evaluate(self._sbom(), scan, self._vex(), today=TODAY)

    def test_unfixed_high_is_recorded_but_does_not_fail_demo_gate(self):
        scan = {
            "Results": [{"Vulnerabilities": [{
                "VulnerabilityID": "CVE-TEST-HIGH-UNFIXED",
                "PkgName": "demo",
                "InstalledVersion": "1.0",
                "FixedVersion": "",
                "Severity": "HIGH",
            }]}]
        }
        result = evaluate(self._sbom(), scan, self._vex(), today=TODAY)
        self.assertEqual(result["status"], "V30_SUPPLY_CHAIN_POLICY_PASS")
        self.assertEqual(result["vulnerability_policy"]["high_unfixed"], 1)

    def test_supply_chain_actions_are_immutable_pins(self):
        workflow = (ROOT / ".github/workflows/v30-sbom-security.yml").read_text(encoding="utf-8")
        self.assertEqual(workflow.count(f"aquasecurity/trivy-action@{TRIVY_ACTION_SHA}"), 2)
        self.assertIn(f"actions/attest@{ATTEST_ACTION_SHA}", workflow)
        self.assertNotIn("aquasecurity/trivy-action@v0.36.0", workflow)

    def test_repository_vex_has_debian_tracker_references(self):
        vex = json.loads((ROOT / "security/vex_v30.json").read_text(encoding="utf-8"))
        expected = {"CVE-2026-13221", "CVE-2026-42496", "CVE-2026-8376"}
        self.assertEqual({s["vulnerability"] for s in vex["statements"]}, expected)
        for statement in vex["statements"]:
            refs = statement.get("references") or []
            self.assertEqual(
                refs,
                [f"https://security-tracker.debian.org/tracker/{statement['vulnerability']}"],
            )


if __name__ == "__main__":
    unittest.main()
