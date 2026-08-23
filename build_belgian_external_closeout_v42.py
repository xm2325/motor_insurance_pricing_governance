from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

PREREG_PATH = Path("governance/external_validation_prereg_v40.json")
OBSERVATIONS_PATH = Path("governance/belgian_external_reproducibility_observations_v42.json")
USE_LEDGER_PATH = Path("governance/external_validation_use_ledger_v42.json")
ORIGIN_DIR = Path("action_results/v41/origin/32637884887")
ORIGIN_RESULT_PATH = ORIGIN_DIR / "belgian_external_replication_first_execution.json"
ORIGIN_STATUS_PATH = ORIGIN_DIR / "ACTION_V41_STATUS.json"
OUTDIR = Path("results_v42")
OUTPATH = OUTDIR / "belgian_external_closeout_summary.json"


class BelgianExternalCloseoutV42Error(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _within_registered_tolerance(a: float, b: float, *, rel_tol: float, abs_tol: float) -> bool:
    return math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=abs_tol)


def _relative_difference(a: float, b: float) -> float:
    denominator = max(abs(float(a)), abs(float(b)), 1e-300)
    return abs(float(a) - float(b)) / denominator


def _flatten_main_metrics(result: dict[str, Any]) -> dict[str, dict[str, float | str]]:
    flattened: dict[str, dict[str, float | str]] = {}
    for target in ("frequency", "pure_premium"):
        payload = result[target]
        test = payload["locked_test"]
        bootstrap = payload["paired_bootstrap_relative_deviance_improvement"]
        scales = payload["calibration_scales"]
        reference_cal = test["reference_calibration"]
        challenger_cal = test["challenger_calibration"]
        if target == "frequency":
            reference_capture = test["reference_top_10_percent_exposure_claim_capture"]
            challenger_capture = test["challenger_top_10_percent_exposure_claim_capture"]
        else:
            reference_capture = test["reference_top_10_percent_exposure_loss_capture"]
            challenger_capture = test["challenger_top_10_percent_exposure_loss_capture"]
        flattened[target] = {
            "reference_calibration_scale": scales["reference"],
            "challenger_calibration_scale": scales["challenger"],
            "reference_deviance": test["reference_deviance"],
            "challenger_deviance": test["challenger_deviance"],
            "relative_deviance_improvement": test["relative_deviance_improvement"],
            "reference_calibration_ratio": reference_cal["calibration_ratio_pred_over_actual"],
            "reference_abs_log_calibration_error": reference_cal["abs_log_calibration_error"],
            "challenger_calibration_ratio": challenger_cal["calibration_ratio_pred_over_actual"],
            "challenger_abs_log_calibration_error": challenger_cal["abs_log_calibration_error"],
            "reference_top10_capture": reference_capture,
            "challenger_top10_capture": challenger_capture,
            "bootstrap_q025": bootstrap["q025"],
            "bootstrap_median": bootstrap["median"],
            "bootstrap_q975": bootstrap["q975"],
            "bootstrap_positive_draw_rate": bootstrap["positive_draw_rate"],
            "registered_decision": payload["registered_gate"]["decision"],
        }
    return flattened


