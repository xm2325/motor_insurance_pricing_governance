from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance

from build_deployment_bundle_v21 import canonicalise_features, records_from_frame
from deployment.bundle import ShadowModelBundle
from deployment.recalibration import (
    apply_segment_multipliers,
    calibration_ratio,
    fit_segment_multipliers,
    portfolio_mix_decomposition,
    segment_calibration_rows,
)
from run_spanish_oot_2024 import load_data


BUNDLE_DIR = Path("deployment_artifacts")
OUTDIR = Path("results_v32")
V31_REFERENCE = Path("action_results/v31/outcome_review_summary.json")
BATCH_SIZE = 10_000
MINIMUM_SEGMENT_ROWS = 500
MINIMUM_SEGMENT_EXPOSURE_SHARE = 0.01
MULTIPLIER_FLOOR = 0.50
MULTIPLIER_CAP = 2.00
MAX_RELATIVE_DEVIANCE_WORSENING = 0.001

FIELD_CONFIG = {
    "reference_frequency": {"target": "frequency", "role": "GLM reference"},
    "challenger_frequency": {"target": "frequency", "role": "XGBoost challenger"},
    "reference_pure_premium": {"target": "pure_premium", "role": "GLM reference"},
    "challenger_pure_premium": {"target": "pure_premium", "role": "XGBoost challenger"},
}


def _score_frame(bundle: ShadowModelBundle, feature_frame) -> dict[str, np.ndarray]:
    collected = {field: [] for field in FIELD_CONFIG}
    for start in range(0, len(feature_frame), BATCH_SIZE):
        stop = min(start + BATCH_SIZE, len(feature_frame))
        records = records_from_frame(feature_frame.iloc[start:stop])
        scores = bundle.score_records(records)
        for row in scores:
            for field in collected:
                collected[field].append(float(row[field]))
    return {field: np.asarray(values, dtype=float) for field, values in collected.items()}


