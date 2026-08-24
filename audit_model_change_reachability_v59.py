from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICY_PATH = Path("governance/model_change_reachability_policy_v59.json")
COMMITTEE_POLICY_PATH = Path("governance/model_change_committee_policy_v44.json")
COMMITTEE_DECISION_PATH = Path("action_results/v44/model_change_committee_decision_v44.json")
SYNTHESIS_PATH = Path("action_results/v43/model_family_evidence_synthesis_summary.json")
LATEST_STATE_PATH = Path("action_results/v58/ACTION_V58_STATUS.json")
OUT_PATH = Path("results_v59/committee_gate_reachability_audit_v59.json")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate_by_id(decision: dict[str, Any], gate_id: str) -> dict[str, Any]:
    matches = [g for g in decision["gate_results"] if g["gate_id"] == gate_id]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {gate_id} gate, found {len(matches)}")
    return matches[0]


def _policy_gate_by_id(policy: dict[str, Any], gate_id: str) -> dict[str, Any]:
    matches = [g for g in policy["gates"] if g["id"] == gate_id]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {gate_id} policy gate, found {len(matches)}")
    return matches[0]


def main() -> None:
    audit_policy = _read(POLICY_PATH)
    committee_policy = _read(COMMITTEE_POLICY_PATH)
    committee_decision = _read(COMMITTEE_DECISION_PATH)
    synthesis = _read(SYNTHESIS_PATH)
    latest = _read(LATEST_STATE_PATH)

    request_id = audit_policy["request_id"]
    if committee_policy["candidate_change_request"]["request_id"] != request_id:
        raise RuntimeError("Committee policy request changed")
    if committee_decision["request"]["request_id"] != request_id:
        raise RuntimeError("Committee decision request changed")
    if committee_decision["machine_gate_decision"]["request_id"] != request_id:
        raise RuntimeError("Machine-gate request changed")

    policy_decision = committee_policy["decision_policy"]
    if policy_decision["all_required_gates_must_pass_to_advance_to_human_review"] is not True:
        raise RuntimeError("v0.44 all-required-gates rule changed")
    if policy_decision["human_signoff_can_override_failed_evidence_gate"] is not False:
        raise RuntimeError("v0.44 failed-evidence override rule changed")
    if policy_decision["benchmark_can_override_validation_failure"] is not False:
        raise RuntimeError("v0.44 benchmark override rule changed")
    if policy_decision["consumed_validation_can_be_relabelled_fresh"] is not False:
        raise RuntimeError("v0.44 consumed-validation rule changed")

    g2_policy = _policy_gate_by_id(committee_policy, "G2_LOCKED_TEMPORAL_SUPPORT")
    expected_g2_description = (
        "The original locked temporal evaluation supports a global model-family change under its registered rule."
    )
    if g2_policy["description"] != expected_g2_description:
        raise RuntimeError("G2 description changed; reachability audit requires exact v0.44 semantics")

    g2 = _gate_by_id(committee_decision, "G2_LOCKED_TEMPORAL_SUPPORT")
    if g2["passed"] is not False or g2["status"] != "FAIL":
        raise RuntimeError("Persisted G2 result no longer matches the failed original locked decision")

    spanish = [
        item for item in synthesis["evidence_basis"]
        if item["id"] in {"spanish_2024_frequency", "spanish_2024_pure_premium"}
    ]
    if {item["id"] for item in spanish} != {"spanish_2024_frequency", "spanish_2024_pure_premium"}:
        raise RuntimeError("Spanish locked evidence is incomplete")
    if any(item["gate_passed"] is not False or item["registered_decision"] != "HOLD" for item in spanish):
        raise RuntimeError("Spanish locked evidence has been relabelled")

    machine = committee_decision["machine_gate_decision"]
    required_gate_count = int(machine["required_gate_count"])
    current_pass_count = int(machine["required_gate_pass_count"])
    failed_gate_ids = [g["gate_id"] for g in committee_decision["gate_results"] if g["required"] and not g["passed"]]
    if failed_gate_ids != [
        "G2_LOCKED_TEMPORAL_SUPPORT",
        "G3_PREREGISTERED_EXTERNAL_SUPPORT",
        "G4_FRESH_INDEPENDENT_EVIDENCE",
    ]:
        raise RuntimeError(f"Unexpected current blocker set: {failed_gate_ids}")
    if required_gate_count != 8 or current_pass_count != 5:
        raise RuntimeError("Persisted committee gate count changed")
    if latest["committee_gate_count"] != 8 or latest["committee_gate_pass_count"] != 5:
        raise RuntimeError("Latest persisted project state is not the expected 5/8 HOLD")

    structurally_unreachable = ["G2_LOCKED_TEMPORAL_SUPPORT"]
    potentially_resolvable = ["G3_PREREGISTERED_EXTERNAL_SUPPORT", "G4_FRESH_INDEPENDENT_EVIDENCE"]
    maximum_reachable_pass_count = required_gate_count - len(structurally_unreachable)
    human_review_reachable = maximum_reachable_pass_count == required_gate_count

    if maximum_reachable_pass_count != 7 or human_review_reachable:
        raise RuntimeError("Reachability calculation did not produce the expected terminal 7/8 ceiling")

    output = {
        "status": "V59_EXISTING_MODEL_CHANGE_REQUEST_STRUCTURALLY_UNREACHABLE",
        "request_id": request_id,
        "current_machine_gate_state": {
            "status": machine["status"],
            "passed": current_pass_count,
            "required": required_gate_count,
            "failed_gate_ids": failed_gate_ids,
        },
        "structural_blocker": {
            "gate_id": "G2_LOCKED_TEMPORAL_SUPPORT",
            "registered_requirement": g2_policy["description"],
            "persisted_result": g2["status"],
            "persisted_evidence": g2["evidence"],
            "historical_event_complete": True,
            "future_external_evidence_can_retroactively_change_this_gate": False,
            "reason": (
                "G2 is defined on the original locked temporal evaluation. Both Spanish 2024 registered target "
                "decisions are HOLD, so new external evidence cannot make that historical event supportive "
                "without changing the existing request's gate semantics."
            ),
        },
        "spanish_locked_evidence": [
            {
                "id": item["id"],
                "target": item["target"],
                "registered_decision": item["registered_decision"],
                "gate_passed": item["gate_passed"],
                "relative_deviance_improvement": item["relative_deviance_improvement"],
            }
            for item in spanish
        ],
        "reachability": {
            "structurally_unreachable_gate_ids": structurally_unreachable,
            "potentially_resolvable_current_failed_gate_ids": potentially_resolvable,
            "maximum_machine_gate_pass_count_without_redefining_existing_request": maximum_reachable_pass_count,
            "required_machine_gate_pass_count": required_gate_count,
            "ready_for_human_committee_review_reachable_for_existing_request": human_review_reachable,
            "terminal_existing_request_state": audit_policy["stop_rule"]["terminal_label_for_existing_request"],
        },
        "stop_rule": {
            "continue_external_dataset_shopping_only_to_open_MCR_XGB_MOTOR_001": False,
            "rewrite_G2_after_observing_new_evidence": False,
            "relabel_spanish_2024_supportive": False,
            "relabel_consumed_validation_fresh": False,
            "new_external_research_for_distinct_prospectively_registered_question_allowed": True,
            "new_change_request_requires_prospective_registration_before_fresh_outcome_access": True,
            "old_failed_request_history_must_remain_visible": True,
        },
        "governance": {
            "committee_status": "EVIDENCE_GAP_HOLD",
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "promotion_review_status": "NOT_OPEN",
            "model_promotion_authorised": False,
            "customer_pricing_authorised": False,
            "new_change_request_authorised": False,
            "first_central_or_current_uk_transport_claimed": False,
        },
        "evidence_boundary": {
            "row_level_external_data_accessed": False,
            "outcome_values_inspected": False,
            "candidate_selection_performed": False,
            "performance_metric_computed": False,
            "new_performance_gate_created": False,
            "v44_policy_modified": False,
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["reachability"], indent=2))


if __name__ == "__main__":
    main()
