from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "action_results/v28/release_control_result.json"


class TestReleaseRollbackEvidenceV28(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))
        cls.registry = cls.result["registry"]
        cls.container = cls.result["container_switch"]

    def test_overall_status_and_governance(self) -> None:
        self.assertEqual(self.result["status"], "V28_SHADOW_RELEASE_CONTROL_PASS")
        self.assertEqual(self.registry["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(self.container["governance_status"], "HOLD_SHADOW_ONLY")

    def test_distinct_release_identity_with_identical_locked_artifacts(self) -> None:
        self.assertTrue(self.registry["distinct_release_lock_digests"])
        self.assertTrue(self.registry["identical_locked_artifact_hashes"])
        self.assertEqual(self.registry["locked_artifact_count"], 9)
        self.assertNotEqual(
            self.registry["release_a"]["lock_digest_sha256"],
            self.registry["release_b"]["lock_digest_sha256"],
        )
        self.assertEqual(self.registry["release_a"]["release_label"], "shadow-release-a")
        self.assertEqual(self.registry["release_b"]["release_label"], "shadow-release-b")

    def test_review_did_not_auto_switch_and_unauthorised_rollback_failed(self) -> None:
        self.assertEqual(self.registry["active_before_review"], "shadow-release-b")
        self.assertEqual(self.registry["active_after_review"], "shadow-release-b")
        self.assertFalse(self.registry["review_caused_automatic_serving_change"])
        self.assertTrue(self.registry["unauthorised_rollback_rejected"])
        self.assertIn("operator authorisation", self.registry["unauthorised_rejection"])

    def test_operator_authorised_rollback_returns_to_lkg_without_retraining(self) -> None:
        self.assertEqual(self.registry["selected_rollback_target"], "shadow-release-a")
        self.assertTrue(self.registry["operator_authorised_rollback"])
        self.assertEqual(self.registry["final_active_release_id"], "shadow-release-a")
        self.assertEqual(self.registry["last_known_good_release_id"], "shadow-release-a")
        self.assertFalse(self.registry["model_retraining_during_rollback"])
        self.assertFalse(self.registry["pricing_change_during_rollback"])

    def test_release_event_chain_is_verified(self) -> None:
        chain = self.registry["event_chain"]
        self.assertEqual(chain["status"], "RELEASE_EVENT_CHAIN_VERIFIED")
        self.assertEqual(chain["event_count"], 7)
        self.assertEqual(len(chain["head_event_sha256"]), 64)

    def test_both_container_mounts_have_exact_same_fit_http_parity(self) -> None:
        self.assertEqual(self.container["status"], "V28_CONTAINER_ROLLBACK_SWITCH_PASS")
        self.assertTrue(self.container["distinct_release_identities"])
        self.assertEqual(self.container["candidate_b_comparisons"], 100)
        self.assertEqual(self.container["rollback_a_comparisons"], 100)
        self.assertEqual(self.container["candidate_b_max_absolute_error"], 0.0)
        self.assertEqual(self.container["rollback_a_max_absolute_error"], 0.0)
        self.assertFalse(self.container["model_retraining_during_switch"])
        self.assertFalse(self.container["pricing_change_during_switch"])

    def test_interpretation_boundary_marks_replay_synthetic(self) -> None:
        boundary = self.registry["interpretation_boundary"].lower()
        self.assertIn("synthetic", boundary)
        self.assertIn("not a production incident", boundary)
        self.assertIn("not", self.result["automation_boundary"].lower())


if __name__ == "__main__":
    unittest.main()
