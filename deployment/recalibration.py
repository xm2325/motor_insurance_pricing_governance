from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def _as_float_array(values: Iterable[float], *, name: str) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _as_segment_array(values: Iterable[str]) -> np.ndarray:
    arr = np.asarray([str(value) for value in values], dtype=object)
    if arr.ndim != 1:
        raise ValueError("segment must be one-dimensional")
    return arr


def calibration_ratio(actual: np.ndarray, pred_rate: np.ndarray, exposure: np.ndarray) -> float:
    predicted = float(np.sum(pred_rate * exposure))
    observed = float(np.sum(actual))
    return predicted / max(observed, 1e-12)


def fit_segment_multipliers(
    segment: Iterable[str],
    actual: Iterable[float],
    pred_rate: Iterable[float],
    exposure: Iterable[float],
    *,
    minimum_segment_rows: int = 500,
    minimum_segment_exposure_share: float = 0.01,
    multiplier_floor: float = 0.50,
    multiplier_cap: float = 2.00,
) -> dict[str, dict[str, Any]]:
    """Fit multiplicative segment recalibration using calibration-period labels only.

    Predictions supplied here are expected to already contain the existing global
    calibration scale. A segment multiplier of 1 therefore means retain the global
    calibration. Small/unsupported segments fall back to 1.0, and supported factors
    are bounded by project guardrails before any later OOT evaluation.
    """
    segments = _as_segment_array(segment)
    actual_arr = _as_float_array(actual, name="actual")
    pred_arr = _as_float_array(pred_rate, name="pred_rate")
    exposure_arr = _as_float_array(exposure, name="exposure")

    n = len(exposure_arr)
    if any(len(arr) != n for arr in (segments, actual_arr, pred_arr)):
        raise ValueError("segment, actual, pred_rate and exposure must have equal length")
    if n == 0:
        raise ValueError("at least one row is required")
    if np.any(exposure_arr <= 0):
        raise ValueError("exposure must be strictly positive")
    if np.any(actual_arr < 0):
        raise ValueError("actual must be non-negative")
    if np.any(pred_arr <= 0):
        raise ValueError("pred_rate must be strictly positive")
    if minimum_segment_rows < 1:
        raise ValueError("minimum_segment_rows must be positive")
    if not (0.0 < minimum_segment_exposure_share <= 1.0):
        raise ValueError("minimum_segment_exposure_share must be in (0, 1]")
    if not (0.0 < multiplier_floor <= 1.0 <= multiplier_cap):
        raise ValueError("multiplier bounds must satisfy 0 < floor <= 1 <= cap")

    total_exposure = float(exposure_arr.sum())
    fitted: dict[str, dict[str, Any]] = {}
    for group in sorted(np.unique(segments).tolist()):
        mask = segments == group
        group_exposure = float(exposure_arr[mask].sum())
        exposure_share = group_exposure / max(total_exposure, 1e-12)
        observed = float(actual_arr[mask].sum())
        predicted = float(np.sum(pred_arr[mask] * exposure_arr[mask]))
        raw_ratio = predicted / max(observed, 1e-12)
        raw_multiplier = 1.0 / max(raw_ratio, 1e-12)

        supported = (
            int(mask.sum()) >= int(minimum_segment_rows)
            and exposure_share >= float(minimum_segment_exposure_share)
            and observed > 0.0
        )
        if supported:
            multiplier = float(np.clip(raw_multiplier, multiplier_floor, multiplier_cap))
            fallback_reason = None
        else:
            multiplier = 1.0
            if observed <= 0.0:
                fallback_reason = "NO_OBSERVED_OUTCOME"
            elif int(mask.sum()) < int(minimum_segment_rows):
                fallback_reason = "INSUFFICIENT_ROWS"
            else:
                fallback_reason = "INSUFFICIENT_EXPOSURE_SHARE"

        fitted[str(group)] = {
            "segment": str(group),
            "rows": int(mask.sum()),
            "exposure": group_exposure,
            "exposure_share": exposure_share,
            "observed": observed,
            "predicted": predicted,
            "calibration_ratio_pred_over_actual": raw_ratio,
            "raw_multiplier": raw_multiplier,
            "locked_multiplier": multiplier,
            "supported": bool(supported),
            "fallback_reason": fallback_reason,
            "multiplier_was_clipped": bool(supported and not np.isclose(multiplier, raw_multiplier)),
        }
    return fitted


def apply_segment_multipliers(
    segment: Iterable[str],
    pred_rate: Iterable[float],
    fitted: dict[str, dict[str, Any]],
) -> np.ndarray:
    segments = _as_segment_array(segment)
    pred_arr = _as_float_array(pred_rate, name="pred_rate")
    if len(segments) != len(pred_arr):
        raise ValueError("segment and pred_rate must have equal length")
    multipliers = np.ones(len(pred_arr), dtype=float)
    for idx, group in enumerate(segments):
        metadata = fitted.get(str(group))
        multipliers[idx] = 1.0 if metadata is None else float(metadata["locked_multiplier"])
    return np.clip(pred_arr * multipliers, 1e-12, None)


