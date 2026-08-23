from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PREREG = Path("governance/external_validation_prereg_v36.json")
OUTDIR = Path("results_v36")

EXPECTED_SOURCE_COMMIT = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
EXPECTED_FEATURES = {
    "numeric": ["VehValue"],
    "categorical": ["VehAge", "VehBody", "DrivAge"],
}
EXPECTED_EXCLUDED = ["Exposure", "Gender", "ClaimOcc", "ClaimNb", "ClaimAmount"]


class ExternalPreregistrationError(ValueError):
    pass


def canonical_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_prereg(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "0.36":
        raise ExternalPreregistrationError("schema_version must be 0.36")
    if payload.get("registered_before_row_level_access") is not True:
        raise ExternalPreregistrationError("row-level access boundary must be explicit")

    source = payload["source"]
    if source["dataset"] != "ausprivauto0405":
        raise ExternalPreregistrationError("external dataset changed")
    if source["upstream_repository"] != "dutangc/CASdatasets":
        raise ExternalPreregistrationError("upstream repository changed")
    if source["upstream_commit"] != EXPECTED_SOURCE_COMMIT:
        raise ExternalPreregistrationError("upstream source must remain commit-pinned")
    if source["upstream_path"] != "data/ausprivauto0405.rda":
        raise ExternalPreregistrationError("upstream data path changed")
    known = source["known_from_public_documentation_before_row_level_access"]
    if known["rows"] != 67856 or known["columns"] != 9:
        raise ExternalPreregistrationError("documented source dimensions changed")
    if known["policies_with_at_least_one_claim"] != 4624:
        raise ExternalPreregistrationError("pre-access public claim-occurrence metadata changed")

    independence = payload["independence_statement"]
    if independence["not_previously_used_by_project"] is not True:
        raise ExternalPreregistrationError("dataset must be new to this project")
    if independence["not_a_transport_test_of_the_spanish_fitted_parameters"] is not True:
        raise ExternalPreregistrationError("external replication boundary must remain explicit")
    if independence["evidence_class"] != "EXTERNAL_PORTFOLIO_MODEL_FAMILY_REPLICATION":
        raise ExternalPreregistrationError("external evidence class changed")

    data = payload["data_contract"]
    if data["required_rows"] != 67856:
        raise ExternalPreregistrationError("required row count changed")
    for key in (
        "fail_on_missing_required_value",
        "fail_on_nonpositive_exposure",
        "fail_on_negative_claim_count",
        "fail_on_noninteger_claim_count",
        "fail_on_negative_claim_amount",
        "no_post_download_row_filtering",
    ):
        if data[key] is not True:
            raise ExternalPreregistrationError(f"data fail-closed rule {key} relaxed")

    features = payload["features"]
    if features["numeric"] != EXPECTED_FEATURES["numeric"]:
        raise ExternalPreregistrationError("numeric feature set changed")
    if features["categorical"] != EXPECTED_FEATURES["categorical"]:
        raise ExternalPreregistrationError("categorical feature set changed")
    if features["excluded_from_predictors"] != EXPECTED_EXCLUDED:
        raise ExternalPreregistrationError("excluded feature set changed")
    if "ClaimOcc" not in features["excluded_from_predictors"]:
        raise ExternalPreregistrationError("ClaimOcc leakage boundary removed")
    if "Gender" not in features["excluded_from_predictors"]:
        raise ExternalPreregistrationError("registered primary feature policy changed")

    split = payload["split"]
    if split["seed"] != 20260823:
        raise ExternalPreregistrationError("split seed changed")
    if (split["train_fraction"], split["calibration_fraction"], split["locked_test_fraction"]) != (0.60, 0.20, 0.20):
        raise ExternalPreregistrationError("60/20/20 split changed")
    if split["test_used_for_hyperparameter_selection"] is not False:
        raise ExternalPreregistrationError("test tuning must remain forbidden")
    if split["calibration_used_for_hyperparameter_selection"] is not False:
        raise ExternalPreregistrationError("calibration tuning must remain forbidden")
    if split["resplitting_after_outcome_inspection_allowed"] is not False:
        raise ExternalPreregistrationError("post-outcome resplitting must remain forbidden")

    models = payload["models"]
    if models["hyperparameter_search_allowed"] is not False or models["early_stopping_allowed"] is not False:
        raise ExternalPreregistrationError("post-registration tuning must remain disabled")
    for name in ("frequency_xgb", "pure_premium_xgb"):
        model = models[name]
        expected = {
            "n_estimators": 400,
            "max_depth": 3,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 20,
            "reg_lambda": 5.0,
            "random_state": 20260823,
            "n_jobs": 2,
        }
        for key, value in expected.items():
            if model[key] != value:
                raise ExternalPreregistrationError(f"{name}.{key} changed")

    calibration = payload["calibration"]
    if calibration["scale_guardrails"] != [0.5, 2.0]:
        raise ExternalPreregistrationError("calibration scale guardrails changed")
    if calibration["scale_clipping_allowed"] is not False:
        raise ExternalPreregistrationError("calibration scale clipping must remain forbidden")

    bootstrap = payload["paired_bootstrap"]
    if bootstrap["draws"] != 500 or bootstrap["seed"] != 20260824:
        raise ExternalPreregistrationError("paired bootstrap registration changed")
    if bootstrap["paired_across_models"] is not True:
        raise ExternalPreregistrationError("paired bootstrap requirement removed")

    gate = payload["registered_external_replication_gate"]
    if gate["minimum_relative_deviance_improvement"] != 0.005:
        raise ExternalPreregistrationError("minimum deviance improvement changed")
    if gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"] != 0.0:
        raise ExternalPreregistrationError("bootstrap CI rule changed")
    if gate["maximum_additional_abs_log_aggregate_calibration_error"] != 0.01:
        raise ExternalPreregistrationError("calibration non-inferiority rule changed")

    decision = payload["decision_boundary"]
    if decision["model_family_decision_after_v36"] != "HOLD":
        raise ExternalPreregistrationError("model-family boundary changed")
    if decision["serving_status_after_v36"] != "HOLD_SHADOW_ONLY":
        raise ExternalPreregistrationError("serving boundary changed")
    if decision["external_replication_can_directly_authorise_model_promotion"] is not False:
        raise ExternalPreregistrationError("external replication may not directly promote")
    if decision["external_replication_can_directly_authorise_customer_pricing"] is not False:
        raise ExternalPreregistrationError("external replication may not directly change pricing")
    if decision["no_rule_split_or_hyperparameter_changes_after_test_results"] is not True:
        raise ExternalPreregistrationError("post-result rule changes must remain forbidden")


def ensure_no_row_level_external_data_present() -> None:
    forbidden = [
        Path("data_external/ausprivauto0405.rda"),
        Path("data_external/ausprivauto0405.csv"),
        Path("data_external/ausprivauto0405.parquet"),
    ]
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise ExternalPreregistrationError(
            "v0.36 must be registered before row-level external data are present: " + ", ".join(present)
        )


def main() -> None:
    payload = json.loads(PREREG.read_text(encoding="utf-8"))
    validate_prereg(payload)
    ensure_no_row_level_external_data_present()
    digest = canonical_sha256(payload)
    result = {
        "status": "V36_EXTERNAL_VALIDATION_PREREGISTRATION_LOCKED",
        "preregistration_sha256": digest,
        "source_dataset": payload["source"]["dataset"],
        "source_commit": payload["source"]["upstream_commit"],
        "registered_before_row_level_access": True,
        "row_level_external_data_present": False,
        "primary_target": payload["targets"]["primary"]["name"],
        "secondary_target": payload["targets"]["secondary_confirmatory"]["name"],
        "split": {
            "seed": payload["split"]["seed"],
            "fractions": [
                payload["split"]["train_fraction"],
                payload["split"]["calibration_fraction"],
                payload["split"]["locked_test_fraction"],
            ],
        },
        "bootstrap_draws": payload["paired_bootstrap"]["draws"],
        "model_family_decision": "HOLD",
        "serving_status": "HOLD_SHADOW_ONLY",
        "execution_allowed_only_after_preregistration_is_on_main": True,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "external_validation_prereg_lock.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
