from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import mean_poisson_deviance

from build_deployment_bundle_v21 import canonicalise_features, records_from_frame
from deployment.bundle import ShadowModelBundle
from deployment.calibration_uncertainty import (
    evaluate_segment_factor_draw,
    group_frequency_sufficient_statistics,
    paired_stratified_bootstrap_factors,
    quantile_summary,
)
from deployment.recalibration import calibration_ratio
from run_spanish_oot_2024 import load_data


BUNDLE_DIR = Path("deployment_artifacts")
V32_EVIDENCE = Path("action_results/v32/business_type_recalibration_summary.json")
OUTDIR = Path("results_v34")
BATCH_SIZE = 10_000
BOOTSTRAP_DRAWS = 500
BOOTSTRAP_SEED = 20260823
FACTOR_FLOOR = 0.50
FACTOR_CAP = 2.00
FRESH_RETRAIN_RELATIVE_TOLERANCE = 0.002
ORIGINAL_V32_MAX_RELATIVE_DEVIANCE_WORSENING = 0.001
MIN_DEVIANCE_IMPROVEMENT_RATE = 0.80
MIN_AGGREGATE_CALIBRATION_NONWORSE_RATE = 0.80
MIN_WORST_SEGMENT_CALIBRATION_IMPROVEMENT_RATE = 0.80
MIN_ORIGINAL_DEVIANCE_GUARDRAIL_PASS_RATE = 0.95

FREQUENCY_FIELDS = ("reference_frequency", "challenger_frequency")


def _score_frequency(bundle: ShadowModelBundle, feature_frame) -> dict[str, np.ndarray]:
    collected = {field: [] for field in FREQUENCY_FIELDS}
    for start in range(0, len(feature_frame), BATCH_SIZE):
        stop = min(start + BATCH_SIZE, len(feature_frame))
        scores = bundle.score_records(records_from_frame(feature_frame.iloc[start:stop]))
        for row in scores:
            for field in FREQUENCY_FIELDS:
                collected[field].append(float(row[field]))
    return {field: np.asarray(values, dtype=float) for field, values in collected.items()}


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


def _relative_difference(observed: float, expected: float) -> float:
    return abs(float(observed) - float(expected)) / max(abs(float(expected)), 1e-12)


