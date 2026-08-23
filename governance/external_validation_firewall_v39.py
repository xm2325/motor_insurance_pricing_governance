from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "governance" / "external_validation_use_ledger_v39.json"

ALLOWED_CONSUMED_PURPOSES = frozenset({
    "regression_reproduction",
    "numerical_reproducibility_audit",
    "post_hoc_diagnostics_no_candidate_selection",
    "governance_contract_testing",
})

FORBIDDEN_CONSUMED_PURPOSES = frozenset({
    "fit_new_model_parameters",
    "fit_new_calibration_parameters",
    "hyperparameter_search",
    "select_new_candidate_policy",
    "independent_confirmation",
    "authorise_model_family_promotion",
    "authorise_customer_pricing",
})

PREREGISTRATION_ONLY_PURPOSE = "preregistration_only_before_row_level_access"


class ExternalValidationFirewallError(ValueError):
    """Raised when a proposed external-data use violates the registered firewall."""


def load_ledger(path: Path = DEFAULT_LEDGER) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_ledger(ledger: dict[str, Any]) -> None:
    if ledger.get("schema_version") != "0.39":
        raise ExternalValidationFirewallError("unexpected external validation ledger version")
    if ledger.get("status") != "V39_EXTERNAL_VALIDATION_FIREWALL_ACTIVE":
        raise ExternalValidationFirewallError("external validation firewall must remain active")

    datasets = ledger.get("datasets")
    if set(datasets or {}) != {"ausprivauto0405"}:
        raise ExternalValidationFirewallError("registered consumed external dataset set changed")

    australian = datasets["ausprivauto0405"]
    expected_source = {
        "source_repository": "dutangc/CASdatasets",
        "source_commit": "227fb56b8734bdb7c0327a41180e01d2ddaeaf26",
        "source_path": "data/ausprivauto0405.rda",
        "source_file_sha256": "c8aeabd0b75e16a2b9a7452cfb3e8e2b3ec36a27171d35c2862bc8278777461c",
        "rows": 67856,
        "v36_preregistration_sha256": "b20d38b51f767761fe4b4f85d58988f7032dbcc7d7afc96041f3858c0165e3c1",
    }
    for key, value in expected_source.items():
        if australian.get(key) != value:
            raise ExternalValidationFirewallError(f"Australian source identity changed: {key}")

    required_false = (
        "independent_external_validation_available",
        "candidate_selection_allowed",
        "model_or_calibration_parameter_fitting_allowed",
        "promotion_evidence_allowed",
        "customer_pricing_authorisation_allowed",
    )
    if australian.get("initial_role") != "INDEPENDENT_EXTERNAL_VALIDATION_FIRST_USE":
        raise ExternalValidationFirewallError("Australian first-use role changed")
    if australian.get("current_role") != "CONSUMED_EXTERNAL_VALIDATION_DATASET":
        raise ExternalValidationFirewallError("Australian dataset must remain consumed")
    if any(australian.get(key) is not False for key in required_false):
        raise ExternalValidationFirewallError("consumed Australian evidence cannot regain independence or promotion use")
    if australian.get("all_registered_splits_have_been_used") is not True:
        raise ExternalValidationFirewallError("Australian registered splits have already been used")
    if australian.get("locked_test_rows") != 13572:
        raise ExternalValidationFirewallError("Australian locked-test row count changed")

    if set(australian.get("allowed_future_purposes", [])) != set(ALLOWED_CONSUMED_PURPOSES):
        raise ExternalValidationFirewallError("allowed consumed-data purposes changed")
    if set(australian.get("forbidden_future_purposes", [])) != set(FORBIDDEN_CONSUMED_PURPOSES):
        raise ExternalValidationFirewallError("forbidden consumed-data purposes changed")

    events = australian.get("material_use_events", [])
    if [event.get("id") for event in events] != ["v0.36", "v0.37", "v0.38"]:
        raise ExternalValidationFirewallError("external validation history cannot be dropped or reordered")
    if events[0].get("row_level_data_accessed") is not False or events[0].get("outcomes_inspected") is not False:
        raise ExternalValidationFirewallError("v0.36 must remain preregistration-only")
    if events[1].get("independent_at_time_of_use") is not True:
        raise ExternalValidationFirewallError("v0.37 first external execution was independent at first use")
    if events[2].get("independent_at_time_of_use") is not False:
        raise ExternalValidationFirewallError("v0.38 reused already-inspected Australian outcomes")
    for event in events:
        source = ROOT / event["source"]
        if not source.is_file():
            raise ExternalValidationFirewallError(f"missing external evidence source: {event['source']}")

    firewall = ledger.get("new_external_dataset_firewall", {})
    if firewall.get("row_level_access_requires_registered_dataset") is not True:
        raise ExternalValidationFirewallError("new external row-level access must require registration")
    if firewall.get("preregistration_only_before_row_level_access_is_allowed_for_unregistered_dataset") is not True:
        raise ExternalValidationFirewallError("unseen datasets must be able to enter via preregistration-only stage")
    if firewall.get("minimum_independent_actions_executions_for_positive_external_support") != 2:
        raise ExternalValidationFirewallError("future positive external support must require two Actions executions")
    if firewall.get("positive_external_support_requires_matching_decisions") is not True:
        raise ExternalValidationFirewallError("future positive external decisions must reproduce")
    if firewall.get("positive_external_support_requires_registered_metric_reproducibility") is not True:
        raise ExternalValidationFirewallError("future positive external metrics must reproduce")
    if firewall.get("iterative_estimators_require_registered_solver_and_tolerance") is not True:
        raise ExternalValidationFirewallError("iterative estimator settings must be preregistered")
    if firewall.get("default_thread_environment") != {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }:
        raise ExternalValidationFirewallError("default external numerical thread environment changed")

    decision = ledger.get("decision", {})
    if decision.get("model_family_decision") != "HOLD" or decision.get("serving_status") != "HOLD_SHADOW_ONLY":
        raise ExternalValidationFirewallError("external validation firewall cannot promote serving")
    if decision.get("model_promotion_authorised") is not False or decision.get("pricing_change_authorised") is not False:
        raise ExternalValidationFirewallError("external validation firewall cannot authorise promotion or pricing")


