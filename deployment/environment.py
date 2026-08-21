from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
import xgboost


CRITICAL_MODEL_ENV_KEYS = (
    "python_major_minor",
    "numpy",
    "pandas",
    "scipy",
    "scikit_learn",
    "xgboost",
    "joblib",
)


def capture_model_environment() -> dict[str, str]:
    """Capture versions that affect the persisted sklearn/joblib model pipeline."""
    return {
        "python_major_minor": f"{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}",
        "python_full": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "xgboost": xgboost.__version__,
        "joblib": joblib.__version__,
    }


@dataclass(frozen=True)
class EnvironmentCompatibility:
    status: str
    expected: dict[str, str]
    runtime: dict[str, str]
    mismatches: dict[str, dict[str, str]]

    @property
    def compatible(self) -> bool:
        return self.status == "EXACT_MODEL_STACK_MATCH"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "compatible": self.compatible,
            "policy": "exact_match_for_joblib_pickle_model_stack",
            "critical_keys": list(CRITICAL_MODEL_ENV_KEYS),
            "expected": self.expected,
            "runtime": self.runtime,
            "mismatches": self.mismatches,
        }


def compare_model_environments(
    expected: dict[str, str], runtime: dict[str, str] | None = None
) -> EnvironmentCompatibility:
    runtime = capture_model_environment() if runtime is None else dict(runtime)
    missing = [key for key in CRITICAL_MODEL_ENV_KEYS if key not in expected]
    if missing:
        mismatches = {
            key: {"expected": "<missing>", "runtime": runtime.get(key, "<missing>")}
            for key in missing
        }
        return EnvironmentCompatibility(
            status="REJECT_MISSING_TRAINING_ENVIRONMENT",
            expected=dict(expected),
            runtime=runtime,
            mismatches=mismatches,
        )

    mismatches = {
        key: {"expected": str(expected[key]), "runtime": str(runtime.get(key, "<missing>"))}
        for key in CRITICAL_MODEL_ENV_KEYS
        if str(expected[key]) != str(runtime.get(key, "<missing>"))
    }
    return EnvironmentCompatibility(
        status="EXACT_MODEL_STACK_MATCH" if not mismatches else "REJECT_MODEL_STACK_MISMATCH",
        expected=dict(expected),
        runtime=runtime,
        mismatches=mismatches,
    )


def require_model_environment_compatibility(
    expected: dict[str, str], runtime: dict[str, str] | None = None
) -> EnvironmentCompatibility:
    report = compare_model_environments(expected, runtime)
    if not report.compatible:
        details = ", ".join(
            f"{key}: expected={value['expected']} runtime={value['runtime']}"
            for key, value in report.mismatches.items()
        )
        raise RuntimeError(
            f"Model environment compatibility gate failed ({report.status}). {details}"
        )
    return report
