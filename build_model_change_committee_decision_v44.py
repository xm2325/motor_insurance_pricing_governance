import json
from pathlib import Path

from governance.model_change_committee_v44 import GateInput, evaluate_change_request

ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "governance/model_change_committee_policy_v44.json"
OUT = ROOT / "results_v44"


def read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    src = policy["source_contracts"]
    synthesis = read_json(src["evidence_synthesis"])
    shadow = read_json(src["shadow_manifest"])
    release = read_json(src["release_control"])
    admission = read_json(src["attested_shadow_admission"])

    evidence_by_id = {e["id"]: e for e in synthesis["evidence_basis"]}
    benchmark = evidence_by_id["fremtpl2_cross_sectional_frequency"]
    spanish_freq = evidence_by_id["spanish_2024_frequency"]
    spanish_pp = evidence_by_id["spanish_2024_pure_premium"]

    development_signal = (
        benchmark["relative_deviance_improvement"] >= 0.05
        and benchmark["registered_decision"] == "DEVELOPMENT_BENCHMARK_ONLY"
    )
    locked_temporal_support = (
        spanish_freq["gate_passed"] is True and spanish_pp["gate_passed"] is True
    )
    prereg_external_support = (
        synthesis["portfolio_level_summary"]["external_target_gates_passed"] >= 1
    )
    fresh_independent_evidence = synthesis["portfolio_level_summary"][
        "current_fresh_independent_validation_dataset_available"
    ] is True

    reopen_text = " ".join(synthesis["reopen_requirements"]).lower()
    belgian_reproduction = all(
        e.get("numerically_reproduced_within_registered_tolerance") is True
        for e in synthesis["evidence_basis"]
        if e["id"].startswith("belgian_external_")
    )
    reproducibility_control = (
        "two-independent-actions" in reopen_text and belgian_reproduction
    )

    shadow_boundary = (
        shadow["governance_status"] == "HOLD_SHADOW_ONLY"
        and "Shadow comparison only" in shadow["interpretation_boundary"]
    )
    release_control = (
        release["status"] == "V28_SHADOW_RELEASE_CONTROL_PASS"
        and release["registry"]["unauthorised_rollback_rejected"] is True
        and release["registry"]["review_caused_automatic_serving_change"] is False
        and release["registry"]["pricing_change_during_rollback"] is False
    )
    attested_shadow_admission = (
        admission["status"] == "V30_ATTESTED_RELEASE_ADMISSION_PASS"
        and admission["decision"] == "ADMIT_TO_SHADOW_REGISTRY_ONLY"
        and admission["archive"]["raw_source_data_members"] == 0
        and "does not promote the model family" in admission["admission_boundary"]
    )

    gates = [
        GateInput(
            "G1_DEVELOPMENT_SIGNAL",
            development_signal,
            "freMTPL2 XGBoost frequency relative deviance improvement is {:.4%}; development benchmark only.".format(
                benchmark["relative_deviance_improvement"]
            ),
        ),
        GateInput(
            "G2_LOCKED_TEMPORAL_SUPPORT",
            locked_temporal_support,
            "Spanish 2024 registered decisions remain HOLD for frequency and pure premium; both original locked target gates are not supportive of a global family switch.",
        ),
        GateInput(
            "G3_PREREGISTERED_EXTERNAL_SUPPORT",
            prereg_external_support,
            "Preregistered external target gates passed: {}/{}.".format(
                synthesis["portfolio_level_summary"]["external_target_gates_passed"],
                synthesis["portfolio_level_summary"]["external_target_gates_evaluated"],
            ),
        ),
        GateInput(
            "G4_FRESH_INDEPENDENT_EVIDENCE",
            fresh_independent_evidence,
            "Spanish 2024, Australian ausprivauto0405 and Belgian beMTPL97 are all consumed for fresh candidate selection; no current fresh independent validation dataset is available.",
        ),
        GateInput(
            "G5_REPRODUCIBILITY_CONTROL",
            reproducibility_control,
            "Prospective two-independent-Actions reproducibility rule is registered; Belgian observed point metrics reproduced within registered tolerance.",
        ),
        GateInput(
            "G6_SHADOW_DEPLOYMENT_BOUNDARY",
            shadow_boundary,
            "v0.21 manifest is HOLD_SHADOW_ONLY and explicitly limits scores to shadow comparison rather than customer pricing.",
        ),
        GateInput(
            "G7_RELEASE_AND_ROLLBACK_CONTROL",
            release_control,
            "v0.28 release-control replay rejects unauthorised rollback, performs no automatic serving switch from review, and performs no pricing change.",
        ),
        GateInput(
            "G8_ATTESTED_SHADOW_ADMISSION",
            attested_shadow_admission,
            "v0.30 attested release admission permits shadow-registry entry only, with zero raw-source-data archive members and no model-family promotion authority.",
        ),
    ]

    request_id = policy["candidate_change_request"]["request_id"]
    decision = evaluate_change_request(request_id, gates)
    result = {
        "status": "V44_MODEL_CHANGE_COMMITTEE_GATE_COMPLETE",
        "request": policy["candidate_change_request"],
        "machine_gate_decision": {
            "request_id": decision.request_id,
            "status": decision.status,
            "required_gate_count": decision.required_gate_count,
            "required_gate_pass_count": decision.required_gate_pass_count,
            "required_gate_fail_count": decision.required_gate_count - decision.required_gate_pass_count,
            "blocker_ids": decision.blocker_ids,
            "human_committee_review_open": decision.human_committee_review_open,
            "automatic_model_promotion_authorised": decision.automatic_model_promotion_authorised,
            "automatic_customer_pricing_change_authorised": decision.automatic_customer_pricing_change_authorised,
            "human_signoff_recorded": decision.human_signoff_recorded,
            "human_signoff_can_override_failed_evidence_gate": decision.human_signoff_can_override_failed_evidence_gate,
        },
        "gate_results": decision.gate_results,
        "operational_readiness": {
            "shadow_deployment_boundary": shadow_boundary,
            "release_and_rollback_control": release_control,
            "attested_shadow_admission": attested_shadow_admission,
            "note": "Operational controls are demonstrated in project shadow workflows, but they cannot compensate for failed validation-evidence gates.",
        },
        "evidence_readiness": {
            "development_signal_present": development_signal,
            "locked_temporal_support": locked_temporal_support,
            "preregistered_external_support": prereg_external_support,
            "fresh_independent_evidence_available": fresh_independent_evidence,
            "registered_reproducibility_control_present": reproducibility_control,
        },
        "reopen_requirements": synthesis["reopen_requirements"],
        "governance_boundary": {
            "project_demo_not_insurer_policy": True,
            "first_central_or_current_uk_transport_claimed": False,
            "human_committee_decision_recorded": False,
            "customer_pricing_authority_present": False,
        },
    }

    assert result["machine_gate_decision"]["status"] == "EVIDENCE_GAP_HOLD"
    assert result["machine_gate_decision"]["required_gate_pass_count"] == 5
    assert result["machine_gate_decision"]["blocker_ids"] == [
        "G2_LOCKED_TEMPORAL_SUPPORT",
        "G3_PREREGISTERED_EXTERNAL_SUPPORT",
        "G4_FRESH_INDEPENDENT_EVIDENCE",
    ]
    assert result["machine_gate_decision"]["human_committee_review_open"] is False
    assert result["machine_gate_decision"]["automatic_model_promotion_authorised"] is False
    assert result["machine_gate_decision"]["automatic_customer_pricing_change_authorised"] is False

    OUT.mkdir(exist_ok=True)
    (OUT / "model_change_committee_decision_v44.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    gate_lines = []
    for row in decision.gate_results:
        gate_lines.append(
            f"| {row['gate_id']} | {row['status']} | {row['evidence']} |"
        )
    md = """# v0.44 Model Change Committee Gate\n\n## Current machine decision\n\n**EVIDENCE_GAP_HOLD — do not advance the XGBoost model-family request to human approval review.**\n\nThis result is intentionally stricter than deployment readiness. The project can package, attest, shadow-score and roll back models, but those operational controls do not replace validation evidence.\n\n## Gate matrix\n\n| Gate | Status | Evidence |\n|---|---|---|\n""" + "\n".join(gate_lines) + """\n\n## Blocking evidence gaps\n\n- `G2_LOCKED_TEMPORAL_SUPPORT`: the original Spanish locked OOT did not support a global model-family switch.\n- `G3_PREREGISTERED_EXTERNAL_SUPPORT`: Australia + Belgium provide four preregistered external target gates and **0 passes**.\n- `G4_FRESH_INDEPENDENT_EVIDENCE`: all three validation datasets currently used for model-family decisions are consumed; none can be relabelled fresh by rerunning or retuning.\n\n## Controls already demonstrated\n\n- Development signal exists in the cross-sectional freMTPL2 frequency benchmark.\n- Prospective numerical-reproducibility policy exists; Belgian negative decisions reproduced within registered tolerance.\n- Shadow deployment, manual rollback control and attested shadow admission are demonstrated.\n\n## Fail-closed approval boundary\n\nEven a recorded human sign-off flag cannot override a failed evidence gate in this project contract. If every required machine gate passed, the only possible result would be `READY_FOR_HUMAN_COMMITTEE_REVIEW` — never automatic model promotion or customer pricing.\n\nThis is a project governance demonstration, not FIRST CENTRAL policy and not evidence of current UK-market transport.\n"""
    (OUT / "MODEL_CHANGE_COMMITTEE_PACK_V44.md").write_text(md, encoding="utf-8")
    print(json.dumps(result["machine_gate_decision"], indent=2))


if __name__ == "__main__":
    main()
