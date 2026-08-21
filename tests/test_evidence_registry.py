from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class TestEvidenceRegistry(unittest.TestCase):
    def test_fremtpl2_full_frequency_claims(self) -> None:
        path = ROOT / "results/fremtpl2_full_frequency_benchmark.csv"
        with path.open(newline="", encoding="utf-8") as f:
            rows = {row["model"]: row for row in csv.DictReader(f)}
        glm = rows["Poisson GLM - + geography"]
        xgb = rows["XGBoost Poisson - + geography"]
        glm_dev = float(glm["poisson_deviance"])
        xgb_dev = float(xgb["poisson_deviance"])
        glm_capture = float(glm["top10_exposure_claim_capture"])
        xgb_capture = float(xgb["top10_exposure_claim_capture"])
        relative_gain = (glm_dev - xgb_dev) / glm_dev
        capture_gain = xgb_capture - glm_capture
        self.assertAlmostEqual(relative_gain, 0.054274168383486865, places=10)
        self.assertAlmostEqual(capture_gain, 0.10578731880048686, places=10)

    def test_locked_2024_oot_claims(self) -> None:
        summary = load_json("action_results/spanish_oot_2024/oot_2024_summary.json")
        self.assertEqual(summary["split"], {"train": 2022, "calibration": 2023, "test": 2024})
        freq = {row["model"]: row for row in summary["frequency_results"]}
        glm = freq["Poisson_GLM"]
        xgb = freq["XGBoost_Poisson"]
        self.assertEqual(int(glm["n_test"]), 168085)
        self.assertAlmostEqual(glm["test_locked_poisson_deviance"], 1.1185362628672493, places=10)
        self.assertAlmostEqual(xgb["test_locked_poisson_deviance"], 1.1188352761606644, places=10)
        gain = xgb["test_locked_top10_claim_capture"] - glm["test_locked_top10_claim_capture"]
        self.assertAlmostEqual(gain, 0.00420103880232203, places=10)
        ci = summary["bootstrap"]["glm_minus_xgb_frequency_deviance"]
        self.assertLess(ci["ci95_low"], 0)
        self.assertGreater(ci["ci95_high"], 0)
        self.assertEqual(summary["model_change_decision"]["overall"], "HOLD")

    def test_rolling_origin_claims(self) -> None:
        summary = load_json("action_results/spanish_oot_2024/rolling_origin_v14_summary.json")
        windows = {(tuple(w["train_years"]), w["test_year"]): w for w in summary["windows"]}
        early = windows[((2022,), 2023)]
        late = windows[((2022, 2023), 2024)]

        early_freq = {row["model"]: row for row in early["frequency"]}
        self.assertGreaterEqual(
            early_freq["XGBoost_Poisson"]["deviance"],
            early_freq["Poisson_GLM"]["deviance"],
        )
        early_ci = early["frequency_bootstrap_glm_minus_xgb"]
        self.assertLess(early_ci["ci95_low"], 0)
        self.assertGreater(early_ci["ci95_high"], 0)

        late_freq = {row["model"]: row for row in late["frequency"]}
        glm_dev = late_freq["Poisson_GLM"]["deviance"]
        xgb_dev = late_freq["XGBoost_Poisson"]["deviance"]
        relative_gain = (glm_dev - xgb_dev) / glm_dev
        self.assertAlmostEqual(relative_gain, 0.003205, places=5)
        late_ci = late["frequency_bootstrap_glm_minus_xgb"]
        self.assertGreater(late_ci["ci95_low"], 0)

        late_loss = {row["model"]: row for row in late["pure_premium"]}
        self.assertLess(
            late_loss["Tweedie_GLM"]["deviance"],
            late_loss["XGBoost_Tweedie"]["deviance"],
        )
        loss_ci = late["pure_premium_bootstrap_glm_minus_xgb"]
        self.assertLess(loss_ci["ci95_low"], 0)
        self.assertGreater(loss_ci["ci95_high"], 0)


if __name__ == "__main__":
    unittest.main()
