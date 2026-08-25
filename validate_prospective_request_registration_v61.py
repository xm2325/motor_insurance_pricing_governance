#!/usr/bin/env python3
"""Validate the v0.61 prospective request registration without touching source data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "governance" / "prospective_request_registration_v61.json"
V60 = ROOT / "governance" / "prospective_evidence_program_template_v60.json"
DEFAULT_OUTPUT = ROOT / "results" / "v61" / "prospective_request_registration_lock.json"

EXPECTED_SOURCE_IDS = {
    "S1_TEMPORAL_QUALIFICATION": "PRICING_GAME_2015_FRENCH_PRIVATE_MOTOR_TPL_2009_2010",
    "S2_EXTERNAL_REPLICATION": "SWEDISH_MOTORCYCLE_PARTIAL_CASCO_1994_1998",
    "S3_SEALED_CONFIRMATION": "BRAZIL_SUSEP_AUTOSEG_VEHICLE_INSURANCE_2011",
}
EXPECTED_BLOBS = {
    "S1_TEMPORAL_QUALIFICATION": ["9e670d214c05a7454d558ab32de5df96a6b0aba6"],
    "S2_EXTERNAL_REPLICATION": ["d48b2e78a94939f57d389110814037410a18c13c"],
    "S3_SEALED_CONFIRMATION": [
        "65132d163702f169d7932eba81cb4038f320acd7",
        "5e6a7a91863dfa3b0d4cc0af8a26b2e68f4bd33b",
        "6e60324ccf8fb6654cf97ff907efb15ea733d5d3",
        "efba95dcb82022a15d80929e9969fce6db3f2907",
        "4e7270940edd7d7c6e31cd7bd98399a15d90d8ce",
    ],
}


def canonical_sha256(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate(protocol: dict[str, Any]) -> dict[str, Any]:
    require(protocol["version"] == "v0.61", "wrong version")
    require(protocol["request_id"] == "MCR-XGB-MOTOR-002", "wrong request id")
    require(protocol["status"] == "REGISTERED_SEALED_BEFORE_S1", "wrong lifecycle state")
    require(protocol["activation"]["programme_scope"] == "GLOBAL_TWO_TARGET", "scope drift")
    require(protocol["activation"]["three_source_identities_registered_atomically"] is True, "not atomic")
    require(protocol["activation"]["minimum_pairwise_distinct_underlying_source_identities"] == 3, "wrong source count")
    require(protocol["activation"]["stage_sequence"] == list(EXPECTED_SOURCE_IDS), "stage order drift")
    require(protocol["activation"]["s2_may_open_only_after_reproducible_s1_pass"] is True, "S2 opening rule drift")
    require(protocol["activation"]["s3_may_open_only_after_reproducible_s1_and_s2_pass"] is True, "S3 opening rule drift")
    require(protocol["activation"]["reserve_cannot_rescue_s1_or_s2_failure"] is True, "reserve rescue drift")
    require(protocol["activation"]["source_substitution_after_stage_access_forbidden"] is True, "source substitution drift")

    require(protocol["distribution_channel"]["pinned_commit"] == "227fb56b8734bdb7c0327a41180e01d2ddaeaf26", "upstream pin drift")
    rules = protocol["source_identity_rules"]
    require(rules["schema_contract"] == "REQUIRED_COLUMN_NAME_SET_AND_SEMANTICS_NOT_COLUMN_ORDER", "schema contract drift")
    require(rules["column_order_is_not_identity_or_schema_gate"] is True, "column order was made a gate")
    require(rules["public_row_counts_are_provenance_expectations_not_binary_identity_gates"] is True, "row count was made identity gate")

    sources = protocol["sources"]
    require(set(sources) == set(EXPECTED_SOURCE_IDS), "source role set drift")
    identities = []
    for stage, expected_id in EXPECTED_SOURCE_IDS.items():
        src = sources[stage]
        require(src["underlying_source_identity"] == expected_id, f"{stage} source identity drift")
        identities.append(src["underlying_source_identity"])
        blobs = [x["git_blob_sha1"] for x in src["rda_files"]]
        require(blobs == EXPECTED_BLOBS[stage], f"{stage} blob set/order drift")
        require(src["row_level_accessed_at_v61"] is False, f"{stage} row access must be false")
        require(src["outcomes_accessed_at_v61"] is False, f"{stage} outcome access must be false")
    require(len(set(identities)) == 3, "underlying source identities are not pairwise distinct")
    require(sources["S3_SEALED_CONFIRMATION"]["five_files_form_one_underlying_source_identity"] is True, "S3 chunks misclassified")
    require(sources["S3_SEALED_CONFIRMATION"]["may_open_at_v61"] is False, "S3 opened early")

    s1 = sources["S1_TEMPORAL_QUALIFICATION"]
    require(s1["time_contract"]["required_calendar_year_set"] == [2009, 2010], "S1 year contract drift")
    require(s1["time_contract"]["development_year"] == 2009, "S1 development year drift")
    require(s1["time_contract"]["locked_temporal_test_year"] == 2010, "S1 test year drift")
    split = s1["time_contract"]["train_calibration_split"]
    require(split["hash"] == "SHA256" and split["salt"] == "v61|S1|20260825|", "S1 hash split drift")
    require(split["bucket_modulus"] == 10000, "S1 bucket modulus drift")
    require(split["expected_fraction_train"] == 0.8 and split["expected_fraction_calibration"] == 0.2, "S1 split fraction drift")
    leak = s1["pre_outcome_leakage_control"]
    require(leak["allowed_fields_before_outcome_access_after_schema_validation"] == ["PolNum", "CalYear"], "S1 pre-outcome fields drift")
    require("remove every row" in leak["action"], "S1 cross-year removal drift")
    require(leak["observed_cross_year_count_is_descriptive_not_a_tuning_or_validity_target"] is True, "S1 public count became gate")

    s2 = sources["S2_EXTERNAL_REPLICATION"]
    require(s2["split"]["method"] == "pinned_source_order_random_permutation", "S2 split method drift")
    require((s2["split"]["train_fraction"], s2["split"]["calibration_fraction"], s2["split"]["locked_test_fraction"]) == (0.6, 0.2, 0.2), "S2 split fraction drift")
    require(s2["may_open_at_v61"] is False, "S2 opened early")

    s3 = sources["S3_SEALED_CONFIRMATION"]
    require(s3["split"]["method"] == "fixed_concatenation_then_source_order_random_permutation", "S3 split method drift")
    require(s3["split"]["concatenation_order"] == ["brvehins1a", "brvehins1b", "brvehins1c", "brvehins1d", "brvehins1e"], "S3 chunk order drift")
    require((s3["split"]["train_fraction"], s3["split"]["calibration_fraction"], s3["split"]["locked_test_fraction"]) == (0.6, 0.2, 0.2), "S3 split fraction drift")

    model = protocol["registered_model_family"]
    require(model["frequency_reference"] == {"estimator": "PoissonRegressor", "alpha": 1e-8, "solver": "newton-cholesky", "tol": 1e-10, "max_iter": 2000}, "frequency GLM drift")
    require(model["pure_premium_reference"] == {"estimator": "TweedieRegressor", "power": 1.5, "link": "log", "alpha": 1e-6, "solver": "newton-cholesky", "tol": 1e-10, "max_iter": 3000}, "Tweedie GLM drift")
    for key, objective in (("frequency_challenger", "count:poisson"), ("pure_premium_challenger", "reg:tweedie")):
        challenger = model[key]
        require(challenger["objective"] == objective, f"{key} objective drift")
        require(challenger["n_estimators"] == 400 and challenger["max_depth"] == 3, f"{key} tree drift")
        require(challenger["learning_rate"] == 0.05 and challenger["subsample"] == 0.8 and challenger["colsample_bytree"] == 0.8, f"{key} sampling drift")
        require(challenger["min_child_weight"] == 20 and challenger["reg_lambda"] == 5, f"{key} regularisation drift")
        require(challenger["random_state"] == 20260823 and challenger["n_jobs"] == 1, f"{key} reproducibility drift")
    require(model["hyperparameter_search"] is False and model["early_stopping"] is False, "search/early stopping enabled")
    require(set(model["thread_environment"].values()) == {"1"}, "single-thread environment drift")

    require(protocol["calibration"] == {
        "method": "single_multiplicative_scale_on_calibration_partition_only",
        "lower_guard": 0.5,
        "upper_guard": 2.0,
        "prediction_clipping": False,
        "invalid_or_out_of_guard_scale_fails_target": True,
    }, "calibration rule drift")
    gate = protocol["target_gate"]
    require(gate["point_relative_deviance_improvement_min"] == 0.005, "point gate drift")
    require(gate["bootstrap_relative_deviance_improvement_q025_must_be_strictly_greater_than"] == 0.0, "bootstrap gate drift")
    require(gate["challenger_absolute_log_calibration_error_must_be_lte_reference_plus"] == 0.01, "calibration noninferiority drift")
    stage_gate = protocol["stage_gate"]
    require(stage_gate["GLOBAL_TWO_TARGET_requires_frequency_and_pure_premium_both_pass"] is True, "two-target conjunction drift")
    require(stage_gate["positive_stage_requires_two_independent_github_actions_executions"] is True, "positive reproducibility drift")
    require(stage_gate["decision_labels_must_match"] is True, "decision reproducibility drift")
    require(stage_gate["point_metric_relative_reproducibility_tolerance_max"] == 0.001, "metric reproducibility drift")

    state = protocol["v61_access_state"]
    for key in ("new_rda_downloaded", "new_rda_decoded", "row_level_new_source_accessed", "new_outcome_values_accessed", "model_fit_executed", "performance_metrics_computed", "s1_open", "s2_open", "s3_open"):
        require(state[key] is False, f"v61 access boundary violated: {key}")
    require(state["s3_reserve_sealed"] is True, "reserve not sealed")
    boundary = protocol["governance_boundary"]
    for key, value in boundary.items():
        require(value is True, f"governance boundary not asserted: {key}")
    require(protocol["inherits"]["historical_committee_gate_pass_count"] == 5, "historical gate count drift")
    require(protocol["inherits"]["historical_committee_gate_count"] == 8, "historical gate denominator drift")
    require(protocol["inherits"]["historical_model_family_decision"] == "HOLD", "historical decision drift")

    v60 = json.loads(V60.read_text())
    return {
        "version": "v0.61",
        "status": "V61_PROSPECTIVE_THREE_SOURCE_REGISTRATION_LOCK_PASS",
        "request_id": protocol["request_id"],
        "registration_status": protocol["status"],
        "programme_scope": protocol["activation"]["programme_scope"],
        "protocol_canonical_sha256": canonical_sha256(protocol),
        "v60_template_canonical_sha256": canonical_sha256(v60),
        "source_identity_count": len(identities),
        "source_identities_pairwise_distinct": len(set(identities)) == 3,
        "source_roles": {stage: sources[stage]["dataset"] for stage in EXPECTED_SOURCE_IDS},
        "s1_temporal_years": [2009, 2010],
        "s1_cross_year_policy_removal_pre_outcome": True,
        "s2_sealed": True,
        "s3_sealed": True,
        "new_rda_downloaded": False,
        "new_rda_decoded": False,
        "row_level_new_source_accessed": False,
        "new_outcome_values_accessed": False,
        "model_fit_executed": False,
        "performance_metrics_computed": False,
        "historical_committee_gate_pass_count": 5,
        "historical_committee_gate_count": 8,
        "historical_model_family_decision": "HOLD",
        "historical_serving_status": "HOLD_SHADOW_ONLY",
        "historical_promotion_review_status": "NOT_OPEN",
        "evidence_role": "PROSPECTIVE_REQUEST_REGISTRATION_ONLY_NOT_VALIDATION",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text())
    summary = validate(protocol)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
