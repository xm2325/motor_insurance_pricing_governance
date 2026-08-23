from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V37 = ROOT / "RESULTS_V37.md"
V38 = ROOT / "RESULTS_V38.md"


class ExternalReproducibilityDocsV38Tests(unittest.TestCase):
    def test_v37_uses_authoritative_main_point_result(self) -> None:
        text = V37.read_text(encoding="utf-8")
        self.assertIn("129.8409", text)
        self.assertIn("+11.4639%", text)
        self.assertIn("32633520755", text)
        self.assertIn("must **not** be described as having exact pure-premium point-metric reproducibility", text)

    def test_v38_keeps_both_observed_point_results(self) -> None:
        text = V38.read_text(encoding="utf-8")
        self.assertIn("126.220469", text)
        self.assertIn("129.840909", text)
        self.assertIn("decision is reproducible", text)
        self.assertIn("does not establish a unique causal mechanism", text)

    def test_no_document_claims_runner_variation_changed_gate(self) -> None:
        text = V37.read_text(encoding="utf-8") + "\n" + V38.read_text(encoding="utf-8")
        self.assertIn("NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT", text)
        self.assertIn("NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT", text)
        self.assertIn("HOLD_SHADOW_ONLY", text)


if __name__ == "__main__":
    unittest.main()
