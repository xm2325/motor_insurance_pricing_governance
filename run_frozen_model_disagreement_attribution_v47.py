from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_deployment_bundle_v21 import canonicalise_features, model_definitions
from deployment.contracts import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, feature_contract_hash
from run_spanish_oot_2024 import DATA_PATH, locked_scale

OUTDIR = Path("results_v47")
SEED = 20260823
DIAGNOSTIC_SAMPLE_SIZE = 20000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_training_and_calibration() -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = FEATURES + ["year", "total_exposure", "total_claims", "total_incurred"]
    frame = pd.read_csv(DATA_PATH, sep=";", usecols=cols, low_memory=False)
    for col in [*NUMERIC_FEATURES, "year", "total_exposure", "total_claims", "total_incurred"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    valid = (
        frame["year"].isin([2022, 2023])
        & frame["total_exposure"].notna()
        & (frame["total_exposure"] > 0)
        & frame["total_claims"].notna()
        & (frame["total_claims"] >= 0)
        & frame["total_incurred"].notna()
        & (frame["total_incurred"] >= 0)
    )
    frame = frame.loc[valid].copy()
    return (
        frame[frame["year"] == 2022].reset_index(drop=True),
        frame[frame["year"] == 2023].reset_index(drop=True),
    )


def read_2024_features_only() -> pd.DataFrame:
    # Deliberately excludes 2024 claim counts and incurred losses. This analysis is
    # a post-hoc model-disagreement diagnostic, not another outcome-based model gate.
    cols = FEATURES + ["year", "total_exposure"]
    frame = pd.read_csv(DATA_PATH, sep=";", usecols=cols, low_memory=False)
    for col in [*NUMERIC_FEATURES, "year", "total_exposure"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    valid = (
        (frame["year"] == 2024)
        & frame["total_exposure"].notna()
        & (frame["total_exposure"] > 0)
    )
    return frame.loc[valid].reset_index(drop=True)


def fit_frozen_models(train: pd.DataFrame, calibration: pd.DataFrame):
    x_train = canonicalise_features(train)
    x_cal = canonicalise_features(calibration)
    e_train = train["total_exposure"].to_numpy(float)
    e_cal = calibration["total_exposure"].to_numpy(float)
    targets_train = {
        "frequency": train["total_claims"].to_numpy(float) / e_train,
        "pure_premium": train["total_incurred"].to_numpy(float) / e_train,
    }
    actual_cal = {
        "frequency": calibration["total_claims"].to_numpy(float),
        "pure_premium": calibration["total_incurred"].to_numpy(float),
    }

    fitted = {}
    scales = {}
    for name, spec in model_definitions().items():
        model = spec["model"]
        target = spec["target"]
        model.fit(x_train, targets_train[target], model__sample_weight=e_train)
        pred_cal = np.clip(model.predict(x_cal), 1e-12, None)
        scales[name] = float(locked_scale(actual_cal[target], pred_cal, e_cal))
        fitted[name] = model
    return fitted, scales, x_train


def score_pair(frame: pd.DataFrame, models: dict, scales: dict, target: str) -> tuple[np.ndarray, np.ndarray]:
    if target == "frequency":
        ref_name, ch_name = "poisson_glm_frequency", "xgb_poisson_frequency"
    elif target == "pure_premium":
        ref_name, ch_name = "tweedie_glm_pure_premium", "xgb_tweedie_pure_premium"
    else:
        raise ValueError(target)
    ref = np.clip(models[ref_name].predict(frame), 1e-12, None) * scales[ref_name]
    ch = np.clip(models[ch_name].predict(frame), 1e-12, None) * scales[ch_name]
    return ref, ch


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(values * weights) / np.sum(weights))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cumulative = np.cumsum(w) - 0.5 * w
    cumulative = cumulative / np.sum(w)
    return float(np.interp(q, cumulative, v))


def disagreement_stats(log_ratio: np.ndarray, weights: np.ndarray) -> dict:
    return {
        "exposure_weighted_mean_log_challenger_over_reference": weighted_mean(log_ratio, weights),
        "exposure_weighted_mean_absolute_log_disagreement": weighted_mean(np.abs(log_ratio), weights),
        "exposure_weighted_q05_log_ratio": weighted_quantile(log_ratio, weights, 0.05),
        "exposure_weighted_median_log_ratio": weighted_quantile(log_ratio, weights, 0.50),
        "exposure_weighted_q95_log_ratio": weighted_quantile(log_ratio, weights, 0.95),
        "challenger_above_reference_exposure_share": weighted_mean((log_ratio > 0).astype(float), weights),
    }


def reference_values(x_train: pd.DataFrame) -> dict:
    refs = {}
    for col in NUMERIC_FEATURES:
        refs[col] = float(pd.to_numeric(x_train[col], errors="coerce").median())
    for col in CATEGORICAL_FEATURES:
        mode = x_train[col].dropna().astype(str).mode()
        if mode.empty:
            raise RuntimeError(f"No training mode for categorical feature {col}")
        refs[col] = str(mode.iloc[0])
    return refs


def diagnostic_sample(test: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    n = len(test)
    size = min(DIAGNOSTIC_SAMPLE_SIZE, n)
    rng = np.random.default_rng(SEED)
    indices = np.sort(rng.choice(n, size=size, replace=False))
    sampled = test.iloc[indices].reset_index(drop=True)
    return sampled, indices, sampled["total_exposure"].to_numpy(float)


def feature_attribution(
    x_sample: pd.DataFrame,
    weights: np.ndarray,
    models: dict,
    scales: dict,
    refs: dict,
) -> tuple[dict, pd.DataFrame]:
    summaries = {}
    rows = []
    for target in ["frequency", "pure_premium"]:
        ref_pred, ch_pred = score_pair(x_sample, models, scales, target)
        baseline = np.log(ch_pred / ref_pred)
        base_stats = disagreement_stats(baseline, weights)
        summaries[target] = {"baseline": base_stats, "features": {}}
        baseline_abs = base_stats["exposure_weighted_mean_absolute_log_disagreement"]

        for feature in FEATURES:
            counterfactual = x_sample.copy()
            counterfactual[feature] = refs[feature]
            ref_cf, ch_cf = score_pair(counterfactual, models, scales, target)
            cf_log = np.log(ch_cf / ref_cf)
            cf_stats = disagreement_stats(cf_log, weights)
            cf_abs = cf_stats["exposure_weighted_mean_absolute_log_disagreement"]
            reduction = baseline_abs - cf_abs
            share = reduction / baseline_abs if baseline_abs > 0 else 0.0
            sign_flip = weighted_mean((np.sign(baseline) != np.sign(cf_log)).astype(float), weights)
            item = {
                "reference_value": refs[feature],
                "counterfactual_mean_absolute_log_disagreement": cf_abs,
                "absolute_disagreement_reduction": reduction,
                "fraction_of_baseline_abs_disagreement_reduced": share,
                "weighted_sign_flip_rate": sign_flip,
                "interpretation": "Positive reduction means one-factor substitution to the 2022 training reference makes GLM and XGBoost scores more similar on this diagnostic sample. Effects are non-additive and non-causal.",
            }
            summaries[target]["features"][feature] = item
            rows.append({"target": target, "feature": feature, **item})

    frame = pd.DataFrame(rows).sort_values(
        ["target", "absolute_disagreement_reduction"], ascending=[True, False]
    )
    return summaries, frame


def segment_frame(x_sample: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=x_sample.index)
    for col in ["business_type", "policy_type", "payment_frequency"]:
        out[col] = x_sample[col].astype(str)
    age = pd.to_numeric(x_sample["driver_age"], errors="coerce")
    out["driver_age_band"] = pd.cut(
        age,
        bins=[-np.inf, 24, 34, 49, 64, np.inf],
        labels=["<25", "25-34", "35-49", "50-64", "65+"],
    ).astype(str)
    return out


def segment_disagreement(
    x_sample: pd.DataFrame,
    weights: np.ndarray,
    models: dict,
    scales: dict,
) -> pd.DataFrame:
    groups = segment_frame(x_sample)
    base = pd.DataFrame({"exposure": weights})
    for target in ["frequency", "pure_premium"]:
        ref_pred, ch_pred = score_pair(x_sample, models, scales, target)
        base[f"{target}_log_ratio"] = np.log(ch_pred / ref_pred)

    rows = []
    total_exposure = float(np.sum(weights))
    for dimension in groups.columns:
        for group in sorted(groups[dimension].dropna().unique()):
            mask = (groups[dimension] == group).to_numpy()
            w = weights[mask]
            if not len(w) or np.sum(w) <= 0:
                continue
            row = {
                "dimension": dimension,
                "group": str(group),
                "rows": int(np.sum(mask)),
                "exposure": float(np.sum(w)),
                "exposure_share": float(np.sum(w) / total_exposure),
            }
            for target in ["frequency", "pure_premium"]:
                lr = base.loc[mask, f"{target}_log_ratio"].to_numpy(float)
                row[f"{target}_mean_log_ratio"] = weighted_mean(lr, w)
                row[f"{target}_mean_abs_log_disagreement"] = weighted_mean(np.abs(lr), w)
                row[f"{target}_challenger_above_reference_share"] = weighted_mean((lr > 0).astype(float), w)
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["dimension", "exposure_share"], ascending=[True, False])


def main() -> None:
    OUTDIR.mkdir(exist_ok=True)
    train, calibration = read_training_and_calibration()
    test = read_2024_features_only()
    models, scales, x_train = fit_frozen_models(train, calibration)
    sample, sample_indices, weights = diagnostic_sample(test)
    x_sample = canonicalise_features(sample)
    refs = reference_values(x_train)

    attribution, attribution_frame = feature_attribution(x_sample, weights, models, scales, refs)
    segments = segment_disagreement(x_sample, weights, models, scales)

    top_features = {}
    for target in ["frequency", "pure_premium"]:
        subset = attribution_frame[attribution_frame["target"] == target]
        top_features[target] = [
            {
                "feature": row.feature,
                "absolute_disagreement_reduction": float(row.absolute_disagreement_reduction),
                "fraction_of_baseline_abs_disagreement_reduced": float(row.fraction_of_baseline_abs_disagreement_reduced),
                "weighted_sign_flip_rate": float(row.weighted_sign_flip_rate),
            }
            for row in subset.head(5).itertuples()
        ]

    summary = {
        "status": "V47_FROZEN_MODEL_DISAGREEMENT_ATTRIBUTION_COMPLETE",
        "analysis_role": "POST_HOC_DIAGNOSTIC_ON_CONSUMED_RETROSPECTIVE_VALIDATION",
        "candidate_selection_allowed": False,
        "model_or_calibration_parameter_change": False,
        "promotion_evidence_created": False,
        "customer_pricing_authorised": False,
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "source_file_sha256": sha256_file(DATA_PATH),
            "training_year": 2022,
            "calibration_year": 2023,
            "diagnostic_year": 2024,
            "diagnostic_2024_outcome_labels_read": False,
            "diagnostic_rows_with_positive_exposure": int(len(test)),
            "diagnostic_sample_rows": int(len(sample)),
            "diagnostic_sample_seed": SEED,
            "outcome_stratified_sample": False,
        },
        "frozen_model_definition": {
            "source": "build_deployment_bundle_v21.py::model_definitions",
            "source_sha256": sha256_file(Path("build_deployment_bundle_v21.py")),
            "feature_contract_hash": feature_contract_hash(),
            "locked_calibration_scales": scales,
        },
        "reference_values": refs,
        "targets": attribution,
        "top_features_by_disagreement_reduction": top_features,
        "method_boundary": {
            "one_factor_at_a_time_reference_substitution": True,
            "effects_additive": False,
            "causal_interpretation_claimed": False,
            "shap_values_claimed": False,
            "feature_importance_for_model_performance_claimed": False,
            "interpretation": "The diagnostic asks how GLM-vs-XGBoost score disagreement changes when one observed rating factor is replaced by its 2022 training reference while all other factors remain fixed. It is a model sensitivity diagnostic, not causal attribution and not a promotion gate.",
        },
        "persisted_row_level_data": False,
    }

    attribution_frame.to_csv(OUTDIR / "feature_disagreement_attribution_v47.csv", index=False)
    segments.to_csv(OUTDIR / "segment_disagreement_v47.csv", index=False)
    (OUTDIR / "disagreement_attribution_summary_v47.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTDIR / "diagnostic_sample_manifest_v47.json").write_text(
        json.dumps({
            "seed": SEED,
            "sample_size": int(len(sample_indices)),
            "source_population_rows": int(len(test)),
            "sample_index_sha256": hashlib.sha256(sample_indices.astype(np.int64).tobytes()).hexdigest(),
            "outcome_stratified": False,
            "2024_outcome_labels_used": False,
        }, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "status": summary["status"],
        "diagnostic_rows": len(test),
        "sample_rows": len(sample),
        "frequency_baseline": summary["targets"]["frequency"]["baseline"],
        "pure_premium_baseline": summary["targets"]["pure_premium"]["baseline"],
        "top_features": top_features,
    }, indent=2))


if __name__ == "__main__":
    main()
