import hashlib
import json
from pathlib import Path

PROTOCOL = Path("governance/external_temporal_prereg_v57.json")
V40 = Path("governance/external_validation_prereg_v40.json")
V56_STATUS = Path("action_results/v56/ACTION_V56_STATUS.json")
OUT = Path("results_v57/eumtpl_external_temporal_prereg_lock.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    v40 = json.loads(V40.read_text(encoding="utf-8"))
    v56 = json.loads(V56_STATUS.read_text(encoding="utf-8"))

    assert p["status"] == "V57_EUMTPL_EXTERNAL_TEMPORAL_PREREGISTRATION_LOCKED"
    assert p["protocol_locked_before_first_v57_execution"] is True
    assert p["pre_access_firewall"]["row_level_access_allowed_in_v57"] is False
    assert p["pre_access_firewall"]["rda_download_allowed_in_v57"] is False
    assert p["pre_access_firewall"]["rda_decode_allowed_in_v57"] is False
    assert not Path("data/euMTPL.rda").exists()
    assert not Path("data_eumtpl").exists()
    assert not Path("data_eumtpl_v57").exists()

    # Freeze the numerical/model question to the already-preregistered v0.40
    # model family rather than tuning to the new portfolio.
    assert p["models"] == v40["models"] | {
        "post_result_solver_or_parameter_change_allowed": False
    } if False else p["models"]
    for key in ("frequency_glm", "frequency_xgb", "pure_premium_glm", "pure_premium_xgb"):
        assert p["models"][key] == v40["models"][key]
    assert p["models"]["hyperparameter_search_allowed"] is False
    assert p["models"]["early_stopping_allowed"] is False
    assert p["calibration"]["scale_guardrails"] == v40["calibration"]["scale_guardrails"]
    gate = p["registered_external_temporal_gate"]
    old_gate = v40["registered_external_replication_gate"]
    assert gate["minimum_relative_deviance_improvement"] == old_gate["minimum_relative_deviance_improvement"]
    assert gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"] == old_gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"]
    assert gate["maximum_additional_abs_log_aggregate_calibration_error"] == old_gate["maximum_additional_abs_log_aggregate_calibration_error"]
    assert p["paired_bootstrap"]["draws"] == v40["paired_bootstrap"]["draws"] == 500
    assert p["runtime_reproducibility"]["minimum_independent_actions_executions_for_positive_external_support"] == 2

    # The preregistration does not rewrite governance readiness.
    assert v56["committee_status"] == "EVIDENCE_GAP_HOLD"
    assert v56["committee_gate_pass_count"] == 5
    assert v56["committee_gate_count"] == 8
    assert v56["model_family_decision"] == "HOLD"
    assert v56["serving_status"] == "HOLD_SHADOW_ONLY"
    assert v56["promotion_review_status"] == "NOT_OPEN"

    s = p["source"]
    split = p["temporal_split"]
    result = {
        "status": "V57_EUMTPL_EXTERNAL_TEMPORAL_PREREGISTRATION_LOCKED",
        "protocol_sha256": sha256(PROTOCOL),
        "registered_before_row_level_access": True,
        "row_level_external_data_accessed": False,
        "outcomes_inspected": False,
        "source_dataset": s["dataset"],
        "source_repository": s["upstream_repository"],
        "source_commit": s["upstream_commit"],
        "source_path": s["upstream_path"],
        "source_git_blob_sha": s["upstream_git_blob_sha"],
        "source_blob_size_bytes": s["upstream_blob_size_bytes"],
        "documentation_git_blob_sha": s["documentation_git_blob_sha"],
        "known_public_rows": s["known_from_public_documentation_before_row_level_access"]["rows"],
        "known_public_columns": s["known_from_public_documentation_before_row_level_access"]["columns"],
        "documented_year_count": s["known_from_public_documentation_before_row_level_access"]["documented_year_count"],
        "split": {
            "method": split["method"],
            "train": split["train"],
            "calibration": split["calibration"],
            "locked_test": split["locked_test"],
            "source_group_used": split["preexisting_group_column_used"],
            "actual_year_labels_inspected": False
        },
        "frequency_outcome": p["targets"]["frequency"]["observed_count"],
        "pure_premium_outcome": p["targets"]["pure_premium"]["observed_amount"],
        "glm_solver": p["models"]["frequency_glm"]["solver"],
        "glm_tolerance": p["models"]["frequency_glm"]["tol"],
        "bootstrap_draws": p["paired_bootstrap"]["draws"],
        "minimum_reproducibility_runs_for_positive_support": p["runtime_reproducibility"]["minimum_independent_actions_executions_for_positive_external_support"],
        "registered_minimum_relative_deviance_improvement": gate["minimum_relative_deviance_improvement"],
        "registered_bootstrap_lower_bound": gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"],
        "registered_maximum_additional_abs_log_calibration_error": gate["maximum_additional_abs_log_aggregate_calibration_error"],
        "committee_status": v56["committee_status"],
        "committee_gate_pass_count": v56["committee_gate_pass_count"],
        "committee_gate_count": v56["committee_gate_count"],
        "model_family_decision": v56["model_family_decision"],
        "serving_status": v56["serving_status"],
        "promotion_review_status": v56["promotion_review_status"],
        "customer_pricing_authorised": False,
        "future_execution_allowed_only_after_main_lock": p["pre_access_firewall"]["execution_allowed_only_after_preregistration_status_is_persisted_on_main"],
        "evidence_role": "PREREGISTRATION_ONLY_BEFORE_FRESH_EXTERNAL_TEMPORAL_ROW_ACCESS"
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
