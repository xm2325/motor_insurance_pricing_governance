from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "action_results/v28/release_control_result.json"


class TestReleaseControlEvidenceV28(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))
        cls.registry = cls.result["registry"]
        cls.container = cls.result["container_switch"]

    def test_overall_status_and_governance(self) -> None:
        self.assertEqual(self.result["status"], "V28_SHADOW_RELEASE_CONTROL_PASS")
        self.assertEqual(self.registry["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(self.container["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertIn("HOLD_SHADOW_ONLY", self.result["governance_boundary"])

    def test_releases_are_distinct_packages_with_identical_model_content(self) -> None:
        self.assertTrue(self.registry["distinct_release_lock_digests"])
        self.assertTrue(self.registry["identical_locked_artifact_hashes"])
        self.assertEqual(self.registry["locked_artifact_count"], 9)
        self.assertNotEqual(
            self.registry["release_a"]["lock_digest_sha256"],
            self.registry["release_b"]["lock_digest_sha256"],
        )
        self.assertEqual(self.registry["release_a"]["release_label"], "shadow-release-a")
        self.assertEqual(self.registry["release_b"]["release_label"], "shadow-release-b")

    def test_review_does_not_automatically_change_serving(self) -> None:
        self.assertEqual(self.registry["active_before_review"], "shadow-release-b")
        self.assertEqual(self.registry["active_after_review"], "shadow-release-b")
        self.assertFalse(self.registry["review_caused_automatic_serving_change"])

    def test_unauthorised_rollback_is_rejected(self) -> None:
        self.assertTrue(self.registry["unauthorised_rollback_rejected"])
        self.assertIn("operator authorisation", self.registry["unauthorised_rejection"])
        self.assertEqual(self.registry["selected_rollback_target"], "shadow-release-a")

    def test_authorised_rollback_restores_last_known_good_without_retraining(self) -> None:
        self.assertTrue(self.registry["operator_authorised_rollback"])
        self.assertEqual(self.registry["final_active_release_id"], "shadow-release-a")
        self.assertEqual(self.registry["last_known_good_release_id"], "shadow-release-a")
        self.assertFalse(self.registry["model_retraining_during_rollback"])
        self.assertFalse(self.registry["pricing_change_during_rollback"])

    def test_event_chain_is_verified(self) -> None:
        chain = self.registry["event_chain"]
        self.assertEqual(chain["status"], "RELEASE_EVENT_CHAIN_VERIFIED")
        self.assertEqual(chain["event_count"], 7)
        self.assertEqual(len(chain["head_event_sha256"]), 64)

    def test_container_switch_has_exact_same_fit_parity(self) -> None:
        self.assertEqual(self.container["status"], "V28_CONTAINER_ROLLBACK_SWITCH_PASS")
        self.assertTrue(self.container["distinct_release_identities"])
        self.assertEqual(self.container["candidate_b_comparisons"], 100)
        self.assertEqual(self.container["rollback_a_comparisons"], 100)
        self.assertEqual(self.container["candidate_b_max_absolute_error"], 0.0)
        self.assertEqual(self.container["rollback_a_max_absolute_error"], 0.0)
        self.assertFalse(self.container["model_retraining_during_switch"])
        self.assertFalse(self.container["pricing_change_during_switch"])

    def test_boundary_does_not_claim_real_authentication_or_incident(self) -> None:
        boundary = self.registry["interpretation_boundary"].lower()
        self.assertIn("synthetic", boundary)
        self.assertIn("not a production incident", boundary)
        automation = self.result["automation_boundary"].lower()
        self.assertIn("did not switch serving", automation)
        self.assertIn("operator-authorised", automation)


if __name__ == "__main__":
    unittest.main()
