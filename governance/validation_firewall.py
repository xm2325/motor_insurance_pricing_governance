from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_REUSED_2024_PURPOSES = {
    "regression_reproduction",
    "monitoring_replay",
    "post_hoc_diagnostics",
    "governance_contract_testing",
}

FORBIDDEN_REUSED_2024_PURPOSES = {
    "fit_new_model_parameters",
    "fit_new_calibration_parameters",
    "select_new_candidate_policy",
    "independent_confirmation",
    "authorise_model_family_promotion",
    "authorise_customer_pricing",
}


class ValidationFirewallError(ValueError):
    """Raised when validation-use governance would overstate reused evidence."""


def load_ledger(path: str | Path) -> dict[str, Any]:
    ledger = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_ledger(ledger)
    return ledger


def validate_ledger(ledger: dict[str, Any]) -> None:
    if ledger.get("schema_version") != "0.35":
        raise ValidationFirewallError("validation ledger schema_version must be 0.35")

    periods = ledger.get("periods")
    if not isinstance(periods, dict):
        raise ValidationFirewallError("periods must be a mapping")
    for year in ("2022", "2023", "2024"):
        if year not in periods:
            raise ValidationFirewallError(f"missing validation period {year}")

    period_2024 = periods["2024"]
    if period_2024.get("initial_role") != "LOCKED_OOT_FIRST_USE":
        raise ValidationFirewallError("2024 initial role must preserve the first-use OOT history")
    if period_2024.get("current_role") != "CONSUMED_RETROSPECTIVE_VALIDATION":
        raise ValidationFirewallError("2024 must be marked as consumed retrospective validation")
    if period_2024.get("independent_holdout_available") is not False:
        raise ValidationFirewallError("2024 may not remain an independent holdout")
    if period_2024.get("candidate_selection_allowed") is not False:
        raise ValidationFirewallError("2024 may not be used for further candidate selection")
    if period_2024.get("promotion_evidence_class") != "REUSED_HISTORICAL_VALIDATION":
        raise ValidationFirewallError("2024 evidence class must state historical reuse")

    reuse_events = period_2024.get("material_reuse_events")
    if not isinstance(reuse_events, list) or len(reuse_events) < 6:
        raise ValidationFirewallError("2024 ledger must retain material reuse history")
    ids = [str(event.get("id")) for event in reuse_events]
    if len(ids) != len(set(ids)):
        raise ValidationFirewallError("validation reuse event ids must be unique")
    required_ids = {"initial_locked_oot", "v0.22", "v0.31", "v0.32", "v0.33", "v0.34"}
    missing = required_ids.difference(ids)
    if missing:
        raise ValidationFirewallError(f"missing material 2024 reuse events: {sorted(missing)}")

    for event in reuse_events:
        if event.get("year") != 2024:
            raise ValidationFirewallError("all registered 2024 reuse events must target year 2024")
        if event.get("fit_parameters_from_2024_labels") is not False:
            raise ValidationFirewallError("registered reuse must not imply 2024 parameter fitting")

    firewall = ledger.get("promotion_firewall")
    if not isinstance(firewall, dict):
        raise ValidationFirewallError("promotion_firewall must be a mapping")
    if firewall.get("status") != "BLOCK_NEW_PROMOTION_FROM_2024_REUSE":
        raise ValidationFirewallError("2024 reuse must block new promotion claims")
    if firewall.get("requires_new_independent_period_or_external_validation") is not True:
        raise ValidationFirewallError("new promotion evidence must require independent data")
    if firewall.get("model_family_decision") != "HOLD":
        raise ValidationFirewallError("model family must remain HOLD")
    if firewall.get("serving_status") != "HOLD_SHADOW_ONLY":
        raise ValidationFirewallError("serving must remain HOLD_SHADOW_ONLY")

    allowed = set(firewall.get("allowed_future_2024_purposes", []))
    forbidden = set(firewall.get("forbidden_future_2024_purposes", []))
    if allowed != ALLOWED_REUSED_2024_PURPOSES:
        raise ValidationFirewallError("allowed future 2024 purposes changed")
    if forbidden != FORBIDDEN_REUSED_2024_PURPOSES:
        raise ValidationFirewallError("forbidden future 2024 purposes changed")
    if allowed.intersection(forbidden):
        raise ValidationFirewallError("allowed and forbidden purpose sets overlap")


def assess_proposed_use(ledger: dict[str, Any], *, year: int, purpose: str) -> dict[str, Any]:
    """Fail closed on any new promotion/candidate-selection use of consumed 2024 evidence."""
    validate_ledger(ledger)
    purpose = str(purpose)
    if year != 2024:
        return {
            "allowed": True,
            "year": int(year),
            "purpose": purpose,
            "reason": "V0_35_FIREWALL_ONLY_CLASSIFIES_REUSED_2024",
        }
    if purpose in FORBIDDEN_REUSED_2024_PURPOSES:
        raise ValidationFirewallError(
            f"2024 is consumed retrospective validation and cannot be used for {purpose}"
        )
    if purpose not in ALLOWED_REUSED_2024_PURPOSES:
        raise ValidationFirewallError(
            f"unregistered 2024 purpose {purpose!r}; validation firewall fails closed"
        )
    return {
        "allowed": True,
        "year": 2024,
        "purpose": purpose,
        "evidence_class": "REUSED_HISTORICAL_VALIDATION",
        "independent_confirmation": False,
        "promotion_authorised": False,
    }
