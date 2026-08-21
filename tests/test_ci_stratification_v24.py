from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestCIStratificationV24(unittest.TestCase):
    def _text(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_deployment_heavy_workflow_has_narrow_dependency_paths(self) -> None:
        text = self._text(".github/workflows/v21-deployment.yml")
        self.assertNotIn("'deployment/**'", text)
        self.assertNotIn("deployment/review.py", text)
        self.assertIn("deployment/app.py", text)
        self.assertIn("deployment/bundle.py", text)
        self.assertIn("deployment/monitoring.py", text)
        self.assertIn("actions/cache@v4", text)
        self.assertIn("cancel-in-progress: true", text)
        self.assertNotIn("tests/test_evidence_registry.py", text)

    def test_monitoring_heavy_workflow_has_narrow_dependency_paths(self) -> None:
        text = self._text(".github/workflows/v22-monitoring.yml")
        self.assertNotIn("'deployment/**'", text)
        self.assertNotIn("deployment/review.py", text)
        self.assertIn("deployment/app.py", text)
        self.assertIn("deployment/monitoring.py", text)
        self.assertIn("deployment/drift.py", text)
        self.assertIn("actions/cache@v4", text)
        self.assertIn("cancel-in-progress: true", text)
        self.assertNotIn("tests/test_evidence_registry.py", text)

    def test_light_ci_owns_persisted_evidence_validation(self) -> None:
        text = self._text(".github/workflows/ci.yml")
        for path in [
            "action_results/v21/**",
            "action_results/v22/**",
            "action_results/v23/**",
            "tests/test_evidence_registry.py",
        ]:
            self.assertIn(path, text)


if __name__ == "__main__":
    unittest.main()
