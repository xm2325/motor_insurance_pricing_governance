from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from build_deployment_bundle_v21 import canonicalise_features, records_from_frame
from deployment.bundle import ShadowModelBundle
from deployment.outcome_monitoring import (
    deterministic_exposure_maturity_mask,
    outcome_performance_snapshot,
    segment_calibration_snapshot,
)
from run_spanish_oot_2024 import load_data


BUNDLE_DIR = Path("deployment_artifacts")
OUTDIR = Path("results_v31")
EXPECTED_OOT = Path("action_results/spanish_oot_2024/oot_2024_summary.json")
BATCH_SIZE = 10_000
EARLY_EXPOSURE_FRACTION = 0.60
MINIMUM_MATURE_EXPOSURE_FRACTION = 0.95


def _score_2024(bundle: ShadowModelBundle, feature_frame) -> dict[str, np.ndarray]:
    collected = {
        "reference_frequency": [],
        "challenger_frequency": [],
        "reference_pure_premium": [],
        "challenger_pure_premium": [],
    }
    for start in range(0, len(feature_frame), BATCH_SIZE):
        stop = min(start + BATCH_SIZE, len(feature_frame))
        records = records_from_frame(feature_frame.iloc[start:stop])
        scores = bundle.score_records(records)
        for row in scores:
            for field in collected:
                collected[field].append(float(row[field]))
    return {field: np.asarray(values, dtype=float) for field, values in collected.items()}


def _historical_reconciliation(mature: dict) -> dict:
    if not EXPECTED_OOT.is_file():
        raise FileNotFoundError(EXPECTED_OOT)
    expected = json.loads(EXPECTED_OOT.read_text(encoding="utf-8"))

    freq = {row["model"]: row for row in expected["frequency_results"]}
    loss = {row["model"]: row for row in expected["pure_premium_results"]}

    pairs = {
        "reference_frequency_poisson_deviance": (
            mature["frequency"]["reference"]["poisson_deviance"],
            freq["Poisson_GLM"]["test_locked_poisson_deviance"],
        ),
        "challenger_frequency_poisson_deviance": (
            mature["frequency"]["challenger"]["poisson_deviance"],
            freq["XGBoost_Poisson"]["test_locked_poisson_deviance"],
        ),
        "reference_frequency_calibration": (
            mature["frequency"]["reference"]["calibration_ratio_pred_over_actual"],
            freq["Poisson_GLM"]["test_locked_calibration_ratio_pred_over_actual"],
        ),
        "challenger_frequency_calibration": (
            mature["frequency"]["challenger"]["calibration_ratio_pred_over_actual"],
            freq["XGBoost_Poisson"]["test_locked_calibration_ratio_pred_over_actual"],
        ),
        "reference_pure_premium_tweedie_deviance": (
            mature["pure_premium"]["reference"]["tweedie_deviance_p1_5"],
            loss["Tweedie_GLM"]["test_locked_tweedie_deviance_p1_5"],
        ),
        "challenger_pure_premium_tweedie_deviance": (
            mature["pure_premium"]["challenger"]["tweedie_deviance_p1_5"],
            loss["XGBoost_Tweedie"]["test_locked_tweedie_deviance_p1_5"],
        ),
        "reference_pure_premium_calibration": (
            mature["pure_premium"]["reference"]["calibration_ratio_pred_over_actual"],
            loss["Tweedie_GLM"]["test_locked_calibration_ratio_pred_over_actual"],
        ),
        "challenger_pure_premium_calibration": (
            mature["pure_premium"]["challenger"]["calibration_ratio_pred_over_actual"],
            loss["XGBoost_Tweedie"]["test_locked_calibration_ratio_pred_over_actual"],
        ),
    }

    rows = {}
    max_relative_difference = 0.0
    for name, (observed, historical) in pairs.items():
        absolute = abs(float(observed) - float(historical))
        relative = absolute / max(abs(float(historical)), 1e-12)
        max_relative_difference = max(max_relative_difference, relative)
        rows[name] = {
            "current_bundle_outcome_replay": float(observed),
            "historical_locked_oot": float(historical),
            "absolute_difference": float(absolute),
            "relative_difference": float(relative),
        }

    tolerance = 0.002
    if max_relative_difference > tolerance:
        raise AssertionError(
            "Fresh-bundle outcome replay moved too far from the registered 2024 OOT evidence: "
            f"{max_relative_difference:.6f} > {tolerance:.6f}"
        )
    return {
        "status": "HISTORICAL_OOT_RECONCILIATION_PASS",
        "checks": rows,
        "max_relative_difference": float(max_relative_difference),
        "relative_tolerance": tolerance,
        "interpretation": (
            "Fresh training/build replay against the same historical 2024 outcomes. "
            "This is a regression diagnostic, not an exact same-fit serialization claim."
        ),
    }


