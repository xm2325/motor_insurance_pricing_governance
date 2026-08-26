import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REG_PATH = ROOT / "governance" / "prospective_request_registration_v61.json"
IMPL_PATH = ROOT / "governance" / "s1_execution_implementation_v62.json"
RUNNER_PATH = ROOT / "run_pricing_game_s1_temporal_v62.py"
DOWNLOADER_PATH = ROOT / "download_pricing_game_motor_v62.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "v62-pricing-game-s1-temporal.yml"
V61_STATUS = ROOT / "action_results" / "v61" / "origin" / "32793349122" / "ACTION_V61_STATUS.json"

spec = importlib.util.spec_from_file_location("v62_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class PricingGameS1TemporalV62Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registration = json.loads(REG_PATH.read_text())
        cls.impl = json.loads(IMPL_PATH.read_text())
        cls.v61 = json.loads(V61_STATUS.read_text())

    def test_parent_registration_and_immutable_lock_are_exact(self):
        self.assertEqual(runner.canonical_sha256(self.registration), runner.EXPECTED_PROTOCOL_SHA256)
        self.assertEqual(runner.EXPECTED_PROTOCOL_SHA256, "80533141f88b042a02618d609f77d355f32c9d81ce53569aece27aab207a58c9")
        self.assertEqual(self.v61["run_id"], "32793349122")
        self.assertEqual(self.v61["protocol_canonical_sha256"], runner.EXPECTED_PROTOCOL_SHA256)
        self.assertEqual(self.v61["request_lifecycle"], "REGISTERED_SEALED_BEFORE_S1")
        self.assertFalse(self.v61["s1_open"])
        self.assertFalse(self.v61["s2_open"])
        self.assertFalse(self.v61["s3_open"])
        self.assertTrue(self.v61["s3_reserve_sealed"])

    def test_implementation_seal_precedes_access_and_does_not_change_registered_question(self):
        self.assertEqual(self.impl["request_id"], "MCR-XGB-MOTOR-002")
        self.assertEqual(self.impl["stage"], "S1_TEMPORAL_QUALIFICATION")
        self.assertEqual(self.impl["parent_registration"]["canonical_sha256"], runner.EXPECTED_PROTOCOL_SHA256)
        for key in ["pg15training_downloaded", "pg15training_decoded", "pg15training_row_values_accessed", "pg15training_outcome_values_accessed", "model_fit_executed", "s2_open", "s3_open"]:
            self.assertFalse(self.impl["access_state_at_seal"][key], key)
        self.assertEqual(self.registration["activation"]["programme_scope"], "GLOBAL_TWO_TARGET")
        self.assertFalse(self.registration["registered_model_family"]["hyperparameter_search"])
        self.assertFalse(self.registration["registered_model_family"]["early_stopping"])

    def test_s1_binary_identity_is_exact_and_s2_s3_are_not_execution_inputs(self):
        s1 = self.registration["sources"]["S1_TEMPORAL_QUALIFICATION"]
        self.assertEqual(s1["rda_files"], [{"path": "data/pg15training.rda", "git_blob_sha1": "9e670d214c05a7454d558ab32de5df96a6b0aba6", "bytes": 1934161}])
        downloader = DOWNLOADER_PATH.read_text()
        runner_text = RUNNER_PATH.read_text()
        self.assertNotIn("swmotorcycle.rda", downloader + runner_text)
        self.assertNotIn("brvehins1a.rda", downloader + runner_text)
        self.assertNotIn("brvehins1b.rda", downloader + runner_text)

    def test_policy_id_canonicalisation_is_frozen(self):
        self.assertEqual(runner.canonical_policy_id(123), "123")
        self.assertEqual(runner.canonical_policy_id(123.0), "123")
        self.assertEqual(runner.canonical_policy_id(" 123.000 "), "123")
        self.assertEqual(runner.canonical_policy_id("00123"), "00123")
        self.assertEqual(runner.canonical_policy_id(" ABC-7 "), "ABC-7")
        with self.assertRaises(RuntimeError):
            runner.canonical_policy_id(123.5)
        with self.assertRaises(RuntimeError):
            runner.canonical_policy_id(np.nan)

    def test_cross_year_filter_uses_keys_only_and_removes_every_cross_year_row(self):
        keys = pd.DataFrame({
            "PolNum": [1, 1, 2, 2, 3, 4],
            "CalYear": [2009, 2010, 2009, 2009, 2010, 2010],
        })
        keep, ids, years, meta = runner.pre_outcome_cross_year_filter(keys)
        self.assertEqual(keep.tolist(), [False, False, True, True, True, True])
        self.assertEqual(ids.tolist(), ["2", "2", "3", "4"])
        self.assertEqual(years.tolist(), [2009, 2009, 2010, 2010])
        self.assertEqual(meta["cross_year_policy_ids_observed"], 1)
        self.assertEqual(meta["rows_removed_for_cross_year_policies"], 2)
        self.assertEqual(meta["outcome_columns_accessed_during_barrier"], [])
        with self.assertRaises(RuntimeError):
            runner.pre_outcome_cross_year_filter(pd.DataFrame({"PolNum": [1], "CalYear": [2009], "Numtppd": [0]}))

    def test_year_set_must_be_exact_before_outcomes(self):
        with self.assertRaises(RuntimeError):
            runner.pre_outcome_cross_year_filter(pd.DataFrame({"PolNum": [1, 2], "CalYear": [2009, 2011]}))

    def test_temporal_hash_split_keeps_policy_ids_disjoint(self):
        ids = np.array([str(i) for i in range(100)] + ["200", "201"], dtype=object)
        years = np.array([2009] * 100 + [2010, 2010], dtype=int)
        splits = runner.temporal_split(ids, years)
        train_ids = set(ids[splits["train"]])
        cal_ids = set(ids[splits["calibration"]])
        test_ids = set(ids[splits["test"]])
        self.assertFalse(train_ids & cal_ids)
        self.assertFalse(train_ids & test_ids)
        self.assertFalse(cal_ids & test_ids)
        self.assertEqual(test_ids, {"200", "201"})
        for idx in splits["train"]:
            self.assertLess(runner.policy_bucket(str(ids[idx])), 8000)
        for idx in splits["calibration"]:
            self.assertGreaterEqual(runner.policy_bucket(str(ids[idx])), 8000)

    def test_runner_source_order_encodes_pre_outcome_barrier(self):
        text = RUNNER_PATH.read_text()
        key_access = text.index('key_frame = frame[["PolNum", "CalYear"]].copy()')
        barrier = text.index("pre_outcome_cross_year_filter(key_frame)")
        clean = text.index("clean = frame.loc[keep].reset_index(drop=True)")
        exposure = text.index('clean["Expdays"]')
        claim = text.index('clean["Numtppd"]')
        loss = text.index('clean["Indtppd"]')
        self.assertLess(key_access, barrier)
        self.assertLess(barrier, clean)
        self.assertLess(clean, exposure)
        self.assertLess(clean, claim)
        self.assertLess(clean, loss)

    def test_registered_models_and_gates_are_unchanged(self):
        model = self.registration["registered_model_family"]
        self.assertEqual(model["frequency_reference"], {"estimator": "PoissonRegressor", "alpha": 1e-8, "solver": "newton-cholesky", "tol": 1e-10, "max_iter": 2000})
        self.assertEqual(model["pure_premium_reference"], {"estimator": "TweedieRegressor", "power": 1.5, "link": "log", "alpha": 1e-6, "solver": "newton-cholesky", "tol": 1e-10, "max_iter": 3000})
        for key in ("frequency_challenger", "pure_premium_challenger"):
            self.assertEqual(model[key]["n_estimators"], 400)
            self.assertEqual(model[key]["max_depth"], 3)
            self.assertEqual(model[key]["learning_rate"], 0.05)
            self.assertEqual(model[key]["n_jobs"], 1)
            self.assertEqual(model[key]["random_state"], 20260823)
        gate = self.registration["target_gate"]
        self.assertEqual(gate["point_relative_deviance_improvement_min"], 0.005)
        self.assertEqual(gate["bootstrap_relative_deviance_improvement_q025_must_be_strictly_greater_than"], 0.0)
        self.assertEqual(gate["challenger_absolute_log_calibration_error_must_be_lte_reference_plus"], 0.01)
        self.assertTrue(self.registration["stage_gate"]["GLOBAL_TWO_TARGET_requires_frequency_and_pure_premium_both_pass"])
        self.assertTrue(self.registration["stage_gate"]["positive_stage_requires_two_independent_github_actions_executions"])

    def test_workflow_orders_contracts_download_then_execution(self):
        text = WORKFLOW_PATH.read_text()
        contracts = text.index("Verify v0.62 contracts before S1 data access")
        download = text.index("Fetch and verify pinned Pricing Game S1 binary")
        execute = text.index("Execute frozen S1 temporal qualification once")
        self.assertLess(contracts, download)
        self.assertLess(download, execute)
        self.assertIn("OMP_NUM_THREADS: '1'", text)
        self.assertIn("OPENBLAS_NUM_THREADS: '1'", text)
        self.assertIn("MKL_NUM_THREADS: '1'", text)

    def test_first_execution_cannot_open_s2_or_s3(self):
        labels = self.impl["stage_decision_labels"]
        self.assertIn("PENDING_INDEPENDENT_REPRODUCTION", labels["first_execution_both_targets_pass"])
        self.assertIn("TERMINAL", labels["any_target_fails"])
        self.assertIn("only a first execution with both target gates passing", labels["second_execution_opening_rule"])
        runner_text = RUNNER_PATH.read_text()
        self.assertIn('"s2_open_authorised": False', runner_text)
        self.assertIn('"s3_open_authorised": False', runner_text)


if __name__ == "__main__":
    unittest.main()
