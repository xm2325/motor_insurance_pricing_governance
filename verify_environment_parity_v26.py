from __future__ import annotations

import json
from pathlib import Path

import numpy as np


REFERENCE = Path("tests/fixtures/v26_locked_parity_reference.json")
CURRENT = Path("deployment_artifacts/parity_reference.json")
OUTDIR = Path("results_v26")
FIELDS = [
    "reference_frequency",
    "challenger_frequency",
    "reference_pure_premium",
    "challenger_pure_premium",
]


def main() -> None:
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    current = json.loads(CURRENT.read_text(encoding="utf-8"))

    if current["records"] != reference["records"]:
        raise AssertionError(
            "Parity-record inputs changed relative to the validated pre-v0.26 reference"
        )
    if len(current["scores"]) != len(reference["scores"]):
        raise AssertionError("Parity score count changed")

    max_abs_error = 0.0
    max_rel_error = 0.0
    per_field = {field: 0.0 for field in FIELDS}
    for record_index, (expected, observed) in enumerate(
        zip(reference["scores"], current["scores"])
    ):
        for field in FIELDS:
            expected_value = float(expected[field])
            observed_value = float(observed[field])
            absolute_error = abs(observed_value - expected_value)
            relative_error = absolute_error / max(abs(expected_value), 1e-12)
            max_abs_error = max(max_abs_error, absolute_error)
            max_rel_error = max(max_rel_error, relative_error)
            per_field[field] = max(per_field[field], absolute_error)
            if not np.isclose(observed_value, expected_value, rtol=1e-10, atol=1e-10):
                raise AssertionError(
                    f"v0.26 dependency alignment changed locked prediction: "
                    f"record={record_index} field={field} expected={expected_value} "
                    f"observed={observed_value} abs_error={absolute_error}"
                )

    result = {
        "status": "V26_FROZEN_PARITY_PASS",
        "reference_fixture": str(REFERENCE),
        "reference_source_head_sha": reference["provenance"]["source_head_sha"],
        "reference_artifact_digest": reference["provenance"]["source_artifact_digest"],
        "records_tested": len(current["records"]),
        "fields_per_record": len(FIELDS),
        "comparisons": len(current["records"]) * len(FIELDS),
        "max_absolute_error": max_abs_error,
        "max_relative_error": max_rel_error,
        "max_absolute_error_by_field": per_field,
        "acceptance_tolerance": {"rtol": 1e-10, "atol": 1e-10},
        "interpretation": (
            "Dependency alignment is accepted only if it reproduces the frozen v0.25-era "
            "deployment scores. This gate does not change model-family approval."
        ),
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "frozen_parity_summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
