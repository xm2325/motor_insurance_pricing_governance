from __future__ import annotations

import unittest

from evaluate_supply_chain_v30 import evaluate


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

    def test_clean_runtime_passes(self):
        result = evaluate(self._sbom(), {"Results": []})
        self.assertEqual(result["status"], "V30_SUPPLY_CHAIN_POLICY_PASS")
        self.assertEqual(result["vulnerability_policy"]["critical_total"], 0)

    def test_forbidden_dev_package_rejects(self):
        sbom = self._sbom()
        sbom["components"].append({"type": "library", "name": "pytest", "version": "9.0"})
        with self.assertRaisesRegex(AssertionError, "Forbidden"):
            evaluate(sbom, {"Results": []})

    def test_critical_vulnerability_rejects_even_without_fix(self):
        scan = {
            "Results": [
                {
                    "Target": "python-pkg",
                    "Class": "lang-pkgs",
                    "Type": "python-pkg",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-TEST-CRITICAL",
                            "PkgName": "demo",
                            "InstalledVersion": "1.0",
                            "FixedVersion": "",
                            "Severity": "CRITICAL",
                        }
                    ],
                }
            ]
        }
        with self.assertRaises(RuntimeError):
            evaluate(self._sbom(), scan)

    def test_fixable_high_rejects(self):
        scan = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-TEST-HIGH",
                            "PkgName": "demo",
                            "InstalledVersion": "1.0",
                            "FixedVersion": "1.1",
                            "Severity": "HIGH",
                        }
                    ]
                }
            ]
        }
        with self.assertRaises(RuntimeError):
            evaluate(self._sbom(), scan)

    def test_unfixed_high_is_recorded_but_does_not_fail_demo_gate(self):
        scan = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-TEST-HIGH-UNFIXED",
                            "PkgName": "demo",
                            "InstalledVersion": "1.0",
                            "FixedVersion": "",
                            "Severity": "HIGH",
                        }
                    ]
                }
            ]
        }
        result = evaluate(self._sbom(), scan)
        self.assertEqual(result["status"], "V30_SUPPLY_CHAIN_POLICY_PASS")
        self.assertEqual(result["vulnerability_policy"]["high_unfixed"], 1)


if __name__ == "__main__":
    unittest.main()
