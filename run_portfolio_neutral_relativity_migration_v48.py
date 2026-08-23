from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from deployment.contracts import FEATURES, feature_contract_hash
from run_frozen_model_disagreement_attribution_v47 import (
    read_training_and_calibration,
    read_2024_features_only,
    fit_frozen_models,
    score_pair,
    canonicalise_features,
    segment_frame,
    weighted_mean,
    weighted_quantile,
)
from run_spanish_oot_2024 import DATA_PATH

OUTDIR = Path("results_v48")

# Fixed project diagnostic bins. They are not insurer, actuarial, commercial or
# regulatory thresholds and are frozen before this v0.48 result is observed.
CHANGE_BANDS = [
    {"id": "LT_MINUS_20", "label": "< -20%", "low": None, "high": -0.20},
    {"id": "MINUS_20_TO_MINUS_10", "label": "[-20%, -10%)", "low": -0.20, "high": -0.10},
    {"id": "MINUS_10_TO_MINUS_5", "label": "[-10%, -5%)", "low": -0.10, "high": -0.05},
    {"id": "WITHIN_5", "label": "[-5%, +5%]", "low": -0.05, "high": 0.05},
    {"id": "PLUS_5_TO_PLUS_10", "label": "(+5%, +10%]", "low": 0.05, "high": 0.10},
    {"id": "PLUS_10_TO_PLUS_20", "label": "(+10%, +20%]", "low": 0.10, "high": 0.20},
    {"id": "GT_PLUS_20", "label": "> +20%", "low": 0.20, "high": None},
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def portfolio_neutralise(reference: np.ndarray, challenger: np.ndarray, exposure: np.ndarray):
    # XGBoost predictions can arrive as float32. Cast the three arrays before
    # aggregate normalisation so the portfolio-neutral identity is not limited by
    # float32 multiplication/accumulation. This changes no fitted model score;
    # it only improves the precision of the aggregate-neutral diagnostic scale.
    reference64 = np.asarray(reference, dtype=np.float64)
    challenger64 = np.asarray(challenger, dtype=np.float64)
    exposure64 = np.asarray(exposure, dtype=np.float64)
    reference_total = float(np.sum(reference64 * exposure64, dtype=np.float64))
    challenger_total = float(np.sum(challenger64 * exposure64, dtype=np.float64))
    if reference_total <= 0 or challenger_total <= 0:
        raise RuntimeError("Predicted technical-risk totals must be positive")
    neutral_scale = reference_total / challenger_total
    normalised_challenger = challenger64 * neutral_scale
    normalised_total = float(np.sum(normalised_challenger * exposure64, dtype=np.float64))
    return normalised_challenger, {
        "calculation_dtype": "float64",
        "reference_predicted_total": reference_total,
        "raw_challenger_predicted_total": challenger_total,
        "raw_challenger_total_over_reference": challenger_total / reference_total,
        "portfolio_neutral_scale_applied_to_challenger": neutral_scale,
        "normalised_challenger_predicted_total": normalised_total,
        "normalised_total_over_reference": normalised_total / reference_total,
        "absolute_total_difference_after_neutralisation": abs(normalised_total - reference_total),
    }


def band_id(change: np.ndarray) -> np.ndarray:
    out = np.empty(len(change), dtype=object)
    out[change < -0.20] = "LT_MINUS_20"
    out[(change >= -0.20) & (change < -0.10)] = "MINUS_20_TO_MINUS_10"
    out[(change >= -0.10) & (change < -0.05)] = "MINUS_10_TO_MINUS_5"
    out[(change >= -0.05) & (change <= 0.05)] = "WITHIN_5"
    out[(change > 0.05) & (change <= 0.10)] = "PLUS_5_TO_PLUS_10"
    out[(change > 0.10) & (change <= 0.20)] = "PLUS_10_TO_PLUS_20"
    out[change > 0.20] = "GT_PLUS_20"
    if any(v is None for v in out):
        raise RuntimeError("Unassigned relativity migration band")
    return out


def distribution_summary(change: np.ndarray, exposure: np.ndarray) -> dict:
    quantiles = {
        f"q{int(q * 100):02d}": weighted_quantile(change, exposure, q)
        for q in [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    }
    return {
        "exposure_weighted_mean_change": weighted_mean(change, exposure),
        "exposure_weighted_mean_absolute_change": weighted_mean(np.abs(change), exposure),
        "challenger_higher_exposure_share": weighted_mean((change > 0).astype(float), exposure),
        "challenger_lower_exposure_share": weighted_mean((change < 0).astype(float), exposure),
        "absolute_change_gt_5pct_exposure_share": weighted_mean((np.abs(change) > 0.05).astype(float), exposure),
        "absolute_change_gt_10pct_exposure_share": weighted_mean((np.abs(change) > 0.10).astype(float), exposure),
        "absolute_change_gt_20pct_exposure_share": weighted_mean((np.abs(change) > 0.20).astype(float), exposure),
        "quantiles": quantiles,
    }


def migration_bands(target: str, change: np.ndarray, exposure: np.ndarray) -> list[dict]:
    ids = band_id(change)
    total_exposure = float(np.sum(exposure))
    rows = []
    for spec in CHANGE_BANDS:
        mask = ids == spec["id"]
        band_exposure = float(np.sum(exposure[mask]))
        rows.append({
            "target": target,
            "band_id": spec["id"],
            "band_label": spec["label"],
            "low": spec["low"],
            "high": spec["high"],
            "rows": int(np.sum(mask)),
            "exposure": band_exposure,
            "exposure_share": band_exposure / total_exposure,
        })
    return rows


def segment_migration(
    features: pd.DataFrame,
    exposure: np.ndarray,
    target_values: dict[str, dict[str, np.ndarray]],
) -> pd.DataFrame:
    groups = segment_frame(features)
    total_exposure = float(np.sum(exposure))
    rows = []
    for dimension in groups.columns:
        for group in sorted(groups[dimension].dropna().unique()):
            mask = (groups[dimension] == group).to_numpy()
            w = exposure[mask]
            if len(w) == 0 or float(np.sum(w)) <= 0:
                continue
            row = {
                "dimension": dimension,
                "group": str(group),
                "rows": int(np.sum(mask)),
                "exposure": float(np.sum(w)),
                "exposure_share": float(np.sum(w) / total_exposure),
            }
            for target, values in target_values.items():
                ref = values["reference"][mask]
                normalised = values["normalised_challenger"][mask]
                change = values["change"][mask]
                ref_total = float(np.sum(ref * w))
                ch_total = float(np.sum(normalised * w))
                row[f"{target}_segment_total_relativity_change"] = ch_total / ref_total - 1.0
                row[f"{target}_mean_absolute_change"] = weighted_mean(np.abs(change), w)
                row[f"{target}_challenger_higher_exposure_share"] = weighted_mean((change > 0).astype(float), w)
                row[f"{target}_abs_change_gt_10pct_exposure_share"] = weighted_mean((np.abs(change) > 0.10).astype(float), w)
                row[f"{target}_abs_change_gt_20pct_exposure_share"] = weighted_mean((np.abs(change) > 0.20).astype(float), w)
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["dimension", "exposure_share"], ascending=[True, False])


def main() -> None:
    OUTDIR.mkdir(exist_ok=True)

    train, calibration = read_training_and_calibration()
    test = read_2024_features_only()
    models, locked_scales, _ = fit_frozen_models(train, calibration)

    x_test = canonicalise_features(test)
    exposure = test["total_exposure"].to_numpy(float)
    target_values: dict[str, dict[str, np.ndarray]] = {}
    target_summaries = {}
    band_rows = []

    for target in ["frequency", "pure_premium"]:
        reference, challenger = score_pair(x_test, models, locked_scales, target)
        normalised, neutralisation = portfolio_neutralise(reference, challenger, exposure)
        ratio = normalised / np.asarray(reference, dtype=np.float64)
        change = ratio - 1.0
        target_values[target] = {
            "reference": np.asarray(reference, dtype=np.float64),
            "raw_challenger": np.asarray(challenger, dtype=np.float64),
            "normalised_challenger": normalised,
            "change": change,
        }
        distribution = distribution_summary(change, exposure)
        bands = migration_bands(target, change, exposure)
        band_rows.extend(bands)
        target_summaries[target] = {
            "portfolio_neutralisation": neutralisation,
            "relativity_change_distribution": distribution,
            "migration_bands": bands,
        }

    segments = segment_migration(x_test, exposure, target_values)

    summary = {
        "status": "V48_PORTFOLIO_NEUTRAL_RELATIVITY_MIGRATION_COMPLETE",
        "analysis_role": "POST_HOC_LABEL_FREE_TECHNICAL_RELATIVITY_DIAGNOSTIC",
        "validation_role": "CONSUMED_RETROSPECTIVE_VALIDATION_DIAGNOSTIC_ONLY",
        "candidate_selection_allowed": False,
        "model_or_calibration_parameter_change": False,
        "promotion_evidence_created": False,
        "customer_pricing_authorised": False,
        "actual_customer_premium_used": False,
        "commercial_uplift_claimed": False,
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "source_file_sha256": sha256_file(DATA_PATH),
            "training_year": 2022,
            "calibration_year": 2023,
            "diagnostic_year": 2024,
            "diagnostic_rows": int(len(test)),
            "diagnostic_exposure": float(np.sum(exposure)),
            "diagnostic_2024_outcome_labels_read": False,
            "full_positive_exposure_population_used": True,
        },
        "frozen_model_definition": {
            "source": "build_deployment_bundle_v21.py::model_definitions via v0.47 helper",
            "feature_contract_hash": feature_contract_hash(),
            "locked_calibration_scales": locked_scales,
            "frozen_tweedie_glm_convergence_limitation_inherited": True,
        },
        "portfolio_neutralisation": {
            "formula": "normalised_challenger = raw_challenger * sum(reference * exposure) / sum(raw_challenger * exposure)",
            "calculation_dtype": "float64",
            "purpose": "Force the challenger and reference to the same aggregate predicted technical-risk total before measuring redistribution across policies and segments.",
            "uses_2024_outcomes": False,
            "uses_actual_premium": False,
        },
        "fixed_change_bands": CHANGE_BANDS,
        "targets": target_summaries,
        "segment_dimensions": ["business_type", "policy_type", "payment_frequency", "driver_age_band"],
        "interpretation_boundary": {
            "technical_risk_score_only": True,
            "actual_premium_or_quote": False,
            "pricing_action_or_rate_change": False,
            "expense_commission_reinsurance_profit_tax_demand_components_included": False,
            "fairness_or_regulatory_conclusion_claimed": False,
            "causal_interpretation_claimed": False,
            "interpretation": "The result measures how two frozen technical risk-score families redistribute relative indications after aggregate predicted totals are forced equal. It is not a customer premium, quote, rate filing, commercial impact estimate or pricing recommendation.",
        },
        "persisted_row_level_data": False,
    }

    pd.DataFrame(band_rows).to_csv(OUTDIR / "relativity_migration_bands_v48.csv", index=False)
    segments.to_csv(OUTDIR / "segment_relativity_migration_v48.csv", index=False)
    (OUTDIR / "portfolio_neutral_relativity_summary_v48.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "status": summary["status"],
        "diagnostic_rows": len(test),
        "frequency": target_summaries["frequency"],
        "pure_premium": target_summaries["pure_premium"],
    }, indent=2))


if __name__ == "__main__":
    main()
