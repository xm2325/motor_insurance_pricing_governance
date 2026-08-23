from __future__ import annotations

import argparse
import json
from pathlib import Path

from governance.external_validation_firewall_v39 import load_ledger, validate_ledger


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results_v39" / "external_validation_firewall_summary.json"


def build_summary() -> dict:
    ledger = load_ledger()
    validate_ledger(ledger)
    australian = ledger["datasets"]["ausprivauto0405"]
    firewall = ledger["new_external_dataset_firewall"]
    return {
        "status": "V39_EXTERNAL_VALIDATION_FIREWALL_PASS",
        "consumed_external_dataset": {
            "dataset_id": "ausprivauto0405",
            "source_file_sha256": australian["source_file_sha256"],
            "rows": australian["rows"],
            "locked_test_rows": australian["locked_test_rows"],
            "initial_role": australian["initial_role"],
            "current_role": australian["current_role"],
            "independent_external_validation_available": australian["independent_external_validation_available"],
            "candidate_selection_allowed": australian["candidate_selection_allowed"],
            "material_use_event_count": len(australian["material_use_events"]),
            "material_use_event_ids": [event["id"] for event in australian["material_use_events"]],
            "allowed_future_purposes": australian["allowed_future_purposes"],
            "forbidden_future_purposes": australian["forbidden_future_purposes"],
        },
        "new_external_dataset_firewall": firewall,
        "decision": ledger["decision"],
        "interpretation": (
            "The Australian portfolio was independent at its preregistered first external execution in v0.37, "
            "but its train/calibration/test outcomes have now been used and its locked test has been repeatedly "
            "reproduced for numerical audit. It therefore cannot supply fresh candidate-selection or independent "
            "confirmation evidence. A new external dataset or period must be preregistered on main before row-level access."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = build_summary()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
