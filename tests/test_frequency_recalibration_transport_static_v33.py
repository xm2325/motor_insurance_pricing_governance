from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run_frequency_recalibration_transport_v33.py"
WORKFLOW = ROOT / ".github" / "workflows" / "v33-transport.yml"


class FrequencyRecalibrationTransportStaticV33Tests(unittest.TestCase):
    def test_runner_consumes_persisted_v32_factors_without_refit(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn(
            'V32_EVIDENCE = Path("action_results/v32/business_type_recalibration_summary.json")',
            source,
        )
        self.assertNotIn("fit_segment_multipliers", source)
        self.assertIn('"multipliers_refit_in_v33": False', source)
        self.assertIn('"2024_labels_used_for_fit": False', source)
        self.assertIn('"test_2024_labels_used_for_fit"', source)

    def test_transport_dimensions_are_ast_locked_and_orthogonal_to_fit_dimension(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = [
            node
            for node in tree.body
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and (
                (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TRANSPORT_DIMENSIONS" for t in node.targets))
                or (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "TRANSPORT_DIMENSIONS")
            )
        ]
        self.assertEqual(len(assignments), 1)
        value = assignments[0].value
        self.assertIsInstance(value, (ast.Tuple, ast.List))
        dimensions = [
            element.value
            for element in value.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
        self.assertEqual(
            dimensions,
            ["seen_before_2024", "driver_age_band", "policy_type", "payment_frequency"],
        )
        self.assertNotIn("business_type", dimensions)

    def test_governance_and_guardrails_are_explicit(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("MAJOR_COHORT_MIN_ROWS = 2_000", source)
        self.assertIn("MAJOR_COHORT_MIN_EXPOSURE_SHARE = 0.02", source)
        self.assertIn("MAJOR_COHORT_MIN_CLAIMS = 100", source)
        self.assertIn("MAX_ABS_LOG_CALIBRATION_DETERIORATION = 0.02", source)
        self.assertIn("MAX_RELATIVE_DEVIANCE_WORSENING = 0.005", source)
        self.assertIn('"bundle_change_authorised": False', source)
        self.assertIn('"pricing_change_authorised": False', source)
        self.assertIn('"model_promotion_authorised": False', source)
        self.assertIn('"model_family_decision": "HOLD"', source)
        self.assertIn('"serving_status": "HOLD_SHADOW_ONLY"', source)

    def test_workflow_rebuilds_and_verifies_bundle_before_transport_review(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("tests/test_frequency_recalibration_transport_v33.py", workflow)
        self.assertIn("python download_spanish_motor_2022_2024.py", workflow)
        self.assertIn("python audit_spanish_motor_2022_2024.py", workflow)
        self.assertIn("python build_deployment_bundle_v21.py", workflow)
        self.assertIn("python build_bundle_lock_v27.py", workflow)
        self.assertIn("python verify_bundle_v27.py deployment_artifacts", workflow)
        self.assertIn("python run_frequency_recalibration_transport_v33.py", workflow)
        self.assertIn("scripts/push_evidence_with_rebase.sh", workflow)
        self.assertIn("github.event_name == 'push'", workflow)


if __name__ == "__main__":
    unittest.main()