def _point_factor_by_segment(
    segments: np.ndarray,
    claims: np.ndarray,
    exposure: np.ndarray,
    pred: np.ndarray,
) -> dict[str, float]:
    output: dict[str, float] = {}
    for group in sorted(np.unique(segments).tolist()):
        mask = segments == group
        observed = float(claims[mask].sum())
        predicted = float(np.sum(exposure[mask] * pred[mask]))
        if observed <= 0.0 or predicted <= 0.0:
            raise RuntimeError(f"Cannot derive point factor for {group}")
        output[str(group)] = observed / predicted
    return output


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not V32_EVIDENCE.is_file():
        raise FileNotFoundError(V32_EVIDENCE)
    v32 = json.loads(V32_EVIDENCE.read_text(encoding="utf-8"))

    frame = load_data()
    calibration = frame[frame["year"] == 2023].copy().reset_index(drop=True)
    test = frame[frame["year"] == 2024].copy().reset_index(drop=True)
    if len(calibration) == 0 or len(test) == 0:
        raise RuntimeError("Expected non-empty 2023 calibration and 2024 OOT cohorts")

    bundle = ShadowModelBundle.load(BUNDLE_DIR)
    if bundle.manifest.get("governance_status") != "HOLD_SHADOW_ONLY":
        raise RuntimeError("v0.34 must run only against HOLD_SHADOW_ONLY bundles")
    if bundle.bundle_integrity is None:
        raise RuntimeError("v0.34 requires a verified content-addressed bundle lock")

    calibration_scores = _score_frequency(bundle, canonicalise_features(calibration))
    test_scores = _score_frequency(bundle, canonicalise_features(test))

    segment_calibration = calibration["business_type"].fillna("MISSING").astype(str).to_numpy(dtype=object)
    claims_calibration = calibration["total_claims"].to_numpy(float)
    exposure_calibration = calibration["total_exposure"].to_numpy(float)

    segment_test = test["business_type"].fillna("MISSING").astype(str).to_numpy(dtype=object)
    claims_test = test["total_claims"].to_numpy(float)
    exposure_test = test["total_exposure"].to_numpy(float)

    if set(np.unique(segment_calibration).tolist()) != {"NB", "P"}:
        raise RuntimeError("v0.34 registered uncertainty review expects 2023 NB/P business_type segments")
    if set(np.unique(segment_test).tolist()) != {"NB", "P"}:
        raise RuntimeError("v0.34 registered uncertainty review expects 2024 NB/P business_type segments")

    # Leakage boundary: paired bootstrap factor draws use 2023 calibration rows only.
    # No 2024 claim or loss value is passed to this factor-estimation function.
    bootstrap_factors = paired_stratified_bootstrap_factors(
        segment_calibration,
        claims_calibration,
        exposure_calibration,
        {field: calibration_scores[field] for field in FREQUENCY_FIELDS},
        draws=BOOTSTRAP_DRAWS,
        seed=BOOTSTRAP_SEED,
    )

    factor_rows: list[dict[str, Any]] = []
    draw_rows: list[dict[str, Any]] = []
    model_results: dict[str, Any] = {}

    for field in FREQUENCY_FIELDS:
        persisted = v32["results"][field]
        if persisted["candidate_gate"]["decision"] != "SUPPORTED_FOR_FURTHER_SHADOW_TESTING":
            raise RuntimeError(f"v0.34 only evaluates v0.32-supported field {field}")

        fresh_point_factors = _point_factor_by_segment(
            segment_calibration,
            claims_calibration,
            exposure_calibration,
            calibration_scores[field],
        )
        persisted_factors = {
            group: float(metadata["locked_multiplier"])
            for group, metadata in persisted["fit_period"]["multipliers"].items()
        }
        factor_reconciliation = {
            group: {
                "fresh_point_factor": float(fresh_point_factors[group]),
                "v32_persisted_factor": float(persisted_factors[group]),
                "relative_difference": _relative_difference(
                    fresh_point_factors[group], persisted_factors[group]
                ),
            }
            for group in sorted(persisted_factors)
        }
        max_factor_reconciliation = max(
            row["relative_difference"] for row in factor_reconciliation.values()
        )
        if max_factor_reconciliation > FRESH_RETRAIN_RELATIVE_TOLERANCE:
            raise AssertionError(
                f"fresh 2023 factor moved too far for {field}: {max_factor_reconciliation}"
            )

        baseline_test_pred = test_scores[field]
        baseline_deviance = float(
            mean_poisson_deviance(
                claims_test / exposure_test,
                baseline_test_pred,
                sample_weight=exposure_test,
            )
        )
        baseline_ratio = calibration_ratio(claims_test, baseline_test_pred, exposure_test)
        baseline_aggregate_error = float(abs(np.log(max(baseline_ratio, 1e-12))))
        group_stats = group_frequency_sufficient_statistics(
            segment_test,
            claims_test,
            exposure_test,
            baseline_test_pred,
        )
        baseline_max_segment_error = max(
            abs(
                np.log(
                    max(
                        float(stat["baseline_expected_claims"]) / max(float(stat["claims"]), 1e-12),
                        1e-12,
                    )
                )
            )
            for stat in group_stats.values()
        )

        point_candidate = evaluate_segment_factor_draw(
            baseline_poisson_deviance=baseline_deviance,
            group_stats=group_stats,
            factors=persisted_factors,
        )
        persisted_baseline = persisted["baseline_2024"]
        persisted_candidate = persisted["candidate_2024"]
        reconciliation_checks = {
            "baseline_deviance": _relative_difference(
                baseline_deviance, persisted_baseline["deviance"]
            ),
            "baseline_calibration": _relative_difference(
                baseline_ratio, persisted_baseline["calibration_ratio_pred_over_actual"]
            ),
            "candidate_deviance": _relative_difference(
                point_candidate["poisson_deviance"], persisted_candidate["deviance"]
            ),
            "candidate_calibration": _relative_difference(
                point_candidate["aggregate_calibration_ratio_pred_over_actual"],
                persisted_candidate["calibration_ratio_pred_over_actual"],
            ),
        }
        max_metric_reconciliation = max(reconciliation_checks.values())
        if max_metric_reconciliation > FRESH_RETRAIN_RELATIVE_TOLERANCE:
            raise AssertionError(
                f"fresh 2024 metrics moved too far for {field}: {max_metric_reconciliation}"
            )

        deviance_improved: list[bool] = []
        aggregate_nonworse: list[bool] = []
        worst_segment_improved: list[bool] = []
        original_deviance_guardrail: list[bool] = []
        candidate_deviances: list[float] = []
        aggregate_errors: list[float] = []
        max_segment_errors: list[float] = []

        for draw in range(BOOTSTRAP_DRAWS):
            factors = {
                group: float(bootstrap_factors[field][group][draw])
                for group in sorted(bootstrap_factors[field])
            }
            evaluated = evaluate_segment_factor_draw(
                baseline_poisson_deviance=baseline_deviance,
                group_stats=group_stats,
                factors=factors,
            )
            deviance = float(evaluated["poisson_deviance"])
            aggregate_error = float(evaluated["aggregate_abs_log_calibration_error"])
            max_segment_error = float(evaluated["max_segment_abs_log_calibration_error"])
            relative_deviance_change = deviance / baseline_deviance - 1.0
            d_improved = bool(deviance < baseline_deviance)
            a_nonworse = bool(aggregate_error <= baseline_aggregate_error)
            s_improved = bool(max_segment_error < baseline_max_segment_error)
            guardrail = bool(
                relative_deviance_change <= ORIGINAL_V32_MAX_RELATIVE_DEVIANCE_WORSENING
            )
            deviance_improved.append(d_improved)
            aggregate_nonworse.append(a_nonworse)
            worst_segment_improved.append(s_improved)
            original_deviance_guardrail.append(guardrail)
            candidate_deviances.append(deviance)
            aggregate_errors.append(aggregate_error)
            max_segment_errors.append(max_segment_error)
            draw_rows.append(
                {
                    "prediction_field": field,
                    "draw": draw,
                    "NB_factor": factors["NB"],
                    "P_factor": factors["P"],
                    "candidate_poisson_deviance": deviance,
                    "relative_deviance_change": relative_deviance_change,
                    "aggregate_abs_log_calibration_error": aggregate_error,
                    "max_segment_abs_log_calibration_error": max_segment_error,
                    "deviance_improved": d_improved,
                    "aggregate_calibration_not_worse": a_nonworse,
                    "worst_segment_calibration_improved": s_improved,
                    "original_v32_deviance_guardrail_pass": guardrail,
                }
            )

        factor_interval_direction_stable = True
        factors_within_guardrails = True
        factor_summary: dict[str, Any] = {}
        for group in sorted(bootstrap_factors[field]):
            draws = bootstrap_factors[field][group]
            quantiles = quantile_summary(draws)
            crosses_one = bool(quantiles["q025"] <= 1.0 <= quantiles["q975"])
            within_guardrails = bool(
                float(np.min(draws)) >= FACTOR_FLOOR and float(np.max(draws)) <= FACTOR_CAP
            )
            factor_interval_direction_stable = factor_interval_direction_stable and not crosses_one
            factors_within_guardrails = factors_within_guardrails and within_guardrails
            factor_summary[group] = {
                **factor_reconciliation[group],
                **quantiles,
                "interval_crosses_one": crosses_one,
                "min_draw": float(np.min(draws)),
                "max_draw": float(np.max(draws)),
                "all_draws_within_factor_guardrails": within_guardrails,
            }
            factor_rows.append(
                {
                    "prediction_field": field,
                    "segment": group,
                    **factor_summary[group],
                }
            )

        deviance_improvement_rate = float(np.mean(deviance_improved))
        aggregate_nonworse_rate = float(np.mean(aggregate_nonworse))
        worst_segment_improvement_rate = float(np.mean(worst_segment_improved))
        original_guardrail_rate = float(np.mean(original_deviance_guardrail))
        strong_robustness = bool(
            factor_interval_direction_stable
            and factors_within_guardrails
            and deviance_improvement_rate >= MIN_DEVIANCE_IMPROVEMENT_RATE
            and aggregate_nonworse_rate >= MIN_AGGREGATE_CALIBRATION_NONWORSE_RATE
            and worst_segment_improvement_rate
            >= MIN_WORST_SEGMENT_CALIBRATION_IMPROVEMENT_RATE
            and original_guardrail_rate >= MIN_ORIGINAL_DEVIANCE_GUARDRAIL_PASS_RATE
        )

        model_results[field] = {
            "v32_point_candidate_decision": persisted["candidate_gate"]["decision"],
            "factor_reconciliation": {
                "segments": factor_reconciliation,
                "max_relative_difference": max_factor_reconciliation,
                "relative_tolerance": FRESH_RETRAIN_RELATIVE_TOLERANCE,
            },
            "fresh_v32_metric_reconciliation": {
                "relative_differences": reconciliation_checks,
                "max_relative_difference": max_metric_reconciliation,
                "relative_tolerance": FRESH_RETRAIN_RELATIVE_TOLERANCE,
            },
            "baseline_2024": {
                "poisson_deviance": baseline_deviance,
                "aggregate_calibration_ratio_pred_over_actual": baseline_ratio,
                "aggregate_abs_log_calibration_error": baseline_aggregate_error,
                "max_segment_abs_log_calibration_error": baseline_max_segment_error,
            },
            "persisted_v32_point_candidate_replay": point_candidate,
            "factor_bootstrap": factor_summary,
            "bootstrap_metric_distributions": {
                "poisson_deviance": quantile_summary(candidate_deviances),
                "aggregate_abs_log_calibration_error": quantile_summary(aggregate_errors),
                "max_segment_abs_log_calibration_error": quantile_summary(max_segment_errors),
            },
            "robustness_rates": {
                "deviance_improvement_rate": deviance_improvement_rate,
                "aggregate_calibration_not_worse_rate": aggregate_nonworse_rate,
                "worst_segment_calibration_improvement_rate": worst_segment_improvement_rate,
                "original_v32_deviance_guardrail_pass_rate": original_guardrail_rate,
            },
            "strong_robustness_gate": {
                "factor_interval_direction_stable": bool(factor_interval_direction_stable),
                "all_factor_draws_within_guardrails": bool(factors_within_guardrails),
                "decision": (
                    "ROBUST_TO_2023_FACTOR_ESTIMATION_FOR_FURTHER_SHADOW_TESTING"
                    if strong_robustness
                    else "FACTOR_UNCERTAINTY_REVIEW_REQUIRED"
                ),
            },
        }

    robust_fields = [
        field
        for field, result in model_results.items()
        if result["strong_robustness_gate"]["decision"]
        == "ROBUST_TO_2023_FACTOR_ESTIMATION_FOR_FURTHER_SHADOW_TESTING"
    ]
    summary = {
        "status": "V34_RECALIBRATION_FACTOR_UNCERTAINTY_REVIEW_PASS",
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "model_train_year": 2022,
            "global_calibration_year": 2023,
            "factor_bootstrap_year": 2023,
            "evaluation_year": 2024,
            "factor_segment": "business_type",
            "calibration_rows": int(len(calibration)),
            "evaluation_rows": int(len(test)),
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_stratified_by": "business_type",
            "paired_indices_across_frequency_fields": True,
            "2024_labels_used_for_bootstrap_factor_fit": False,
            "factor_draws_are_clipped": False,
        },
        "registered_robustness_gate": {
            "factor_interval": "95% percentile interval for every NB/P factor must not cross 1",
            "factor_draw_guardrails": [FACTOR_FLOOR, FACTOR_CAP],
            "minimum_deviance_improvement_rate": MIN_DEVIANCE_IMPROVEMENT_RATE,
            "minimum_aggregate_calibration_nonworse_rate": MIN_AGGREGATE_CALIBRATION_NONWORSE_RATE,
            "minimum_worst_segment_calibration_improvement_rate": MIN_WORST_SEGMENT_CALIBRATION_IMPROVEMENT_RATE,
            "minimum_original_v32_deviance_guardrail_pass_rate": MIN_ORIGINAL_DEVIANCE_GUARDRAIL_PASS_RATE,
            "original_v32_max_relative_deviance_worsening": ORIGINAL_V32_MAX_RELATIVE_DEVIANCE_WORSENING,
            "fresh_retrain_relative_tolerance": FRESH_RETRAIN_RELATIVE_TOLERANCE,
            "threshold_boundary": "Project retrospective shadow-review rules; not insurer or regulatory thresholds.",
        },
        "models": model_results,
        "decision": {
            "robust_fields": robust_fields,
            "robust_field_count": len(robust_fields),
            "tested_field_count": len(model_results),
            "bundle_change_authorised": False,
            "pricing_change_authorised": False,
            "model_promotion_authorised": False,
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
        },
        "interpretation_boundary": (
            "This is a conditional row-bootstrap sensitivity analysis of the incremental 2023 business_type "
            "frequency factors given the rebuilt globally calibrated prediction functions. It does not bootstrap "
            "model fitting, global calibration, claim development or a new calendar period. 2024 outcomes are "
            "used only after each 2023 factor draw is fixed. It is retrospective evidence from one Spanish insurer "
            "and does not establish transfer to FIRST CENTRAL or the UK market."
        ),
    }

    _write_csv(OUTDIR / "frequency_recalibration_factor_bootstrap_summary.csv", factor_rows)
    _write_csv(OUTDIR / "frequency_recalibration_bootstrap_metrics.csv", draw_rows)
    (OUTDIR / "frequency_recalibration_uncertainty_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
