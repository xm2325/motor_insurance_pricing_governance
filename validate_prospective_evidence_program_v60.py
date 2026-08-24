from __future__ import annotations

import json
from pathlib import Path

TEMPLATE_PATH = Path("governance/prospective_evidence_program_template_v60.json")
V57_PATH = Path("governance/external_temporal_prereg_v57.json")
OUT_PATH = Path("results_v60/prospective_evidence_program_validation_v60.json")


def main() -> None:
    t = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    v57 = json.loads(V57_PATH.read_text(encoding="utf-8"))

    if t["status"] != "V60_PROSPECTIVE_EVIDENCE_PROGRAM_TEMPLATE_NOT_ACTIVE_REQUEST":
        raise RuntimeError("Unexpected v0.60 template status")
    registration = t["future_request_registration"]
    if registration["active_request_id"] is not None or registration["selected_scope_mode"] is not None:
        raise RuntimeError("v0.60 must remain a template, not an activated request")
    if registration["template_does_not_authorise_MCR_XGB_MOTOR_002"] is not True:
        raise RuntimeError("Template accidentally authorises a future request")

    stages = {x["stage_id"]: x for x in t["fresh_evidence_stages"]}
    expected_stages = {
        "S1_LOCKED_TEMPORAL_QUALIFICATION",
        "S2_INDEPENDENT_EXTERNAL_REPLICATION",
        "S3_SEALED_RESERVE_CONFIRMATION",
    }
    if set(stages) != expected_stages:
        raise RuntimeError(f"Unexpected evidence stages: {sorted(stages)}")
    if t["independence_contract"]["minimum_pairwise_distinct_fresh_source_identities"] != 3:
        raise RuntimeError("Prospective programme must reserve three pairwise-distinct source identities")
    if t["independence_contract"]["one_dataset_cannot_simultaneously_count_as_qualification_replication_and_reserve"] is not True:
        raise RuntimeError("One-source multi-role reuse is not allowed")
    if stages["S2_INDEPENDENT_EXTERNAL_REPLICATION"]["must_be_distinct_from"] != ["S1_LOCKED_TEMPORAL_QUALIFICATION"]:
        raise RuntimeError("S2 independence contract changed")
    if set(stages["S3_SEALED_RESERVE_CONFIRMATION"]["must_be_distinct_from"]) != {
        "S1_LOCKED_TEMPORAL_QUALIFICATION",
        "S2_INDEPENDENT_EXTERNAL_REPLICATION",
    }:
        raise RuntimeError("S3 reserve independence contract changed")
    if stages["S3_SEALED_RESERVE_CONFIRMATION"]["must_remain_row_level_unaccessed_until_separate_authorised_release"] is not True:
        raise RuntimeError("S3 is not sealed")
    if stages["S3_SEALED_RESERVE_CONFIRMATION"]["can_be_used_to_rescue_failed_S1_or_S2"] is not False:
        raise RuntimeError("Reserve cannot rescue a failed qualification stage")

    budget = t["evidence_budget_and_stop_rules"]
    for key in [
        "maximum_fresh_source_identities_registered_for_S1",
        "maximum_fresh_source_identities_registered_for_S2",
        "maximum_fresh_source_identities_registered_for_S3",
    ]:
        if budget[key] != 1:
            raise RuntimeError(f"Evidence budget changed: {key}")
    for key in [
        "replace_failed_S1_with_another_dataset_allowed",
        "replace_failed_S2_with_another_dataset_allowed",
        "promote_S3_to_rescue_failed_S1_or_S2_allowed",
        "change_target_scope_after_failure_allowed",
        "weaken_performance_gate_after_failure_allowed",
    ]:
        if budget[key] is not False:
            raise RuntimeError(f"Stop rule weakened: {key}")

    gate = t["registered_default_performance_gate"]
    prior_gate = v57["registered_external_temporal_gate"]
    comparisons = {
        "minimum_relative_deviance_improvement": "minimum_relative_deviance_improvement",
        "bootstrap_relative_improvement_ci_lower_bound_must_exceed": "bootstrap_relative_improvement_ci_lower_bound_must_exceed",
        "maximum_additional_abs_log_aggregate_calibration_error": "maximum_additional_abs_log_aggregate_calibration_error",
    }
    for current_key, prior_key in comparisons.items():
        if gate[current_key] != prior_gate[prior_key]:
            raise RuntimeError(f"v0.60 weakened or changed inherited gate: {current_key}")
    if gate["paired_bootstrap_draws"] != v57["paired_bootstrap"]["draws"]:
        raise RuntimeError("Bootstrap draw count differs from v0.57")

    scope_logic = t["scope_gate_logic"]
    if set(scope_logic) != set(registration["allowed_scope_modes"]):
        raise RuntimeError("Every allowed future scope must have explicit gate logic")
    if "both frequency and pure-premium registered gates must pass" not in scope_logic["GLOBAL_TWO_TARGET"]:
        raise RuntimeError("Global scope does not require both targets")

    current = t["current_state"]
    required_false = [
        "fresh_source_identity_selected",
        "row_level_external_data_accessed",
        "outcome_values_inspected",
        "candidate_selection_performed",
        "customer_pricing_authorised",
    ]
    if any(current[key] is not False for key in required_false):
        raise RuntimeError("Template current state crossed a no-data/governance boundary")
    if current["model_family_decision"] != "HOLD" or current["serving_status"] != "HOLD_SHADOW_ONLY" or current["promotion_review_status"] != "NOT_OPEN":
        raise RuntimeError("Existing governance state changed")

    result = {
        "status": "V60_PROSPECTIVE_EVIDENCE_PROGRAM_TEMPLATE_VALIDATED",
        "active_change_request_created": False,
        "historical_parent_request": t["historical_parent"]["request_id"],
        "historical_parent_terminal_state_required": t["historical_parent"]["required_state"],
        "allowed_future_scope_modes": registration["allowed_scope_modes"],
        "selected_scope_mode": None,
        "fresh_evidence_stage_ids": list(stages),
        "minimum_pairwise_distinct_fresh_source_identities": 3,
        "sealed_reserve_required": True,
        "failed_stage_replacement_allowed": False,
        "inherited_gate": {
            "minimum_relative_deviance_improvement": gate["minimum_relative_deviance_improvement"],
            "bootstrap_ci_lower_bound_must_exceed": gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"],
            "maximum_additional_abs_log_calibration_error": gate["maximum_additional_abs_log_aggregate_calibration_error"],
            "paired_bootstrap_draws": gate["paired_bootstrap_draws"],
        },
        "external_row_data_accessed": False,
        "outcome_values_inspected": False,
        "candidate_selection_performed": False,
        "model_family_decision": "HOLD",
        "serving_status": "HOLD_SHADOW_ONLY",
        "promotion_review_status": "NOT_OPEN",
        "customer_pricing_authorised": False,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