def _deviance(target: str, actual: np.ndarray, pred: np.ndarray, exposure: np.ndarray) -> float:
    rate = actual / exposure
    if target == "frequency":
        return float(mean_poisson_deviance(rate, pred, sample_weight=exposure))
    if target == "pure_premium":
        return float(mean_tweedie_deviance(rate, pred, sample_weight=exposure, power=1.5))
    raise ValueError(f"Unsupported target: {target}")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _historical_baseline_reconciliation(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not V31_REFERENCE.is_file():
        raise FileNotFoundError(V31_REFERENCE)
    reference = json.loads(V31_REFERENCE.read_text(encoding="utf-8"))["fully_mature_outcomes"]
    expected = {
        "reference_frequency": reference["frequency"]["reference"]["poisson_deviance"],
        "challenger_frequency": reference["frequency"]["challenger"]["poisson_deviance"],
        "reference_pure_premium": reference["pure_premium"]["reference"]["tweedie_deviance_p1_5"],
        "challenger_pure_premium": reference["pure_premium"]["challenger"]["tweedie_deviance_p1_5"],
    }
    checks: dict[str, Any] = {}
    max_relative_difference = 0.0
    for field, expected_value in expected.items():
        observed = float(results[field]["baseline_2024"]["deviance"])
        absolute = abs(observed - float(expected_value))
        relative = absolute / max(abs(float(expected_value)), 1e-12)
        max_relative_difference = max(max_relative_difference, relative)
        checks[field] = {
            "v32_baseline": observed,
            "v31_persisted": float(expected_value),
            "absolute_difference": absolute,
            "relative_difference": relative,
        }
    if max_relative_difference > 1e-12:
        raise AssertionError(
            "v0.32 baseline does not reproduce persisted v0.31 OOT deviance: "
            f"max relative difference={max_relative_difference}"
        )
    return {
        "status": "V31_BASELINE_RECONCILIATION_PASS",
        "checks": checks,
        "max_relative_difference": max_relative_difference,
        "relative_tolerance": 1e-12,
    }


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    frame = load_data()
    calibration = frame[frame["year"] == 2023].copy().reset_index(drop=True)
    test = frame[frame["year"] == 2024].copy().reset_index(drop=True)
    if len(calibration) == 0 or len(test) == 0:
        raise RuntimeError("Expected non-empty 2023 calibration and 2024 OOT cohorts")

    bundle = ShadowModelBundle.load(BUNDLE_DIR)
    if bundle.manifest.get("governance_status") != "HOLD_SHADOW_ONLY":
        raise RuntimeError("v0.32 must run only against HOLD_SHADOW_ONLY bundles")
    if bundle.bundle_integrity is None:
        raise RuntimeError("v0.32 requires a content-addressed v0.27 bundle lock")

    calibration_scores = _score_frame(bundle, canonicalise_features(calibration))
    test_scores = _score_frame(bundle, canonicalise_features(test))

    segment_calibration = calibration["business_type"].fillna("MISSING").astype(str).to_numpy()
    segment_test = test["business_type"].fillna("MISSING").astype(str).to_numpy()
    exposure_calibration = calibration["total_exposure"].to_numpy(float)
    exposure_test = test["total_exposure"].to_numpy(float)
    claims_calibration = calibration["total_claims"].to_numpy(float)
    claims_test = test["total_claims"].to_numpy(float)
    incurred_calibration = calibration["total_incurred"].to_numpy(float)
    incurred_test = test["total_incurred"].to_numpy(float)

    results: dict[str, dict[str, Any]] = {}
    multiplier_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    decomposition_rows: list[dict[str, Any]] = []

    for field, config in FIELD_CONFIG.items():
        target = str(config["target"])
        actual_calibration = claims_calibration if target == "frequency" else incurred_calibration
        test_actual = claims_test if target == "frequency" else incurred_test
        baseline_calibration_pred = calibration_scores[field]
        baseline_test_pred = test_scores[field]

        # Leakage boundary: all fitted multipliers are functions only of 2023 labels,
        # 2023 exposure, 2023 business_type and already globally calibrated predictions.
        fitted = fit_segment_multipliers(
            segment_calibration,
            actual_calibration,
            baseline_calibration_pred,
            exposure_calibration,
            minimum_segment_rows=MINIMUM_SEGMENT_ROWS,
            minimum_segment_exposure_share=MINIMUM_SEGMENT_EXPOSURE_SHARE,
            multiplier_floor=MULTIPLIER_FLOOR,
            multiplier_cap=MULTIPLIER_CAP,
        )
        candidate_test_pred = apply_segment_multipliers(segment_test, baseline_test_pred, fitted)

        baseline_2024_deviance = _deviance(target, test_actual, baseline_test_pred, exposure_test)
        candidate_2024_deviance = _deviance(target, test_actual, candidate_test_pred, exposure_test)
        baseline_2024_ratio = calibration_ratio(test_actual, baseline_test_pred, exposure_test)
        candidate_2024_ratio = calibration_ratio(test_actual, candidate_test_pred, exposure_test)

        per_segment = segment_calibration_rows(
            segment_test,
            test_actual,
            exposure_test,
            baseline_test_pred,
            candidate_test_pred,
        )
        baseline_max_segment_error = max(row["baseline_abs_log_calibration_error"] for row in per_segment)
        candidate_max_segment_error = max(row["candidate_abs_log_calibration_error"] for row in per_segment)
        relative_deviance_change = candidate_2024_deviance / baseline_2024_deviance - 1.0
        segment_calibration_improved = candidate_max_segment_error < baseline_max_segment_error
        aggregate_calibration_not_worse = (
            abs(np.log(max(candidate_2024_ratio, 1e-12)))
            <= abs(np.log(max(baseline_2024_ratio, 1e-12))) + 1e-12
        )
        deviance_guardrail_pass = relative_deviance_change <= MAX_RELATIVE_DEVIANCE_WORSENING
        all_segments_supported = all(bool(metadata["supported"]) for metadata in fitted.values())
        candidate_supported = bool(
            all_segments_supported
            and segment_calibration_improved
            and aggregate_calibration_not_worse
            and deviance_guardrail_pass
        )

        decomposition = portfolio_mix_decomposition(
            segment_calibration,
            actual_calibration,
            exposure_calibration,
            baseline_calibration_pred,
            segment_test,
            test_actual,
            exposure_test,
            baseline_test_pred,
        )

        for metadata in fitted.values():
            multiplier_rows.append({"prediction_field": field, "target": target, **metadata})
        for row in per_segment:
            segment_rows.append({"prediction_field": field, "target": target, **row})
        decomposition_rows.append({"prediction_field": field, "target": target, **decomposition})

        results[field] = {
            "target": target,
            "role": config["role"],
            "fit_period": {
                "year": 2023,
                "rows": int(len(calibration)),
                "labels_used": "total_claims" if target == "frequency" else "total_incurred",
                "test_2024_labels_used_for_fit": False,
                "segment": "business_type",
                "multipliers": fitted,
            },
            "baseline_2024": {
                "deviance": baseline_2024_deviance,
                "calibration_ratio_pred_over_actual": baseline_2024_ratio,
                "max_segment_abs_log_calibration_error": baseline_max_segment_error,
            },
            "candidate_2024": {
                "deviance": candidate_2024_deviance,
                "calibration_ratio_pred_over_actual": candidate_2024_ratio,
                "max_segment_abs_log_calibration_error": candidate_max_segment_error,
                "relative_deviance_change": relative_deviance_change,
            },
            "candidate_gate": {
                "all_segments_supported": all_segments_supported,
                "segment_calibration_improved": segment_calibration_improved,
                "aggregate_calibration_not_worse": aggregate_calibration_not_worse,
                "deviance_guardrail_pass": deviance_guardrail_pass,
                "max_relative_deviance_worsening": MAX_RELATIVE_DEVIANCE_WORSENING,
                "decision": (
                    "SUPPORTED_FOR_FURTHER_SHADOW_TESTING"
                    if candidate_supported
                    else "RETAIN_GLOBAL_CALIBRATION"
                ),
            },
            "portfolio_mix_decomposition": decomposition,
        }

    baseline_reconciliation = _historical_baseline_reconciliation(results)
    supported_fields = [
        field
        for field, result in results.items()
        if result["candidate_gate"]["decision"] == "SUPPORTED_FOR_FURTHER_SHADOW_TESTING"
    ]

    summary = {
        "status": "V32_BUSINESS_TYPE_RECALIBRATION_REVIEW_PASS",
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "model_train_year": 2022,
            "global_calibration_year": 2023,
            "segment_recalibration_fit_year": 2023,
            "untouched_evaluation_year": 2024,
            "segment": "business_type",
            "calibration_rows": int(len(calibration)),
            "evaluation_rows": int(len(test)),
            "2024_labels_used_for_candidate_fit": False,
        },
        "guardrails": {
            "minimum_segment_rows": MINIMUM_SEGMENT_ROWS,
            "minimum_segment_exposure_share": MINIMUM_SEGMENT_EXPOSURE_SHARE,
            "multiplier_floor": MULTIPLIER_FLOOR,
            "multiplier_cap": MULTIPLIER_CAP,
            "max_relative_deviance_worsening": MAX_RELATIVE_DEVIANCE_WORSENING,
            "candidate_support_rule": (
                "all 2023 segments supported AND 2024 worst-segment absolute log calibration error improves "
                "AND aggregate calibration is not worse AND relative deviance worsening <= 0.1%"
            ),
        },
        "results": results,
        "v31_baseline_reconciliation": baseline_reconciliation,
        "candidate_summary": {
            "supported_fields": supported_fields,
            "supported_field_count": len(supported_fields),
            "total_field_count": len(results),
            "bundle_change_authorised": False,
            "pricing_change_authorised": False,
            "model_promotion_authorised": False,
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "interpretation": (
                "A field-level SUPPORTED_FOR_FURTHER_SHADOW_TESTING result is evidence for more shadow "
                "validation of that recalibration rule only. It is not permission to alter the sealed serving bundle."
            ),
        },
        "interpretation_boundary": (
            "Segment multipliers use only 2023 labels. 2024 labels are used only after the candidate is locked, "
            "for OOT comparison. The mix-only counterfactual uses 2024 business_type/exposure shares but not 2024 "
            "claims or incurred values. This remains one Spanish insurer and does not establish transfer to FIRST "
            "CENTRAL or the UK motor market."
        ),
    }

    _write_csv(OUTDIR / "business_type_recalibration_multipliers.csv", multiplier_rows)
    _write_csv(OUTDIR / "business_type_2024_candidate_comparison.csv", segment_rows)
    _write_csv(OUTDIR / "business_type_mix_decomposition.csv", decomposition_rows)
    (OUTDIR / "business_type_recalibration_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
