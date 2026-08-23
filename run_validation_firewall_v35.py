from __future__ import annotations

import json
from pathlib import Path

from governance.validation_firewall import load_ledger


LEDGER = Path("governance/validation_use_ledger_v35.json")
OUTDIR = Path("results_v35")


def main() -> None:
    ledger = load_ledger(LEDGER)
    period = ledger["periods"]["2024"]
    events = period["material_reuse_events"]
    post_first = [event for event in events if event["id"] != "initial_locked_oot"]
    label_uses = [event for event in events if event["uses_2024_labels"]]
    firewall = ledger["promotion_firewall"]

    result = {
        "status": "V35_VALIDATION_FIREWALL_PASS",
        "dataset": ledger["dataset"],
        "2024": {
            "initial_role": period["initial_role"],
            "current_role": period["current_role"],
            "independent_holdout_available": period["independent_holdout_available"],
            "candidate_selection_allowed": period["candidate_selection_allowed"],
            "promotion_evidence_class": period["promotion_evidence_class"],
            "material_reuse_event_count": len(events),
            "post_first_use_reuse_event_count": len(post_first),
            "label_using_event_count": len(label_uses),
            "registered_event_ids": [event["id"] for event in events],
        },
        "firewall": {
            "status": firewall["status"],
            "requires_new_independent_period_or_external_validation": firewall[
                "requires_new_independent_period_or_external_validation"
            ],
            "allowed_future_2024_purposes": firewall["allowed_future_2024_purposes"],
            "forbidden_future_2024_purposes": firewall["forbidden_future_2024_purposes"],
            "next_promotion_evidence_requirement": firewall["next_promotion_evidence_requirement"],
        },
        "decision": {
            "model_family_decision": firewall["model_family_decision"],
            "serving_status": firewall["serving_status"],
            "model_promotion_authorised": False,
            "pricing_change_authorised": False,
        },
        "interpretation": (
            "2024 was independent at the first locked OOT evaluation, but repeated later monitoring, "
            "outcome, recalibration, cohort and uncertainty analyses consume that independence for "
            "future candidate selection. Future 2024 use is restricted to reproduction, monitoring, "
            "post-hoc diagnostics and governance testing."
        ),
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "validation_firewall_summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
