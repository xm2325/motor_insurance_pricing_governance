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


CRITICAL_PICKLE_ENV_KEYS = (
    "python_major_minor",
    "numpy",
    "pandas",
    "scipy",
    "scikit_learn",
    "joblib",
)


def _major_minor(version: str) -> str:
    parts = str(version).split(".")
    if len(parts) < 2:
        return str(version)
    return ".".join(parts[:2])


def capture_model_environment() -> dict[str, str]:
    """Capture versions that affect the persisted sklearn/joblib + native-XGBoost bundle."""
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
    pickle_mismatches: dict[str, dict[str, str]]
    xgboost_native_compatible: bool

    @property
    def compatible(self) -> bool:
        return self.status == "HYBRID_MODEL_IO_COMPATIBLE"

    @property
    def mismatches(self) -> dict[str, dict[str, str]]:
        result = dict(self.pickle_mismatches)
        if not self.xgboost_native_compatible:
            result["xgboost"] = {
                "expected": self.expected.get("xgboost", "<missing>"),
                "runtime": self.runtime.get("xgboost", "<missing>"),
            }
        return result

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "compatible": self.compatible,
            "pickle_policy": "exact_match_for_joblib_pickle_stack",
            "xgboost_policy": "same_major_minor_for_native_model_io",
            "critical_pickle_keys": list(CRITICAL_PICKLE_ENV_KEYS),
            "expected": self.expected,
            "runtime": self.runtime,
            "pickle_mismatches": self.pickle_mismatches,
            "xgboost_native_compatible": self.xgboost_native_compatible,
            "mismatches": self.mismatches,
        }


def compare_model_environments(
    expected: dict[str, str], runtime: dict[str, str] | None = None
) -> EnvironmentCompatibility:
    runtime = capture_model_environment() if runtime is None else dict(runtime)
    required = (*CRITICAL_PICKLE_ENV_KEYS, "xgboost")
    missing = [key for key in required if key not in expected]
    if missing:
        pickle_mismatches = {
            key: {"expected": "<missing>", "runtime": runtime.get(key, "<missing>")}
            for key in missing
            if key in CRITICAL_PICKLE_ENV_KEYS
        }
        xgb_ok = "xgboost" not in missing
        return EnvironmentCompatibility(
            status="REJECT_MISSING_TRAINING_ENVIRONMENT",
            expected=dict(expected),
            runtime=runtime,
            pickle_mismatches=pickle_mismatches,
            xgboost_native_compatible=xgb_ok,
        )

    pickle_mismatches = {
        key: {"expected": str(expected[key]), "runtime": str(runtime.get(key, "<missing>"))}
        for key in CRITICAL_PICKLE_ENV_KEYS
        if str(expected[key]) != str(runtime.get(key, "<missing>"))
    }
    xgb_runtime = runtime.get("xgboost", "<missing>")
    xgb_ok = _major_minor(expected["xgboost"]) == _major_minor(xgb_runtime)

    if pickle_mismatches:
        status = "REJECT_PICKLE_STACK_MISMATCH"
    elif not xgb_ok:
        status = "REJECT_XGBOOST_NATIVE_VERSION_MISMATCH"
    else:
        status = "HYBRID_MODEL_IO_COMPATIBLE"

    return EnvironmentCompatibility(
        status=status,
        expected=dict(expected),
        runtime=runtime,
        pickle_mismatches=pickle_mismatches,
        xgboost_native_compatible=xgb_ok,
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