def build_closeout() -> dict[str, Any]:
    prereg = _load(PREREG_PATH)
    observations = _load(OBSERVATIONS_PATH)
    ledger = _load(USE_LEDGER_PATH)
    origin = _load(ORIGIN_RESULT_PATH)
    origin_status = _load(ORIGIN_STATUS_PATH)

    if prereg["schema_version"] != "0.40":
        raise BelgianExternalCloseoutV42Error("v0.40 preregistration schema changed")
    runtime = prereg["runtime_reproducibility"]
    rel_tol = float(runtime["point_metric_relative_tolerance"])
    abs_tol = float(runtime["point_metric_absolute_tolerance"])
    if rel_tol != float(observations["registered_relative_tolerance"]) or abs_tol != float(observations["registered_absolute_tolerance"]):
        raise BelgianExternalCloseoutV42Error("v0.42 observations do not use the registered v0.40 tolerance")

    events = observations["execution_events"]
    aborted = [event for event in events if event["role"] == "SOURCE_ACCESSED_ABORTED_BEFORE_MODEL_FIT"]
    completed = [event for event in events if event.get("counted_as_completed_model_execution") is True]
    if len(aborted) != 1 or aborted[0]["run_id"] != 32637645586:
        raise BelgianExternalCloseoutV42Error("pre-fit abort lineage changed")
    if aborted[0]["model_fit_completed"] or aborted[0]["locked_test_metrics_generated"]:
        raise BelgianExternalCloseoutV42Error("pre-fit abort must not be counted as model evidence")
    if [event["run_id"] for event in completed] != [32637809066, 32637884887]:
        raise BelgianExternalCloseoutV42Error("completed execution lineage changed")

    pr_event = completed[0]
    main_event = completed[1]
    if pr_event["azure_region"] != "eastus2" or main_event["azure_region"] != "centralus":
        raise BelgianExternalCloseoutV42Error("observed runner-region provenance changed")
    if pr_event["artifact_zip_sha256"] != "18eacc7a39a460b01021e9295b4241779738e566206668782b147372f56abcb5":
        raise BelgianExternalCloseoutV42Error("PR artifact provenance changed")
    if main_event["artifact_zip_sha256"] != "34b59e5e492d434bcb3e85856acb7b53a6298aeb8b138f3df18158e821151bf8":
        raise BelgianExternalCloseoutV42Error("main artifact provenance changed")

    if origin_status["run_id"] != "32637884887" or origin_status["sha"] != "241df6c2b6e6f20472a0bc236b27474c9b20583b":
        raise BelgianExternalCloseoutV42Error("immutable main origin identity changed")
    if origin_status["evidence_role"] != "IMMUTABLE_EXECUTION_SNAPSHOT" or origin_status["status"] != "success":
        raise BelgianExternalCloseoutV42Error("main origin is not an immutable successful snapshot")
    if origin_status["raw_external_data_persisted"] or origin_status["positive_external_support_authorised"]:
        raise BelgianExternalCloseoutV42Error("v0.41 governance boundary changed")

    expected_source_sha = observations["source_file_sha256"]
    if origin["source"]["file_sha256"] != expected_source_sha or main_event["source_file_sha256"] != expected_source_sha or pr_event["source_file_sha256"] != expected_source_sha:
        raise BelgianExternalCloseoutV42Error("Belgian source identity differs between executions")
    if origin["source"]["rows"] != 163212 or origin["source"]["unique_policy_ids"] != 163212:
        raise BelgianExternalCloseoutV42Error("Belgian source dimensions changed")
    if origin["source"]["raw_data_persisted_to_repository"] is not False:
        raise BelgianExternalCloseoutV42Error("raw Belgian source must not be persisted")

    expected_split_rows = {"train": 97927, "calibration": 32642, "locked_test": 32643}
    for split_name, rows in expected_split_rows.items():
        if origin["split"][split_name]["rows"] != rows:
            raise BelgianExternalCloseoutV42Error(f"{split_name} row count changed")
    if origin["split"]["outcome_stratified"] or origin["split"]["resplit_after_outcome_inspection"]:
        raise BelgianExternalCloseoutV42Error("registered split boundary changed")

    if origin["runtime"]["glm_fit"]["frequency"] != {"n_iter": 5, "warnings": []}:
        raise BelgianExternalCloseoutV42Error("frequency GLM convergence evidence changed")
    if origin["runtime"]["glm_fit"]["pure_premium"] != {"n_iter": 4, "warnings": []}:
        raise BelgianExternalCloseoutV42Error("pure-premium GLM convergence evidence changed")
    if origin["runtime"]["thread_environment"] != {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}:
        raise BelgianExternalCloseoutV42Error("single-thread runtime evidence changed")

    main_metrics = _flatten_main_metrics(origin)
    comparisons: dict[str, Any] = {}
    max_abs_difference = 0.0
    max_relative_difference = 0.0
    all_numeric_within_tolerance = True
    decisions_match = True
    for target in ("frequency", "pure_premium"):
        pr_metrics = pr_event["metrics"][target]
        target_comparisons: dict[str, Any] = {}
        for key, pr_value in pr_metrics.items():
            main_value = main_metrics[target][key]
            if key == "registered_decision":
                matches = pr_value == main_value
                decisions_match = decisions_match and matches
                target_comparisons[key] = {"pr": pr_value, "main": main_value, "matches": matches}
                continue
            abs_difference = abs(float(pr_value) - float(main_value))
            relative_difference = _relative_difference(float(pr_value), float(main_value))
            within = _within_registered_tolerance(float(pr_value), float(main_value), rel_tol=rel_tol, abs_tol=abs_tol)
            max_abs_difference = max(max_abs_difference, abs_difference)
            max_relative_difference = max(max_relative_difference, relative_difference)
            all_numeric_within_tolerance = all_numeric_within_tolerance and within
            target_comparisons[key] = {
                "pr": pr_value,
                "main": main_value,
                "absolute_difference": abs_difference,
                "relative_difference": relative_difference,
                "within_registered_tolerance": within,
            }
        comparisons[target] = target_comparisons

    if not decisions_match:
        raise BelgianExternalCloseoutV42Error("registered Belgian decisions did not reproduce")
    if not all_numeric_within_tolerance:
        raise BelgianExternalCloseoutV42Error("Belgian registered metrics exceed v0.40 reproducibility tolerance")
    if main_metrics["frequency"]["registered_decision"] != "NO_SECOND_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT":
        raise BelgianExternalCloseoutV42Error("frequency negative decision changed")
    if main_metrics["pure_premium"]["registered_decision"] != "NO_SECOND_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT":
        raise BelgianExternalCloseoutV42Error("pure-premium negative decision changed")
    if origin["reproducibility"]["any_first_execution_registered_gate_positive"] is not False:
        raise BelgianExternalCloseoutV42Error("v0.41 unexpectedly contains a positive registered gate")
    if origin["reproducibility"]["status"] != "NO_POSITIVE_GATE_TO_REPRODUCE":
        raise BelgianExternalCloseoutV42Error("negative-result reproducibility status changed")

    if ledger["current_role"] != "CONSUMED_EXTERNAL_VALIDATION_DATASET":
        raise BelgianExternalCloseoutV42Error("Belgian dataset must be consumed after locked-test inspection")
    if ledger["independent_external_validation_available"] or ledger["candidate_selection_allowed"] or ledger["fresh_independent_confirmation_allowed"]:
        raise BelgianExternalCloseoutV42Error("consumed Belgian dataset cannot provide fresh candidate evidence")
    required_forbidden = {
        "fit_new_model_parameters", "fit_new_calibration_parameters", "hyperparameter_search",
        "change_feature_set_after_outcome_inspection", "change_solver_or_tolerance_to_improve_locked_test_result",
        "resplit_or_reseed_for_candidate_selection", "select_new_candidate_policy", "independent_confirmation",
        "authorise_model_family_promotion", "authorise_customer_pricing",
    }
    if not required_forbidden.issubset(set(ledger["forbidden_future_purposes"])):
        raise BelgianExternalCloseoutV42Error("Belgian consumption firewall was relaxed")

    result = {
        "status": "V42_BELGIAN_EXTERNAL_CLOSEOUT_PASS",
        "reproducibility": {
            "status": "V42_BELGIAN_POINT_METRICS_REPRODUCED_WITHIN_REGISTERED_TOLERANCE",
            "completed_model_execution_run_ids": [32637809066, 32637884887],
            "observed_regions": ["eastus2", "centralus"],
            "aborted_pre_fit_run_id": 32637645586,
            "aborted_run_counted_as_completed_execution": False,
            "registered_relative_tolerance": rel_tol,
            "registered_absolute_tolerance": abs_tol,
            "max_absolute_difference": max_abs_difference,
            "max_relative_difference": max_relative_difference,
            "all_registered_numeric_metrics_within_tolerance": all_numeric_within_tolerance,
            "registered_decisions_match": decisions_match,
            "universal_bitwise_determinism_claimed": False,
            "hardware_or_region_cause_claimed": False,
            "comparisons": comparisons,
        },
        "registered_results": {
            "frequency_decision": main_metrics["frequency"]["registered_decision"],
            "frequency_relative_deviance_improvement": main_metrics["frequency"]["relative_deviance_improvement"],
            "frequency_bootstrap_q025": main_metrics["frequency"]["bootstrap_q025"],
            "pure_premium_decision": main_metrics["pure_premium"]["registered_decision"],
            "pure_premium_relative_deviance_improvement": main_metrics["pure_premium"]["relative_deviance_improvement"],
            "pure_premium_bootstrap_q025": main_metrics["pure_premium"]["bootstrap_q025"],
            "positive_gate_present": False,
            "positive_support_reproduction_required_for_observed_result": False,
        },
        "external_validation_use": {
            "dataset_id": ledger["dataset_id"],
            "current_role": ledger["current_role"],
            "independent_external_validation_available": ledger["independent_external_validation_available"],
            "candidate_selection_allowed": ledger["candidate_selection_allowed"],
            "fresh_independent_confirmation_allowed": ledger["fresh_independent_confirmation_allowed"],
        },
        "decision": ledger["decision"],
        "interpretation": "The Belgian negative registered decisions reproduce across the two completed observed GitHub Actions executions and all registered aggregate numerical metrics are within the preregistered v0.40 tolerance. This is an observed reproducibility result, not a universal determinism claim and not positive XGBoost support. The Belgian locked test is now consumed for future candidate selection.",
    }
    if result["decision"] != {"model_family_decision": "HOLD", "serving_status": "HOLD_SHADOW_ONLY", "model_promotion_authorised": False, "pricing_change_authorised": False}:
        raise BelgianExternalCloseoutV42Error("governance HOLD boundary changed")
    return result


def main() -> None:
    result = build_closeout()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUTPATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
