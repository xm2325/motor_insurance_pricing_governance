from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTDIR = ROOT / "results_v49"

SOURCES = {
    "committee": ROOT / "action_results/v44/model_change_committee_decision_v44.json",
    "inventory": ROOT / "action_results/v46/model_risk_inventory_v46.json",
    "disagreement": ROOT / "action_results/v47/disagreement_attribution_summary_v47.json",
    "relativity": ROOT / "action_results/v48/portfolio_neutral_relativity_summary_v48.json",
    "repeat_audit": ROOT / "action_results/v48/v48_repeat_run_audit.json",
    "segments": ROOT / "action_results/v48/segment_relativity_migration_v48.csv",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def segment_lookup(path: Path) -> dict[tuple[str, str], dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {(r["dimension"], r["group"]): r for r in rows}


def pct(value: float, digits: int = 2) -> str:
    return f"{100.0 * value:.{digits}f}%"


def build_assessment() -> dict:
    committee = load_json(SOURCES["committee"])
    inventory = load_json(SOURCES["inventory"])
    disagreement = load_json(SOURCES["disagreement"])
    relativity = load_json(SOURCES["relativity"])
    repeat = load_json(SOURCES["repeat_audit"])
    segments = segment_lookup(SOURCES["segments"])

    gate = committee["machine_gate_decision"]
    current = inventory["current_decision"]
    if gate["status"] != "EVIDENCE_GAP_HOLD":
        raise RuntimeError("v0.49 expects the current committee gate to remain EVIDENCE_GAP_HOLD")
    if gate["required_gate_pass_count"] != 5 or gate["required_gate_count"] != 8:
        raise RuntimeError("v0.49 decision-critical committee gate count changed")
    if gate["blocker_ids"] != [
        "G2_LOCKED_TEMPORAL_SUPPORT",
        "G3_PREREGISTERED_EXTERNAL_SUPPORT",
        "G4_FRESH_INDEPENDENT_EVIDENCE",
    ]:
        raise RuntimeError("v0.49 decision-critical blocker set changed")
    if inventory["evidence_summary"]["preregistered_external_target_gates_passed"] != 0:
        raise RuntimeError("v0.49 external-support state changed")
    if inventory["evidence_summary"]["preregistered_external_target_gates_evaluated"] != 4:
        raise RuntimeError("v0.49 external gate denominator changed")
    if inventory["evidence_summary"]["current_fresh_independent_validation_dataset_available"]:
        raise RuntimeError("v0.49 fresh-validation state changed")
    if current["model_family_decision"] != "HOLD":
        raise RuntimeError("v0.49 cannot synthesise a non-HOLD decision from this evidence snapshot")
    if current["pricing_change_authorised"]:
        raise RuntimeError("Pricing authority must remain false")
    if disagreement["promotion_evidence_created"] or relativity["promotion_evidence_created"]:
        raise RuntimeError("Post-hoc diagnostics must not become promotion evidence")

    freq = relativity["targets"]["frequency"]["relativity_change_distribution"]
    pp = relativity["targets"]["pure_premium"]["relativity_change_distribution"]
    f_top = disagreement["top_features_by_disagreement_reduction"]["frequency"][:3]
    p_top = disagreement["top_features_by_disagreement_reduction"]["pure_premium"][:3]
    if [x["feature"] for x in f_top] != ["vehicle_brand", "policy_type", "vehicle_value"]:
        raise RuntimeError("v0.49 frequency disagreement headline changed")
    if [x["feature"] for x in p_top] != ["business_type", "power_to_weight_ratio", "vehicle_value"]:
        raise RuntimeError("v0.49 pure-premium disagreement headline changed")

    selected_segments = []
    for dimension, group in [
        ("business_type", "NB"),
        ("business_type", "P"),
        ("policy_type", "COMP_E"),
        ("policy_type", "CC"),
        ("driver_age_band", "35-49"),
        ("driver_age_band", "50-64"),
    ]:
        row = segments[(dimension, group)]
        selected_segments.append({
            "dimension": dimension,
            "group": group,
            "exposure_share": float(row["exposure_share"]),
            "frequency_total_relativity_change": float(row["frequency_segment_total_relativity_change"]),
            "pure_premium_total_relativity_change": float(row["pure_premium_segment_total_relativity_change"]),
        })

    return {
        "status": "V49_MODEL_CHANGE_IMPACT_ASSESSMENT_COMPLETE",
        "scope": "aggregate_committee_ready_synthesis_of_persisted_evidence",
        "row_level_data_accessed": False,
        "model_fit_executed": False,
        "historical_decisions_changed": False,
        "new_performance_gate_created": False,
        "new_promotion_threshold_created": False,
        "customer_pricing_authorised": False,
        "source_lineage": {
            key: {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for key, path in SOURCES.items()
        },
        "decision_sequence": [
            {
                "stage": 1,
                "name": "EVIDENCE_ADEQUACY",
                "current_status": gate["status"],
                "must_pass_before_next_stage_can_authorise_promotion": True,
            },
            {
                "stage": 2,
                "name": "MODEL_IMPACT_REVIEW",
                "current_status": "DIAGNOSTIC_EVIDENCE_AVAILABLE_BUT_NOT_PROMOTION_AUTHORITY",
                "must_pass_before_next_stage_can_authorise_pricing": True,
            },
            {
                "stage": 3,
                "name": "COMMERCIAL_AND_CUSTOMER_PRICING_GOVERNANCE",
                "current_status": "OUT_OF_SCOPE_NOT_AUTHORISED",
                "must_be_separately_authorised": True,
            },
        ],
        "evidence_adequacy": {
            "committee_request_id": gate["request_id"],
            "status": gate["status"],
            "required_gate_pass_count": gate["required_gate_pass_count"],
            "required_gate_count": gate["required_gate_count"],
            "blocker_ids": gate["blocker_ids"],
            "human_committee_review_open": gate["human_committee_review_open"],
            "human_signoff_can_override_failed_evidence_gate": gate["human_signoff_can_override_failed_evidence_gate"],
            "external_target_gates_passed": inventory["evidence_summary"]["preregistered_external_target_gates_passed"],
            "external_target_gates_evaluated": inventory["evidence_summary"]["preregistered_external_target_gates_evaluated"],
            "fresh_independent_validation_available": inventory["evidence_summary"]["current_fresh_independent_validation_dataset_available"],
        },
        "operational_readiness": inventory["operational_controls"],
        "impact_diagnostics": {
            "disagreement_analysis_role": disagreement["analysis_role"],
            "relativity_analysis_role": relativity["analysis_role"],
            "frequency": {
                "baseline_mean_absolute_log_disagreement": disagreement["targets"]["frequency"]["baseline"]["exposure_weighted_mean_absolute_log_disagreement"],
                "top_disagreement_sensitivities": f_top,
                "mean_absolute_portfolio_neutral_relativity_change": freq["exposure_weighted_mean_absolute_change"],
                "exposure_share_abs_change_gt_10pct": freq["absolute_change_gt_10pct_exposure_share"],
                "exposure_share_abs_change_gt_20pct": freq["absolute_change_gt_20pct_exposure_share"],
            },
            "pure_premium": {
                "baseline_mean_absolute_log_disagreement": disagreement["targets"]["pure_premium"]["baseline"]["exposure_weighted_mean_absolute_log_disagreement"],
                "top_disagreement_sensitivities": p_top,
                "mean_absolute_portfolio_neutral_relativity_change": pp["exposure_weighted_mean_absolute_change"],
                "exposure_share_abs_change_gt_10pct": pp["absolute_change_gt_10pct_exposure_share"],
                "exposure_share_abs_change_gt_20pct": pp["absolute_change_gt_20pct_exposure_share"],
            },
            "selected_major_segments": selected_segments,
            "impact_interpretation": "The diagnostics quantify differences between frozen technical-risk score families after aggregate neutralisation. They are not observed premium changes, performance gates, fairness conclusions or commercial outcomes.",
        },
        "numerical_limitations": {
            "frozen_tweedie_glm_max_iter_warning_retained": repeat["interpretation"]["tweedie_glm_max_iter_warning_retained"],
            "repeat_run_conclusion": repeat["interpretation"]["conclusion"],
            "pure_premium_reference_total_relative_range": repeat["derived_envelope"]["pure_premium_reference_total_relative_range"],
            "pure_premium_abs_change_gt_10pct_exposure_share_range": repeat["derived_envelope"]["pure_premium_abs_change_gt_10pct_exposure_share_range"],
            "pure_premium_abs_change_gt_20pct_exposure_share_range": repeat["derived_envelope"]["pure_premium_abs_change_gt_20pct_exposure_share_range"],
            "headline_major_segment_max_absolute_shift_range": repeat["derived_envelope"]["headline_major_segment_max_absolute_shift_range"],
            "bitwise_reproducibility_claimed": repeat["interpretation"]["bitwise_reproducibility_claimed"],
        },
        "current_disposition": {
            "model_family_decision": current["model_family_decision"],
            "serving_status": current["serving_status"],
            "promotion_review_status": current["promotion_review_status"],
            "model_promotion_authorised": current["model_promotion_authorised"],
            "pricing_change_authorised": current["pricing_change_authorised"],
            "impact_pack_disposition": "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
        },
        "future_review_order": [
            "Resolve G2/G3/G4 using genuinely new prospectively governed evidence; v0.47/v0.48 cannot clear these blockers.",
            "If evidence adequacy is later achieved, explicitly review model-family disagreement drivers and portfolio-neutral redistribution before any serving change.",
            "Evaluate pricing/commercial components separately; technical-risk relativity is not a customer premium.",
            "Require separate authorised governance for any serving-bundle or customer-pricing action.",
        ],
        "interpretation_boundaries": {
            "benchmark_is_not_pricing_uplift": True,
            "consumed_validation_is_not_fresh_evidence": True,
            "impact_diagnostics_do_not_clear_evidence_blockers": True,
            "operational_readiness_does_not_clear_evidence_blockers": True,
            "technical_relativity_is_not_customer_premium": True,
            "project_demo_not_insurer_policy": True,
            "first_central_or_current_uk_transport_claimed": False,
            "commercial_uplift_claimed": False,
        },
    }


def render_markdown(a: dict) -> str:
    ev = a["evidence_adequacy"]
    f = a["impact_diagnostics"]["frequency"]
    p = a["impact_diagnostics"]["pure_premium"]
    lines = [
        "# Model Change Impact Assessment",
        "",
        "**Current disposition: `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`.**",
        "",
        "This pack is generated from persisted aggregate evidence. It does not access policy rows, refit a model, create a new performance gate, or authorise customer pricing.",
        "",
        "## 1. Evidence adequacy comes first",
        "",
        f"The machine committee gate remains **`{ev['status']}`** with **{ev['required_gate_pass_count']}/{ev['required_gate_count']}** required gates passing. The unresolved blockers are `{', '.join(ev['blocker_ids'])}`. Preregistered external support is **{ev['external_target_gates_passed']}/{ev['external_target_gates_evaluated']}**, and no fresh independent validation asset is currently available.",
        "",
        "Operational shadow controls are demonstrated, but they cannot compensate for failed validation-evidence gates. Human sign-off is not recorded and cannot override failed evidence gates in this project contract.",
        "",
        "## 2. Impact evidence is diagnostic, not promotion authority",
        "",
        f"For frequency, frozen GLM/XGBoost disagreement has exposure-weighted mean absolute log-ratio **{f['baseline_mean_absolute_log_disagreement']:.4f}**. After portfolio-neutral alignment, mean absolute technical-relativity redistribution is **{pct(f['mean_absolute_portfolio_neutral_relativity_change'])}**; **{pct(f['exposure_share_abs_change_gt_10pct'])}** of exposure moves by more than ±10% and **{pct(f['exposure_share_abs_change_gt_20pct'])}** by more than ±20%.",
        "",
        f"For pure premium, mean absolute log-ratio disagreement is **{p['baseline_mean_absolute_log_disagreement']:.4f}**. After portfolio-neutral alignment, mean absolute redistribution is **{pct(p['mean_absolute_portfolio_neutral_relativity_change'])}**; **{pct(p['exposure_share_abs_change_gt_10pct'])}** of exposure moves by more than ±10% and **{pct(p['exposure_share_abs_change_gt_20pct'])}** by more than ±20%.",
        "",
        "Largest one-factor disagreement sensitivities are descriptive only: frequency is led by `vehicle_brand`, `policy_type`, `vehicle_value`; pure premium by `business_type`, `power_to_weight_ratio`, `vehicle_value`. These are non-additive, non-causal sensitivities, not SHAP values or predictive feature importance.",
        "",
        "### Major segment redistribution",
        "",
        "| Dimension | Group | Exposure share | Frequency relativity shift | Pure-premium relativity shift |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in a["impact_diagnostics"]["selected_major_segments"]:
        lines.append(
            f"| {row['dimension']} | {row['group']} | {pct(row['exposure_share'])} | {pct(row['frequency_total_relativity_change'])} | {pct(row['pure_premium_total_relativity_change'])} |"
        )
    lines += [
        "",
        "These are technical-risk score redistributions, not segment accuracy, fairness, causality or realised customer-price effects.",
        "",
        "## 3. Numerical limitation is retained",
        "",
        "The frozen Tweedie GLM still reaches its registered `max_iter=900` limit. Same-head repeat runs show the descriptive pure-premium redistribution headline is stable at the reporting precision used here, but bitwise reproducibility is not claimed.",
        "",
        "## 4. Required review order",
        "",
    ]
    for i, item in enumerate(a["future_review_order"], 1):
        lines.append(f"{i}. {item}")
    lines += [
        "",
        "## Decision boundary",
        "",
        "The current decision remains **`HOLD / HOLD_SHADOW_ONLY / EVIDENCE_GAP_HOLD`**. This pack does not reopen model-family promotion, authorise a serving change, estimate a customer premium, claim commercial uplift, or establish transfer to FIRST CENTRAL / the current UK motor market.",
        "",
        "Source hashes are recorded in `results_v49/model_change_impact_assessment_v49.json` for lineage. CI separately pins the decision-critical status, gate counts, blocker set and impact headlines used by this pack.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTDIR.mkdir(exist_ok=True)
    assessment = build_assessment()
    (OUTDIR / "model_change_impact_assessment_v49.json").write_text(
        json.dumps(assessment, indent=2), encoding="utf-8"
    )
    (ROOT / "MODEL_CHANGE_IMPACT_ASSESSMENT.md").write_text(
        render_markdown(assessment), encoding="utf-8"
    )
    print(json.dumps({
        "status": assessment["status"],
        "disposition": assessment["current_disposition"]["impact_pack_disposition"],
        "committee": assessment["evidence_adequacy"],
        "frequency_gt10": assessment["impact_diagnostics"]["frequency"]["exposure_share_abs_change_gt_10pct"],
        "pure_premium_gt10": assessment["impact_diagnostics"]["pure_premium"]["exposure_share_abs_change_gt_10pct"],
    }, indent=2))


if __name__ == "__main__":
    main()
