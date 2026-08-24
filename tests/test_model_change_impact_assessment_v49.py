import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ModelChangeImpactAssessmentV49Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assessment = json.loads(
            (ROOT / "results_v49/model_change_impact_assessment_v49.json").read_text(encoding="utf-8")
        )
        cls.markdown = (ROOT / "MODEL_CHANGE_IMPACT_ASSESSMENT.md").read_text(encoding="utf-8")

    def test_scope_is_aggregate_only_and_non_decisional(self):
        a = self.assessment
        self.assertEqual(a["status"], "V49_MODEL_CHANGE_IMPACT_ASSESSMENT_COMPLETE")
        self.assertEqual(a["scope"], "aggregate_committee_ready_synthesis_of_persisted_evidence")
        self.assertFalse(a["row_level_data_accessed"])
        self.assertFalse(a["model_fit_executed"])
        self.assertFalse(a["historical_decisions_changed"])
        self.assertFalse(a["new_performance_gate_created"])
        self.assertFalse(a["new_promotion_threshold_created"])
        self.assertFalse(a["customer_pricing_authorised"])

    def test_review_sequence_is_evidence_then_impact_then_pricing(self):
        stages = self.assessment["decision_sequence"]
        self.assertEqual([x["stage"] for x in stages], [1, 2, 3])
        self.assertEqual([x["name"] for x in stages], [
            "EVIDENCE_ADEQUACY",
            "MODEL_IMPACT_REVIEW",
            "COMMERCIAL_AND_CUSTOMER_PRICING_GOVERNANCE",
        ])
        self.assertEqual(stages[0]["current_status"], "EVIDENCE_GAP_HOLD")
        self.assertEqual(
            stages[1]["current_status"],
            "DIAGNOSTIC_EVIDENCE_AVAILABLE_BUT_NOT_PROMOTION_AUTHORITY",
        )
        self.assertEqual(stages[2]["current_status"], "OUT_OF_SCOPE_NOT_AUTHORISED")

    def test_evidence_blockers_are_fail_closed(self):
        e = self.assessment["evidence_adequacy"]
        self.assertEqual(e["status"], "EVIDENCE_GAP_HOLD")
        self.assertEqual(e["required_gate_pass_count"], 5)
        self.assertEqual(e["required_gate_count"], 8)
        self.assertEqual(e["blocker_ids"], [
            "G2_LOCKED_TEMPORAL_SUPPORT",
            "G3_PREREGISTERED_EXTERNAL_SUPPORT",
            "G4_FRESH_INDEPENDENT_EVIDENCE",
        ])
        self.assertEqual(e["external_target_gates_passed"], 0)
        self.assertEqual(e["external_target_gates_evaluated"], 4)
        self.assertFalse(e["fresh_independent_validation_available"])
        self.assertFalse(e["human_committee_review_open"])
        self.assertFalse(e["human_signoff_can_override_failed_evidence_gate"])

    def test_operational_readiness_does_not_imply_model_approval(self):
        o = self.assessment["operational_readiness"]
        self.assertTrue(o["shadow_serving_boundary"])
        self.assertTrue(o["manual_rollback_control"])
        self.assertTrue(o["attested_shadow_admission"])
        self.assertFalse(o["automatic_review_serving_switch"])
        self.assertEqual(o["raw_source_data_members_in_release_archive"], 0)
        self.assertTrue(
            self.assessment["interpretation_boundaries"]["operational_readiness_does_not_clear_evidence_blockers"]
        )

    def test_frequency_impact_headline_is_current(self):
        f = self.assessment["impact_diagnostics"]["frequency"]
        self.assertAlmostEqual(f["baseline_mean_absolute_log_disagreement"], 0.09926441568172852, places=12)
        self.assertEqual(
            [x["feature"] for x in f["top_disagreement_sensitivities"]],
            ["vehicle_brand", "policy_type", "vehicle_value"],
        )
        self.assertAlmostEqual(f["mean_absolute_portfolio_neutral_relativity_change"], 0.10181561928799863, places=12)
        self.assertAlmostEqual(f["exposure_share_abs_change_gt_10pct"], 0.36806017091811, places=12)
        self.assertAlmostEqual(f["exposure_share_abs_change_gt_20pct"], 0.10979322361662487, places=12)

    def test_pure_premium_impact_headline_is_current(self):
        p = self.assessment["impact_diagnostics"]["pure_premium"]
        self.assertAlmostEqual(p["baseline_mean_absolute_log_disagreement"], 0.31707691256990944, places=12)
        self.assertEqual(
            [x["feature"] for x in p["top_disagreement_sensitivities"]],
            ["business_type", "power_to_weight_ratio", "vehicle_value"],
        )
        self.assertAlmostEqual(p["mean_absolute_portfolio_neutral_relativity_change"], 0.322801992361319, places=12)
        self.assertAlmostEqual(p["exposure_share_abs_change_gt_10pct"], 0.782600691988952, places=12)
        self.assertAlmostEqual(p["exposure_share_abs_change_gt_20pct"], 0.5816832188493929, places=12)

    def test_selected_segments_exclude_tiny_tail_and_preserve_major_pattern(self):
        rows = {
            (x["dimension"], x["group"]): x
            for x in self.assessment["impact_diagnostics"]["selected_major_segments"]
        }
        self.assertEqual(set(rows), {
            ("business_type", "NB"), ("business_type", "P"),
            ("policy_type", "COMP_E"), ("policy_type", "CC"),
            ("driver_age_band", "35-49"), ("driver_age_band", "50-64"),
        })
        self.assertNotIn(("driver_age_band", "<25"), rows)
        self.assertGreater(rows[("business_type", "NB")]["pure_premium_total_relativity_change"], 0.08)
        self.assertLess(rows[("business_type", "P")]["pure_premium_total_relativity_change"], -0.06)
        self.assertGreater(rows[("policy_type", "COMP_E")]["pure_premium_total_relativity_change"], 0.13)
        self.assertLess(rows[("policy_type", "CC")]["pure_premium_total_relativity_change"], -0.09)
        self.assertGreater(rows[("driver_age_band", "35-49")]["pure_premium_total_relativity_change"], 0.05)
        self.assertLess(rows[("driver_age_band", "50-64")]["pure_premium_total_relativity_change"], -0.05)
        for row in rows.values():
            self.assertGreater(row["exposure_share"], 0.25 if row["dimension"] == "business_type" else 0.09)

    def test_numerical_limitation_is_visible_not_hidden(self):
        n = self.assessment["numerical_limitations"]
        self.assertTrue(n["frozen_tweedie_glm_max_iter_warning_retained"])
        self.assertEqual(
            n["repeat_run_conclusion"],
            "DESCRIPTIVE_REDISTRIBUTION_HEADLINES_STABLE_WITH_REGISTERED_TWEEDIE_GLM_NUMERICAL_LIMITATION",
        )
        self.assertLess(n["pure_premium_reference_total_relative_range"], 5e-5)
        self.assertLess(n["pure_premium_abs_change_gt_10pct_exposure_share_range"], 5e-5)
        self.assertLess(n["pure_premium_abs_change_gt_20pct_exposure_share_range"], 1e-4)
        self.assertLess(n["headline_major_segment_max_absolute_shift_range"], 2e-4)
        self.assertFalse(n["bitwise_reproducibility_claimed"])

    def test_current_disposition_remains_hold(self):
        d = self.assessment["current_disposition"]
        self.assertEqual(d["model_family_decision"], "HOLD")
        self.assertEqual(d["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(d["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(d["model_promotion_authorised"])
        self.assertFalse(d["pricing_change_authorised"])
        self.assertEqual(
            d["impact_pack_disposition"],
            "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
        )

    def test_source_lineage_has_all_inputs_and_sha256(self):
        lineage = self.assessment["source_lineage"]
        self.assertEqual(set(lineage), {
            "committee", "inventory", "disagreement", "relativity", "repeat_audit", "segments"
        })
        for item in lineage.values():
            self.assertEqual(len(item["sha256"]), 64)
            self.assertTrue((ROOT / item["path"]).exists())

    def test_interpretation_boundaries_are_explicit(self):
        b = self.assessment["interpretation_boundaries"]
        self.assertTrue(b["benchmark_is_not_pricing_uplift"])
        self.assertTrue(b["consumed_validation_is_not_fresh_evidence"])
        self.assertTrue(b["impact_diagnostics_do_not_clear_evidence_blockers"])
        self.assertTrue(b["operational_readiness_does_not_clear_evidence_blockers"])
        self.assertTrue(b["technical_relativity_is_not_customer_premium"])
        self.assertTrue(b["project_demo_not_insurer_policy"])
        self.assertFalse(b["first_central_or_current_uk_transport_claimed"])
        self.assertFalse(b["commercial_uplift_claimed"])

    def test_markdown_matches_decision_and_boundaries(self):
        for marker in [
            "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
            "EVIDENCE_GAP_HOLD",
            "5/8",
            "0/4",
            "36.81%",
            "78.26%",
            "58.17%",
            "HOLD / HOLD_SHADOW_ONLY / EVIDENCE_GAP_HOLD",
            "not a customer premium",
            "FIRST CENTRAL / the current UK motor market",
        ]:
            self.assertIn(marker, self.markdown)
        lower = self.markdown.lower()
        self.assertIn("does not reopen model-family promotion", lower)
        self.assertIn("does not access policy rows", lower)
        self.assertIn("not segment accuracy", lower)


if __name__ == "__main__":
    unittest.main()
