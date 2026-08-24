from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTDIR = ROOT / "results_v53"
PACK = ROOT / "RATING_FACTOR_REVIEW_PACK.md"

SOURCES = {
    "v51_summary": ROOT / "action_results/v51/rating_factor_relativity_summary_v51.json",
    "v51_numeric": ROOT / "action_results/v51/numeric_rating_factor_relativities_v51.csv",
    "v51_categorical": ROOT / "action_results/v51/categorical_rating_factor_relativities_v51.csv",
    "v52_summary": ROOT / "action_results/v52/rating_factor_support_summary_v52.json",
    "v52_numeric": ROOT / "action_results/v52/numeric_feature_support_v52.csv",
    "v52_categorical": ROOT / "action_results/v52/categorical_feature_support_v52.csv",
    "v52_levels": ROOT / "action_results/v52/categorical_level_shift_v52.csv",
    "v49_impact": ROOT / "action_results/v49/model_change_impact_assessment_v49.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def pct(value: float, digits: int = 2) -> str:
    return f"{100.0 * value:.{digits}f}%"


def find_row(rows: list[dict[str, str]], **matches: str) -> dict[str, str]:
    found = [row for row in rows if all(str(row[key]) == str(value) for key, value in matches.items())]
    if len(found) != 1:
        raise RuntimeError(f"Expected exactly one row for {matches}, found {len(found)}")
    return found[0]


def numeric_point(rows: list[dict[str, str]], feature: str, value: float) -> dict:
    candidates = [row for row in rows if row["feature"] == feature and abs(float(row["value"]) - value) < 1e-9]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one {feature} point at {value}, found {len(candidates)}")
    row = candidates[0]
    return {
        "value": float(row["value"]),
        "glm_relativity": float(row["glm_frequency_relativity"]),
        "xgb_relativity": float(row["xgb_frequency_relativity"]),
        "xgb_over_glm": float(row["xgb_over_glm_relativity"]),
    }


def build_pack() -> dict:
    v51 = load_json(SOURCES["v51_summary"])
    v52 = load_json(SOURCES["v52_summary"])
    v49 = load_json(SOURCES["v49_impact"])
    v51_numeric = load_csv(SOURCES["v51_numeric"])
    v51_cat = load_csv(SOURCES["v51_categorical"])
    v52_numeric = {row["feature"]: row for row in load_csv(SOURCES["v52_numeric"])}
    v52_cat = {row["feature"]: row for row in load_csv(SOURCES["v52_categorical"])}
    v52_levels = load_csv(SOURCES["v52_levels"])

    # Fail closed on decision-critical roles and boundaries, not on invented post-hoc approval thresholds.
    if v51["status"] != "V51_DEVELOPMENT_RATING_FACTOR_RELATIVITY_AUDIT_COMPLETE":
        raise RuntimeError("Unexpected v0.51 evidence role")
    if v51["source"]["years_read"] != [2022] or v51["interpretation_boundary"]["validation_performance_evidence_created"]:
        raise RuntimeError("v0.51 must remain development interpretability only")
    if v52["status"] != "V52_LABEL_FREE_RATING_FACTOR_SUPPORT_AUDIT_COMPLETE":
        raise RuntimeError("Unexpected v0.52 evidence role")
    if v52["source"]["years_read"] != [2022, 2024] or v52["source"]["claim_outcomes_read"]:
        raise RuntimeError("v0.52 must remain label-free feature support evidence")
    if v52["interpretation_boundary"]["model_fit_executed"]:
        raise RuntimeError("v0.52 must not fit a model")
    evidence = v49["evidence_adequacy"]
    current = v49["current_disposition"]
    if evidence["status"] != "EVIDENCE_GAP_HOLD" or evidence["required_gate_pass_count"] != 5 or evidence["required_gate_count"] != 8:
        raise RuntimeError("Committee evidence state changed; review v0.53 pack assumptions")
    if evidence["external_target_gates_passed"] != 0 or evidence["external_target_gates_evaluated"] != 4:
        raise RuntimeError("External evidence state changed; review v0.53 pack assumptions")
    if current["model_family_decision"] != "HOLD" or current["promotion_review_status"] != "NOT_OPEN" or current["pricing_change_authorised"]:
        raise RuntimeError("v0.53 cannot synthesise a promoted/pricing-authorised state")

    driver_age = {
        "shape_gap": float(v51["numeric_grid"]["features"]["driver_age"]["max_absolute_log_relativity_gap"]),
        "points": [numeric_point(v51_numeric, "driver_age", 30.0), numeric_point(v51_numeric, "driver_age", 47.0), numeric_point(v51_numeric, "driver_age", 68.0)],
        "strict_extrapolation_share": float(v52_numeric["driver_age"]["current_outside_development_observed_range_exposure_share"]),
        "q05_q95_tail_share": float(v52_numeric["driver_age"]["current_outside_development_q05_q95_exposure_share"]),
        "development_median": float(v52_numeric["driver_age"]["development_q50"]),
        "current_median": float(v52_numeric["driver_age"]["current_q50"]),
    }
    vehicle_age = {
        "shape_gap": float(v51["numeric_grid"]["features"]["vehicle_age"]["max_absolute_log_relativity_gap"]),
        "points": [numeric_point(v51_numeric, "vehicle_age", 7.0), numeric_point(v51_numeric, "vehicle_age", 23.0), numeric_point(v51_numeric, "vehicle_age", 44.0)],
        "strict_extrapolation_share": float(v52_numeric["vehicle_age"]["current_outside_development_observed_range_exposure_share"]),
        "q05_q95_tail_share": float(v52_numeric["vehicle_age"]["current_outside_development_q05_q95_exposure_share"]),
        "development_median": float(v52_numeric["vehicle_age"]["development_q50"]),
        "current_median": float(v52_numeric["vehicle_age"]["current_q50"]),
    }
    vehicle_value = {
        "shape_gap": float(v51["numeric_grid"]["features"]["vehicle_value"]["max_absolute_log_relativity_gap"]),
        "strict_extrapolation_share": float(v52_numeric["vehicle_value"]["current_outside_development_observed_range_exposure_share"]),
        "q05_q95_tail_share": float(v52_numeric["vehicle_value"]["current_outside_development_q05_q95_exposure_share"]),
    }

    bt = v52["categorical_features"]["business_type"]
    nb = find_row(v52_levels, feature="business_type", level="NB")
    p = find_row(v52_levels, feature="business_type", level="P")
    business_type = {
        "frequency_shape_gap": float(v51["categorical_grid"]["features"]["business_type"]["max_absolute_log_relativity_gap"]),
        "total_variation": float(bt["total_variation_distance_2022_vs_2024"]),
        "unseen_exposure_share": float(bt["current_unseen_nonmissing_exposure_share"]),
        "nb_development_share": float(nb["development_share"]),
        "nb_current_share": float(nb["current_share"]),
        "p_development_share": float(p["development_share"]),
        "p_current_share": float(p["current_share"]),
    }

    bmw = find_row(v51_cat, feature="vehicle_brand", level="BMW")
    brand = v52["categorical_features"]["vehicle_brand"]
    vehicle_brand = {
        "bmw_development_exposure_share_v51": float(bmw["development_exposure_share"]),
        "bmw_glm_relativity": float(bmw["glm_frequency_relativity"]),
        "bmw_xgb_relativity": float(bmw["xgb_frequency_relativity"]),
        "unseen_2024_level_count": int(brand["current_unseen_nonmissing_level_count"]),
        "unseen_2024_exposure_share": float(brand["current_unseen_nonmissing_exposure_share"]),
        "mix_total_variation": float(brand["total_variation_distance_2022_vs_2024"]),
    }

    impact = v49["impact_diagnostics"]
    business_segments = {
        row["group"]: row
        for row in impact["selected_major_segments"]
        if row["dimension"] == "business_type"
    }

    return {
        "status": "V53_RATING_FACTOR_REVIEW_PACK_COMPLETE",
        "scope": "aggregate_rating_structure_support_mix_and_impact_synthesis",
        "row_level_data_accessed": False,
        "model_fit_executed": False,
        "historical_decisions_changed": False,
        "new_performance_gate_created": False,
        "new_support_threshold_created": False,
        "composite_risk_score_created": False,
        "customer_pricing_authorised": False,
        "source_lineage": {
            key: {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for key, path in SOURCES.items()
        },
        "review_sequence": [
            "RATING_STRUCTURE__WHAT_SHAPE_DID_EACH_MODEL_LEARN",
            "FEATURE_SUPPORT__IS_CURRENT_BOOK_OUTSIDE_DEVELOPMENT_SUPPORT",
            "PORTFOLIO_MIX__HAVE_KNOWN_RATING_CELLS_REWEIGHTED",
            "PORTFOLIO_IMPACT__HOW_DIFFERENTLY_DO_FROZEN_MODEL_FAMILIES_REDISTRIBUTE_TECHNICAL_RISK",
            "EVIDENCE_ADEQUACY__DO_VALIDATION_GATES_ALLOW_PROMOTION_REVIEW",
            "PRICING_GOVERNANCE__SEPARATE_AUTHORISATION_REQUIRED",
        ],
        "rating_structure_and_support": {
            "driver_age": driver_age,
            "vehicle_age": vehicle_age,
            "vehicle_value_counterexample": vehicle_value,
            "business_type": business_type,
            "vehicle_brand": vehicle_brand,
        },
        "portfolio_neutral_impact": {
            "frequency_mean_absolute_relativity_change": impact["frequency"]["mean_absolute_portfolio_neutral_relativity_change"],
            "frequency_exposure_share_abs_change_gt_10pct": impact["frequency"]["exposure_share_abs_change_gt_10pct"],
            "frequency_exposure_share_abs_change_gt_20pct": impact["frequency"]["exposure_share_abs_change_gt_20pct"],
            "pure_premium_mean_absolute_relativity_change": impact["pure_premium"]["mean_absolute_portfolio_neutral_relativity_change"],
            "pure_premium_exposure_share_abs_change_gt_10pct": impact["pure_premium"]["exposure_share_abs_change_gt_10pct"],
            "pure_premium_exposure_share_abs_change_gt_20pct": impact["pure_premium"]["exposure_share_abs_change_gt_20pct"],
            "business_type_nb_pure_premium_total_relativity_change": business_segments["NB"]["pure_premium_total_relativity_change"],
            "business_type_p_pure_premium_total_relativity_change": business_segments["P"]["pure_premium_total_relativity_change"],
            "technical_risk_not_customer_premium": True,
        },
        "evidence_adequacy": {
            "status": evidence["status"],
            "gate_pass_count": evidence["required_gate_pass_count"],
            "gate_count": evidence["required_gate_count"],
            "blocker_ids": evidence["blocker_ids"],
            "external_target_gates": f"{evidence['external_target_gates_passed']}/{evidence['external_target_gates_evaluated']}",
            "fresh_independent_validation_available": evidence["fresh_independent_validation_available"],
        },
        "current_disposition": current,
        "interpretation_boundaries": {
            "v51_is_development_interpretability_not_validation": True,
            "v52_is_label_free_support_mix_not_performance": True,
            "strict_support_and_tail_shift_are_distinct": True,
            "shape_gap_and_mix_shift_are_not_combined_into_score": True,
            "portfolio_neutral_impact_is_not_customer_price": True,
            "impact_and_monitoring_do_not_clear_validation_blockers": True,
            "first_central_or_current_uk_transport_claimed": False,
            "fairness_or_causal_conclusion_claimed": False,
            "commercial_uplift_claimed": False,
        },
    }


def render_markdown(a: dict) -> str:
    rs = a["rating_structure_and_support"]
    da = rs["driver_age"]
    va = rs["vehicle_age"]
    bt = rs["business_type"]
    brand = rs["vehicle_brand"]
    impact = a["portfolio_neutral_impact"]
    ev = a["evidence_adequacy"]

    lines = [
        "# Rating Factor Review Pack",
        "",
        "This pack joins persisted aggregate evidence from v0.51 (development rating structure), v0.52 (label-free feature support/mix), v0.48/v0.49 (portfolio-neutral impact and committee context). It does not access policy rows, refit a model, create a new performance/support gate, or authorise customer pricing.",
        "",
        "## Executive review answer",
        "",
        "The current 2024 book is **not broadly outside the numeric support seen in 2022**. Strict out-of-range exposure is near zero for the main numeric factors. The larger monitoring issue is **portfolio reweighting among known rating cells**, especially business type. Separately, the frozen GLM and XGBoost can encode materially different response shapes for supported factors such as driver age and vehicle age, and v0.48 shows that those model-family differences can materially redistribute technical risk even after aggregate predicted totals are forced equal.",
        "",
        "None of that repairs the validation evidence gap: the committee state remains **`EVIDENCE_GAP_HOLD` (5/8)** with external support **0/4**, so model-family promotion review remains closed.",
        "",
        "## 1. Rating structure: what shape did each frequency model learn?",
        "",
        "### Driver age",
        "",
        f"v0.51 max absolute log-relativity gap: **{da['shape_gap']:.5f}**. Development median age is {da['development_median']:.0f}; the 2024 feature-population median is {da['current_median']:.0f}.",
        "",
        "| Driver age | GLM relativity | XGB relativity | XGB / GLM |",
        "|---:|---:|---:|---:|",
    ]
    for point in da["points"]:
        lines.append(f"| {point['value']:.0f} | {point['glm_relativity']:.3f} | {point['xgb_relativity']:.3f} | {point['xgb_over_glm']:.3f} |")
    lines += [
        "",
        f"Only **{pct(da['strict_extrapolation_share'], 4)}** of 2024 exposure is outside the actual observed 2022 driver-age range; **{pct(da['q05_q95_tail_share'])}** lies outside the 2022 q05–q95 interval. The structural disagreement is therefore mainly **within supported ages**, not broad extrapolation.",
        "",
        "### Vehicle age",
        "",
        f"v0.51 max absolute log-relativity gap: **{va['shape_gap']:.5f}**. Development median is {va['development_median']:.0f}; 2024 median is {va['current_median']:.0f}.",
        "",
        "| Vehicle age | GLM relativity | XGB relativity | XGB / GLM |",
        "|---:|---:|---:|---:|",
    ]
    for point in va["points"]:
        lines.append(f"| {point['value']:.0f} | {point['glm_relativity']:.3f} | {point['xgb_relativity']:.3f} | {point['xgb_over_glm']:.3f} |")
    lines += [
        "",
        f"Strict 2024 out-of-range exposure is only **{pct(va['strict_extrapolation_share'], 4)}**; q05–q95 tail exposure is **{pct(va['q05_q95_tail_share'])}**.",
        "",
        f"`vehicle_value` is a useful counterexample: its model-family shape gap is only **{rs['vehicle_value_counterexample']['shape_gap']:.5f}**, despite **{pct(rs['vehicle_value_counterexample']['q05_q95_tail_share'])}** of 2024 exposure lying outside the development q05–q95 interval. Flexibility does not imply a large response-shape difference for every factor.",
        "",
        "## 2. Feature support and portfolio mix: is the current book unfamiliar?",
        "",
        "For the main numeric rating factors, strict extrapolation outside observed 2022 min/max is negligible. The dominant change is categorical mix.",
        "",
        "### Business type",
        "",
        f"Both business-type categories were seen in 2022, so unseen 2024 exposure is **{pct(bt['unseen_exposure_share'], 4)}**. Yet total-variation distance is **{pct(bt['total_variation'])}**:",
        "",
        "| Business type | 2022 exposure share | 2024 exposure share |",
        "|---|---:|---:|",
        f"| NB | {pct(bt['nb_development_share'])} | {pct(bt['nb_current_share'])} |",
        f"| P | {pct(bt['p_development_share'])} | {pct(bt['p_current_share'])} |",
        "",
        f"The v0.51 **frequency** response-shape gap for business type is only **{bt['frequency_shape_gap']:.5f}**. This is the opposite pattern from driver age: **small shape gap, very large portfolio-mix shift**.",
        "",
        "### Vehicle brand",
        "",
        f"For `BMW` in the 2022 reference-profile audit, GLM/XGB frequency relativities are **{brand['bmw_glm_relativity']:.3f} / {brand['bmw_xgb_relativity']:.3f}**. In 2024 there are {brand['unseen_2024_level_count']} brand levels absent from 2022, but together they represent only **{pct(brand['unseen_2024_exposure_share'], 4)}** of exposure; brand mix TV is **{pct(brand['mix_total_variation'])}**.",
        "",
        "## 3. Portfolio impact: if aggregate technical-risk level is fixed, how much redistribution remains?",
        "",
        f"v0.48 forces GLM and XGBoost aggregate predicted technical-risk totals equal before comparison. Frequency still shows mean absolute relativity redistribution **{pct(impact['frequency_mean_absolute_relativity_change'])}**, with **{pct(impact['frequency_exposure_share_abs_change_gt_10pct'])}** of exposure moving by more than ±10%.",
        "",
        f"Pure premium is more sensitive: mean absolute redistribution **{pct(impact['pure_premium_mean_absolute_relativity_change'])}**, **{pct(impact['pure_premium_exposure_share_abs_change_gt_10pct'])}** exposure >±10% and **{pct(impact['pure_premium_exposure_share_abs_change_gt_20pct'])}** >±20%. Business-type pure-premium total relativity shifts are approximately **NB {pct(impact['business_type_nb_pure_premium_total_relativity_change'])} / P {pct(impact['business_type_p_pure_premium_total_relativity_change'])}**.",
        "",
        "These are **technical-risk score redistributions, not customer premium changes**. v0.51 contains frequency response-shape analysis only; the pure-premium impact evidence comes from the separate frozen-model v0.48 diagnostic.",
        "",
        "## 4. Review matrix: do not collapse different risks into one score",
        "",
        "| Question | Driver age | Business type | What it means |",
        "|---|---|---|---|",
        f"| Do GLM/XGB frequency shapes differ? | Yes — gap {da['shape_gap']:.3f} | Much less — gap {bt['frequency_shape_gap']:.3f} | Model-structure question |",
        f"| Is 2024 outside development support? | Strict extrapolation {pct(da['strict_extrapolation_share'], 4)} | Unseen exposure {pct(bt['unseen_exposure_share'], 4)} | Support question |",
        f"| Has portfolio weight shifted? | Median age {da['development_median']:.0f} → {da['current_median']:.0f} | TV {pct(bt['total_variation'])}; NB/P almost reverse | Portfolio-mix question |",
        "| Does this prove XGBoost is better? | No | No | Requires outcome-based validation evidence |",
        "",
        "No composite score is created because these columns answer different questions and have different governance meanings.",
        "",
        "## 5. Evidence adequacy still comes first",
        "",
        f"Current state: **`{ev['status']}`**, **{ev['gate_pass_count']}/{ev['gate_count']}** machine gates pass, external target support **{ev['external_target_gates']}**, and there is no fresh independent validation asset. Blockers remain `{', '.join(ev['blocker_ids'])}`.",
        "",
        "The rating-factor review pack can explain **what differs, where the current book has shifted, and how large technical-risk redistribution could be**. It cannot establish which model is more accurate, clear the failed validation gates, open promotion review, or authorise a serving/customer-pricing change.",
        "",
        "## Decision boundary",
        "",
        "Current disposition remains **`HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`** and `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`. No FIRST CENTRAL/current UK transport, causal/fairness conclusion, realised premium effect or commercial uplift is claimed.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTDIR.mkdir(exist_ok=True)
    assessment = build_pack()
    (OUTDIR / "rating_factor_review_pack_v53.json").write_text(json.dumps(assessment, indent=2), encoding="utf-8")
    PACK.write_text(render_markdown(assessment), encoding="utf-8")
    print(json.dumps({
        "status": assessment["status"],
        "driver_age_shape_gap": assessment["rating_structure_and_support"]["driver_age"]["shape_gap"],
        "driver_age_strict_extrapolation": assessment["rating_structure_and_support"]["driver_age"]["strict_extrapolation_share"],
        "business_type_tv": assessment["rating_structure_and_support"]["business_type"]["total_variation"],
        "committee": assessment["evidence_adequacy"],
    }, indent=2))


if __name__ == "__main__":
    main()
