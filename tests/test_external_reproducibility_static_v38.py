from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "governance" / "external_reproducibility_audit_v38.json"
V36 = ROOT / "governance" / "external_validation_prereg_v36.json"


class ExternalReproducibilityStaticV38Tests(unittest.TestCase):
    def test_v38_policy_is_prospective_not_posthoc_v36_rewrite(self) -> None:
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        policy = audit["future_external_evidence_policy"]
        self.assertTrue(policy["applies_to_protocols_registered_after_v38"])
        self.assertTrue(policy["no_retroactive_change_to_v36_protocol"])
        original = json.loads(V36.read_text(encoding="utf-8"))
        self.assertEqual(original["schema_version"], "0.36")
        self.assertFalse(original["models"]["hyperparameter_search_allowed"])
        self.assertFalse(original["models"]["early_stopping_allowed"])

    def test_positive_external_claim_requires_two_runs_and_metric_reproducibility(self) -> None:
        policy = json.loads(AUDIT.read_text(encoding="utf-8"))["future_external_evidence_policy"]
        self.assertGreaterEqual(policy["minimum_independent_actions_executions_for_positive_gate"], 2)
        self.assertTrue(policy["same_locked_source_split_features_models_and_gate_required"])
        self.assertTrue(policy["decision_labels_must_agree"])
        self.assertTrue(policy["positive_external_support_requires_metric_reproducibility"])
        self.assertIn("NO_POSITIVE_EXTERNAL_CLAIM", policy["if_decision_labels_disagree"])

    def test_future_default_threads_are_single_threaded(self) -> None:
        env = json.loads(AUDIT.read_text(encoding="utf-8"))["future_external_evidence_policy"]["future_thread_environment_defaults"]
        self.assertEqual(env, {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        })


if __name__ == "__main__":
    unittest.main()
