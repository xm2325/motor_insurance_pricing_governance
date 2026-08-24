import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RatingContextRepeatEvidenceV56Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(
            (ROOT / "governance/rating_context_repeat_evidence_v56.json").read_text(encoding="utf-8")
        )

    def test_exact_scoring_head_repeated_cross_region(self):
        e = self.evidence
        self.assertEqual(e["status"], "V56_HOSTED_REPEAT_NUMERICAL_REVIEW_COMPLETE")
        self.assertEqual(e["locked_scoring_head_sha"], "a1d4dbe60e79bf4f1967a4bf6e34d00fcaa122e1")
        self.assertEqual(e["protocol_commit_sha"], "5bf450c1fcca8cd65d349d2ed3ba649ff1da813b")
        self.assertEqual(e["workflow_run_id"], 32776747130)
        self.assertEqual([a["attempt"] for a in e["attempts"]], [1, 2])
        self.assertEqual({a["azure_region"] for a in e["attempts"]}, {"centralus", "northcentralus"})

    def test_repeat_is_not_mislabelled_exact(self):
        c = self.evidence["comparison"]
        i = self.evidence["interpretation"]
        self.assertFalse(c["byte_identical_outputs"])
        self.assertFalse(i["claim_bitwise_reproducibility"])
        self.assertFalse(i["claim_exact_metric_reproducibility"])
        self.assertTrue(c["non_numeric_keys_and_rows_equal"])
        self.assertTrue(c["xgb_frequency_relativity_exactly_equal"])

    def test_context_interpretation_survives_repeat(self):
        c = self.evidence["comparison"]
        self.assertLess(c["max_absolute_difference_glm_frequency_relativity"], 1e-6)
        self.assertLess(c["max_absolute_difference_log_xgb_over_glm_relativity"], 1e-6)
        self.assertLess(c["max_absolute_difference_cross_context_q95_range"], 1e-12)
        self.assertEqual(c["driver_age_q95_same_sign_fraction_both_attempts"], 1.0)
        self.assertEqual(c["vehicle_age_q95_same_sign_fraction_both_attempts"], 1.0)
        self.assertTrue(c["vehicle_age_q05_context_sign_pattern_unchanged"])
        self.assertEqual(c["vehicle_age_q05_positive_contexts_both_attempts"], ["BASE", "BUSINESS_TYPE_P"])
        self.assertEqual(
            c["vehicle_age_q05_negative_contexts_both_attempts"],
            ["POLICY_TYPE_COMP_E", "FUEL_TYPE_G", "CIRCULATION_AREA_R"],
        )
        self.assertFalse(c["interpretive_conclusion_changed"])

    def test_repeat_creates_no_new_authority(self):
        i = self.evidence["interpretation"]
        self.assertTrue(i["context_effect_interpretation_numerically_robust_across_two_hosted_regions"])
        self.assertFalse(i["numerical_drift_is_material_relative_to_observed_context_ranges"])
        self.assertFalse(i["predictive_validation_evidence_created"])
        self.assertFalse(i["causal_interaction_evidence_created"])
        self.assertFalse(i["observed_segment_effect_created"])
        self.assertFalse(i["model_promotion_evidence_created"])
        self.assertFalse(i["customer_pricing_authorised"])


if __name__ == "__main__":
    unittest.main()
