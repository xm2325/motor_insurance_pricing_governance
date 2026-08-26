from __future__ import annotations

import json
from pathlib import Path

import pyreadr

from validate_prospective_request_registration_v61 import canonical_sha256, validate

REGISTRATION = Path("governance/prospective_request_registration_v61.json")
V61_STATUS = Path("action_results/v61/origin/32793349122/ACTION_V61_STATUS.json")
SOURCE_AUDIT = Path("results_v62/pricing_game_source_binary_audit.json")
DATA_PATH = Path("data_external_v62/pg15training.rda")
OUT = Path("results_v62/pricing_game_s1_schema_incident_v62.json")
EXPECTED_PROTOCOL_SHA256 = "80533141f88b042a02618d609f77d355f32c9d81ce53569aece27aab207a58c9"
EXPECTED_V61_MAIN_EVIDENCE_COMMIT = "9a4520d9647eb7a1c51ff1d8e49345fd783def10"
EXPECTED_SOURCE_BLOB = "9e670d214c05a7454d558ab32de5df96a6b0aba6"


def main() -> None:
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    validate(registration)
    digest = canonical_sha256(registration)
    if digest != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError(f"v0.61 registration digest changed: {digest}")

    parent = json.loads(V61_STATUS.read_text(encoding="utf-8"))
    if parent["status"] != "success":
        raise RuntimeError("v0.61 immutable registration is not successful")
    if parent["protocol_canonical_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.61 immutable protocol digest changed")
    if parent["request_id"] != "MCR-XGB-MOTOR-002":
        raise RuntimeError("unexpected prospective request id")
    if parent["request_lifecycle"] != "REGISTERED_SEALED_BEFORE_S1":
        raise RuntimeError("v0.61 lifecycle does not match the pre-S1 lock")

    source = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
    if source["status"] != "V62_PINNED_PG15TRAINING_BINARY_VERIFIED_BEFORE_DECODE":
        raise RuntimeError("S1 binary identity was not verified before decode")
    if source["git_blob_sha1"] != EXPECTED_SOURCE_BLOB:
        raise RuntimeError("S1 binary Git blob does not match registration")

    payload = pyreadr.read_r(str(DATA_PATH))
    if "pg15training" not in payload:
        raise RuntimeError(f"Expected pg15training object; found {sorted(str(k) for k in payload)}")
    frame = payload["pg15training"]

    # Deliberately inspect schema only. Do not access PolNum, CalYear, exposure,
    # outcomes, rating values, row summaries, or model scores after a mismatch.
    actual_columns = list(frame.columns)
    registered_columns = list(registration["sources"]["S1_TEMPORAL_QUALIFICATION"]["required_columns"])
    actual_set = set(actual_columns)
    registered_set = set(registered_columns)

    if actual_set == registered_set:
        raise RuntimeError("Expected the already-observed S1 semantic schema mismatch, but column sets now match")

    registered_only = sorted(registered_set - actual_set)
    decoded_only = sorted(actual_set - registered_set)
    if registered_only != ["Expdays"] or decoded_only != ["Exppdays"]:
        raise RuntimeError(
            "Observed S1 mismatch differs from the first legal access; refusing to reinterpret incident: "
            f"registered_only={registered_only}, decoded_only={decoded_only}"
        )

    activation = registration["activation"]
    if activation["failed_or_source_contract_incident_consumes_stage"] is not True:
        raise RuntimeError("v0.61 does not encode fail-closed stage consumption")
    if activation["source_substitution_after_stage_access_forbidden"] is not True:
        raise RuntimeError("v0.61 source-substitution prohibition changed")
    if activation["reserve_cannot_rescue_s1_or_s2_failure"] is not True:
        raise RuntimeError("v0.61 reserve rule changed")

    incident = {
        "status": "V62_FAIL_CLOSED_S1_SEMANTIC_SCHEMA_CONTRACT_INCIDENT",
        "request_id": "MCR-XGB-MOTOR-002",
        "stage": "S1_TEMPORAL_QUALIFICATION",
        "v61_protocol_canonical_sha256": EXPECTED_PROTOCOL_SHA256,
        "v61_main_evidence_commit": EXPECTED_V61_MAIN_EVIDENCE_COMMIT,
        "v61_main_run_id": parent["run_id"],
        "source_identity": {
            "dataset": "pg15training",
            "source_commit": source["source_commit"],
            "git_blob_sha1": source["git_blob_sha1"],
            "file_sha256": source["file_sha256"],
            "file_bytes": source["file_bytes"],
            "binary_identity_passed_before_decode": True,
        },
        "schema_contract": {
            "registered_required_columns": registered_columns,
            "decoded_columns": actual_columns,
            "registered_only_columns": registered_only,
            "decoded_only_columns": decoded_only,
            "same_column_set": False,
            "column_order_is_not_the_failure": True,
            "material_mismatch": "registered exposure field Expdays; decoded field Exppdays",
            "post_access_alias_or_protocol_amendment_used": False,
        },
        "access_boundary": {
            "binary_downloaded": True,
            "r_object_decoded": True,
            "row_level_source_access_occurred": True,
            "schema_names_inspected": True,
            "policy_id_values_inspected": False,
            "calendar_year_values_inspected": False,
            "exposure_values_inspected": False,
            "outcome_values_inspected": False,
            "rating_feature_values_inspected": False,
            "row_count_computed": False,
            "cross_year_filter_executed": False,
            "model_fit_executed": False,
            "calibration_executed": False,
            "performance_metrics_computed": False,
            "registered_gate_evaluated": False,
            "s2_accessed": False,
            "s3_accessed": False,
            "raw_data_persisted": False,
        },
        "request_lifecycle": {
            "s1_stage_consumed": True,
            "s1_pass_created": False,
            "s1_reproduction_authorised": False,
            "s2_open_authorised": False,
            "s3_open_authorised": False,
            "s2_remains_sealed": True,
            "s3_remains_sealed": True,
            "source_substitution_authorised": False,
            "reserve_rescue_authorised": False,
            "request_state": "TERMINAL_S1_SOURCE_CONTRACT_INCIDENT",
            "request_can_progress_under_v61": False,
        },
        "governance": {
            "fresh_temporal_model_evidence_created": False,
            "fresh_external_model_evidence_created": False,
            "committee_gate_credit_created": False,
            "historical_committee_gate_pass_count": 5,
            "historical_committee_gate_count": 8,
            "historical_model_family_decision": "HOLD",
            "historical_serving_status": "HOLD_SHADOW_ONLY",
            "historical_promotion_review_status": "NOT_OPEN",
            "customer_pricing_authorised": False,
        },
        "interpretation": (
            "The first legal opening of S1 authenticated the pinned pg15training binary, then failed the v0.61 "
            "semantic column-name contract because the registered exposure field was Expdays while the decoded "
            "object contains Exppdays. Execution stopped at schema inspection before policy/year values, exposure, "
            "outcomes, features, model fitting, calibration or registered metrics were accessed. Under the v0.61 "
            "anti-data-shopping lifecycle a source-contract incident consumes S1; S2 and S3 remain sealed and cannot "
            "rescue MCR-XGB-MOTOR-002."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(incident, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(incident, indent=2))


if __name__ == "__main__":
    main()
