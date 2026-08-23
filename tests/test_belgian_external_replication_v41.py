from __future__ import annotations

import json
import unittest
from pathlib import Path

from external_validation.replication import deterministic_split_indices
from validate_external_validation_prereg_v40 import canonical_sha256, validate_prereg

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "governance" / "external_validation_prereg_v40.json"
LOCK = ROOT / "action_results" / "v40" / "belgian_external_validation_prereg_lock.json"
STATUS = ROOT / "action_results" / "v40" / "ACTION_V40_STATUS.json"
RUNNER = ROOT / "run_belgian_external_replication_v41.py"
DOWNLOADER = ROOT / "download_belgian_motor_v41.py"
WORKFLOW = ROOT / ".github" / "workflows" / "v41-belgian-external-replication.yml"
EXPECTED_HASH = "19658e3a6b12e55ffaa564585bf69dd09ad1371b567f0c1b03c7d17103796822"
EXPECTED_MAIN_SHA = "833e861ee797d3751090e4d08a512d9f340b5378"


class BelgianExternalReplicationV41Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        cls.lock = json.loads(LOCK.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS.read_text(encoding="utf-8"))

    def test_v40_preregistration_is_main_persisted_before_execution(self) -> None:
        validate_prereg(self.prereg)
        self.assertEqual(canonical_sha256(self.prereg), EXPECTED_HASH)
        self.assertEqual(self.lock["preregistration_sha256"], EXPECTED_HASH)
        self.assertEqual(self.status["sha"], EXPECTED_MAIN_SHA)
        self.assertEqual(self.status["status"], "success")
        self.assertFalse(self.status["row_level_external_data_accessed"])
        self.assertEqual(self.status["positive_support_minimum_independent_executions"], 2)

    def test_deterministic_split_sizes_are_fixed_before_outcomes(self) -> None:
        split = deterministic_split_indices(163212, seed=20260825, train_fraction=0.6, calibration_fraction=0.2)
        self.assertEqual(len(split["train"]), 97927)
        self.assertEqual(len(split["calibration"]), 32642)
        self.assertEqual(len(split["test"]), 32643)
        self.assertEqual(len(set(split["train"]) | set(split["calibration"]) | set(split["test"])), 163212)

    def test_downloader_uses_only_registered_pinned_source(self) -> None:
        text = DOWNLOADER.read_text(encoding="utf-8")
        self.assertIn("source['upstream_repository']", text)
        self.assertIn("source['upstream_commit']", text)
        self.assertIn("source['upstream_path']", text)
        self.assertIn('destination = OUTDIR / "beMTPL97.rda"', text)
        self.assertIn('frame["id"].duplicated()', text)
        self.assertIn('(exposure > 1)', text)

    def test_runner_enforces_registered_preprocessing_and_solver(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("StandardScaler()", text)
        self.assertIn('OneHotEncoder(handle_unknown="ignore", sparse_output=False)', text)
        self.assertIn("ConvergenceWarning", text)
        self.assertIn('"lbfgs" in message.lower()', text)
        self.assertIn("positive_external_support_authorised\": False", text)
        self.assertNotIn("np.clip", text)

    def test_first_execution_cannot_satisfy_two_run_positive_support_rule(self) -> None:
        runtime = self.prereg["runtime_reproducibility"]
        self.assertEqual(runtime["minimum_independent_actions_executions_for_positive_external_support"], 2)
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('"executions_completed_for_this_new_portfolio": 1', text)
        self.assertIn('"positive_external_support_authorised": False', text)
        self.assertIn("SECOND_EXECUTION_REQUIRED_BEFORE_ANY_POSITIVE_SUPPORT", text)

    def test_workflow_sets_registered_single_thread_environment(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        for assignment in ("OMP_NUM_THREADS: '1'", "OPENBLAS_NUM_THREADS: '1'", "MKL_NUM_THREADS: '1'"):
            self.assertIn(assignment, text)
        self.assertIn("tests/test_belgian_external_replication_v41.py", text)
        self.assertIn("download_belgian_motor_v41.py", text)
        self.assertIn("run_belgian_external_replication_v41.py", text)
        self.assertIn("scripts/push_evidence_with_rebase.sh", text)


if __name__ == "__main__":
    unittest.main()
