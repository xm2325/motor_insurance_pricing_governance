from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from deployment.contracts import CATEGORICAL_FEATURES, NUMERIC_FEATURES

MISSING = "__MISSING__"
UNSEEN = "__UNSEEN__"


def psi(expected: list[float], actual: list[float], epsilon: float = 1e-6) -> float:
    expected_arr = np.asarray(expected, dtype=float) + epsilon
    actual_arr = np.asarray(actual, dtype=float) + epsilon
    expected_arr /= expected_arr.sum()
    actual_arr /= actual_arr.sum()
    return float(np.sum((actual_arr - expected_arr) * np.log(actual_arr / expected_arr)))


def build_monitoring_baseline(frame: pd.DataFrame) -> dict[str, Any]:
    numeric: dict[str, Any] = {}
    categorical: dict[str, Any] = {}

    for field in NUMERIC_FEATURES:
        series = pd.to_numeric(frame[field], errors="coerce")
        non_missing = series.dropna().to_numpy(float)
        if len(non_missing) == 0:
            cut_points: list[float] = []
        else:
            quantiles = np.quantile(non_missing, np.linspace(0.1, 0.9, 9))
            cut_points = sorted({float(value) for value in quantiles})
        regular_bins = len(cut_points) + 1
        counts = np.zeros(regular_bins + 1, dtype=float)  # last bucket is missing
        for value in series:
            if pd.isna(value):
                counts[-1] += 1
            else:
                counts[int(np.searchsorted(cut_points, float(value), side="right"))] += 1
        proportions = counts / max(counts.sum(), 1.0)
        numeric[field] = {
            "cut_points": cut_points,
            "expected_proportions": proportions.tolist(),
            "missing_bucket": regular_bins,
        }

    for field in CATEGORICAL_FEATURES:
        values = frame[field].map(lambda value: MISSING if pd.isna(value) else str(value))
        counts = values.value_counts(dropna=False).to_dict()
        total = max(float(len(values)), 1.0)
        proportions = {str(key): float(value) / total for key, value in counts.items()}
        proportions.setdefault(MISSING, 0.0)
        proportions[UNSEEN] = 0.0
        categorical[field] = {"expected_proportions": proportions}

    return {
        "source": "2022_training_features",
        "numeric": numeric,
        "categorical": categorical,
        "interpretation": (
            "Aggregate feature-distribution baseline for shadow monitoring only. "
            "No policy rows or customer identifiers are stored in the manifest."
        ),
    }