def segment_calibration_rows(
    segment: Iterable[str],
    actual: Iterable[float],
    exposure: Iterable[float],
    baseline_pred: Iterable[float],
    candidate_pred: Iterable[float],
) -> list[dict[str, Any]]:
    segments = _as_segment_array(segment)
    actual_arr = _as_float_array(actual, name="actual")
    exposure_arr = _as_float_array(exposure, name="exposure")
    baseline = _as_float_array(baseline_pred, name="baseline_pred")
    candidate = _as_float_array(candidate_pred, name="candidate_pred")
    n = len(exposure_arr)
    if any(len(arr) != n for arr in (segments, actual_arr, baseline, candidate)):
        raise ValueError("all arrays must have equal length")

    rows: list[dict[str, Any]] = []
    for group in sorted(np.unique(segments).tolist()):
        mask = segments == group
        exp = exposure_arr[mask]
        obs = actual_arr[mask]
        baseline_ratio = calibration_ratio(obs, baseline[mask], exp)
        candidate_ratio = calibration_ratio(obs, candidate[mask], exp)
        rows.append(
            {
                "segment": str(group),
                "rows": int(mask.sum()),
                "exposure": float(exp.sum()),
                "exposure_share": float(exp.sum() / max(exposure_arr.sum(), 1e-12)),
                "observed": float(obs.sum()),
                "baseline_calibration_ratio": baseline_ratio,
                "candidate_calibration_ratio": candidate_ratio,
                "baseline_abs_log_calibration_error": float(abs(np.log(max(baseline_ratio, 1e-12)))),
                "candidate_abs_log_calibration_error": float(abs(np.log(max(candidate_ratio, 1e-12)))),
            }
        )
    return rows


def portfolio_mix_decomposition(
    calibration_segment: Iterable[str],
    calibration_actual: Iterable[float],
    calibration_exposure: Iterable[float],
    calibration_pred: Iterable[float],
    test_segment: Iterable[str],
    test_actual: Iterable[float],
    test_exposure: Iterable[float],
    test_pred: Iterable[float],
) -> dict[str, float]:
    """Exact log-ratio decomposition of calibration drift into mix and residual time effects.

    The mix-only counterfactual applies 2024 exposure shares to 2023 segment-level
    observed and predicted rates. It uses 2024 segment/exposure information but no
    2024 outcomes. The remaining log-ratio change is the within-segment/time component.
    """
    cal_seg = _as_segment_array(calibration_segment)
    cal_actual = _as_float_array(calibration_actual, name="calibration_actual")
    cal_exp = _as_float_array(calibration_exposure, name="calibration_exposure")
    cal_pred = _as_float_array(calibration_pred, name="calibration_pred")
    test_seg = _as_segment_array(test_segment)
    test_actual_arr = _as_float_array(test_actual, name="test_actual")
    test_exp = _as_float_array(test_exposure, name="test_exposure")
    test_pred_arr = _as_float_array(test_pred, name="test_pred")

    if any(len(arr) != len(cal_exp) for arr in (cal_seg, cal_actual, cal_pred)):
        raise ValueError("calibration arrays must have equal length")
    if any(len(arr) != len(test_exp) for arr in (test_seg, test_actual_arr, test_pred_arr)):
        raise ValueError("test arrays must have equal length")

    groups = sorted(set(cal_seg.tolist()) | set(test_seg.tolist()))
    total_test_exposure = float(test_exp.sum())
    mix_pred_rate = 0.0
    mix_actual_rate = 0.0
    supported_test_share = 0.0
    for group in groups:
        cal_mask = cal_seg == group
        test_mask = test_seg == group
        if not np.any(cal_mask) or not np.any(test_mask):
            continue
        cal_group_exp = float(cal_exp[cal_mask].sum())
        test_share = float(test_exp[test_mask].sum() / max(total_test_exposure, 1e-12))
        cal_pred_rate = float(np.sum(cal_pred[cal_mask] * cal_exp[cal_mask]) / max(cal_group_exp, 1e-12))
        cal_actual_rate = float(cal_actual[cal_mask].sum() / max(cal_group_exp, 1e-12))
        mix_pred_rate += test_share * cal_pred_rate
        mix_actual_rate += test_share * cal_actual_rate
        supported_test_share += test_share

    if supported_test_share <= 0.0:
        raise ValueError("no shared calibration/test segments for mix decomposition")
    mix_pred_rate /= supported_test_share
    mix_actual_rate /= supported_test_share

    calibration_ratio_value = calibration_ratio(cal_actual, cal_pred, cal_exp)
    mix_only_ratio = mix_pred_rate / max(mix_actual_rate, 1e-12)
    test_ratio_value = calibration_ratio(test_actual_arr, test_pred_arr, test_exp)

    total_log_change = float(np.log(max(test_ratio_value, 1e-12)) - np.log(max(calibration_ratio_value, 1e-12)))
    mix_log_change = float(np.log(max(mix_only_ratio, 1e-12)) - np.log(max(calibration_ratio_value, 1e-12)))
    residual_log_change = float(np.log(max(test_ratio_value, 1e-12)) - np.log(max(mix_only_ratio, 1e-12)))

    return {
        "calibration_period_ratio": calibration_ratio_value,
        "mix_only_counterfactual_ratio": mix_only_ratio,
        "test_period_ratio": test_ratio_value,
        "total_log_calibration_change": total_log_change,
        "portfolio_mix_log_component": mix_log_change,
        "within_segment_time_log_component": residual_log_change,
        "decomposition_residual": total_log_change - mix_log_change - residual_log_change,
        "shared_test_exposure_share": supported_test_share,
    }
