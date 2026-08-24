from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTDIR = ROOT / "results_v54"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def has_exact_line(text: str, line: str) -> bool:
    return line in text.splitlines()


def has_shell_command(text: str, command_prefix: str) -> bool:
    return any(line.strip().startswith(command_prefix) for line in text.splitlines())


def main() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    interview = (ROOT / "INTERVIEW_EVIDENCE_PACK.md").read_text(encoding="utf-8")
    rating_pack = (ROOT / "RATING_FACTOR_REVIEW_PACK.md").read_text(encoding="utf-8")
    v53 = json.loads((ROOT / "action_results/v53/ACTION_V53_STATUS.json").read_text(encoding="utf-8"))
    v50_workflow = (ROOT / ".github/workflows/v50-recruiter-front-door.yml").read_text(encoding="utf-8")
    v45_workflow = (ROOT / ".github/workflows/v45-repository-front-door.yml").read_text(encoding="utf-8")

    marker = "\n---\n"
    if readme.count(marker) != 1:
        raise RuntimeError("README historical separator contract changed")
    front, historical = readme.split(marker, 1)

    checks = {
        "readme_has_rating_review_pack": "RATING_FACTOR_REVIEW_PACK.md" in front,
        "readme_has_v51_shape_gap": "0.26866 / 0.26771" in front,
        "readme_has_v52_strict_support": "0.00227% exposure" in front,
        "readme_has_v52_business_mix": "48.60%" in front and "0% unseen business-type exposure" in front,
        "readme_has_v53_sequence": "response shape → strict support → portfolio mix → technical-risk redistribution → evidence adequacy → separate pricing governance" in front,
        "readme_has_rating_chain_links": all(x in front for x in ["RESULTS_V51.md", "RESULTS_V52.md", "RESULTS_V53.md"]),
        "interview_has_v51_section": "### 14. Inspect rating-factor response shapes on development data" in interview,
        "interview_has_v52_section": "### 15. Separate feature support from portfolio mix" in interview,
        "interview_has_v53_section": "### 16. Join rating structure, support, impact and evidence without a composite score" in interview,
        "interview_has_support_vs_mix_question": "If strict extrapolation is near zero, why did monitoring show such large drift?" in interview,
        "interview_has_no_composite_question": "Why not combine shape gap, support drift and impact into one risk score?" in interview,
        "rating_pack_has_same_driver_gap": "0.26866" in rating_pack,
        "rating_pack_has_same_business_tv": "48.60%" in rating_pack,
        "v53_main_evidence_success": v53.get("status") == "success",
        "v53_main_scope_aggregate": v53.get("scope") == "aggregate_rating_structure_support_mix_and_impact_synthesis",
        "v50_push_listener_removed": not has_exact_line(v50_workflow, "  push:"),
        "v50_pr_listener_removed": not has_exact_line(v50_workflow, "  pull_request:"),
        "v50_manual_read_only": has_exact_line(v50_workflow, "  workflow_dispatch:") and has_exact_line(v50_workflow, "  contents: read"),
        "v50_has_no_push_command": not has_shell_command(v50_workflow, "git push") and not has_shell_command(v50_workflow, "bash scripts/push_evidence_with_rebase.sh"),
        "v45_still_manual_read_only": not has_exact_line(v45_workflow, "  push:") and not has_exact_line(v45_workflow, "  pull_request:") and has_exact_line(v45_workflow, "  contents: read"),
    }
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise RuntimeError(f"v0.54 front-door checks failed: {failed}")

    boundaries = {
        "benchmark_is_not_pricing_uplift": "not observed pricing/profit uplift" in front,
        "consumed_validation_not_relabelled_fresh": "no longer fresh evidence" in front,
        "v51_not_relabelled_validation": "v0.51 is **development interpretability**" in front,
        "v52_not_relabelled_performance": "v0.52 is a **label-free feature support/mix audit**" in front,
        "v53_not_relabelled_performance": "v0.53 is an **aggregate synthesis/navigation pack**" in front,
        "technical_relativity_not_customer_premium": "not customer premium" in front,
        "first_central_or_current_uk_transfer_claimed": False,
        "commercial_uplift_claimed": False,
    }
    required_true = {
        k: v for k, v in boundaries.items()
        if k not in {"first_central_or_current_uk_transfer_claimed", "commercial_uplift_claimed"}
    }
    if not all(required_true.values()):
        raise RuntimeError(f"v0.54 boundary checks failed: {[k for k, v in required_true.items() if not v]}")

    current = {
        "committee_status": "EVIDENCE_GAP_HOLD",
        "committee_gate_pass_count": v53["committee_gate_pass_count"],
        "committee_gate_count": v53["committee_gate_count"],
        "external_target_gates": v53["external_target_gates"],
        "model_family_decision": v53["model_family_decision"],
        "serving_status": v53["serving_status"],
        "promotion_review_status": v53["promotion_review_status"],
        "customer_pricing_authorised": v53["customer_pricing_authorised"],
    }
    if current != {
        "committee_status": "EVIDENCE_GAP_HOLD",
        "committee_gate_pass_count": 5,
        "committee_gate_count": 8,
        "external_target_gates": "0/4",
        "model_family_decision": "HOLD",
        "serving_status": "HOLD_SHADOW_ONLY",
        "promotion_review_status": "NOT_OPEN",
        "customer_pricing_authorised": False,
    }:
        raise RuntimeError(f"v0.54 current decision changed: {current}")

    result = {
        "status": "V54_RATING_FRONT_DOOR_SYNC_PASS",
        "scope": "documentation_and_evidence_navigation_only",
        "front_door_current_through": "v0.53",
        "row_level_data_accessed": False,
        "model_fit_executed": False,
        "historical_model_or_validation_decisions_changed": False,
        "v50_rolling_writer_frozen": True,
        "v45_rolling_writer_frozen": True,
        "readme_historical_body_sha256": sha256_text(historical),
        "checks": checks,
        "headline_boundaries": boundaries,
        "rating_review_headlines": {
            "driver_age_shape_gap": v53["driver_age_shape_gap"],
            "driver_age_strict_extrapolation_exposure_share": v53["driver_age_strict_extrapolation_exposure_share"],
            "business_type_mix_tv": v53["business_type_mix_tv"],
            "business_type_unseen_exposure_share": v53["business_type_unseen_exposure_share"],
            "frequency_mean_absolute_portfolio_neutral_relativity_change": v53["frequency_mean_absolute_portfolio_neutral_relativity_change"],
            "pure_premium_mean_absolute_portfolio_neutral_relativity_change": v53["pure_premium_mean_absolute_portfolio_neutral_relativity_change"],
        },
        "current_decision": current,
    }
    OUTDIR.mkdir(exist_ok=True)
    (OUTDIR / "rating_front_door_summary_v54.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
