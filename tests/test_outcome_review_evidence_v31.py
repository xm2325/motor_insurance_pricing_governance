from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "action_results/v31/outcome_review_summary.json"
SEGMENT_PATH = ROOT / "action_results/v31/business_type_calibration.csv"
STATUS_PATH = ROOT / "action_results/v31/ACTION_V31_STATUS.json"


class TestOutcomeReviewEvidenceV31(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        with SEGMENT_PATH.open(newline="", encoding="utf-8") as handle:
            cls.segments = list(csv.DictReader(handle))

    def test_workflow_persisted_success(self) -> None:
        self.assertEqual(self.status["status"], "success")
        self.assertEqual(
            self.status["workflow"],
            "Motor pricing outcome-maturity review v0.31",
        )
        self.assertEqual(len(self.status["sha"]), 40)
        self.assertTrue(str(self.status["run_id"]).isdigit())

    def test_source_and_bundle_boundaries(self) -> None:
        source = self.summary["source"]
        bundle = self.summary["bundle"]
        self.assertEqual(self.summary["status"], "V31_OUTCOME_MATURITY_REVIEW_PASS")
        self.assertEqual(source["dataset"], "Mendeley sw4jmdb2sm v1")
        self.assertEqual(source["replay_year"], 2024)
        self.assertEqual(source["rows"], 168085)
        self.assertTrue(source["outcome_values_are_real"])
        self.assertTrue(source["label_arrival_timing_is_synthetic"])
        self.assertEqual(bundle["bundle_contract_version"], "0.27")
        self.assertEqual(bundle["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(bundle["integrity_status"], "CONTENT_ADDRESSED_BUNDLE_VERIFIED")

    def test_partial_maturity_withholds_performance_conclusion(self) -> None:
        policy = self.summary["maturity_policy"]
        early = self.summary["early_partial_outcomes"]
        self.assertAlmostEqual(policy["early_replay_target_exposure_fraction"], 0.60, places=12)
        self.assertAlmostEqual(policy["minimum_mature_exposure_fraction"], 0.95, places=12)
        self.assertEqual(early["status"], "WAIT_FOR_OUTCOME_MATURITY")
        self.assertEqual(early["decision"], "NO_PERFORMANCE_CONCLUSION")
        self.assertGreaterEqual(early["mature_exposure_fraction"], 0.60)
        self.assertLess(early["mature_exposure_fraction"], 0.95)
        self.assertFalse(early["metrics_evaluated"])
        self.assertFalse(early["pricing_change_authorised"])
        self.assertFalse(early["model_promotion_authorised"])
        self.assertNotIn("frequency", early)
        self.assertNotIn("pure_premium", early)

    def test_fully_mature_metrics_match_locked_2024_evidence(self) -> None:
        mature = self.summary["fully_mature_outcomes"]
        self.assertEqual(mature["status"], "OUTCOME_PERFORMANCE_EVALUATED")
        self.assertAlmostEqual(mature["mature_exposure_fraction"], 1.0, places=12)
        self.assertTrue(mature["metrics_evaluated"])
        self.assertEqual(mature["rows_total"], 168085)
        self.assertEqual(mature["rows_with_mature_outcomes"], 168085)
        self.assertAlmostEqual(mature["observed_claims"], 39276.0, places=8)
        self.assertAlmostEqual(mature["observed_incurred"], 38106351.28, places=6)

        self.assertAlmostEqual(
            mature["frequency"]["reference"]["poisson_deviance"],
            1.1185362628672493,
            places=12,
        )
        self.assertAlmostEqual(
            mature["frequency"]["challenger"]["poisson_deviance"],
            1.1188352761606644,
            places=12,
        )
        self.assertAlmostEqual(
            mature["pure_premium"]["reference"]["tweedie_deviance_p1_5"],
            93.93180592411453,
            places=10,
        )
        self.assertAlmostEqual(
            mature["pure_premium"]["challenger"]["tweedie_deviance_p1_5"],
            93.95131588528709,
            places=10,
        )
        self.assertLess(mature["glm_minus_xgb_frequency_deviance"], 0.0)
        self.assertLess(mature["glm_minus_xgb_tweedie_deviance"], 0.0)
        self.assertFalse(mature["pricing_change_authorised"])
        self.assertFalse(mature["model_promotion_authorised"])

    def test_historical_oot_reconciliation_is_exact(self) -> None:
        reconciliation = self.summary["historical_oot_reconciliation"]
        self.assertEqual(reconciliation["status"], "HISTORICAL_OOT_RECONCILIATION_PASS")
        self.assertEqual(len(reconciliation["checks"]), 8)
        self.assertAlmostEqual(reconciliation["max_relative_difference"], 0.0, places=15)
        self.assertAlmostEqual(reconciliation["relative_tolerance"], 0.002, places=12)
        for check in reconciliation["checks"].values():
            self.assertAlmostEqual(check["absolute_difference"], 0.0, places=15)
            self.assertAlmostEqual(check["relative_difference"], 0.0, places=15)

    def test_business_type_evidence_is_aggregate_and_complete(self) -> None:
        self.assertEqual([row["segment"] for row in self.segments], ["NB", "P"])
        self.assertEqual(sum(int(row["rows"]) for row in self.segments), 168085)
        self.assertAlmostEqual(
            sum(float(row["exposure_share"]) for row in self.segments),
            1.0,
            places=12,
        )
        forbidden = {"insured_id", "policy_id", "quote_id", "customer_id"}
        self.assertTrue(forbidden.isdisjoint(self.segments[0].keys()))

        by_segment = {row["segment"]: row for row in self.segments}
        self.assertAlmostEqual(
            float(by_segment["NB"]["challenger_pure_premium_calibration_ratio"]),
            0.9165434439433804,
            places=12,
        )
        self.assertAlmostEqual(
            float(by_segment["P"]["reference_pure_premium_calibration_ratio"]),
            1.0365546180103011,
            places=12,
        )

    def test_review_resolution_remains_hold_only(self) -> None:
        resolution = self.summary["review_resolution"]
        self.assertEqual(
            resolution["v23_recommended_action"],
            "REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION",
        )
        self.assertEqual(
            resolution["v31_action"],
            "EXECUTE_LABEL_BASED_SEGMENT_CALIBRATION_REVIEW",
        )
        self.assertEqual(resolution["model_family_decision"], "HOLD")
        self.assertEqual(resolution["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertFalse(resolution["automatic_serving_change"])
        self.assertFalse(resolution["automatic_pricing_change"])


if __name__ == "__main__":
    unittest.main()
