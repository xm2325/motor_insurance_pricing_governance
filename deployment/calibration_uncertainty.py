from __future__ import annotations

from typing import Any, Iterable, Mapping

import numpy as np


def _float_array(values: Iterable[float], *, name: str) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.ndim != 1 or len(arr) == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _segment_array(values: Iterable[str]) -> np.ndarray:
    arr = np.asarray([str(value) for value in values], dtype=object)
    if arr.ndim != 1 or len(arr) == 0:
        raise ValueError("segment must be a non-empty one-dimensional array")
    return arr


def group_frequency_sufficient_statistics(
    segment: Iterable[str],
    claims: Iterable[float],
    exposure: Iterable[float],
    baseline_pred_rate: Iterable[float],
) -> dict[str, dict[str, float]]:
    """Reduce a frequency evaluation set to sufficient statistics for segment scaling.

    `baseline_pred_rate` is already globally calibrated. A later factor m_g scales the
    rate for one segment. No individual-level rows need to be retained after this step.
    """
    segments = _segment_array(segment)
    claims_arr = _float_array(claims, name="claims")
    exposure_arr = _float_array(exposure, name="exposure")
    pred_arr = _float_array(baseline_pred_rate, name="baseline_pred_rate")
    n = len(segments)
    if any(len(arr) != n for arr in (claims_arr, exposure_arr, pred_arr)):
        raise ValueError("segment, claims, exposure and predictions must have equal length")
    if np.any(claims_arr < 0.0):
        raise ValueError("claims must be non-negative")
    if np.any(exposure_arr <= 0.0):
        raise ValueError("exposure must be strictly positive")
    if np.any(pred_arr <= 0.0):
        raise ValueError("baseline predictions must be strictly positive")

    stats: dict[str, dict[str, float]] = {}
    for group in sorted(np.unique(segments).tolist()):
        mask = segments == group
        stats[str(group)] = {
            "rows": int(mask.sum()),
            "claims": float(claims_arr[mask].sum()),
            "exposure": float(exposure_arr[mask].sum()),
            "baseline_expected_claims": float(np.sum(exposure_arr[mask] * pred_arr[mask])),
        }
    return stats


def evaluate_segment_factor_draw(
    *,
    baseline_poisson_deviance: float,
    group_stats: Mapping[str, Mapping[str, float]],
    factors: Mapping[str, float],
) -> dict[str, Any]:
    """Evaluate one set of segment multipliers from frequency sufficient statistics.

    For Poisson deviance, scaling baseline rate lambda_i by segment factor m_g changes
    exposure-weighted mean deviance by

        2 / sum(exposure) * sum_g[-C_g log(m_g) + B_g (m_g - 1)],

    where C_g is observed claims and B_g is baseline expected claims. This permits
    bootstrap sensitivity evaluation without repeatedly rescoring 2024 policy rows.
    """
    if not np.isfinite(baseline_poisson_deviance) or baseline_poisson_deviance < 0.0:
        raise ValueError("baseline_poisson_deviance must be finite and non-negative")
    if not group_stats:
        raise ValueError("group_stats must not be empty")

    total_exposure = 0.0
    total_claims = 0.0
    candidate_expected = 0.0
    deviance_numerator_change = 0.0
    segment_rows: dict[str, dict[str, float]] = {}

    for group, stat in group_stats.items():
        if group not in factors:
            raise ValueError(f"missing factor for segment {group}")
        claims = float(stat["claims"])
        exposure = float(stat["exposure"])
        baseline_expected = float(stat["baseline_expected_claims"])
        factor = float(factors[group])
        if not np.isfinite(factor) or factor <= 0.0:
            raise ValueError("factors must be finite and strictly positive")
        if claims < 0.0 or exposure <= 0.0 or baseline_expected <= 0.0:
            raise ValueError("invalid group sufficient statistics")

        expected = baseline_expected * factor
        ratio = expected / max(claims, 1e-12)
        segment_rows[str(group)] = {
            "factor": factor,
            "claims": claims,
            "exposure": exposure,
            "baseline_expected_claims": baseline_expected,
            "candidate_expected_claims": expected,
            "candidate_calibration_ratio_pred_over_actual": ratio,
            "candidate_abs_log_calibration_error": float(abs(np.log(max(ratio, 1e-12)))),
        }
        total_exposure += exposure
        total_claims += claims
        candidate_expected += expected
        deviance_numerator_change += -claims * np.log(factor) + baseline_expected * (factor - 1.0)

    candidate_deviance = float(
        baseline_poisson_deviance + 2.0 * deviance_numerator_change / max(total_exposure, 1e-12)
    )
    aggregate_ratio = candidate_expected / max(total_claims, 1e-12)
    max_segment_error = max(row["candidate_abs_log_calibration_error"] for row in segment_rows.values())
    return {
        "poisson_deviance": candidate_deviance,
        "aggregate_calibration_ratio_pred_over_actual": aggregate_ratio,
        "aggregate_abs_log_calibration_error": float(abs(np.log(max(aggregate_ratio, 1e-12)))),
        "max_segment_abs_log_calibration_error": float(max_segment_error),
        "segments": segment_rows,
    }


