import json
import unittest
from pathlib import Path

from scripts.refresh_interview_evidence_pack_v54 import refresh as refresh_interview
from scripts.refresh_repository_front_door_v54 import refresh as refresh_readme

ROOT = Path(__file__).resolve().parents[1]


def has_exact_line(text: str, line: str) -> bool:
    return line in text.splitlines()


def has_shell_command(text: str, command_prefix: str) -> bool:
    return any(line.strip().startswith(command_prefix) for line in text.splitlines())


class RatingFrontDoorV54Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(
            (ROOT / "results_v54/rating_front_door_summary_v54.json").read_text(encoding="utf-8")
        )
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.interview = (ROOT / "INTERVIEW_EVIDENCE_PACK.md").read_text(encoding="utf-8")
        cls.v50_workflow = (ROOT / ".github/workflows/v50-recruiter-front-door.yml").read_text(encoding="utf-8")

    def test_documentation_only_scope(self):
        s = self.summary
        self.assertEqual(s["status"], "V54_RATING_FRONT_DOOR_SYNC_PASS")
        self.assertEqual(s["scope"], "documentation_and_evidence_navigation_only")
        self.assertEqual(s["front_door_current_through"], "v0.53")
        self.assertFalse(s["row_level_data_accessed"])
        self.assertFalse(s["model_fit_executed"])
        self.assertFalse(s["historical_model_or_validation_decisions_changed"])
        self.assertTrue(s["v50_rolling_writer_frozen"])
        self.assertTrue(s["v45_rolling_writer_frozen"])
        self.assertTrue(all(s["checks"].values()))

    def test_rating_headlines_match_v53_main_evidence(self):
        h = self.summary["rating_review_headlines"]
        self.assertAlmostEqual(h["driver_age_shape_gap"], 0.26865990121735667, places=12)
        self.assertAlmostEqual(h["driver_age_strict_extrapolation_exposure_share"], 1.5871206507159884e-05, places=15)
        self.assertAlmostEqual(h["business_type_mix_tv"], 0.48595824222641637, places=12)
        self.assertEqual(h["business_type_unseen_exposure_share"], 0.0)
        self.assertAlmostEqual(h["frequency_mean_absolute_portfolio_neutral_relativity_change"], 0.10181561928799863, places=12)
        self.assertAlmostEqual(h["pure_premium_mean_absolute_portfolio_neutral_relativity_change"], 0.322801992361319, places=12)

    def test_current_decision_is_unchanged_hold(self):
        d = self.summary["current_decision"]
        self.assertEqual(d["committee_status"], "EVIDENCE_GAP_HOLD")
        self.assertEqual((d["committee_gate_pass_count"], d["committee_gate_count"]), (5, 8))
        self.assertEqual(d["external_target_gates"], "0/4")
        self.assertEqual(d["model_family_decision"], "HOLD")
        self.assertEqual(d["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(d["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(d["customer_pricing_authorised"])

    def test_readme_surfaces_insurance_rating_story(self):
        front = self.readme.split("\n---\n", 1)[0]
        for marker in [
            "Rating-factor response shape",
            "0.26866 / 0.26771",
            "0.00227% exposure",
            "48.60%",
            "0% unseen business-type exposure",
            "Rating Factor Review Pack",
            "RESULTS_V51.md",
            "RESULTS_V52.md",
            "RESULTS_V53.md",
            "HOLD / HOLD_SHADOW_ONLY",
        ]:
            self.assertIn(marker, front)
        self.assertIn("model response-shape disagreement, feature support, portfolio mix and technical-risk redistribution are different risks", front)

    def test_interview_pack_has_new_walkthrough_and_questions(self):
        for marker in [
            "### 14. Inspect rating-factor response shapes on development data",
            "### 15. Separate feature support from portfolio mix",
            "### 16. Join rating structure, support, impact and evidence without a composite score",
            "If driver age is well supported, why care about the GLM/XGBoost shape gap?",
            "If strict extrapolation is near zero, why did monitoring show such large drift?",
            "Why not combine shape gap, support drift and impact into one risk score?",
            "RATING_FACTOR_REVIEW_PACK.md",
        ]:
            self.assertIn(marker, self.interview)
        self.assertIn("technical-risk redistributions, not customer-price changes", self.interview)

    def test_claim_boundaries_remain_visible(self):
        b = self.summary["headline_boundaries"]
        self.assertTrue(b["benchmark_is_not_pricing_uplift"])
        self.assertTrue(b["consumed_validation_not_relabelled_fresh"])
        self.assertTrue(b["v51_not_relabelled_validation"])
        self.assertTrue(b["v52_not_relabelled_performance"])
        self.assertTrue(b["v53_not_relabelled_performance"])
        self.assertTrue(b["technical_relativity_not_customer_premium"])
        self.assertFalse(b["first_central_or_current_uk_transfer_claimed"])
        self.assertFalse(b["commercial_uplift_claimed"])
        self.assertIn("No result establishes transport to FIRST CENTRAL", self.readme)
        self.assertIn("not a causal estimate", self.interview)

    def test_v50_writer_is_frozen(self):
        self.assertFalse(has_exact_line(self.v50_workflow, "  push:"))
        self.assertFalse(has_exact_line(self.v50_workflow, "  pull_request:"))
        self.assertTrue(has_exact_line(self.v50_workflow, "  workflow_dispatch:"))
        self.assertTrue(has_exact_line(self.v50_workflow, "  contents: read"))
        self.assertFalse(has_shell_command(self.v50_workflow, "git push"))
        self.assertFalse(has_shell_command(self.v50_workflow, "bash scripts/push_evidence_with_rebase.sh"))

    def test_refreshes_are_idempotent(self):
        self.assertEqual(refresh_readme(self.readme), self.readme)
        self.assertEqual(refresh_interview(self.interview), self.interview)

    def test_historical_readme_body_is_hash_registered(self):
        historical = self.readme.split("\n---\n", 1)[1]
        import hashlib
        observed = hashlib.sha256(historical.encode("utf-8")).hexdigest()
        self.assertEqual(observed, self.summary["readme_historical_body_sha256"])


if __name__ == "__main__":
    unittest.main()