def assess_external_use(
    ledger: dict[str, Any],
    *,
    dataset_id: str,
    purpose: str,
) -> dict[str, Any]:
    validate_ledger(ledger)
    datasets = ledger["datasets"]

    if dataset_id not in datasets:
        if purpose == PREREGISTRATION_ONLY_PURPOSE:
            return {
                "allowed": True,
                "dataset_id": dataset_id,
                "evidence_class": "UNSEEN_EXTERNAL_PREREGISTRATION_ONLY",
                "row_level_access_allowed": False,
                "independent_confirmation": False,
                "promotion_authorised": False,
                "next_required_state": "REGISTER_PROTOCOL_ON_MAIN_BEFORE_ROW_LEVEL_ACCESS",
            }
        raise ExternalValidationFirewallError(
            "unregistered external dataset cannot be accessed or analysed before preregistration is on main"
        )

    dataset = datasets[dataset_id]
    if dataset["current_role"] != "CONSUMED_EXTERNAL_VALIDATION_DATASET":
        raise ExternalValidationFirewallError("unexpected registered external dataset role")

    if purpose in FORBIDDEN_CONSUMED_PURPOSES:
        raise ExternalValidationFirewallError(
            f"{dataset_id} is consumed external validation evidence and cannot be used for {purpose}"
        )
    if purpose not in ALLOWED_CONSUMED_PURPOSES:
        raise ExternalValidationFirewallError(
            f"unregistered purpose for consumed external validation data: {purpose}"
        )

    return {
        "allowed": True,
        "dataset_id": dataset_id,
        "evidence_class": "CONSUMED_EXTERNAL_VALIDATION_REUSE",
        "row_level_access_allowed": True,
        "independent_confirmation": False,
        "candidate_selection_allowed": False,
        "promotion_authorised": False,
        "pricing_change_authorised": False,
        "purpose": purpose,
    }
