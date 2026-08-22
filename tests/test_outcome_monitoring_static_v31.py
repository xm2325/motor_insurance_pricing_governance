from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MONITOR = ROOT / "deployment" / "outcome_monitoring.py"
REPLAY = ROOT / "run_outcome_review_v31.py"
WORKFLOW = ROOT / ".github" / "workflows" / "v31-outcome-review.yml"


class OutcomeMonitoringStaticV31Tests(unittest.TestCase):
    def test_maturity_gate_withholds_early_performance_conclusions(self) -> None:
        source = MONITOR.read_text(encoding="utf-8")
        self.assertIn('"WAIT_FOR_OUTCOME_MATURITY"', source)
        self.assertIn('"NO_PERFORMANCE_CONCLUSION"', source)
        self.assertIn('"metrics_evaluated": False', source)
        self.assertIn('"pricing_change_authorised": False', source)
        self.assertIn('"model_promotion_authorised": False', source)

    def test_replay_uses_real_2024_outcomes_but_synthetic_arrival_timing(self) -> None:
        source = REPLAY.read_text(encoding="utf-8")
        self.assertIn('EARLY_EXPOSURE_FRACTION = 0.60', source)
        self.assertIn('MINIMUM_MATURE_EXPOSURE_FRACTION = 0.95', source)
        self.assertIn('test["total_claims"]', source)
        self.assertIn('test["total_incurred"]', source)
        self.assertIn('"outcome_values_are_real": True', source)
        self.assertIn('"label_arrival_timing_is_synthetic": True', source)
        self.assertIn('test["business_type"]', source)
        self.assertIn('"model_family_decision": "HOLD"', source)
        self.assertIn('"serving_status": "HOLD_SHADOW_ONLY"', source)

    def test_heavy_workflow_runs_numeric_contract_and_real_data_replay(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('tests/test_outcome_monitoring_v31.py', workflow)
        self.assertIn('python download_spanish_motor_2022_2024.py', workflow)
        self.assertIn('python audit_spanish_motor_2022_2024.py', workflow)
        self.assertIn('python build_deployment_bundle_v21.py', workflow)
        self.assertIn('python build_bundle_lock_v27.py', workflow)
        self.assertIn('python run_outcome_review_v31.py', workflow)
        self.assertIn("github.event_name == 'push'", workflow)


if __name__ == "__main__":
    unittest.main()
