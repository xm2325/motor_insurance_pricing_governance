from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class TestRuntimeAndModelIOEvidence(unittest.TestCase):
    def test_v25_runtime_slimming_evidence(self) -> None:
        status = load_json("action_results/v25/ACTION_V25_STATUS.json")
        image = load_json("action_results/v25/image_size_summary.json")
        parity = load_json("action_results/v25/http_parity_summary.json")
        result = load_json("action_results/v25/runtime_slimming_result.json")

        self.assertEqual(status["status"], "success")
        self.assertEqual(result["status"], "V25_RUNTIME_SLIMMING_PASS")
        self.assertEqual(image["status"], "IMAGE_SIZE_AND_PACKAGE_GATE_PASS")
        self.assertEqual(image["full_image_bytes"], 960271925)
        self.assertEqual(image["runtime_image_bytes"], 488778419)
        self.assertEqual(image["absolute_bytes_removed"], 471493506)
        self.assertAlmostEqual(image["relative_size_reduction"], 0.49099999044541476)
        self.assertGreaterEqual(
            image["relative_size_reduction"], image["minimum_required_reduction"]
        )
        self.assertEqual(image["runtime_distribution"], "xgboost-cpu")
        self.assertEqual(image["runtime_xgboost_version"], "3.4.0")
        self.assertEqual(image["forbidden_packages_present"], [])

        self.assertEqual(parity["status"], "FULL_VS_CPU_RUNTIME_HTTP_PARITY_PASS")
        self.assertEqual(parity["records_tested"], 25)
        self.assertEqual(parity["full_vs_runtime_numeric_fields_per_record"], 6)
        self.assertEqual(parity["offline_reference_numeric_fields_per_record"], 4)
        self.assertEqual(parity["full_vs_runtime_max_abs_error"], 0.0)
        self.assertEqual(parity["runtime_vs_offline_max_abs_error"], 0.0)
        self.assertEqual(parity["governance_status"], "HOLD_SHADOW_ONLY")

    def test_v26_hybrid_model_io_evidence(self) -> None:
        status = load_json("action_results/v26/ACTION_V26_STATUS.json")
        provenance = load_json("action_results/v26/verified_pr_evidence_provenance.json")
        result = load_json("action_results/v26/environment_compatibility_result.json")
        same_fit = load_json("action_results/v26/serialization_parity_summary.json")
        runtime = load_json("action_results/v26/environment_compatibility_summary.json")
        drift = load_json("action_results/v26/retrain_drift_audit.json")
        warning = load_json("action_results/v26/serialization_warning_check.json")

        self.assertEqual(status["status"], "success")
        self.assertEqual(provenance["run_id"], 32519475249)
        self.assertEqual(provenance["artifact_id"], 9460042916)
        self.assertEqual(
            provenance["artifact_digest"],
            "sha256:c0c2211e2a45fb690e4d742030ddfed92eec6a3af4f43196ed742ff1d9b4a481",
        )
        self.assertEqual(result["status"], "V26_HYBRID_MODEL_IO_PASS")

        self.assertEqual(same_fit["status"], "SAME_FIT_SERIALIZATION_PARITY_PASS")
        self.assertEqual(same_fit["records_tested"], 25)
        self.assertEqual(same_fit["fields_per_record"], 4)
        self.assertEqual(same_fit["comparisons"], 100)
        self.assertEqual(same_fit["max_absolute_error"], 0.0)
        self.assertEqual(same_fit["acceptance_tolerance"], {"rtol": 1e-12, "atol": 1e-12})

        self.assertEqual(runtime["status"], "V26_HYBRID_RUNTIME_HTTP_PARITY_PASS")
        self.assertEqual(runtime["governance_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(runtime["environment_compatibility"], "HYBRID_MODEL_IO_COMPATIBLE")
        self.assertEqual(runtime["training_environment"]["xgboost"], "3.4.1")
        self.assertEqual(runtime["runtime_environment"]["xgboost"], "3.4.0")
        self.assertEqual(runtime["pickle_mismatches"], {})
        self.assertTrue(runtime["xgboost_native_compatible"])
        self.assertEqual(runtime["comparisons"], 100)
        self.assertEqual(runtime["http_max_absolute_error_vs_same_fit_reference"], 0.0)

        self.assertFalse(drift["acceptance_gate"])
        self.assertAlmostEqual(drift["max_absolute_error"], 0.4795733975596477)
        self.assertAlmostEqual(drift["max_relative_error"], 0.0008742430412423132)
        self.assertEqual(drift["by_field"]["challenger_frequency"]["max_absolute_error"], 0.0)
        self.assertEqual(drift["by_field"]["challenger_pure_premium"]["max_absolute_error"], 0.0)

        self.assertEqual(warning["status"], "NO_XGBOOST_PICKLE_VERSION_WARNING")
        self.assertFalse(warning["warning_detected"])
        self.assertIn("HOLD / HOLD_SHADOW_ONLY", result["governance_boundary"])


if __name__ == "__main__":
    unittest.main()
