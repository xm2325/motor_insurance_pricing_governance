from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PREREG = Path("governance/external_validation_prereg_v40.json")
OUTDIR = Path("results_v40")
EXPECTED_SOURCE_COMMIT = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
EXPECTED_COLUMNS = [
    "id", "expo", "claim", "nclaims", "amount", "average", "coverage", "ageph",
    "sex", "bm", "power", "agec", "fuel", "use", "fleet", "postcode", "long", "lat",
]
EXPECTED_NUMERIC = ["ageph", "bm", "power", "agec"]
EXPECTED_CATEGORICAL = ["coverage", "fuel", "use", "fleet"]
EXPECTED_EXCLUDED = ["id", "expo", "claim", "nclaims", "amount", "average", "sex", "postcode", "long", "lat"]


class ExternalPreregistrationV40Error(ValueError):
    pass


def canonical_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_prereg(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "0.40":
        raise ExternalPreregistrationV40Error("schema_version must be 0.40")
    if payload.get("registered_before_row_level_access") is not True:
        raise ExternalPreregistrationV40Error("row-level access boundary must remain explicit")

    source = payload["source"]
    if source["dataset"] != "beMTPL97" or source["upstream_repository"] != "dutangc/CASdatasets":
        raise ExternalPreregistrationV40Error("Belgian source identity changed")
    if source["upstream_commit"] != EXPECTED_SOURCE_COMMIT or source["upstream_path"] != "data/beMTPL97.rda":
        raise ExternalPreregistrationV40Error("Belgian source must remain commit/path pinned")
    known = source["known_from_public_documentation_before_row_level_access"]
    if known["rows"] != 163212 or known["unique_policyholders"] != 163212 or known["columns"] != 18:
        raise ExternalPreregistrationV40Error("public pre-access dimensions changed")
    if known["column_names"] != EXPECTED_COLUMNS:
        raise ExternalPreregistrationV40Error("public pre-access schema changed")

    independence = payload["independence_statement"]
    for key in (
        "not_previously_used_by_project",
        "not_a_transport_test_of_spanish_or_australian_fitted_parameters",
        "not_a_reuse_of_the_consumed_australian_locked_test",
    ):
        if independence[key] is not True:
            raise ExternalPreregistrationV40Error(f"independence rule {key} relaxed")
    if independence["evidence_class"] != "SECOND_EXTERNAL_PORTFOLIO_MODEL_FAMILY_REPLICATION":
        raise ExternalPreregistrationV40Error("evidence class changed")

    data = payload["data_contract"]
    if data["required_rows"] != 163212 or data["required_columns"] != EXPECTED_COLUMNS:
        raise ExternalPreregistrationV40Error("data contract dimensions/schema changed")
    for key in (
        "fail_on_duplicate_id", "fail_on_nonpositive_exposure", "fail_on_exposure_above_one",
        "fail_on_negative_claim_count", "fail_on_noninteger_claim_count", "fail_on_negative_claim_amount",
        "fail_on_nonfinite_numeric_model_input", "no_post_download_row_filtering",
        "no_outcome_winsorisation_or_clipping",
    ):
        if data[key] is not True:
            raise ExternalPreregistrationV40Error(f"fail-closed data rule {key} relaxed")

    features = payload["features"]
    if features["numeric"] != EXPECTED_NUMERIC or features["categorical"] != EXPECTED_CATEGORICAL:
        raise ExternalPreregistrationV40Error("registered feature set changed")
    if features["excluded_from_predictors"] != EXPECTED_EXCLUDED:
        raise ExternalPreregistrationV40Error("excluded feature set changed")
    for forbidden in ("id", "claim", "average", "sex", "postcode", "long", "lat"):
        if forbidden not in features["excluded_from_predictors"]:
            raise ExternalPreregistrationV40Error(f"excluded predictor {forbidden} reintroduced")
    prep = features["preprocessing"]
    if prep["fit_on_training_only"] is not True or prep["category_pooling_or_target_encoding_allowed"] is not False:
        raise ExternalPreregistrationV40Error("preprocessing leakage boundary relaxed")

    split = payload["split"]
    if split["seed"] != 20260825:
        raise ExternalPreregistrationV40Error("split seed changed")
    if (split["train_fraction"], split["calibration_fraction"], split["locked_test_fraction"]) != (0.6, 0.2, 0.2):
        raise ExternalPreregistrationV40Error("60/20/20 split changed")
    if split["test_used_for_hyperparameter_selection"] or split["calibration_used_for_hyperparameter_selection"]:
        raise ExternalPreregistrationV40Error("holdout/calibration tuning is forbidden")
    if split["resplitting_after_outcome_inspection_allowed"]:
        raise ExternalPreregistrationV40Error("post-outcome resplitting is forbidden")

    runtime = payload["runtime_reproducibility"]
    expected_versions = {
        "python_version": "3.12", "numpy_version": "2.5.2", "scipy_version": "1.18.0",
        "scikit_learn_version": "1.9.0", "xgboost_version": "3.4.1", "pyreadr_version": "0.5.3",
    }
    for key, value in expected_versions.items():
        if runtime[key] != value:
            raise ExternalPreregistrationV40Error(f"runtime pin {key} changed")
    if runtime["thread_environment"] != {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}:
        raise ExternalPreregistrationV40Error("single-thread numeric environment changed")
    if runtime["minimum_independent_actions_executions_for_positive_external_support"] != 2:
        raise ExternalPreregistrationV40Error("two-run positive-evidence rule changed")
    if not runtime["positive_external_support_requires_matching_registered_decisions"]:
        raise ExternalPreregistrationV40Error("matching-decision reproducibility removed")
    if not runtime["positive_external_support_requires_registered_point_metric_reproducibility"]:
        raise ExternalPreregistrationV40Error("point-metric reproducibility removed")
    if runtime["point_metric_relative_tolerance"] != 1e-8 or runtime["point_metric_absolute_tolerance"] != 1e-10:
        raise ExternalPreregistrationV40Error("point-metric tolerance changed")

    models = payload["models"]
    for name in ("frequency_glm", "pure_premium_glm"):
        model = models[name]
        if model["solver"] != "newton-cholesky" or model["tol"] != 1e-10 or model["max_iter"] != 500:
            raise ExternalPreregistrationV40Error(f"{name} solver/tolerance changed")
        if model["convergence_required"] is not True or model["fallback_solver_allowed"] is not False:
            raise ExternalPreregistrationV40Error(f"{name} convergence/fallback boundary changed")
    for name in ("frequency_xgb", "pure_premium_xgb"):
        model = models[name]
        expected = {
            "n_estimators": 400, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.8,
            "colsample_bytree": 0.8, "min_child_weight": 20, "reg_lambda": 5.0,
            "random_state": 20260825, "n_jobs": 1,
        }
        for key, value in expected.items():
            if model[key] != value:
                raise ExternalPreregistrationV40Error(f"{name}.{key} changed")
    if models["hyperparameter_search_allowed"] or models["early_stopping_allowed"] or models["post_result_solver_change_allowed"]:
        raise ExternalPreregistrationV40Error("post-registration model tuning must remain disabled")

    calibration = payload["calibration"]
    if calibration["scale_guardrails"] != [0.5, 2.0] or calibration["scale_clipping_allowed"]:
        raise ExternalPreregistrationV40Error("calibration guardrail changed")

    bootstrap = payload["paired_bootstrap"]
    if bootstrap["draws"] != 500 or bootstrap["seed"] != 20260826 or bootstrap["paired_across_models"] is not True:
        raise ExternalPreregistrationV40Error("paired bootstrap registration changed")

    gate = payload["registered_external_replication_gate"]
    if gate["minimum_relative_deviance_improvement"] != 0.005:
        raise ExternalPreregistrationV40Error("minimum deviance improvement changed")
    if gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"] != 0.0:
        raise ExternalPreregistrationV40Error("bootstrap CI rule changed")
    if gate["maximum_additional_abs_log_aggregate_calibration_error"] != 0.01:
        raise ExternalPreregistrationV40Error("calibration non-inferiority rule changed")

    decision = payload["decision_boundary"]
    if decision["model_family_decision_after_v40"] != "HOLD" or decision["serving_status_after_v40"] != "HOLD_SHADOW_ONLY":
        raise ExternalPreregistrationV40Error("governance HOLD boundary changed")
    if decision["external_replication_can_directly_authorise_model_promotion"] or decision["external_replication_can_directly_authorise_customer_pricing"]:
        raise ExternalPreregistrationV40Error("external replication cannot directly authorise production/pricing")
    if decision["no_rule_split_feature_model_solver_metric_gate_or_reproducibility_changes_after_test_results"] is not True:
        raise ExternalPreregistrationV40Error("post-result rule freeze removed")
    if decision["execution_allowed_only_after_preregistration_is_on_main"] is not True:
        raise ExternalPreregistrationV40Error("execution-before-main boundary removed")


def ensure_no_row_level_belgian_data_present() -> None:
    forbidden = [
        Path("data_external_v40/beMTPL97.rda"), Path("data_external_v40/beMTPL97.csv"), Path("data_external_v40/beMTPL97.parquet"),
        Path("data_external/beMTPL97.rda"), Path("data_external/beMTPL97.csv"), Path("data_external/beMTPL97.parquet"),
    ]
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise ExternalPreregistrationV40Error("v0.40 preregistration must precede Belgian row-level data access: " + ", ".join(present))


def main() -> None:
    payload = json.loads(PREREG.read_text(encoding="utf-8"))
    validate_prereg(payload)
    ensure_no_row_level_belgian_data_present()
    result = {
        "status": "V40_BELGIAN_EXTERNAL_VALIDATION_PREREGISTRATION_LOCKED",
        "preregistration_sha256": canonical_sha256(payload),
        "source_dataset": payload["source"]["dataset"],
        "source_commit": payload["source"]["upstream_commit"],
        "registered_before_row_level_access": True,
        "row_level_external_data_present": False,
        "known_public_rows": payload["source"]["known_from_public_documentation_before_row_level_access"]["rows"],
        "split": {"seed": payload["split"]["seed"], "fractions": [payload["split"]["train_fraction"], payload["split"]["calibration_fraction"], payload["split"]["locked_test_fraction"]]},
        "bootstrap_draws": payload["paired_bootstrap"]["draws"],
        "minimum_reproducibility_runs_for_positive_support": payload["runtime_reproducibility"]["minimum_independent_actions_executions_for_positive_external_support"],
        "glm_solver": payload["models"]["pure_premium_glm"]["solver"],
        "glm_tolerance": payload["models"]["pure_premium_glm"]["tol"],
        "model_family_decision": "HOLD",
        "serving_status": "HOLD_SHADOW_ONLY",
        "execution_allowed_only_after_preregistration_is_on_main": True,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "belgian_external_validation_prereg_lock.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
