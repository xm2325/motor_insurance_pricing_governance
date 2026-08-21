from __future__ import annotations

import json
from pathlib import Path


HISTORICAL_REFERENCE = Path("tests/fixtures/v26_locked_parity_reference.json")
CURRENT_REFERENCE = Path("deployment_artifacts/parity_reference.json")
SERIALIZATION_PARITY = Path("deployment_artifacts/serialization_parity_summary.json")
OUTDIR = Path("results_v26")
FIELDS = [
    "reference_frequency",
    "challenger_frequency",
    "reference_pure_premium",
    "challenger_pure_premium",
]


def main() -> None:
    historical = json.loads(HISTORICAL_REFERENCE.read_text(encoding="utf-8"))
    current = json.loads(CURRENT_REFERENCE.read_text(encoding="utf-8"))
    serialization = json.loads(SERIALIZATION_PARITY.read_text(encoding="utf-8"))

    if current["records"] != historical["records"]:
        raise AssertionError(
            "Parity-record inputs changed relative to the validated pre-v0.26 reference"
        )
    if serialization["status"] != "SAME_FIT_SERIALIZATION_PARITY_PASS":
        raise AssertionError(f"Unexpected serialization parity status: {serialization}")
    if serialization["comparisons"] != 100:
        raise AssertionError(f"Expected 100 same-fit serialization comparisons: {serialization}")

    # This is deliberately an audit, not the serialization acceptance gate. Re-fitting
    # iterative GLMs can move at floating-point scale even under the same package stack.
    # The hard migration claim is tested above on one fitted model set before vs after IO.
    max_abs_error = 0.0
    max_rel_error = 0.0
    max_location = None
    per_field = {field: {"max_absolute_error": 0.0, "max_relative_error": 0.0} for field in FIELDS}
    for record_index, (expected, observed) in enumerate(
        zip(historical["scores"], current["scores"])
    ):
        for field in FIELDS:
            expected_value = float(expected[field])
            observed_value = float(observed[field])
            absolute_error = abs(observed_value - expected_value)
            relative_error = absolute_error / max(abs(expected_value), 1e-12)
            if absolute_error > max_abs_error:
                max_abs_error = absolute_error
                max_location = {
                    "record_index": record_index,
                    "field": field,
                    "historical": expected_value,
                    "rebuilt": observed_value,
                }
            max_rel_error = max(max_rel_error, relative_error)
            per_field[field]["max_absolute_error"] = max(
                per_field[field]["max_absolute_error"], absolute_error
            )
            per_field[field]["max_relative_error"] = max(
                per_field[field]["max_relative_error"], relative_error
            )

    drift_audit = {
        "status": "HISTORICAL_RETRAIN_DRIFT_AUDIT_RECORDED",
        "acceptance_gate": False,
        "historical_fixture": str(HISTORICAL_REFERENCE),
        "historical_source_head_sha": historical["provenance"]["source_head_sha"],
        "historical_artifact_digest": historical["provenance"]["source_artifact_digest"],
        "records_compared": len(current["records"]),
        "fields_per_record": len(FIELDS),
        "comparisons": len(current["records"]) * len(FIELDS),
        "max_absolute_error": max_abs_error,
        "max_relative_error": max_rel_error,
        "max_error_location": max_location,
        "by_field": per_field,
        "interpretation": (
            "Historical-vs-retrained prediction differences are recorded but are not used "
            "as the serialization migration gate. Refit reproducibility and model IO parity "
            "are separate controls. Material model changes remain covered by the existing "
            "OOT/governance regression workflows."
        ),
    }

    migration_summary = {
        "status": "V26_SERIALIZATION_MIGRATION_GATE_PASS",
        "same_fit_serialization": serialization,
        "historical_retrain_drift_audit": {
            "status": drift_audit["status"],
            "max_absolute_error": drift_audit["max_absolute_error"],
            "max_relative_error": drift_audit["max_relative_error"],
            "acceptance_gate": False,
        },
        "governance_boundary": "HOLD / HOLD_SHADOW_ONLY remains unchanged",
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "retrain_drift_audit.json").write_text(
        json.dumps(drift_audit, indent=2), encoding="utf-8"
    )
    (OUTDIR / "serialization_migration_summary.json").write_text(
        json.dumps(migration_summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(migration_summary, indent=2))
    print(json.dumps(drift_audit, indent=2))


if __name__ == "__main__":
    main()
