from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_poisson_deviance

from build_deployment_bundle_v21 import canonicalise_features, records_from_frame
from deployment.bundle import ShadowModelBundle
from deployment.recalibration import apply_segment_multipliers, calibration_ratio
from run_spanish_oot_2024 import load_data


BUNDLE_DIR = Path("deployment_artifacts")
V32_EVIDENCE = Path("action_results/v32/business_type_recalibration_summary.json")
OUTDIR = Path("results_v33")
BATCH_SIZE = 10_000

MAJOR_COHORT_MIN_ROWS = 2_000
MAJOR_COHORT_MIN_EXPOSURE_SHARE = 0.02
MAJOR_COHORT_MIN_CLAIMS = 100
MAX_ABS_LOG_CALIBRATION_DETERIORATION = 0.02
MAX_RELATIVE_DEVIANCE_WORSENING = 0.005
FRESH_RETRAIN_RELATIVE_TOLERANCE = 0.002

FREQUENCY_FIELDS = ("reference_frequency", "challenger_frequency")
TRANSPORT_DIMENSIONS = (
    "seen_before_2024",
    "driver_age_band",
    "policy_type",
    "payment_frequency",
)


def _score_2024(bundle: ShadowModelBundle, feature_frame: pd.DataFrame) -> dict[str, np.ndarray]:
    collected = {field: [] for field in FREQUENCY_FIELDS}
    for start in range(0, len(feature_frame), BATCH_SIZE):
        stop = min(start + BATCH_SIZE, len(feature_frame))
        scores = bundle.score_records(records_from_frame(feature_frame.iloc[start:stop]))
        for row in scores:
            for field in FREQUENCY_FIELDS:
                collected[field].append(float(row[field]))
    return {field: np.asarray(values, dtype=float) for field, values in collected.items()}


def _poisson_deviance(claims: np.ndarray, pred: np.ndarray, exposure: np.ndarray) -> float:
    return float(
        mean_poisson_deviance(
            claims / exposure,
            pred,
            sample_weight=exposure,
        )
    )


