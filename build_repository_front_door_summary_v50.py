from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTDIR = ROOT / "results_v50"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    interview = (ROOT / "INTERVIEW_EVIDENCE_PACK.md").read_text(encoding="utf-8")
    impact = (ROOT / "MODEL_CHANGE_IMPACT_ASSESSMENT.md").read_text(encoding="utf-8")
    v49 = json.loads((ROOT / "action_results/v49/ACTION_V49_STATUS.json").read_text(encoding="utf-8"))
    v45_workflow = (ROOT / ".github/workflows/v45-repository-front-door.yml").read_text(encoding="utf-8")

    marker = "\n---\n"
    if marker not in readme:
        raise RuntimeError("README historical separator missing")
    front, historical = readme.split(marker, 1)

    checks = {
        "readme_has_v47_disagreement": "0.0993 frequency / 0.3171 pure premium" in front,
        "readme_has_v48_frequency_impact": "36.81%" in front,
        "readme_has_v48_pure_premium_impact": "78.26%" in front and "58.17%" in front,
        "readme_has_v49_disposition": "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN" in front,
        "readme_links_impact_pack": "MODEL_CHANGE_IMPACT_ASSESSMENT.md" in front,
        "readme_keeps_consumed_validation": "CONSUMED_RETROSPECTIVE_VALIDATION" in front,
        "interview_has_v47_section": "### 11. Explain model-family disagreement without reusing outcomes" in interview,
        "interview_has_v48_section": "### 12. Translate disagreement into portfolio impact without pretending it is premium" in interview,
        "interview_has_v49_section": "### 13. Put evidence, impact and pricing governance in the right order" in interview,
        "interview_explains_78pct_not_premium": "What does “78.26% of exposure moves by more than ±10%” actually mean?" in interview,
        "impact_pack_current_disposition": "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN" in impact,
        "v49_main_evidence_success": v49.get("status") == "success",
        "v49_committee_still_hold": v49.get("committee_status") == "EVIDENCE_GAP_HOLD",
        "v49_pricing_still_unauthorised": v49.get("customer_pricing_authorised") is False,
        "historical_v45_push_listener_removed": "  push:" not in v45_workflow,
        "historical_v45_pr_listener_removed": "  pull_request:" not in v45_workflow,
        "historical_v45_is_manual_audit": "workflow_dispatch:" in v45_workflow and "contents: read" in v45_workflow,
    }

    boundaries = {
        "benchmark_is_not_pricing_uplift": "not observed pricing/profit uplift" in front,
        "consumed_validation_not_relabelled_fresh": "no longer fresh evidence" in front,
        "impact_diagnostics_not_new_performance_evidence": "not new performance evidence" in front,
        "technical_relativity_not_customer_premium": "not customer premium" in front,
        "tweedie_limitation_visible": "max_iter=900" in front,
        "first_central_or_current_uk_transfer_claimed": False,
        "commercial_uplift_claimed": False,
    }

    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        raise RuntimeError(f"v0.50 front-door checks failed: {failed}")
    if not all(v is True for k, v in boundaries.items() if k not in {
        "first_central_or_current_uk_transfer_claimed", "commercial_uplift_claimed"
    }):
        raise RuntimeError("v0.50 boundary checks failed")

    result = {
        "status": "V50_RECRUITER_FRONT_DOOR_SYNC_PASS",
        "scope": "documentation_and_evidence_navigation_only",
        "front_door_current_through": "v0.49",
        "row_level_data_accessed": False,
        "model_fit_executed": False,
        "historical_model_or_validation_decisions_changed": False,
        "v45_rolling_writer_frozen": True,
        "readme_historical_body_sha256": sha256_text(historical),
        "checks": checks,
        "headline_boundaries": boundaries,
        "current_decision": {
            "committee_status": v49["committee_status"],
            "committee_gate_pass_count": v49["committee_gate_pass_count"],
            "committee_gate_count": v49["committee_gate_count"],
            "external_target_gates": v49["external_target_gates"],
            "impact_pack_disposition": v49["impact_pack_disposition"],
            "model_family_decision": v49["model_family_decision"],
            "serving_status": v49["serving_status"],
            "promotion_review_status": v49["promotion_review_status"],
            "customer_pricing_authorised": v49["customer_pricing_authorised"],
        },
    }
    OUTDIR.mkdir(exist_ok=True)
    (OUTDIR / "repository_front_door_summary_v50.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
