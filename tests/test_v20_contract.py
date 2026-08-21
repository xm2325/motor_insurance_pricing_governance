from __future__ import annotations

import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "run_v20_governance.py"


class TestV20GovernanceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_versions_v16_to_v20_are_explicit(self) -> None:
        for version in ["v0.16", "v0.17", "v0.18", "v0.20"]:
            self.assertIn(version, self.text)
        self.assertIn("v19_model_complexity.csv", self.text)

    def test_same_locked_temporal_partitions_are_reused(self) -> None:
        self.assertIn('df[df["year"] == 2022]', self.text)
        self.assertIn('df[df["year"] == 2023]', self.text)
        self.assertIn('df[df["year"] == 2024]', self.text)

    def test_coverage_premiums_are_audit_only(self) -> None:
        self.assertIn("Coverage premium fields are used only to construct an audit coverage-exposure proxy", self.text)
        self.assertIn("from run_spanish_oot_2024 import", self.text)
        self.assertIn("FEATURES", self.text)

    def test_final_decision_does_not_use_synthetic_proposition_results(self) -> None:
        self.assertIn("No synthetic proposition result is used as deployment evidence", self.text)
        self.assertNotIn("conversion_rate", self.text)
        self.assertNotIn("combined_ratio", self.text)

    def test_value_for_complexity_is_measured(self) -> None:
        self.assertIn("fit_seconds", self.text)
        self.assertIn("serialized_model_mb", self.text)
        self.assertIn("prediction_ms_per_1000_policies", self.text)


if __name__ == "__main__":
    unittest.main()
