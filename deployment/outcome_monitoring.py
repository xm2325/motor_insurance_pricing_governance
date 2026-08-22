from __future__ import annotations

import hashlib
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance


PREDICTION_FIELDS = (
    "reference_frequency",
    "challenger_frequency",
    "reference_pure_premium",
    "challenger_pure_premium",
)


def _as_float_array(values: Iterable[float], *, name: str) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def deterministic_exposure_maturity_mask(
    keys: Iterable[str],
    exposure: Iterable[float],
    *,
    target_exposure_fraction: float,
) -> np.ndarray:
    """Select a deterministic pseudo-random subset until target exposure is reached.

    This is for replay/testing of label-arrival controls. It does not model real claim
    development or settlement timing.
    """
    keys = [str(key) for key in keys]
    exp = _as_float_array(exposure, name="exposure")
    if len(keys) != len(exp):
        raise ValueError("keys and exposure must have equal length")
    if len(exp) == 0:
        raise ValueError("at least one row is required")
    if np.any(exp <= 0):
        raise ValueError("exposure must be strictly positive")
    if not (0.0 < float(target_exposure_fraction) <= 1.0):
        raise ValueError("target_exposure_fraction must be in (0, 1]")

    if float(target_exposure_fraction) == 1.0:
        return np.ones(len(exp), dtype=bool)

    hashes = np.fromiter(
        (
            int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
            for key in keys
        ),
        dtype=np.uint64,
        count=len(keys),
    )
    order = np.argsort(hashes, kind="stable")
    cumulative = np.cumsum(exp[order])
    threshold = float(target_exposure_fraction) * float(exp.sum())
    last = int(np.searchsorted(cumulative, threshold, side="left"))
    selected = order[: min(last + 1, len(order))]
    mask = np.zeros(len(exp), dtype=bool)
    mask[selected] = True
    return mask


def _calibration_ratio(actual: np.ndarray, pred_rate: np.ndarray, exposure: np.ndarray) -> float:
    predicted = float(np.sum(pred_rate * exposure))
    observed = float(np.sum(actual))
    return predicted / max(observed, 1e-12)


def _validate_inputs(
    claims: Iterable[float],
    incurred: Iterable[float],
    exposure: Iterable[float],
    predictions: dict[str, Iterable[float]],
    observed_mask: Iterable[bool],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray]:
    claims_arr = _as_float_array(claims, name="claims")
    incurred_arr = _as_float_array(incurred, name="incurred")
    exposure_arr = _as_float_array(exposure, name="exposure")
    mask_arr = np.asarray(list(observed_mask), dtype=bool)

    n = len(exposure_arr)
    if any(len(arr) != n for arr in (claims_arr, incurred_arr, mask_arr)):
        raise ValueError("claims, incurred, exposure and observed_mask must have equal length")
    if n == 0:
        raise ValueError("at least one row is required")
    if np.any(exposure_arr <= 0):
        raise ValueError("exposure must be strictly positive")
    if np.any(claims_arr < 0) or np.any(incurred_arr < 0):
        raise ValueError("claims and incurred must be non-negative")

    missing = [field for field in PREDICTION_FIELDS if field not in predictions]
    if missing:
        raise ValueError(f"missing prediction fields: {missing}")

    pred_arrays: dict[str, np.ndarray] = {}
    for field in PREDICTION_FIELDS:
        arr = _as_float_array(predictions[field], name=field)
        if len(arr) != n:
            raise ValueError(f"{field} length does not match exposure")
        if np.any(arr <= 0):
            raise ValueError(f"{field} must be strictly positive")
        pred_arrays[field] = arr

    return claims_arr, incurred_arr, exposure_arr, pred_arrays, mask_arr


