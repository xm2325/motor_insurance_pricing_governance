import hashlib
import inspect
import json
import unittest
from pathlib import Path

import build_rating_factor_review_pack_v53 as v53

ROOT = Path(__file__).resolve().parents[1]


class RatingFactorReviewPackV53Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assessment = v53.build_pack()
        cls.markdown = v53.render_markdown(cls.assessment)

    def test_scope_is_aggregate_synthesis_only(self):
        a = self.assessment
        self.assertEqual(a["status"], "V53_RATING_FACTOR_REVIEW_PACK_COMPLETE")
        self.assertEqual(a["scope"], "aggregate_rating_structure_support_mix_and_impact_synthesis")
        self.assertFalse(a["row_level_data_accessed"])
        self.assertFalse(a["model_fit_executed"])
        self.assertFalse(a["historical_decisions_changed"])
        self.assertFalse(a["new_performance_gate_created"])
        self.assertFalse(a["new_support_threshold_created"])
        self.assertFalse(a["composite_risk_score_created"])
        self.assertFalse(a["customer_pricing_authorised"])

    def test_generator_reads_only_persisted_aggregate_evidence(self):
        source = inspect.getsource(v53)
        for forbidden in [
            "run_spanish_oot_2024",
            "DATA_PATH",
            "pandas",
            "sklearn",
            "xgboost",
            ".fit(",
            "total_claims",
            "total_incurred",
            "total_premium",
            "insured_id",
        ]:
            self.assertNotIn(forbidden, source)
        self.assertEqual(set(v53.SOURCES), {
            "v51_summary", "v51_numeric", "v51_categorical",
            "v52_summary", "v52_numeric", "v52_categorical", "v52_levels",
            "v49_impact",
        })

    def test_source_lineage_hashes_match_files(self):
        for key, meta in self.assessment["source_lineage"].items():
            path = ROOT / meta["path"]
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(observed, meta["sha256"], key)

    def test_driver_age_joins_shape_and_support_without_score(self):
        d = self.assessment["rating_structure_and_support"]["driver_age"]
        self.assertAlmostEqual(d["shape_gap"], 0.26865990121735667, places=12)
        self.assertAlmostEqual(d["strict_extrapolation_share"], 1.5871206507159884e-05, places=15)
        self.assertAlmostEqual(d["q05_q95_tail_share"], 0.08748372087087354, places=12)
        self.assertEqual([p["value"] for p in d["points"]], [30.0, 47.0, 68.0])
        self.assertAlmostEqual(d["points"][0]["glm_relativity"], 0.8796810286266358, places=12)
        self.assertAlmostEqual(d["points"][2]["xgb_relativity"], 0.8955651976658229, places=12)
        for p in d["points"]:
            self.assertAlmostEqual(p["xgb_over_glm"], p["xgb_relativity"] / p["glm_relativity"], places=15)
        self.assertFalse(self.assessment["composite_risk_score_created"])

    def test_business_type_is_mix_shift_not_unseen_support(self):
        b = self.assessment["rating_structure_and_support"]["business_type"]
        self.assertAlmostEqual(b["frequency_shape_gap"], 0.02571338968862851, places=12)
        self.assertAlmostEqual(b["total_variation"], 0.48595824222641637, places=12)
        self.assertEqual(b["unseen_exposure_share"], 0.0)
        self.assertAlmostEqual(b["nb_development_share"], 0.9677561751126499, places=12)
        self.assertAlmostEqual(b["nb_current_share"], 0.4817979328862335, places=12)
        self.assertAlmostEqual(b["p_development_share"], 0.0322438248873501, places=12)
        self.assertAlmostEqual(b["p_current_share"], 0.5182020671137666, places=12)

    def test_vehicle_brand_example_uses_real_v51_schema(self):
        b = self.assessment["rating_structure_and_support"]["vehicle_brand"]
        self.assertAlmostEqual(b["bmw_development_exposure_share_v51"], 0.04144015375543345, places=12)
        self.assertAlmostEqual(b["bmw_glm_relativity"], 1.3283456456215432, places=12)
        self.assertAlmostEqual(b["bmw_xgb_relativity"], 1.1743947742520435, places=12)
        self.assertEqual(b["unseen_2024_level_count"], 6)
        self.assertLess(b["unseen_2024_exposure_share"], 0.0001)

    def test_portfolio_neutral_impact_stays_technical_not_customer_price(self):
        p = self.assessment["portfolio_neutral_impact"]
        self.assertAlmostEqual(p["frequency_mean_absolute_relativity_change"], 0.10181561928799863, places=12)
        self.assertAlmostEqual(p["frequency_exposure_share_abs_change_gt_10pct"], 0.36806017091811, places=12)
        self.assertAlmostEqual(p["pure_premium_mean_absolute_relativity_change"], 0.322801992361319, places=12)
        self.assertAlmostEqual(p["pure_premium_exposure_share_abs_change_gt_20pct"], 0.5816832188493929, places=12)
        self.assertTrue(p["technical_risk_not_customer_premium"])

    def test_evidence_gate_remains_hold(self):
        e = self.assessment["evidence_adequacy"]
        self.assertEqual(e["status"], "EVIDENCE_GAP_HOLD")
        self.assertEqual((e["gate_pass_count"], e["gate_count"]), (5, 8))
        self.assertEqual(e["external_target_gates"], "0/4")
        self.assertFalse(e["fresh_independent_validation_available"])
        self.assertEqual(self.assessment["current_disposition"]["model_family_decision"], "HOLD")
        self.assertEqual(self.assessment["current_disposition"]["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(self.assessment["current_disposition"]["pricing_change_authorised"])

    def test_markdown_has_review_logic_and_boundaries(self):
        text = self.markdown
        for phrase in [
            "not broadly outside the numeric support",
            "portfolio reweighting among known rating cells",
            "small shape gap, very large portfolio-mix shift",
            "technical-risk score redistributions, not customer premium changes",
            "EVIDENCE_GAP_HOLD",
            "5/8",
            "0/4",
            "No composite score is created",
            "HOLD / HOLD_SHADOW_ONLY / NOT_OPEN",
        ]:
            self.assertIn(phrase, text)
        self.assertIn("No FIRST CENTRAL/current UK transport", text)

    def test_render_is_deterministic(self):
        second = v53.build_pack()
        self.assertEqual(self.assessment, second)
        self.assertEqual(self.markdown, v53.render_markdown(second))
        json_a = json.dumps(self.assessment, sort_keys=True, separators=(",", ":"))
        json_b = json.dumps(second, sort_keys=True, separators=(",", ":"))
        self.assertEqual(json_a, json_b)


if __name__ == "__main__":
    unittest.main()
