from __future__ import annotations

import json
from pathlib import Path

import pyreadr

PREREG = Path("governance/external_temporal_prereg_v57.json")
V57_LOCK = Path("action_results/v57/eumtpl_external_temporal_prereg_lock.json")
V57_STATUS = Path("action_results/v57/ACTION_V57_STATUS.json")
SOURCE_AUDIT = Path("results_v58/eumtpl_source_binary_audit.json")
DATA_PATH = Path("data_external_v58/euMTPL.rda")
OUT = Path("results_v58/eumtpl_schema_contract_incident_v58.json")
EXPECTED_PROTOCOL_SHA256 = "a2b49e26aeca619323129ee4b56ff39d110cf68a08bfe0064fbd3f5886f74ff5"
EXPECTED_V57_MAIN_SHA = "cacb55a039c6132b7c2466f6356903250dc624d3"


def main() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    lock = json.loads(V57_LOCK.read_text(encoding="utf-8"))
    status = json.loads(V57_STATUS.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))

    if lock["protocol_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.57 preregistration digest changed")
    if status["status"] != "success" or status["sha"] != EXPECTED_V57_MAIN_SHA:
        raise RuntimeError("v0.57 main preregistration source changed")
    if source["status"] != "V58_PINNED_EUMTPL_BINARY_VERIFIED_BEFORE_DECODE":
        raise RuntimeError("pinned binary identity was not verified before decode")
    if source["git_blob_sha1"] != prereg["source"]["upstream_git_blob_sha"]:
        raise RuntimeError("downloaded binary does not match preregistered Git blob")

    payload = pyreadr.read_r(str(DATA_PATH))
    if "euMTPL" not in payload:
        raise RuntimeError(f"Expected euMTPL object; found {sorted(str(k) for k in payload)}")
    frame = payload["euMTPL"]
    actual_columns = list(frame.columns)
    registered_columns = list(prereg["data_contract_for_future_execution"]["required_columns_exactly"])

    # This is deliberately an incident recorder, not a compatibility mapper.
    # Do not inspect outcome values, year labels, row summaries or model scores.
    if actual_columns == registered_columns:
        raise RuntimeError("Expected the already-observed schema mismatch, but schemas now match")

    actual_set = set(actual_columns)
    registered_set = set(registered_columns)
    incident = {
        "status": "V58_FAIL_CLOSED_SOURCE_SCHEMA_PREREGISTRATION_MISMATCH",
        "v57_protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "v57_main_sha": EXPECTED_V57_MAIN_SHA,
        "source_identity": {
            "dataset": "euMTPL",
            "source_commit": prereg["source"]["upstream_commit"],
            "git_blob_sha1": source["git_blob_sha1"],
            "file_sha256": source["file_sha256"],
            "file_bytes": source["file_bytes"],
            "binary_identity_passed_before_decode": True,
        },
        "registered_schema": registered_columns,
        "decoded_schema": actual_columns,
        "registered_only_columns": sorted(registered_set - actual_set),
        "decoded_only_columns": sorted(actual_set - registered_set),
        "same_column_set": registered_set == actual_set,
        "same_column_order": actual_columns == registered_columns,
        "observed_mismatch": {
            "registered_forfait_fields": ["cost_fcd", "num_fcd"],
            "decoded_forfait_fields": ["cost_fcg", "num_fcg"],
            "column_order_also_differs": True,
        },
        "access_boundary": {
            "binary_downloaded": True,
            "r_object_decoded": True,
            "row_level_dataset_access_occurred": True,
            "outcome_values_inspected": False,
            "year_values_inspected": False,
            "row_level_summary_computed": False,
            "model_fit_executed": False,
            "calibration_executed": False,
            "locked_test_performance_metrics_computed": False,
            "registered_gate_evaluated": False,
        },
        "governance": {
            "confirmatory_external_temporal_evidence_created": False,
            "euMTPL_still_eligible_as_fresh_confirmatory_dataset": False,
            "post_access_schema_amendment_used_for_confirmatory_claim": False,
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "promotion_review_status": "NOT_OPEN",
            "customer_pricing_authorised": False,
            "committee_gate_pass_count": 5,
            "committee_gate_count": 8,
            "required_next_step": "REGISTER_ANOTHER_FRESH_EXTERNAL_DATASET_OR_USE_EUMTPL_ONLY_AS_EXPLICITLY_NON_CONFIRMATORY_DIAGNOSTIC",
        },
        "interpretation": "The pinned euMTPL binary was authentic, but its decoded schema did not satisfy the exact v0.57 preregistered source contract. Execution stopped before outcome-value inspection, temporal-label inspection, model fitting, calibration or performance scoring. The dataset has nevertheless been row-level decoded and is therefore not treated as fresh confirmatory evidence after this incident."
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(incident, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(incident, indent=2))


if __name__ == "__main__":
    main()
