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

    def test_v21_shadow_deployment_evidence(self) -> None:
        status = load_json("action_results/v21/ACTION_V21_STATUS.json")
        smoke = load_json("action_results/v21/deployment_smoke_summary.json")
        container = load_json("action_results/v21/container_smoke_summary.json")
        manifest = load_json("action_results/v21/manifest.json")

        for key in [
            "contract_outcome",
            "download_outcome",
            "audit_outcome",
            "bundle_outcome",
            "parity_outcome",
            "docker_build_outcome",
            "container_smoke_outcome",
        ]:
            self.assertEqual(status[key], "success", key)

        self.assertEqual(manifest["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(
            (manifest["train_year"], manifest["calibration_year"], manifest["evaluation_year"]),
            (2022, 2023, 2024),
        )
        self.assertEqual(smoke["parity_records"], 25)
        self.assertEqual(smoke["offline_online_max_abs_error"], 0.0)
        self.assertTrue(smoke["forbidden_outcome_field_rejected"])
        self.assertTrue(smoke["unseen_category_warning_emitted"])
        self.assertTrue(smoke["batch_deterministic"])
        self.assertEqual(smoke["batch_size_tested"], 1000)
        self.assertTrue(container["network_score_parity"])

        for metadata in manifest["models"].values():
            serialization = metadata.get("serialization", "joblib_pipeline")
            if serialization == "sklearn_preprocessor_plus_xgboost_ubj":
                self.assertEqual(len(metadata["preprocessor_sha256"]), 64)
                self.assertEqual(len(metadata["native_model_sha256"]), 64)
                self.assertTrue(metadata["native_model_artifact"].endswith(".ubj"))
            else:
                self.assertEqual(len(metadata["sha256"]), 64)

    def test_v22_shadow_monitoring_evidence(self) -> None:
        replay = load_json("action_results/v22/monitoring_replay_summary.json")
        container = load_json("action_results/v22/container_monitoring_summary.json")

        self.assertEqual(replay["status"], "success")
        self.assertEqual(replay["sample_size_per_replay"], 5000)
        baseline = replay["baseline_2022"]
        temporal = replay["temporal_2024"]
        stress = replay["synthetic_stress"]

        self.assertEqual(baseline["privacy_boundary"], "aggregate_non_pii_only")
        self.assertEqual(baseline["alert_status"], "GREEN")
        self.assertAlmostEqual(baseline["feature_drift"]["max_psi"], 0.009732760622960532)
        self.assertEqual(baseline["records_scored"], 5000)

        self.assertEqual(temporal["records_scored"], 5000)
        self.assertTrue(temporal["alerts"]["feature_drift"])
        self.assertFalse(temporal["alerts"]["frequency_disagreement"])
        self.assertFalse(temporal["alerts"]["pure_premium_disagreement"])
        self.assertEqual(temporal["feature_drift"]["max_psi_feature"], "business_type")
        self.assertAlmostEqual(temporal["feature_drift"]["max_psi"], 1.4115752423025838)

        mix = replay["business_type_distribution_full_year"]
        self.assertAlmostEqual(mix["2022"]["NB"], 0.979053460570782)
        self.assertAlmostEqual(mix["2024"]["P"], 0.42653419400898357)
        temporal_shift = replay["temporal_disagreement_shift"]
        self.assertAlmostEqual(temporal_shift["frequency_ratio"], 0.936055832958704)
        self.assertAlmostEqual(temporal_shift["pure_premium_ratio"], 1.0426489836175252)
        self.assertFalse(temporal_shift["frequency_relative_alert"])
        self.assertFalse(temporal_shift["pure_premium_relative_alert"])

        self.assertEqual(stress["alert_status"], "RED")
        self.assertTrue(stress["alerts"]["error_rate"])
        self.assertTrue(stress["alerts"]["unseen_category_rate"])
        self.assertTrue(stress["alerts"]["feature_drift"])
        self.assertEqual(stress["unseen_category_rate"], 1.0)
        stress_shift = replay["stress_disagreement_shift"]
        self.assertGreater(stress_shift["frequency_ratio"], 2.5)
        self.assertGreater(stress_shift["pure_premium_ratio"], 2.8)

        self.assertEqual(temporal["feature_drift"]["minimum_records"], 500)
        self.assertTrue(container["monitoring_http_verified"])
        self.assertEqual(container["privacy_boundary"], "aggregate_non_pii_only")
        self.assertEqual(container["records_scored"], 5)
        self.assertEqual(container["alert_status"], "GREEN")

    def test_v23_review_lifecycle_evidence(self) -> None:
        review = load_json("action_results/v23/review_lifecycle_summary.json")
        self.assertEqual(review["status"], "success")
        self.assertEqual(review["policy"]["open_after_consecutive_breach_windows"], 2)
        self.assertEqual(review["policy"]["close_after_consecutive_green_windows"], 2)
        self.assertFalse(review["policy"]["automatic_model_or_pricing_change"])
        self.assertTrue(review["aggregate_only_evidence"])
        self.assertTrue(review["deterministic_replay"])
        self.assertEqual(
            review["states"],
            [
                "HEALTHY",
                "WATCH",
                "REVIEW_REQUIRED",
                "RECOVERING",
                "HEALTHY",
                "WATCH",
                "REVIEW_REQUIRED",
            ],
        )
        temporal = review["temporal_review"]
        self.assertEqual(temporal["severity"], "MEDIUM")
        self.assertEqual(temporal["active_alerts"], ["feature_drift"])
        self.assertEqual(
            temporal["action"],
            "REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION",
        )
        self.assertAlmostEqual(temporal["max_feature_psi"], 1.4115752423025838)
        self.assertEqual(temporal["max_feature_psi_feature"], "business_type")
        self.assertTrue(review["recovery"]["closed_after_two_green_windows"])
        self.assertEqual(review["recovery"]["state_after_recovery"], "HEALTHY")
        stress = review["synthetic_stress_review"]
        self.assertEqual(stress["severity"], "HIGH")
        self.assertEqual(stress["action"], "INVESTIGATE_SERVING_DATA_AND_MODEL")
        self.assertIn("error_rate", stress["active_alerts"])
        self.assertIn("unseen_category_rate", stress["active_alerts"])
        self.assertIn("pure_premium_disagreement", stress["active_alerts"])
        self.assertEqual(len(review["source_monitoring_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
