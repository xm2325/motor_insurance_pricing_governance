from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "run_spanish_oot_2024.py"
ROLLING_SOURCE = ROOT / "run_rolling_origin_v14.py"
FORBIDDEN_FEATURES = {
    "insured_id",
    "year",
    "policy_status",
    "total_premium",
    "liability_premium",
    "property_damage_premium",
    "theft_premium",
    "fire_premium",
    "glass_premium",
    "legal_protection_premium",
    "occupants_premium",
    "total_claims",
    "liability_claims",
    "liability_property_claims",
    "liability_injury_claims",
    "property_claims",
    "theft_claims",
    "fire_claims",
    "glass_claims",
    "legal_protection_claims",
    "occupants_claims",
    "total_incurred",
    "liability_incurred",
    "liability_property_incurred",
    "liability_injury_incurred",
    "property_incurred",
    "theft_incurred",
    "fire_incurred",
    "glass_incurred",
    "legal_protection_incurred",
    "occupants_incurred",
    "total_exposure",
    "liability_exposure",
}


def literal_assignments() -> dict[str, object]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"CATEGORICAL", "NUMERIC"}:
                values[name] = ast.literal_eval(node.value)
    return values


class TestOOTContract(unittest.TestCase):
    def test_feature_set_excludes_outcomes_and_post_period_fields(self) -> None:
        assignments = literal_assignments()
        features = set(assignments["CATEGORICAL"]) | set(assignments["NUMERIC"])
        self.assertFalse(features & FORBIDDEN_FEATURES, features & FORBIDDEN_FEATURES)

    def test_expected_feature_count_is_stable(self) -> None:
        assignments = literal_assignments()
        features = list(assignments["CATEGORICAL"]) + list(assignments["NUMERIC"])
        self.assertEqual(len(features), 14)
        self.assertEqual(len(features), len(set(features)))

    def test_calendar_roles_remain_locked(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('df["year"] == 2022', source)
        self.assertIn('df["year"] == 2023', source)
        self.assertIn('df["year"] == 2024', source)
        self.assertIn('"train": 2022', source)
        self.assertIn('"calibration": 2023', source)
        self.assertIn('"test": 2024', source)

    def test_model_gate_requires_calibration_and_bootstrap_evidence(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('0.90 <= freq_xgb["test_locked_calibration_ratio_pred_over_actual"] <= 1.10', source)
        self.assertIn('freq_boot["ci95_low"] > 0', source)
        self.assertIn('0.90 <= loss_xgb["test_locked_calibration_ratio_pred_over_actual"] <= 1.10', source)
        self.assertIn('loss_boot["ci95_low"] > 0', source)

    def test_rolling_origin_uses_only_prior_years(self) -> None:
        source = ROLLING_SOURCE.read_text(encoding="utf-8")
        self.assertIn('fit_window(df, [2022], 2023)', source)
        self.assertIn('fit_window(df, [2022, 2023], 2024)', source)
        self.assertNotIn('fit_window(df, [2024]', source)

    def test_rolling_origin_reuses_locked_feature_contract(self) -> None:
        source = ROLLING_SOURCE.read_text(encoding="utf-8")
        self.assertIn('from run_spanish_oot_2024 import', source)
        self.assertIn('FEATURES,', source)
        for forbidden in ["total_premium", "policy_status", "total_claims", "total_incurred"]:
            self.assertNotIn(f'FEATURES = ["{forbidden}"', source)


if __name__ == "__main__":
    unittest.main()