def outcome_performance_snapshot(
    claims: Iterable[float],
    incurred: Iterable[float],
    exposure: Iterable[float],
    predictions: dict[str, Iterable[float]],
    observed_mask: Iterable[bool],
    *,
    minimum_mature_exposure_fraction: float = 0.95,
) -> dict[str, Any]:
    """Evaluate label-based performance only after sufficient exposure has mature outcomes."""
    if not (0.0 < float(minimum_mature_exposure_fraction) <= 1.0):
        raise ValueError("minimum_mature_exposure_fraction must be in (0, 1]")

    claims_arr, incurred_arr, exposure_arr, pred, mask = _validate_inputs(
        claims, incurred, exposure, predictions, observed_mask
    )

    mature_exposure = float(exposure_arr[mask].sum())
    total_exposure = float(exposure_arr.sum())
    mature_fraction = mature_exposure / max(total_exposure, 1e-12)

    base: dict[str, Any] = {
        "rows_total": int(len(exposure_arr)),
        "rows_with_mature_outcomes": int(mask.sum()),
        "total_exposure": total_exposure,
        "mature_exposure": mature_exposure,
        "mature_exposure_fraction": mature_fraction,
        "minimum_mature_exposure_fraction": float(minimum_mature_exposure_fraction),
        "metrics_evaluated": False,
        "pricing_change_authorised": False,
        "model_promotion_authorised": False,
    }

    if mature_fraction + 1e-12 < float(minimum_mature_exposure_fraction):
        base.update(
            {
                "status": "WAIT_FOR_OUTCOME_MATURITY",
                "decision": "NO_PERFORMANCE_CONCLUSION",
                "reason": (
                    "Observed outcome exposure is below the maturity gate; "
                    "performance metrics are intentionally withheld."
                ),
            }
        )
        return base

    obs_claims = claims_arr[mask]
    obs_incurred = incurred_arr[mask]
    obs_exposure = exposure_arr[mask]
    y_frequency = obs_claims / obs_exposure
    y_pure_premium = obs_incurred / obs_exposure

    frequency: dict[str, dict[str, float]] = {}
    pure_premium: dict[str, dict[str, float]] = {}

    for label, field in (
        ("reference", "reference_frequency"),
        ("challenger", "challenger_frequency"),
    ):
        values = pred[field][mask]
        frequency[label] = {
            "poisson_deviance": float(
                mean_poisson_deviance(y_frequency, values, sample_weight=obs_exposure)
            ),
            "calibration_ratio_pred_over_actual": _calibration_ratio(
                obs_claims, values, obs_exposure
            ),
        }

    for label, field in (
        ("reference", "reference_pure_premium"),
        ("challenger", "challenger_pure_premium"),
    ):
        values = pred[field][mask]
        pure_premium[label] = {
            "tweedie_deviance_p1_5": float(
                mean_tweedie_deviance(
                    y_pure_premium, values, sample_weight=obs_exposure, power=1.5
                )
            ),
            "calibration_ratio_pred_over_actual": _calibration_ratio(
                obs_incurred, values, obs_exposure
            ),
        }

    base.update(
        {
            "status": "OUTCOME_PERFORMANCE_EVALUATED",
            "decision": "REVIEW_ONLY_NO_AUTOMATIC_MODEL_CHANGE",
            "metrics_evaluated": True,
            "observed_claims": float(obs_claims.sum()),
            "observed_incurred": float(obs_incurred.sum()),
            "frequency": frequency,
            "pure_premium": pure_premium,
            "glm_minus_xgb_frequency_deviance": (
                frequency["reference"]["poisson_deviance"]
                - frequency["challenger"]["poisson_deviance"]
            ),
            "glm_minus_xgb_tweedie_deviance": (
                pure_premium["reference"]["tweedie_deviance_p1_5"]
                - pure_premium["challenger"]["tweedie_deviance_p1_5"]
            ),
        }
    )
    return base


def segment_calibration_snapshot(
    segment: Iterable[str],
    claims: Iterable[float],
    incurred: Iterable[float],
    exposure: Iterable[float],
    predictions: dict[str, Iterable[float]],
    observed_mask: Iterable[bool],
    *,
    minimum_mature_exposure_fraction: float = 0.95,
) -> list[dict[str, Any]]:
    """Return aggregate segment calibration only when the global maturity gate is met."""
    segments = np.asarray([str(value) for value in segment], dtype=object)
    claims_arr, incurred_arr, exposure_arr, pred, mask = _validate_inputs(
        claims, incurred, exposure, predictions, observed_mask
    )
    if len(segments) != len(exposure_arr):
        raise ValueError("segment length does not match exposure")

    maturity = float(exposure_arr[mask].sum()) / max(float(exposure_arr.sum()), 1e-12)
    if maturity + 1e-12 < float(minimum_mature_exposure_fraction):
        return []

    rows: list[dict[str, Any]] = []
    for group in sorted(np.unique(segments[mask]).tolist()):
        group_mask = mask & (segments == group)
        exp = exposure_arr[group_mask]
        clm = claims_arr[group_mask]
        inc = incurred_arr[group_mask]
        row: dict[str, Any] = {
            "segment": str(group),
            "rows": int(group_mask.sum()),
            "exposure": float(exp.sum()),
            "exposure_share": float(exp.sum() / max(exposure_arr[mask].sum(), 1e-12)),
            "claims": float(clm.sum()),
            "incurred": float(inc.sum()),
        }
        for label, freq_field, loss_field in (
            ("reference", "reference_frequency", "reference_pure_premium"),
            ("challenger", "challenger_frequency", "challenger_pure_premium"),
        ):
            row[f"{label}_frequency_calibration_ratio"] = _calibration_ratio(
                clm, pred[freq_field][group_mask], exp
            )
            row[f"{label}_pure_premium_calibration_ratio"] = _calibration_ratio(
                inc, pred[loss_field][group_mask], exp
            )
        rows.append(row)
    return rows
