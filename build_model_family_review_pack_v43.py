import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICY = ROOT / "governance/model_family_evidence_synthesis_policy_v43.json"
OUT = ROOT / "results_v43"


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_benchmark(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_model = {row["model"]: row for row in rows}
    glm = by_model["Poisson GLM - + geography"]
    xgb = by_model["XGBoost Poisson - + geography"]
    glm_dev = float(glm["poisson_deviance"])
    xgb_dev = float(xgb["poisson_deviance"])
    return {
        "reference_deviance": glm_dev,
        "challenger_deviance": xgb_dev,
        "relative_deviance_improvement": (glm_dev - xgb_dev) / glm_dev,
        "reference_top10_capture": float(glm["top10_exposure_claim_capture"]),
        "challenger_top10_capture": float(xgb["top10_exposure_claim_capture"]),
        "evidence_class": "CROSS_SECTIONAL_DEVELOPMENT_BENCHMARK",
        "promotion_evidence": False,
    }


def main():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    src = policy["source_contracts"]

    benchmark = read_benchmark(src["cross_sectional_benchmark"])
    spanish = read_json(src["spanish_first_use_oot"])
    spanish_firewall = read_json(src["spanish_validation_firewall"])
    australia = read_json(src["australian_external_origin"])
    australia_firewall = read_json(src["australian_validation_firewall"])
    belgium = read_json(src["belgian_external_closeout"])
    belgium_firewall = read_json(src["belgian_validation_firewall"])

    sp_f = {x["model"]: x for x in spanish["frequency_results"]}
    sp_p = {x["model"]: x for x in spanish["pure_premium_results"]}
    sp_f_glm = sp_f["Poisson_GLM"]["test_locked_poisson_deviance"]
    sp_f_xgb = sp_f["XGBoost_Poisson"]["test_locked_poisson_deviance"]
    sp_p_glm = sp_p["Tweedie_GLM"]["test_locked_tweedie_deviance_p1_5"]
    sp_p_xgb = sp_p["XGBoost_Tweedie"]["test_locked_tweedie_deviance_p1_5"]

    belg_f = belgium["reproducibility"]["comparisons"]["frequency"]
    belg_p = belgium["reproducibility"]["comparisons"]["pure_premium"]

    evidence = [
        {
            "id": "fremtpl2_cross_sectional_frequency",
            "portfolio": "freMTPL2",
            "context": "cross-sectional benchmark",
            "independent_at_first_use": False,
            "current_independent_evidence": False,
            "target": "frequency",
            "reference_deviance": benchmark["reference_deviance"],
            "challenger_deviance": benchmark["challenger_deviance"],
            "relative_deviance_improvement": benchmark["relative_deviance_improvement"],
            "registered_decision": "DEVELOPMENT_BENCHMARK_ONLY",
            "gate_passed": None,
            "evidence_class": benchmark["evidence_class"],
        },
        {
            "id": "spanish_2024_frequency",
            "portfolio": "Spanish insurer 2024",
            "context": "locked OOT first use; now consumed retrospective validation",
            "independent_at_first_use": True,
            "current_independent_evidence": spanish_firewall["2024"]["independent_holdout_available"],
            "target": "frequency",
            "reference_deviance": sp_f_glm,
            "challenger_deviance": sp_f_xgb,
            "relative_deviance_improvement": (sp_f_glm - sp_f_xgb) / sp_f_glm,
            "registered_decision": spanish["model_change_decision"]["frequency_challenger"],
            "gate_passed": False,
            "evidence_class": "LOCKED_OOT_FIRST_USE_NOW_CONSUMED_RETROSPECTIVE_VALIDATION",
        },
        {
            "id": "spanish_2024_pure_premium",
            "portfolio": "Spanish insurer 2024",
            "context": "locked OOT first use; now consumed retrospective validation",
            "independent_at_first_use": True,
            "current_independent_evidence": spanish_firewall["2024"]["independent_holdout_available"],
            "target": "pure_premium",
            "reference_deviance": sp_p_glm,
            "challenger_deviance": sp_p_xgb,
            "relative_deviance_improvement": (sp_p_glm - sp_p_xgb) / sp_p_glm,
            "registered_decision": spanish["model_change_decision"]["pure_premium_challenger"],
            "gate_passed": False,
            "evidence_class": "LOCKED_OOT_FIRST_USE_NOW_CONSUMED_RETROSPECTIVE_VALIDATION",
        },
        {
            "id": "australian_external_frequency",
            "portfolio": "Australian ausprivauto0405",
            "context": "preregistered external first use; now consumed",
            "independent_at_first_use": True,
            "current_independent_evidence": australia_firewall["datasets"]["ausprivauto0405"]["independent_external_validation_available"],
            "target": "frequency",
            "reference_deviance": australia["frequency"]["locked_test"]["reference_deviance"],
            "challenger_deviance": australia["frequency"]["locked_test"]["challenger_deviance"],
            "relative_deviance_improvement": australia["frequency"]["locked_test"]["relative_deviance_improvement"],
            "registered_decision": australia["frequency"]["registered_gate"]["decision"],
            "gate_passed": australia["frequency"]["registered_gate"]["passed"],
            "bootstrap_q025": australia["frequency"]["paired_bootstrap_relative_deviance_improvement"]["q025"],
            "evidence_class": "PREREGISTERED_EXTERNAL_MODEL_FAMILY_REPLICATION_NOW_CONSUMED",
        },
        {
            "id": "australian_external_pure_premium",
            "portfolio": "Australian ausprivauto0405",
            "context": "preregistered external first use; now consumed",
            "independent_at_first_use": True,
            "current_independent_evidence": australia_firewall["datasets"]["ausprivauto0405"]["independent_external_validation_available"],
            "target": "pure_premium",
            "reference_deviance": australia["pure_premium"]["locked_test"]["reference_deviance"],
            "challenger_deviance": australia["pure_premium"]["locked_test"]["challenger_deviance"],
            "relative_deviance_improvement": australia["pure_premium"]["locked_test"]["relative_deviance_improvement"],
            "registered_decision": australia["pure_premium"]["registered_gate"]["decision"],
            "gate_passed": australia["pure_premium"]["registered_gate"]["passed"],
            "bootstrap_q025": australia["pure_premium"]["paired_bootstrap_relative_deviance_improvement"]["q025"],
            "evidence_class": "PREREGISTERED_EXTERNAL_MODEL_FAMILY_REPLICATION_NOW_CONSUMED",
        },
        {
            "id": "belgian_external_frequency",
            "portfolio": "Belgian beMTPL97",
            "context": "preregistered external first use; observed two-run reproducibility; now consumed",
            "independent_at_first_use": True,
            "current_independent_evidence": belgium_firewall["independent_external_validation_available"],
            "target": "frequency",
            "reference_deviance": belg_f["reference_deviance"]["main"],
            "challenger_deviance": belg_f["challenger_deviance"]["main"],
            "relative_deviance_improvement": belgium["registered_results"]["frequency_relative_deviance_improvement"],
            "registered_decision": belgium["registered_results"]["frequency_decision"],
            "gate_passed": False,
            "bootstrap_q025": belgium["registered_results"]["frequency_bootstrap_q025"],
            "numerically_reproduced_within_registered_tolerance": belgium["reproducibility"]["all_registered_numeric_metrics_within_tolerance"],
            "evidence_class": "PREREGISTERED_EXTERNAL_MODEL_FAMILY_REPLICATION_NOW_CONSUMED",
        },
        {
            "id": "belgian_external_pure_premium",
            "portfolio": "Belgian beMTPL97",
            "context": "preregistered external first use; observed two-run reproducibility; now consumed",
            "independent_at_first_use": True,
            "current_independent_evidence": belgium_firewall["independent_external_validation_available"],
            "target": "pure_premium",
            "reference_deviance": belg_p["reference_deviance"]["main"],
            "challenger_deviance": belg_p["challenger_deviance"]["main"],
            "relative_deviance_improvement": belgium["registered_results"]["pure_premium_relative_deviance_improvement"],
            "registered_decision": belgium["registered_results"]["pure_premium_decision"],
            "gate_passed": False,
            "bootstrap_q025": belgium["registered_results"]["pure_premium_bootstrap_q025"],
            "numerically_reproduced_within_registered_tolerance": belgium["reproducibility"]["all_registered_numeric_metrics_within_tolerance"],
            "evidence_class": "PREREGISTERED_EXTERNAL_MODEL_FAMILY_REPLICATION_NOW_CONSUMED",
        },
    ]

    external = [e for e in evidence if e["id"].startswith(("australian_", "belgian_"))]
    external_passes = [e for e in external if e["gate_passed"] is True]
    summary = {
        "status": "V43_MODEL_FAMILY_EVIDENCE_SYNTHESIS_COMPLETE",
        "evidence_basis": evidence,
        "portfolio_level_summary": {
            "external_portfolios_evaluated": 2,
            "external_target_gates_evaluated": len(external),
            "external_target_gates_passed": len(external_passes),
            "external_frequency_gates_passed": sum(e["target"] == "frequency" and e["gate_passed"] is True for e in external),
            "external_pure_premium_gates_passed": sum(e["target"] == "pure_premium" and e["gate_passed"] is True for e in external),
            "current_consumed_validation_datasets": [
                "Spanish 2024",
                "Australian ausprivauto0405",
                "Belgian beMTPL97",
            ],
            "current_fresh_independent_validation_dataset_available": False,
        },
        "decision": {
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "promotion_review_status": "NOT_OPEN",
            "model_promotion_authorised": False,
            "pricing_change_authorised": False,
            "reason": policy["review_logic"]["reason"],
        },
        "reopen_requirements": policy["review_logic"]["reopen_requirements"],
        "synthesis_boundaries": {
            "pooled_meta_analysis_claimed": False,
            "evidence_weighting_score_used": False,
            "benchmark_used_as_promotion_evidence": False,
            "consumed_validation_relabelled_independent": False,
            "first_central_or_current_uk_transport_claimed": False,
        },
    }

    assert summary["portfolio_level_summary"]["external_target_gates_passed"] == 0
    assert summary["decision"]["model_family_decision"] == "HOLD"
    assert not summary["decision"]["model_promotion_authorised"]
    assert not summary["decision"]["pricing_change_authorised"]
    assert spanish_firewall["2024"]["current_role"] == "CONSUMED_RETROSPECTIVE_VALIDATION"
    assert australia_firewall["datasets"]["ausprivauto0405"]["current_role"] == "CONSUMED_EXTERNAL_VALIDATION_DATASET"
    assert belgium_firewall["current_role"] == "CONSUMED_EXTERNAL_VALIDATION_DATASET"

    OUT.mkdir(exist_ok=True)
    (OUT / "model_family_evidence_synthesis_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    rows = []
    for e in evidence:
        gain = 100 * e["relative_deviance_improvement"]
        gate = "n/a" if e["gate_passed"] is None else ("PASS" if e["gate_passed"] else "FAIL")
        rows.append(
            f"| {e['portfolio']} | {e['target']} | {gain:+.4f}% | {gate} | {e['registered_decision']} |"
        )
    md = """# v0.43 Model-Family Review Pack\n\n## Executive decision\n\n**HOLD / HOLD_SHADOW_ONLY. Promotion review is NOT OPEN.**\n\nThe project has a strong cross-sectional XGBoost frequency benchmark signal, but that signal does not survive as a consistent, preregistered promotion case across the locked Spanish OOT and two independent external portfolios. Both Australian registered external gates fail and both Belgian registered external gates fail. Belgian negative decisions reproduce within the preregistered numerical tolerances.\n\n## Evidence matrix\n\n| Portfolio / evidence source | Target | XGB relative deviance improvement | Registered gate | Registered decision |\n|---|---|---:|---|---|\n""" + "\n".join(rows) + """\n\n## Why HOLD is the evidence-consistent decision\n\n- freMTPL2 is development/benchmark evidence; it cannot authorise promotion.\n- Spanish 2024 was independent at first locked OOT use and did not support a global challenger switch; it is now consumed retrospective validation.\n- Australian `ausprivauto0405` was preregistered before row-level access. Frequency favoured GLM; pure premium had a favourable XGB point estimate but failed bootstrap confirmation. The portfolio is now consumed external validation.\n- Belgian `beMTPL97` was preregistered before row-level access. Frequency had a small positive XGB direction but missed the fixed 0.5% materiality gate; pure premium failed point/CI support. Both negative decisions reproduced across the two completed observed Actions runs within registered tolerance. The portfolio is now consumed external validation.\n- No preregistered independent external target gate has passed.\n\n## What would reopen promotion review\n\n""" + "\n".join(f"- {x}" for x in policy["review_logic"]["reopen_requirements"]) + """\n\n## Interpretation boundaries\n\n- This is an aggregate evidence-synthesis and model-risk dossier; it does not fit or tune models.\n- No pooled meta-analysis or evidence-weighting score is used because the portfolios differ materially in geography, period, features and context.\n- HOLD does not mean XGBoost is universally inferior; it means current evidence does not support promotion under the registered project contracts.\n- Nothing here establishes transport to FIRST CENTRAL or the current UK motor market.\n"""
    (OUT / "MODEL_FAMILY_REVIEW_PACK_V43.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary["decision"], indent=2))


if __name__ == "__main__":
    main()