def _age_band(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    bands = pd.cut(
        numeric,
        bins=[0, 24, 34, 49, 64, 200],
        labels=["<25", "25-34", "35-49", "50-64", "65+"],
        include_lowest=True,
    )
    out = bands.astype("object")
    return pd.Series(out, index=values.index).where(pd.notna(out), "MISSING").astype(str)


def build_transport_dimensions(frame: pd.DataFrame, prior_ids: set[str]) -> dict[str, np.ndarray]:
    insured = frame["insured_id"].astype(str)
    return {
        "seen_before_2024": np.where(insured.isin(prior_ids), "seen", "unseen").astype(object),
        "driver_age_band": _age_band(frame["driver_age"]).to_numpy(dtype=object),
        "policy_type": frame["policy_type"].fillna("MISSING").astype(str).to_numpy(dtype=object),
        "payment_frequency": frame["payment_frequency"].fillna("MISSING").astype(str).to_numpy(dtype=object),
    }


def evaluate_cohorts(
    dimensions: dict[str, np.ndarray],
    claims: np.ndarray,
    exposure: np.ndarray,
    baseline_pred: np.ndarray,
    candidate_pred: np.ndarray,
) -> list[dict[str, Any]]:
    n = len(exposure)
    if any(len(arr) != n for arr in (claims, baseline_pred, candidate_pred)):
        raise ValueError("claims, exposure and predictions must have equal length")
    if np.any(exposure <= 0):
        raise ValueError("exposure must be strictly positive")

    total_exposure = float(exposure.sum())
    rows: list[dict[str, Any]] = []
    for dimension in TRANSPORT_DIMENSIONS:
        groups = np.asarray(dimensions[dimension], dtype=object)
        if len(groups) != n:
            raise ValueError(f"dimension {dimension} length does not match exposure")
        for group in sorted(np.unique(groups).tolist()):
            mask = groups == group
            exp = exposure[mask]
            obs = claims[mask]
            baseline = baseline_pred[mask]
            candidate = candidate_pred[mask]
            group_rows = int(mask.sum())
            group_exposure = float(exp.sum())
            exposure_share = group_exposure / max(total_exposure, 1e-12)
            group_claims = float(obs.sum())
            baseline_ratio = calibration_ratio(obs, baseline, exp)
            candidate_ratio = calibration_ratio(obs, candidate, exp)
            baseline_error = float(abs(np.log(max(baseline_ratio, 1e-12))))
            candidate_error = float(abs(np.log(max(candidate_ratio, 1e-12))))
            baseline_deviance = _poisson_deviance(obs, baseline, exp)
            candidate_deviance = _poisson_deviance(obs, candidate, exp)
            relative_deviance_change = candidate_deviance / max(baseline_deviance, 1e-12) - 1.0
            major = bool(
                group_rows >= MAJOR_COHORT_MIN_ROWS
                and exposure_share >= MAJOR_COHORT_MIN_EXPOSURE_SHARE
                and group_claims >= MAJOR_COHORT_MIN_CLAIMS
            )
            calibration_delta = candidate_error - baseline_error
            calibration_guardrail_pass = bool(
                (not major)
                or calibration_delta <= MAX_ABS_LOG_CALIBRATION_DETERIORATION
            )
            deviance_guardrail_pass = bool(
                (not major)
                or relative_deviance_change <= MAX_RELATIVE_DEVIANCE_WORSENING
            )
            rows.append(
                {
                    "dimension": dimension,
                    "group": str(group),
                    "rows": group_rows,
                    "exposure": group_exposure,
                    "exposure_share": exposure_share,
                    "claims": group_claims,
                    "major_cohort": major,
                    "baseline_calibration_ratio": baseline_ratio,
                    "candidate_calibration_ratio": candidate_ratio,
                    "baseline_abs_log_calibration_error": baseline_error,
                    "candidate_abs_log_calibration_error": candidate_error,
                    "abs_log_calibration_error_change": calibration_delta,
                    "baseline_poisson_deviance": baseline_deviance,
                    "candidate_poisson_deviance": candidate_deviance,
                    "relative_deviance_change": relative_deviance_change,
                    "calibration_guardrail_pass": calibration_guardrail_pass,
                    "deviance_guardrail_pass": deviance_guardrail_pass,
                    "cohort_gate_pass": bool(calibration_guardrail_pass and deviance_guardrail_pass),
                }
            )
    return rows


def _reconcile_scalar(observed: float, expected: float) -> dict[str, float]:
    absolute = abs(float(observed) - float(expected))
    relative = absolute / max(abs(float(expected)), 1e-12)
    return {
        "observed": float(observed),
        "v32_persisted": float(expected),
        "absolute_difference": absolute,
        "relative_difference": relative,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not V32_EVIDENCE.is_file():
        raise FileNotFoundError(V32_EVIDENCE)
    v32 = json.loads(V32_EVIDENCE.read_text(encoding="utf-8"))

    supported = v32["candidate_summary"]["supported_fields"]
    if supported != ["reference_frequency", "challenger_frequency"]:
        raise RuntimeError(f"Unexpected v0.32 supported fields: {supported}")

    frame = load_data()
    test = frame[frame["year"] == 2024].copy().reset_index(drop=True)
    prior_ids = set(frame.loc[frame["year"].isin([2022, 2023]), "insured_id"].astype(str))
    if len(test) == 0:
        raise RuntimeError("No 2024 rows available")

    bundle = ShadowModelBundle.load(BUNDLE_DIR)
    if bundle.manifest.get("governance_status") != "HOLD_SHADOW_ONLY":
        raise RuntimeError("v0.33 requires HOLD_SHADOW_ONLY bundle")
    if bundle.bundle_integrity is None:
        raise RuntimeError("v0.33 requires a content-addressed bundle lock")

    baseline_scores = _score_2024(bundle, canonicalise_features(test))
    claims = test["total_claims"].to_numpy(float)
    exposure = test["total_exposure"].to_numpy(float)
    business_type = test["business_type"].fillna("MISSING").astype(str).to_numpy(dtype=object)
    dimensions = build_transport_dimensions(test, prior_ids)

    all_rows: list[dict[str, Any]] = []
    model_results: dict[str, Any] = {}

    for field in FREQUENCY_FIELDS:
        source = v32["results"][field]
        if source["candidate_gate"]["decision"] != "SUPPORTED_FOR_FURTHER_SHADOW_TESTING":
            raise RuntimeError(f"v0.33 cannot test unsupported v0.32 field: {field}")

        # v0.33 does not fit or update multipliers. It consumes the exact persisted
        # v0.32 2023-only factors and uses 2024 labels only for evaluation.
        fitted = source["fit_period"]["multipliers"]
        baseline = baseline_scores[field]
        candidate = apply_segment_multipliers(business_type, baseline, fitted)

        baseline_deviance = _poisson_deviance(claims, baseline, exposure)
        candidate_deviance = _poisson_deviance(claims, candidate, exposure)
        baseline_ratio = calibration_ratio(claims, baseline, exposure)
        candidate_ratio = calibration_ratio(claims, candidate, exposure)

        reconciliation = {
            "baseline_deviance": _reconcile_scalar(
                baseline_deviance, source["baseline_2024"]["deviance"]
            ),
            "candidate_deviance": _reconcile_scalar(
                candidate_deviance, source["candidate_2024"]["deviance"]
            ),
            "baseline_calibration": _reconcile_scalar(
                baseline_ratio, source["baseline_2024"]["calibration_ratio_pred_over_actual"]
            ),
            "candidate_calibration": _reconcile_scalar(
                candidate_ratio, source["candidate_2024"]["calibration_ratio_pred_over_actual"]
            ),
        }
        max_reconciliation_difference = max(
            item["relative_difference"] for item in reconciliation.values()
        )
        if max_reconciliation_difference > FRESH_RETRAIN_RELATIVE_TOLERANCE:
            raise AssertionError(
                f"{field} fresh replay moved too far from persisted v0.32 evidence: "
                f"{max_reconciliation_difference} > {FRESH_RETRAIN_RELATIVE_TOLERANCE}"
            )

        rows = evaluate_cohorts(dimensions, claims, exposure, baseline, candidate)
        for row in rows:
            all_rows.append({"prediction_field": field, **row})

        major = [row for row in rows if row["major_cohort"]]
        breaches = [row for row in major if not row["cohort_gate_pass"]]
        improved_calibration = [
            row for row in major if row["abs_log_calibration_error_change"] < 0.0
        ]
        improved_deviance = [row for row in major if row["relative_deviance_change"] < 0.0]
        max_calibration_deterioration = max(
            (row["abs_log_calibration_error_change"] for row in major),
            default=float("nan"),
        )
        max_deviance_worsening = max(
            (row["relative_deviance_change"] for row in major),
            default=float("nan"),
        )

        stable = bool(len(major) > 0 and not breaches)
        model_results[field] = {
            "v32_candidate_source": {
                "fit_year": source["fit_period"]["year"],
                "test_2024_labels_used_for_fit": source["fit_period"]["test_2024_labels_used_for_fit"],
                "multipliers": fitted,
                "v32_decision": source["candidate_gate"]["decision"],
            },
            "fresh_replay_reconciliation": {
                "checks": reconciliation,
                "max_relative_difference": max_reconciliation_difference,
                "relative_tolerance": FRESH_RETRAIN_RELATIVE_TOLERANCE,
            },
            "major_cohort_summary": {
                "major_cohort_count": len(major),
                "gate_breach_count": len(breaches),
                "calibration_improved_count": len(improved_calibration),
                "deviance_improved_count": len(improved_deviance),
                "max_abs_log_calibration_deterioration": max_calibration_deterioration,
                "max_relative_deviance_worsening": max_deviance_worsening,
                "decision": (
                    "TRANSPORT_STABLE_FOR_FURTHER_SHADOW_TESTING"
                    if stable
                    else "TRANSPORT_REVIEW_REQUIRED"
                ),
            },
            "breaches": [
                {
                    "dimension": row["dimension"],
                    "group": row["group"],
                    "abs_log_calibration_error_change": row["abs_log_calibration_error_change"],
                    "relative_deviance_change": row["relative_deviance_change"],
                    "calibration_guardrail_pass": row["calibration_guardrail_pass"],
                    "deviance_guardrail_pass": row["deviance_guardrail_pass"],
                }
                for row in breaches
            ],
        }

    stable_fields = [
        field
        for field, result in model_results.items()
        if result["major_cohort_summary"]["decision"]
        == "TRANSPORT_STABLE_FOR_FURTHER_SHADOW_TESTING"
    ]

    summary = {
        "status": "V33_FREQUENCY_RECALIBRATION_TRANSPORT_REVIEW_PASS",
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "evaluation_year": 2024,
            "rows": int(len(test)),
            "candidate_source": "persisted v0.32 2023-only business_type multipliers",
            "multipliers_refit_in_v33": False,
            "2024_labels_used_for_fit": False,
            "transport_dimensions": list(TRANSPORT_DIMENSIONS),
        },
        "guardrails": {
            "major_cohort_min_rows": MAJOR_COHORT_MIN_ROWS,
            "major_cohort_min_exposure_share": MAJOR_COHORT_MIN_EXPOSURE_SHARE,
            "major_cohort_min_claims": MAJOR_COHORT_MIN_CLAIMS,
            "max_abs_log_calibration_deterioration": MAX_ABS_LOG_CALIBRATION_DETERIORATION,
            "max_relative_deviance_worsening": MAX_RELATIVE_DEVIANCE_WORSENING,
            "fresh_retrain_relative_tolerance": FRESH_RETRAIN_RELATIVE_TOLERANCE,
            "interpretation": (
                "Project transport guardrails for retrospective shadow review; they are not insurer or regulatory thresholds."
            ),
        },
        "models": model_results,
        "decision": {
            "stable_fields": stable_fields,
            "stable_field_count": len(stable_fields),
            "tested_field_count": len(FREQUENCY_FIELDS),
            "bundle_change_authorised": False,
            "pricing_change_authorised": False,
            "model_promotion_authorised": False,
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
        },
        "interpretation_boundary": (
            "v0.33 checks transport of fixed v0.32 frequency recalibration across orthogonal 2024 cohorts. "
            "It does not create a new temporal test because the public source has calendar year but no intra-year date. "
            "It remains retrospective evidence from one Spanish insurer and does not establish transfer to FIRST CENTRAL or the UK market."
        ),
    }

    _write_csv(OUTDIR / "frequency_recalibration_transport_cohorts.csv", all_rows)
    (OUTDIR / "frequency_recalibration_transport_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
