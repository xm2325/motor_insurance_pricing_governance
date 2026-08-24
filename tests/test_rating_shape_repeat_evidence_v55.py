import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RatingShapeRepeatEvidenceV55Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(
            (ROOT / "governance/rating_shape_repeat_evidence_v55.json").read_text(encoding="utf-8")
        )

    def test_same_locked_head_was_repeated_cross_region(self):
        e = self.evidence
        self.assertEqual(e["status"], "V55_HOSTED_REPEAT_NUMERICAL_REVIEW_COMPLETE")
        self.assertEqual(e["locked_head_sha"], "cc6babb828680fef050a1267055373e3cc8ae455")
        self.assertEqual(e["workflow_run_id"], 32703117264)
        self.assertEqual([a["attempt"] for a in e["attempts"]], [1, 2])
        self.assertEqual({a["azure_region"] for a in e["attempts"]}, {"westus", "eastus2"})
        self.assertEqual({a["runner_image_version"] for a in e["attempts"]}, {"20260816.277.1"})

    def test_repeat_is_not_mislabelled_bitwise_or_exact(self):
        c = self.evidence["comparison"]
        i = self.evidence["interpretation"]
        self.assertFalse(c["byte_identical_outputs"])
        self.assertFalse(i["claim_bitwise_reproducibility"])
        self.assertFalse(i["claim_exact_metric_reproducibility"])
        self.assertTrue(c["non_numeric_keys_and_rows_equal"])
        self.assertTrue(c["xgb_frequency_relativity_exactly_equal"])

    def test_recorded_numerical_drift_is_tiny_and_non_decisional(self):
        c = self.evidence["comparison"]
        self.assertLess(c["max_absolute_difference_glm_frequency_relativity"], 1e-8)
        self.assertLess(c["max_absolute_difference_log_xgb_over_glm_relativity"], 1e-8)
        self.assertLess(c["max_absolute_difference_point_summary_fold_log_gap_range"], 1e-8)
        self.assertTrue(c["preselected_same_sign_fractions_unchanged"])
        self.assertFalse(c["interpretive_conclusion_changed"])
        self.assertEqual(c["driver_age_q95_same_sign_fraction_both_attempts"], 1.0)
        self.assertEqual(c["vehicle_age_q95_same_sign_fraction_both_attempts"], 1.0)
        self.assertEqual(c["vehicle_value_q95_same_sign_fraction_both_attempts"], 0.4)

    def test_repeat_creates_no_validation_or_pricing_authority(self):
        i = self.evidence["interpretation"]
        self.assertFalse(i["predictive_validation_evidence_created"])
        self.assertFalse(i["promotion_evidence_created"])
        self.assertFalse(i["customer_pricing_authorised"])
        self.assertFalse(i["numerical_drift_is_material_relative_to_observed_fold_ranges"])


if __name__ == "__main__":
    unittest.main()
