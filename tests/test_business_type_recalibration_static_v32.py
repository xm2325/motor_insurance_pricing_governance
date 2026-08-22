from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run_business_type_recalibration_v32.py"
WORKFLOW = ROOT / ".github" / "workflows" / "v32-recalibration.yml"


class BusinessTypeRecalibrationStaticV32Tests(unittest.TestCase):
    def test_fit_call_uses_calibration_period_only(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        fit_calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name == "fit_segment_multipliers":
                fit_calls.append(node)

        self.assertEqual(len(fit_calls), 1)
        names = {
            item.id
            for item in ast.walk(fit_calls[0])
            if isinstance(item, ast.Name)
        }
        self.assertIn("segment_calibration", names)
        self.assertIn("actual_calibration", names)
        self.assertIn("baseline_calibration_pred", names)
        self.assertIn("exposure_calibration", names)
        self.assertFalse(any("test" in name.lower() or "2024" in name.lower() for name in names))

    def test_runner_declares_leakage_and_governance_boundaries(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('"2024_labels_used_for_candidate_fit": False', source)
        self.assertIn('"test_2024_labels_used_for_fit": False', source)
        self.assertIn('"bundle_change_authorised": False', source)
        self.assertIn('"pricing_change_authorised": False', source)
        self.assertIn('"model_promotion_authorised": False', source)
        self.assertIn('"model_family_decision": "HOLD"', source)
        self.assertIn('"serving_status": "HOLD_SHADOW_ONLY"', source)
        self.assertIn("MAX_RELATIVE_DEVIANCE_WORSENING = 0.001", source)

    def test_workflow_rebuilds_and_verifies_bundle_before_replay(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python download_spanish_motor_2022_2024.py", workflow)
        self.assertIn("python audit_spanish_motor_2022_2024.py", workflow)
        self.assertIn("python build_deployment_bundle_v21.py", workflow)
        self.assertIn("python build_bundle_lock_v27.py", workflow)
        self.assertIn("python verify_bundle_v27.py deployment_artifacts", workflow)
        self.assertIn("python run_business_type_recalibration_v32.py", workflow)
        self.assertIn("tests/test_business_type_recalibration_v32.py", workflow)
        self.assertIn("github.event_name == 'push'", workflow)
        self.assertIn("scripts/push_evidence_with_rebase.sh", workflow)


if __name__ == "__main__":
    unittest.main()