def _write_segment_csv(rows: list[dict]) -> None:
    path = OUTDIR / "business_type_calibration.csv"
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    frame = load_data()
    test = frame[frame["year"] == 2024].copy().reset_index(drop=True)
    if len(test) == 0:
        raise RuntimeError("No 2024 rows available for outcome replay")

    bundle = ShadowModelBundle.load(BUNDLE_DIR)
    if bundle.manifest.get("governance_status") != "HOLD_SHADOW_ONLY":
        raise RuntimeError("v0.31 must run only against HOLD_SHADOW_ONLY bundles")
    if bundle.bundle_integrity is None:
        raise RuntimeError("v0.31 requires a v0.27 content-addressed bundle lock")

    features = canonicalise_features(test)
    predictions = _score_2024(bundle, features)

    exposure = test["total_exposure"].to_numpy(float)
    claims = test["total_claims"].to_numpy(float)
    incurred = test["total_incurred"].to_numpy(float)
    keys = [
        f"2024|{insured_id}|{idx}"
        for idx, insured_id in enumerate(test["insured_id"].astype(str).tolist())
    ]

    early_mask = deterministic_exposure_maturity_mask(
        keys,
        exposure,
        target_exposure_fraction=EARLY_EXPOSURE_FRACTION,
    )
    mature_mask = np.ones(len(test), dtype=bool)

    early = outcome_performance_snapshot(
        claims,
        incurred,
        exposure,
        predictions,
        early_mask,
        minimum_mature_exposure_fraction=MINIMUM_MATURE_EXPOSURE_FRACTION,
    )
    mature = outcome_performance_snapshot(
        claims,
        incurred,
        exposure,
        predictions,
        mature_mask,
        minimum_mature_exposure_fraction=MINIMUM_MATURE_EXPOSURE_FRACTION,
    )

    if early["status"] != "WAIT_FOR_OUTCOME_MATURITY":
        raise AssertionError("Early partial-outcome replay must not evaluate performance")
    if mature["status"] != "OUTCOME_PERFORMANCE_EVALUATED":
        raise AssertionError("Fully mature 2024 replay must evaluate performance")

    segment_rows = segment_calibration_snapshot(
        test["business_type"].fillna("MISSING").astype(str).tolist(),
        claims,
        incurred,
        exposure,
        predictions,
        mature_mask,
        minimum_mature_exposure_fraction=MINIMUM_MATURE_EXPOSURE_FRACTION,
    )
    if not segment_rows:
        raise AssertionError("Expected mature business_type calibration evidence")

    reconciliation = _historical_reconciliation(mature)
    _write_segment_csv(segment_rows)

    summary = {
        "status": "V31_OUTCOME_MATURITY_REVIEW_PASS",
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "replay_year": 2024,
            "rows": int(len(test)),
            "outcomes": ["total_claims", "total_incurred"],
            "outcome_values_are_real": True,
            "label_arrival_timing_is_synthetic": True,
        },
        "bundle": {
            "model_version": bundle.manifest.get("model_version"),
            "bundle_contract_version": bundle.manifest.get("bundle_contract_version"),
            "governance_status": bundle.manifest.get("governance_status"),
            "integrity_status": getattr(bundle.bundle_integrity, "status", None),
        },
        "maturity_policy": {
            "early_replay_target_exposure_fraction": EARLY_EXPOSURE_FRACTION,
            "minimum_mature_exposure_fraction": MINIMUM_MATURE_EXPOSURE_FRACTION,
            "early_status": early["status"],
            "mature_status": mature["status"],
        },
        "early_partial_outcomes": early,
        "fully_mature_outcomes": mature,
        "business_type_calibration": segment_rows,
        "historical_oot_reconciliation": reconciliation,
        "review_resolution": {
            "v23_recommended_action": "REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION",
            "v31_action": "EXECUTE_LABEL_BASED_SEGMENT_CALIBRATION_REVIEW",
            "automatic_serving_change": False,
            "automatic_pricing_change": False,
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
        },
        "interpretation_boundary": (
            "This replays fully observed historical 2024 outcomes through a freshly rebuilt "
            "shadow bundle. The outcomes are real, but the partial-maturity timing is synthetic. "
            "The exercise validates delayed-label monitoring and review controls; it is not "
            "post-deployment production evidence and does not establish transfer to FIRST CENTRAL "
            "or the UK motor market."
        ),
    }

    (OUTDIR / "outcome_review_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
