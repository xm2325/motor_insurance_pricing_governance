import unittest
from pathlib import Path

from scripts.refresh_repository_front_door_v45 import refresh

ROOT = Path(__file__).resolve().parents[1]


class RepositoryFrontDoorV45Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme_path = ROOT / "README.md"
        cls.original_readme = cls.readme_path.read_text(encoding="utf-8")
        cls.refreshed_readme = refresh(cls.original_readme)
        cls.interview = (ROOT / "INTERVIEW_EVIDENCE_PACK.md").read_text(encoding="utf-8")

    def test_readme_refresh_is_idempotent(self):
        self.assertEqual(refresh(self.refreshed_readme), self.refreshed_readme)

    def test_readme_front_door_contains_latest_external_evidence(self):
        top = self.refreshed_readme.split("\n---\n", 1)[0]
        for marker in [
            "Australian external replication",
            "Belgian external replication",
            "0/4 preregistered external target gates pass",
            "1.42×10⁻¹⁴",
            "EVIDENCE_GAP_HOLD",
            "5/8",
            "promotion_review_status=NOT_OPEN",
        ]:
            self.assertIn(marker, top)

    def test_readme_links_current_review_and_committee_packs(self):
        top = self.refreshed_readme.split("\n---\n", 1)[0]
        self.assertIn("RESULTS_V43.md", top)
        self.assertIn("RESULTS_V44.md", top)
        self.assertIn("action_results/v43/MODEL_FAMILY_REVIEW_PACK_V43.md", top)
        self.assertIn("action_results/v44/MODEL_CHANGE_COMMITTEE_PACK_V44.md", top)

    def test_historical_detail_is_preserved_after_separator(self):
        old_historical = self.original_readme.split("\n---\n", 1)[1]
        new_historical = self.refreshed_readme.split("\n---\n", 1)[1]
        self.assertEqual(old_historical, new_historical)
        self.assertIn("## Evidence track 1 — freMTPL2 governance benchmark", new_historical)

    def test_front_door_describes_2024_as_first_use_not_current_fresh_holdout(self):
        top = self.refreshed_readme.split("\n---\n", 1)[0]
        self.assertIn("2024 locked first-use OOT", top)
        self.assertIn("CONSUMED_RETROSPECTIVE_VALIDATION", top)
        self.assertNotIn("2024 untouched at first locked OOT evaluation", top)

    def test_interview_pack_is_current_through_v44(self):
        for marker in [
            "0 of 4 preregistered Australian/Belgian target gates passed",
            "EVIDENCE_GAP_HOLD",
            "5 of 8 required gates pass",
            "1.42×10⁻¹⁴",
            "G2_LOCKED_TEMPORAL_SUPPORT",
            "G3_PREREGISTERED_EXTERNAL_SUPPORT",
            "G4_FRESH_INDEPENDENT_EVIDENCE",
        ]:
            self.assertIn(marker, self.interview)

    def test_interview_pack_preserves_scientific_boundaries(self):
        for marker in [
            "project demonstration rule",
            "not FIRST CENTRAL/insurer policy",
            "No observed commercial uplift",
            "failed evidence gates cannot be overridden",
            "never authorise model promotion or customer pricing",
        ]:
            self.assertIn(marker.lower(), self.interview.lower())

    def test_current_pack_does_not_call_consumed_data_fresh(self):
        self.assertIn("CONSUMED_RETROSPECTIVE_VALIDATION", self.interview)
        self.assertIn("validation-use ledger marks them consumed", self.interview)
        self.assertNotIn("2024: untouched out-of-time evaluation.", self.interview)

    def test_front_door_references_exist(self):
        for path in [
            "RESULTS_V36.md",
            "RESULTS_V37.md",
            "RESULTS_V38.md",
            "RESULTS_V39.md",
            "RESULTS_V40.md",
            "RESULTS_V41.md",
            "RESULTS_V42.md",
            "RESULTS_V43.md",
            "RESULTS_V44.md",
            "action_results/v43/MODEL_FAMILY_REVIEW_PACK_V43.md",
            "action_results/v44/MODEL_CHANGE_COMMITTEE_PACK_V44.md",
        ]:
            self.assertTrue((ROOT / path).exists(), path)


if __name__ == "__main__":
    unittest.main()
