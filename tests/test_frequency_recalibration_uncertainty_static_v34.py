from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run_frequency_recalibration_uncertainty_v34.py"
MODULE = ROOT / "deployment" / "calibration_uncertainty.py"
WORKFLOW = ROOT / ".github" / "workflows" / "v34-recalibration-uncertainty.yml"
RESULTS = ROOT / "RESULTS_V34.md"


class FrequencyRecalibrationUncertaintyStaticV34Tests(unittest.TestCase):
    def test_bootstrap_fit_call_contains_calibration_variables_only(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
            if name == "paired_stratified_bootstrap_factors":
                calls.append(node)
        self.assertEqual(len(calls), 1)
        names = {node.id for node in ast.walk(calls[0]) if isinstance(node, ast.Name)}
        self.assertIn("segment_calibration", names)
        self.assertIn("claims_calibration", names)
        self.assertIn("exposure_calibration", names)
        self.assertIn("calibration_scores", names)
        self.assertFalse(any("test" in name.lower() or "2024" in name.lower() for name in names))

    def test_registered_bootstrap_and_robustness_rules_are_locked(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        expected = [
            "BOOTSTRAP_DRAWS = 500",
            "BOOTSTRAP_SEED = 20260823",
            "FACTOR_FLOOR = 0.50",
            "FACTOR_CAP = 2.00",
            "ORIGINAL_V32_MAX_RELATIVE_DEVIANCE_WORSENING = 0.001",
            "MIN_DEVIANCE_IMPROVEMENT_RATE = 0.80",
            "MIN_AGGREGATE_CALIBRATION_NONWORSE_RATE = 0.80",
            "MIN_WORST_SEGMENT_CALIBRATION_IMPROVEMENT_RATE = 0.80",
            "MIN_ORIGINAL_DEVIANCE_GUARDRAIL_PASS_RATE = 0.95",
            '"2024_labels_used_for_bootstrap_factor_fit": False',
            '"factor_draws_are_clipped": False',
            '"bundle_change_authorised": False',
            '"pricing_change_authorised": False',
            '"model_promotion_authorised": False',
            '"model_family_decision": "HOLD"',
            '"serving_status": "HOLD_SHADOW_ONLY"',
        ]
        for token in expected:
            self.assertIn(token, source)

    def test_uncertainty_module_does_not_clip_bootstrap_factors(self) -> None:
        source = MODULE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        bootstrap = next(
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "paired_stratified_bootstrap_factors"
        )
        bootstrap_source = ast.get_source_segment(source, bootstrap) or ""
        self.assertNotIn("np.clip", bootstrap_source)
        self.assertIn("intentionally *not clipped*", bootstrap_source)

    def test_workflow_rebuilds_bundle_runs_real_data_and_uses_race_safe_persistence(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for token in [
            "tests/test_frequency_recalibration_uncertainty_v34.py",
            "python discover_spanish_motor_2022_2024.py",
            "python download_spanish_motor_2022_2024.py",
            "python audit_spanish_motor_2022_2024.py",
            "python build_deployment_bundle_v21.py",
            "python build_bundle_lock_v27.py",
            "python verify_bundle_v27.py deployment_artifacts",
            "python run_frequency_recalibration_uncertainty_v34.py",
            "scripts/push_evidence_with_rebase.sh",
            "github.event_name == 'push'",
        ]:
            self.assertIn(token, workflow)

    def test_results_retain_pre_registered_glm_failure_and_xgb_pass(self) -> None:
        results = RESULTS.read_text(encoding="utf-8")
        self.assertIn("398/500 = 79.6%", results)
        self.assertIn("pre-registered aggregate-calibration requirement is **80%**", results)
        self.assertIn("FACTOR_UNCERTAINTY_REVIEW_REQUIRED", results)
        self.assertIn("424/500 = 84.8%", results)
        self.assertIn("ROBUST_TO_2023_FACTOR_ESTIMATION_FOR_FURTHER_SHADOW_TESTING", results)
        self.assertIn("does **not** resample or refit", results)


if __name__ == "__main__":
    unittest.main()
