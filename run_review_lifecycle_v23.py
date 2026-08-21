from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from deployment.review import ReviewLifecycle

DEFAULT_SOURCE = Path("action_results/v22/monitoring_replay_summary.json")
OUTDIR = Path("results_v23")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_sequence(source: dict) -> dict:
    controller = ReviewLifecycle(open_after_breaches=2, close_after_green=2)
    baseline = source["baseline_2022"]
    temporal = source["temporal_2024"]
    stress = source["synthetic_stress"]

    windows = [
        ("2022_control", baseline),
        ("2024_temporal_1", temporal),
        ("2024_temporal_2", temporal),
        ("2022_recovery_1", baseline),
        ("2022_recovery_2", baseline),
        ("synthetic_stress_1", stress),
        ("synthetic_stress_2", stress),
    ]
    events = [controller.observe(snapshot, label) for label, snapshot in windows]

    expected_states = [
        "HEALTHY",
        "WATCH",
        "REVIEW_REQUIRED",
        "RECOVERING",
        "HEALTHY",
        "WATCH",
        "REVIEW_REQUIRED",
    ]
    states = [event["state"] for event in events]
    if states != expected_states:
        raise RuntimeError(f"Unexpected review lifecycle: {states}")

    temporal_review = events[2]
    if temporal_review["recommended_action"] != "REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION":
        raise RuntimeError(f"Unexpected temporal review action: {temporal_review}")
    if temporal_review["active_alerts"] != ["feature_drift"]:
        raise RuntimeError(f"Expected feature-drift-only temporal review: {temporal_review}")

    stress_review = events[-1]
    if stress_review["recommended_action"] != "INVESTIGATE_SERVING_DATA_AND_MODEL":
        raise RuntimeError(f"Unexpected stress review action: {stress_review}")

    first_review_id = temporal_review["review_id_after"]
    recovery_closed = events[4]["review_id_after"] is None
    second_review_id = stress_review["review_id_after"]
    if not first_review_id or not second_review_id or first_review_id == second_review_id:
        raise RuntimeError("Review IDs were not opened independently")
    if not recovery_closed:
        raise RuntimeError("Two green windows did not close the first review")

    return {
        "status": "success",
        "policy": {
            "open_after_consecutive_breach_windows": 2,
            "close_after_consecutive_green_windows": 2,
            "automatic_model_or_pricing_change": False,
        },
        "interpretation": (
            "Lifecycle replay only. The 2024 windows reuse real aggregate temporal-monitoring "
            "evidence from v0.22; the final stress windows are synthetic. The controller makes "
            "review recommendations and does not change pricing, model approval, or serving state."
        ),
        "states": states,
        "temporal_review": {
            "review_id": first_review_id,
            "severity": temporal_review["severity"],
            "action": temporal_review["recommended_action"],
            "active_alerts": temporal_review["active_alerts"],
            "max_feature_psi": temporal_review["evidence"]["max_feature_psi"],
            "max_feature_psi_feature": temporal_review["evidence"]["max_feature_psi_feature"],
            "frequency_abs_log_ratio_p95": temporal_review["evidence"]["frequency_abs_log_ratio_p95"],
            "pure_premium_abs_log_ratio_p95": temporal_review["evidence"]["pure_premium_abs_log_ratio_p95"],
        },
        "recovery": {
            "closed_after_two_green_windows": recovery_closed,
            "state_after_recovery": events[4]["state"],
        },
        "synthetic_stress_review": {
            "review_id": second_review_id,
            "severity": stress_review["severity"],
            "action": stress_review["recommended_action"],
            "active_alerts": stress_review["active_alerts"],
        },
        "aggregate_only_evidence": all(
            event["evidence"]["privacy_boundary"] == "aggregate_non_pii_only" for event in events
        ),
        "lifecycle": controller.snapshot(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    first = run_sequence(source)
    second = run_sequence(source)
    if first != second:
        raise RuntimeError("Review lifecycle is not deterministic for identical monitoring evidence")

    first["source_monitoring_evidence"] = str(args.source)
    first["source_monitoring_sha256"] = file_sha256(args.source)
    first["deterministic_replay"] = True

    OUTDIR.mkdir(parents=True, exist_ok=True)
    path = OUTDIR / "review_lifecycle_summary.json"
    path.write_text(json.dumps(first, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": first["status"],
        "states": first["states"],
        "temporal_review": first["temporal_review"],
        "synthetic_stress_review": first["synthetic_stress_review"],
        "deterministic_replay": first["deterministic_replay"],
    }, indent=2))


if __name__ == "__main__":
    main()
