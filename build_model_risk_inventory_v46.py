import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_v46"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    synthesis = load("action_results/v43/model_family_evidence_synthesis_summary.json")
    committee = load("action_results/v44/model_change_committee_decision_v44.json")
    spanish = load("action_results/v35/validation_firewall_summary.json")
    australia = load("governance/external_validation_use_ledger_v39.json")
    belgium = load("governance/external_validation_use_ledger_v42.json")
    manifest = load("action_results/v21/manifest.json")
    release = load("action_results/v28/release_control_result.json")
    admission = load("action_results/v30/release_admission_result.json")

    external_summary = synthesis["portfolio_level_summary"]
    machine = committee["machine_gate_decision"]

    model_inventory = []
    for model_id, spec in manifest["models"].items():
        model_inventory.append({
            "model_id": model_id,
            "target": spec["target"],
            "role": spec["role"],
            "artifact": spec["artifact"],
            "artifact_sha256": spec["sha256"],
            "serving_boundary": "SHADOW_COMPARISON_ONLY",
            "customer_pricing_authorised": False,
        })

    au = australia["datasets"]["ausprivauto0405"]
    result = {
        "status": "V46_MODEL_RISK_INVENTORY_COMPLETE",
        "inventory_version": "0.46",
        "scope": "aggregate_model_risk_inventory_from_persisted_evidence",
        "row_level_data_accessed": False,
        "model_fit_executed": False,
        "historical_decisions_changed": False,
        "risk_question": "Whether the XGBoost challenger family has enough stable temporal and external evidence to advance beyond shadow-only comparison against GLM references.",
        "models": model_inventory,
        "validation_assets": [
            {
                "dataset": "Spanish 2024",
                "initial_role": spanish["2024"]["initial_role"],
                "current_role": spanish["2024"]["current_role"],
                "fresh_independent_evidence_available": spanish["2024"]["independent_holdout_available"],
                "candidate_selection_allowed": spanish["2024"]["candidate_selection_allowed"],
            },
            {
                "dataset": "Australian ausprivauto0405",
                "initial_role": au["initial_role"],
                "current_role": au["current_role"],
                "fresh_independent_evidence_available": au["independent_external_validation_available"],
                "candidate_selection_allowed": au["candidate_selection_allowed"],
            },
            {
                "dataset": "Belgian beMTPL97",
                "initial_role": belgium["initial_role"],
                "current_role": belgium["current_role"],
                "fresh_independent_evidence_available": belgium["independent_external_validation_available"],
                "candidate_selection_allowed": belgium["candidate_selection_allowed"],
            },
        ],
        "evidence_summary": {
            "development_benchmark_signal_present": True,
            "external_portfolios_evaluated": external_summary["external_portfolios_evaluated"],
            "preregistered_external_target_gates_evaluated": external_summary["external_target_gates_evaluated"],
            "preregistered_external_target_gates_passed": external_summary["external_target_gates_passed"],
            "current_fresh_independent_validation_dataset_available": external_summary["current_fresh_independent_validation_dataset_available"],
            "pooled_meta_analysis_used": False,
            "subjective_evidence_weighting_used": False,
        },
        "operational_controls": {
            "shadow_serving_boundary": manifest["governance_status"] == "HOLD_SHADOW_ONLY",
            "manual_rollback_control": release["registry"]["unauthorised_rollback_rejected"] and release["registry"]["operator_authorised_rollback"],
            "automatic_review_serving_switch": release["registry"]["review_caused_automatic_serving_change"],
            "attested_shadow_admission": admission["decision"] == "ADMIT_TO_SHADOW_REGISTRY_ONLY",
            "raw_source_data_members_in_release_archive": admission["archive"]["raw_source_data_members"],
        },
        "committee_readiness": {
            "request_id": machine["request_id"],
            "status": machine["status"],
            "required_gate_count": machine["required_gate_count"],
            "required_gate_pass_count": machine["required_gate_pass_count"],
            "required_gate_fail_count": machine["required_gate_fail_count"],
            "blocker_ids": machine["blocker_ids"],
            "human_committee_review_open": machine["human_committee_review_open"],
            "human_signoff_can_override_failed_evidence_gate": machine["human_signoff_can_override_failed_evidence_gate"],
        },
        "current_decision": {
            "model_family_decision": synthesis["decision"]["model_family_decision"],
            "serving_status": synthesis["decision"]["serving_status"],
            "promotion_review_status": synthesis["decision"]["promotion_review_status"],
            "model_promotion_authorised": synthesis["decision"]["model_promotion_authorised"],
            "pricing_change_authorised": synthesis["decision"]["pricing_change_authorised"],
        },
        "interpretation_boundaries": {
            "benchmark_is_not_pricing_uplift": True,
            "consumed_validation_not_relabelled_fresh": True,
            "operational_readiness_not_model_approval": True,
            "first_central_or_current_uk_transport_claimed": False,
            "insurer_or_regulatory_policy_claimed": False,
        },
    }

    assert result["evidence_summary"]["preregistered_external_target_gates_passed"] == 0
    assert result["evidence_summary"]["preregistered_external_target_gates_evaluated"] == 4
    assert result["committee_readiness"]["status"] == "EVIDENCE_GAP_HOLD"
    assert result["committee_readiness"]["required_gate_pass_count"] == 5
    assert result["committee_readiness"]["required_gate_count"] == 8
    assert all(not x["fresh_independent_evidence_available"] for x in result["validation_assets"])
    assert all(not x["candidate_selection_allowed"] for x in result["validation_assets"])
    assert result["operational_controls"]["automatic_review_serving_switch"] is False
    assert result["operational_controls"]["raw_source_data_members_in_release_archive"] == 0

    OUT.mkdir(exist_ok=True)
    path = OUT / "model_risk_inventory_v46.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
