from __future__ import annotations

from typing import Callable

import numpy as np
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance


def deterministic_split_indices(
    n_rows: int,
    *,
    seed: int,
    train_fraction: float,
    calibration_fraction: float,
) -> dict[str, np.ndarray]:
    if n_rows < 3:
        raise ValueError("at least three rows are required")
    if not (0 < train_fraction < 1 and 0 < calibration_fraction < 1):
        raise ValueError("split fractions must lie in (0, 1)")
    if train_fraction + calibration_fraction >= 1:
        raise ValueError("train + calibration fractions must leave a locked test")
    permutation = np.random.default_rng(seed).permutation(n_rows)
    train_n = int(np.floor(n_rows * train_fraction))
    calibration_n = int(np.floor(n_rows * calibration_fraction))
    train = permutation[:train_n]
    calibration = permutation[train_n : train_n + calibration_n]
    test = permutation[train_n + calibration_n :]
    if not len(train) or not len(calibration) or not len(test):
        raise ValueError("all split partitions must be non-empty")
    return {"train": train, "calibration": calibration, "test": test}


def multiplicative_calibration_scale(
    observed: np.ndarray,
    predicted_rate: np.ndarray,
    exposure: np.ndarray,
) -> float:
    observed = np.asarray(observed, dtype=float)
    predicted_rate = np.asarray(predicted_rate, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    if not (len(observed) == len(predicted_rate) == len(exposure)) or len(observed) == 0:
        raise ValueError("observed, predicted_rate and exposure must have equal non-zero length")
    if np.any(observed < 0) or np.any(predicted_rate <= 0) or np.any(exposure <= 0):
        raise ValueError("observed must be non-negative and predictions/exposure strictly positive")
    predicted_total = float(np.sum(predicted_rate * exposure))
    observed_total = float(np.sum(observed))
    if observed_total <= 0:
        raise ValueError("calibration split must contain positive observed outcome")
    return observed_total / predicted_total


def aggregate_calibration(
    observed: np.ndarray,
    predicted_rate: np.ndarray,
    exposure: np.ndarray,
) -> dict[str, float]:
    observed = np.asarray(observed, dtype=float)
    predicted_rate = np.asarray(predicted_rate, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    observed_total = float(np.sum(observed))
    predicted_total = float(np.sum(predicted_rate * exposure))
    if observed_total <= 0 or predicted_total <= 0:
        raise ValueError("aggregate calibration requires positive observed and predicted totals")
    ratio = predicted_total / observed_total
    return {
        "predicted_total": predicted_total,
        "observed_total": observed_total,
        "calibration_ratio_pred_over_actual": ratio,
        "abs_log_calibration_error": float(abs(np.log(ratio))),
    }


def poisson_deviance(observed_count: np.ndarray, predicted_rate: np.ndarray, exposure: np.ndarray) -> float:
    observed_count = np.asarray(observed_count, dtype=float)
    predicted_rate = np.asarray(predicted_rate, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    return float(
        mean_poisson_deviance(
            observed_count / exposure,
            predicted_rate,
            sample_weight=exposure,
        )
    )


def tweedie_deviance_p15(observed_amount: np.ndarray, predicted_rate: np.ndarray, exposure: np.ndarray) -> float:
    observed_amount = np.asarray(observed_amount, dtype=float)
    predicted_rate = np.asarray(predicted_rate, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    return float(
        mean_tweedie_deviance(
            observed_amount / exposure,
            predicted_rate,
            sample_weight=exposure,
            power=1.5,
        )
    )


def top_exposure_capture(
    observed: np.ndarray,
    predicted_rate: np.ndarray,
    exposure: np.ndarray,
    *,
    fraction: float = 0.10,
) -> float:
    """Observed outcome captured in the highest predicted-risk exposure share.

    The boundary policy is fractionally allocated when it crosses the requested
    exposure fraction, avoiding a row-size artefact in lift comparisons.
    """
    observed = np.asarray(observed, dtype=float)
    predicted_rate = np.asarray(predicted_rate, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    if not (0 < fraction <= 1):
        raise ValueError("fraction must be in (0, 1]")
    if np.any(exposure <= 0):
        raise ValueError("exposure must be strictly positive")
    total_observed = float(np.sum(observed))
    if total_observed <= 0:
        raise ValueError("capture requires positive observed total")
    target_exposure = float(np.sum(exposure)) * fraction
    order = np.argsort(-predicted_rate, kind="stable")
    captured = 0.0
    consumed_exposure = 0.0
    for idx in order:
        remaining = target_exposure - consumed_exposure
        if remaining <= 0:
            break
        take_fraction = min(1.0, remaining / float(exposure[idx]))
        captured += float(observed[idx]) * take_fraction
        consumed_exposure += float(exposure[idx]) * take_fraction
    return captured / total_observed


def paired_bootstrap_relative_improvement(
    observed: np.ndarray,
    reference_pred: np.ndarray,
    challenger_pred: np.ndarray,
    exposure: np.ndarray,
    *,
    metric: Callable[[np.ndarray, np.ndarray, np.ndarray], float],
    draws: int,
    seed: int,
) -> np.ndarray:
    observed = np.asarray(observed, dtype=float)
    reference_pred = np.asarray(reference_pred, dtype=float)
    challenger_pred = np.asarray(challenger_pred, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    n = len(observed)
    if not (n == len(reference_pred) == len(challenger_pred) == len(exposure)) or n == 0:
        raise ValueError("bootstrap arrays must have equal non-zero length")
    if draws < 1:
        raise ValueError("draws must be positive")
    rng = np.random.default_rng(seed)
    results = np.empty(draws, dtype=float)
    for draw in range(draws):
        index = rng.integers(0, n, size=n)
        reference = metric(observed[index], reference_pred[index], exposure[index])
        challenger = metric(observed[index], challenger_pred[index], exposure[index])
        results[draw] = 1.0 - challenger / reference
    return results


def percentile_interval(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("interval values must be finite and non-empty")
    return {
        "q025": float(np.quantile(values, 0.025)),
        "median": float(np.quantile(values, 0.50)),
        "q975": float(np.quantile(values, 0.975)),
    }


def evaluate_replication_gate(
    *,
    reference_deviance: float,
    challenger_deviance: float,
    reference_abs_log_calibration_error: float,
    challenger_abs_log_calibration_error: float,
    bootstrap_interval: dict[str, float],
    minimum_relative_deviance_improvement: float,
    bootstrap_ci_lower_bound_must_exceed: float,
    maximum_additional_abs_log_calibration_error: float,
    calibration_scales_valid: bool,
    pass_label: str,
    fail_label: str,
) -> dict[str, object]:
    relative_improvement = 1.0 - float(challenger_deviance) / float(reference_deviance)
    checks = {
        "calibration_scales_valid": bool(calibration_scales_valid),
        "point_relative_deviance_improvement": bool(
            relative_improvement >= minimum_relative_deviance_improvement
        ),
        "bootstrap_ci_lower_bound_positive": bool(
            bootstrap_interval["q025"] > bootstrap_ci_lower_bound_must_exceed
        ),
        "aggregate_calibration_noninferior": bool(
            challenger_abs_log_calibration_error
            <= reference_abs_log_calibration_error + maximum_additional_abs_log_calibration_error
        ),
    }
    passed = all(checks.values())
    return {
        "decision": pass_label if passed else fail_label,
        "passed": passed,
        "relative_deviance_improvement": relative_improvement,
        "checks": checks,
    }