def paired_stratified_bootstrap_factors(
    segment: Iterable[str],
    claims: Iterable[float],
    exposure: Iterable[float],
    prediction_rates: Mapping[str, Iterable[float]],
    *,
    draws: int,
    seed: int,
) -> dict[str, dict[str, np.ndarray]]:
    """Bootstrap raw segment factors from calibration-period rows only.

    Sampling is stratified by segment and each bootstrap replicate uses the same sampled
    row indices across all supplied prediction fields, preserving paired GLM/XGBoost
    comparisons. Factors are intentionally *not clipped*: uncertainty outside later
    operational guardrails must remain visible rather than being hidden by truncation.
    """
    if draws < 1:
        raise ValueError("draws must be positive")
    segments = _segment_array(segment)
    claims_arr = _float_array(claims, name="claims")
    exposure_arr = _float_array(exposure, name="exposure")
    n = len(segments)
    if len(claims_arr) != n or len(exposure_arr) != n:
        raise ValueError("segment, claims and exposure must have equal length")
    if np.any(claims_arr < 0.0) or np.any(exposure_arr <= 0.0):
        raise ValueError("claims must be non-negative and exposure strictly positive")

    predictions: dict[str, np.ndarray] = {}
    for field, values in prediction_rates.items():
        arr = _float_array(values, name=f"prediction_rates[{field}]")
        if len(arr) != n:
            raise ValueError("all prediction arrays must match calibration rows")
        if np.any(arr <= 0.0):
            raise ValueError("prediction rates must be strictly positive")
        predictions[str(field)] = arr
    if not predictions:
        raise ValueError("at least one prediction field is required")

    groups = sorted(np.unique(segments).tolist())
    indices = {str(group): np.flatnonzero(segments == group) for group in groups}
    rng = np.random.default_rng(int(seed))
    output = {
        field: {str(group): np.empty(draws, dtype=float) for group in groups}
        for field in predictions
    }

    for draw in range(draws):
        for group in groups:
            group_name = str(group)
            group_idx = indices[group_name]
            sampled = rng.choice(group_idx, size=len(group_idx), replace=True)
            observed = float(claims_arr[sampled].sum())
            if observed <= 0.0:
                raise ValueError(f"bootstrap draw has no observed claims for segment {group_name}")
            sampled_exposure = exposure_arr[sampled]
            for field, pred in predictions.items():
                predicted = float(np.sum(sampled_exposure * pred[sampled]))
                if predicted <= 0.0:
                    raise ValueError("bootstrap predicted claims must be positive")
                output[field][group_name][draw] = observed / predicted
    return output


def quantile_summary(values: Iterable[float]) -> dict[str, float]:
    arr = _float_array(values, name="values")
    return {
        "q025": float(np.quantile(arr, 0.025)),
        "median": float(np.quantile(arr, 0.5)),
        "q975": float(np.quantile(arr, 0.975)),
    }
