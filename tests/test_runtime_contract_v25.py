from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestRuntimeContractV25(unittest.TestCase):
    def test_serving_image_uses_runtime_requirements(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY requirements-runtime.txt ./", dockerfile)
        self.assertIn("pip install --no-cache-dir -r requirements-runtime.txt", dockerfile)
        self.assertNotIn("pip install --no-cache-dir -r requirements.txt", dockerfile)

    def test_runtime_requirements_are_cpu_only_and_serving_scoped(self):
        lines = {
            line.strip().lower()
            for line in (ROOT / "requirements-runtime.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        joined = "\n".join(sorted(lines))
        self.assertIn("xgboost-cpu", joined)
        self.assertNotIn("\nxgboost>=", "\n" + joined)
        for forbidden in ("matplotlib", "pytest", "tabulate", "httpx", "nvidia-nccl"):
            self.assertNotIn(forbidden, joined)
        for required in ("numpy", "pandas", "scipy", "scikit-learn", "joblib", "fastapi", "uvicorn"):
            self.assertIn(required, joined)


if __name__ == "__main__":
    unittest.main()
