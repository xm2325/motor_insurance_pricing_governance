import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryFrontDoorV50Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.interview = (ROOT / "INTERVIEW_EVIDENCE_PACK.md").read_text(encoding="utf-8")
        cls.summary = json.loads(
            (ROOT / "results_v50/repository_front_door_summary_v50.json").read_text(encoding="utf-8")
        )
        cls.v45 = (ROOT / ".github/workflows/v45-repository-front-door.yml").read_text(encoding="utf-8")

    def test_front_door_is_current_through_v49(self):
        s = self.summary
        self.assertEqual(s["status"], "V50_RECRUITER_FRONT_DOOR_SYNC_PASS")
        self.assertEqual(s["front_door_current_through"], "v0.49")
        self.assertFalse(s["row_level_data_accessed"])
        self.assertFalse(s["model_fit_executed"])
        self.assertFalse(s["historical_model_or_validation_decisions_changed"])
        self.assertTrue(s["v45_rolling_writer_frozen"])
        self.assertTrue(all(s["checks"].values()))

    def test_readme_30_second_story_contains_current_evidence(self):
        front = self.readme.split("\n---\n", 1)[0]
        for marker in [
            "5.43%",
            "CONSUMED_RETROSPECTIVE_VALIDATION",
            "0/4",
            "EVIDENCE_GAP_HOLD",
            "5/8",
            "0.0993 frequency / 0.3171 pure premium",
            "36.81%",
            "78.26%",
            "58.17%",
            "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
            "MODEL_CHANGE_IMPACT_ASSESSMENT.md",
            "RESULTS_V47.md",
            "RESULTS_V48.md",
            "RESULTS_V49.md",
        ]:
            self.assertIn(marker, front)

    def test_readme_boundaries_are_visible(self):
        front = self.readme.split("\n---\n", 1)[0]
        for marker in [
            "not observed pricing/profit uplift",
            "not new performance evidence",
            "not customer premium",
            "max_iter=900",
            "not FIRST CENTRAL or regulatory approval states",
            "No result establishes transport to FIRST CENTRAL",
        ]:
            self.assertIn(marker, front)

    def test_readme_front_door_is_not_duplicated(self):
        self.assertEqual(self.readme.count("## 30-second result"), 1)
        self.assertEqual(self.readme.count("## Start here"), 1)
        self.assertEqual(self.readme.count("## Current evidence boundaries"), 1)
        self.assertEqual(self.readme.count("\n---\n"), 1)

    def test_interview_pack_adds_explanation_impact_and_review_order(self):
        for marker in [
            "### 11. Explain model-family disagreement without reusing outcomes",
            "### 12. Translate disagreement into portfolio impact without pretending it is premium",
            "### 13. Put evidence, impact and pricing governance in the right order",
            "What does “78.26% of exposure moves by more than ±10%” actually mean?",
            "Why do impact analysis when the promotion gate is already HOLD?",
            "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
        ]:
            self.assertIn(marker, self.interview)
            self.assertEqual(self.interview.count(marker), 1)

    def test_interview_pack_does_not_turn_impact_into_price(self):
        lower = self.interview.lower()
        for marker in [
            "not customer-price changes",
            "realised premium changes",
            "78.26% of customers would receive a >10% premium change",
            "impact results do not override the failed evidence gates",
        ]:
            self.assertIn(marker.lower(), lower)
        self.assertIn("they are **not** realised premium changes", lower)
        self.assertIn("it is **not** a statement", lower)

    def test_interview_star_is_current(self):
        star = self.interview.split("## STAR version", 1)[1].split("## Claims to avoid", 1)[0]
        for marker in [
            "portfolio-neutral technical-relativity redistribution",
            "all 168,085 positive-exposure 2024 feature rows",
            "0/4",
            "78.26%",
            "58.17%",
            "model promotion and customer pricing remain unauthorised",
        ]:
            self.assertIn(marker, star)

    def test_historical_v45_writer_is_manual_read_only(self):
        self.assertIn("workflow_dispatch:", self.v45)
        self.assertIn("contents: read", self.v45)
        self.assertNotIn("  push:", self.v45)
        self.assertNotIn("  pull_request:", self.v45)
        self.assertNotIn("git push", self.v45)
        self.assertNotIn("Persist v0.45", self.v45)

    def test_current_decision_is_not_changed_by_documentation(self):
        d = self.summary["current_decision"]
        self.assertEqual(d["committee_status"], "EVIDENCE_GAP_HOLD")
        self.assertEqual((d["committee_gate_pass_count"], d["committee_gate_count"]), (5, 8))
        self.assertEqual(d["external_target_gates"], "0/4")
        self.assertEqual(d["impact_pack_disposition"], "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN")
        self.assertEqual(d["model_family_decision"], "HOLD")
        self.assertEqual(d["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(d["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(d["customer_pricing_authorised"])

    def test_summary_boundaries_are_fail_closed(self):
        b = self.summary["headline_boundaries"]
        self.assertTrue(b["benchmark_is_not_pricing_uplift"])
        self.assertTrue(b["consumed_validation_not_relabelled_fresh"])
        self.assertTrue(b["impact_diagnostics_not_new_performance_evidence"])
        self.assertTrue(b["technical_relativity_not_customer_premium"])
        self.assertTrue(b["tweedie_limitation_visible"])
        self.assertFalse(b["first_central_or_current_uk_transfer_claimed"])
        self.assertFalse(b["commercial_uplift_claimed"])


if __name__ == "__main__":
    unittest.main()
