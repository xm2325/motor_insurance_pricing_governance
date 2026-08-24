from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from deployment.contracts import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, feature_contract_hash

DATA_PATH = Path("data_spanish_2022_2024/Dataset_of_motor_insurance_portfolio.csv")
OUTDIR = Path("results_v52")
V51_SUMMARY = Path("action_results/v51/rating_factor_relativity_summary_v51.json")
MISSING_LEVEL = "<MISSING>"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonicalise_support_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame[FEATURES].copy()
    for feature in NUMERIC_FEATURES:
        out[feature] = pd.to_numeric(out[feature], errors="coerce")
    for feature in CATEGORICAL_FEATURES:
        values = out[feature]
        out[feature] = values.map(lambda value: str(value) if pd.notna(value) else np.nan)
    return out


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0:
        raise RuntimeError("No finite positive-weight observations for weighted quantile")
    order = np.argsort(values, kind="mergesort")
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights) - 0.5 * weights
    cumulative = cumulative / np.sum(weights)
    return float(np.interp(q, cumulative, values))


def read_feature_populations() -> tuple[pd.DataFrame, pd.DataFrame]:
    # Label-free support audit. Deliberately reads rating features, year and exposure only.
    cols = FEATURES + ["year", "total_exposure"]
    frame = pd.read_csv(DATA_PATH, sep=";", usecols=cols, low_memory=False)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["total_exposure"] = pd.to_numeric(frame["total_exposure"], errors="coerce")
    valid = frame["total_exposure"].notna() & (frame["total_exposure"] > 0) & frame["year"].isin([2022, 2024])
    frame = frame.loc[valid].copy()
    features = canonicalise_support_features(frame)
    features["year"] = frame["year"].astype(int).to_numpy()
    features["total_exposure"] = frame["total_exposure"].to_numpy(float)
    development = features.loc[features["year"] == 2022].reset_index(drop=True)
    current = features.loc[features["year"] == 2024].reset_index(drop=True)
    if development.empty or current.empty:
        raise RuntimeError("Both 2022 development and 2024 feature populations are required")
    return development, current


def exposure_share(mask: np.ndarray, weights: np.ndarray) -> float:
    total = float(np.sum(weights))
    if total <= 0:
        raise RuntimeError("Positive total exposure required")
    return float(np.sum(weights[mask]) / total)


def numeric_support(development: pd.DataFrame, current: pd.DataFrame, v51: dict) -> tuple[pd.DataFrame, dict]:
    dev_w = development["total_exposure"].to_numpy(float)
    cur_w = current["total_exposure"].to_numpy(float)
    rows = []
    summaries = {}
    for feature in NUMERIC_FEATURES:
        dev = pd.to_numeric(development[feature], errors="coerce").to_numpy(float)
        cur = pd.to_numeric(current[feature], errors="coerce").to_numpy(float)
        dev_valid = np.isfinite(dev)
        cur_valid = np.isfinite(cur)
        if not np.any(dev_valid):
            raise RuntimeError(f"No finite 2022 values for {feature}")

        dev_min = float(np.min(dev[dev_valid]))
        dev_max = float(np.max(dev[dev_valid]))
        q01 = weighted_quantile(dev, dev_w, 0.01)
        q05 = weighted_quantile(dev, dev_w, 0.05)
        q50 = weighted_quantile(dev, dev_w, 0.50)
        q95 = weighted_quantile(dev, dev_w, 0.95)
        q99 = weighted_quantile(dev, dev_w, 0.99)
        cur_q50 = weighted_quantile(cur, cur_w, 0.50)

        missing = ~cur_valid
        below_min = cur_valid & (cur < dev_min)
        above_max = cur_valid & (cur > dev_max)
        below_q01 = cur_valid & (cur < q01)
        above_q99 = cur_valid & (cur > q99)
        below_q05 = cur_valid & (cur < q05)
        above_q95 = cur_valid & (cur > q95)

        item = {
            "feature": feature,
            "development_observed_min": dev_min,
            "development_q01": q01,
            "development_q05": q05,
            "development_q50": q50,
            "development_q95": q95,
            "development_q99": q99,
            "development_observed_max": dev_max,
            "current_q50": cur_q50,
            "current_median_minus_development_median": cur_q50 - q50,
            "current_missing_exposure_share": exposure_share(missing, cur_w),
            "current_below_development_min_exposure_share": exposure_share(below_min, cur_w),
            "current_above_development_max_exposure_share": exposure_share(above_max, cur_w),
            "current_outside_development_observed_range_exposure_share": exposure_share(below_min | above_max, cur_w),
            "current_below_development_q01_exposure_share": exposure_share(below_q01, cur_w),
            "current_above_development_q99_exposure_share": exposure_share(above_q99, cur_w),
            "current_outside_development_q01_q99_exposure_share": exposure_share(below_q01 | above_q99, cur_w),
            "current_below_development_q05_exposure_share": exposure_share(below_q05, cur_w),
            "current_above_development_q95_exposure_share": exposure_share(above_q95, cur_w),
            "current_outside_development_q05_q95_exposure_share": exposure_share(below_q05 | above_q95, cur_w),
            "v51_max_absolute_log_relativity_gap": float(v51["numeric_grid"]["features"][feature]["max_absolute_log_relativity_gap"]),
        }
        rows.append(item)
        summaries[feature] = dict(item)
    return pd.DataFrame(rows), summaries


def categorical_distribution(frame: pd.DataFrame, feature: str) -> pd.DataFrame:
    values = frame[feature].where(frame[feature].notna(), MISSING_LEVEL).astype(str)
    exposure = frame["total_exposure"].to_numpy(float)
    table = pd.DataFrame({"level": values, "exposure": exposure}).groupby("level", as_index=False)["exposure"].sum()
    total = float(table["exposure"].sum())
    table["share"] = table["exposure"] / total
    return table


def categorical_support(development: pd.DataFrame, current: pd.DataFrame, v51: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    feature_rows = []
    level_rows = []
    summaries = {}
    for feature in CATEGORICAL_FEATURES:
        dev = categorical_distribution(development, feature).rename(columns={"exposure": "development_exposure", "share": "development_share"})
        cur = categorical_distribution(current, feature).rename(columns={"exposure": "current_exposure", "share": "current_share"})
        joined = dev.merge(cur, on="level", how="outer").fillna(0.0)
        joined["development_seen"] = joined["development_share"] > 0
        joined["share_change"] = joined["current_share"] - joined["development_share"]
        joined["absolute_share_change"] = joined["share_change"].abs()
        joined["feature"] = feature
        joined = joined[[
            "feature", "level", "development_exposure", "development_share", "current_exposure", "current_share",
            "share_change", "absolute_share_change", "development_seen"
        ]]
        level_rows.extend(joined.to_dict(orient="records"))

        unseen = joined[(~joined["development_seen"]) & (joined["level"] != MISSING_LEVEL)]
        current_missing = float(joined.loc[joined["level"] == MISSING_LEVEL, "current_share"].sum())
        unseen_share = float(unseen["current_share"].sum())
        tv = float(0.5 * joined["absolute_share_change"].sum())
        max_row = joined.sort_values(["absolute_share_change", "level"], ascending=[False, True]).iloc[0]
        item = {
            "feature": feature,
            "development_level_count_including_missing": int(len(dev)),
            "current_level_count_including_missing": int(len(cur)),
            "current_unseen_nonmissing_level_count": int(len(unseen)),
            "current_unseen_nonmissing_exposure_share": unseen_share,
            "current_missing_exposure_share": current_missing,
            "total_variation_distance_2022_vs_2024": tv,
            "max_absolute_level_share_change": float(max_row["absolute_share_change"]),
            "max_shift_level": str(max_row["level"]),
            "max_shift_development_share": float(max_row["development_share"]),
            "max_shift_current_share": float(max_row["current_share"]),
            "max_shift_signed_share_change": float(max_row["share_change"]),
            "v51_max_absolute_log_relativity_gap": float(v51["categorical_grid"]["features"][feature]["max_absolute_log_relativity_gap"]),
        }
        feature_rows.append(item)
        summaries[feature] = dict(item)
    return pd.DataFrame(feature_rows), pd.DataFrame(level_rows), summaries


def main() -> None:
    OUTDIR.mkdir(exist_ok=True)
    development, current = read_feature_populations()
    v51 = json.loads(V51_SUMMARY.read_text(encoding="utf-8"))
    if v51["analysis_role"] != "DEVELOPMENT_ONLY_REFERENCE_PROFILE_INTERPRETABILITY_AUDIT":
        raise RuntimeError("Unexpected v0.51 source role")

    numeric, numeric_summary = numeric_support(development, current, v51)
    categorical, levels, categorical_summary = categorical_support(development, current, v51)
    numeric.to_csv(OUTDIR / "numeric_feature_support_v52.csv", index=False)
    categorical.to_csv(OUTDIR / "categorical_feature_support_v52.csv", index=False)
    levels.to_csv(OUTDIR / "categorical_level_shift_v52.csv", index=False)

    ranked_numeric_extrapolation = numeric.sort_values(
        ["current_outside_development_observed_range_exposure_share", "feature"], ascending=[False, True]
    )["feature"].tolist()
    ranked_numeric_tail_shift = numeric.sort_values(
        ["current_outside_development_q05_q95_exposure_share", "feature"], ascending=[False, True]
    )["feature"].tolist()
    ranked_categorical_unseen = categorical.sort_values(
        ["current_unseen_nonmissing_exposure_share", "feature"], ascending=[False, True]
    )["feature"].tolist()
    ranked_categorical_mix_shift = categorical.sort_values(
        ["total_variation_distance_2022_vs_2024", "feature"], ascending=[False, True]
    )["feature"].tolist()

    summary = {
        "status": "V52_LABEL_FREE_RATING_FACTOR_SUPPORT_AUDIT_COMPLETE",
        "analysis_role": "POST_HOC_LABEL_FREE_FEATURE_SUPPORT_AND_MIX_AUDIT",
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "source_file_sha256": sha256_file(DATA_PATH),
            "years_read": [2022, 2024],
            "development_rows": int(len(development)),
            "development_exposure": float(development["total_exposure"].sum()),
            "current_rows": int(len(current)),
            "current_exposure": float(current["total_exposure"].sum()),
            "2023_rows_read": False,
            "claim_outcomes_read": False,
            "incurred_loss_read": False,
            "actual_premium_read": False,
            "customer_id_read": False,
            "policy_status_read": False,
        },
        "feature_contract_hash": feature_contract_hash(),
        "v51_lineage": {
            "path": str(V51_SUMMARY),
            "source_analysis_role": v51["analysis_role"],
            "development_shape_gap_used_descriptively": True,
        },
        "definitions": {
            "strict_numeric_extrapolation": "2024 non-missing feature value below the observed 2022 minimum or above the observed 2022 maximum.",
            "numeric_tail_shift": "2024 exposure outside the exposure-weighted 2022 q05-q95 or q01-q99 interval. Tail exposure is not automatically extrapolation.",
            "strict_categorical_unseen": "2024 non-missing category absent from the 2022 development population.",
            "categorical_total_variation": "0.5 * sum(abs(2024 exposure share - 2022 exposure share)) over the union of levels, including a missing-value bucket.",
            "no_composite_score": True,
            "no_alert_or_acceptance_threshold_created": True,
        },
        "numeric_features": numeric_summary,
        "categorical_features": categorical_summary,
        "rankings": {
            "numeric_strict_extrapolation": ranked_numeric_extrapolation,
            "numeric_q05_q95_tail_shift": ranked_numeric_tail_shift,
            "categorical_unseen_exposure": ranked_categorical_unseen,
            "categorical_mix_shift": ranked_categorical_mix_shift,
        },
        "interpretation_boundary": {
            "post_hoc_consumed_validation_features_only": True,
            "validation_performance_evidence_created": False,
            "candidate_selection_allowed": False,
            "model_fit_executed": False,
            "model_promotion_evidence_created": False,
            "customer_pricing_authorised": False,
            "causal_interpretation_claimed": False,
            "fairness_conclusion_claimed": False,
            "first_central_or_current_uk_transport_claimed": False,
            "interpretation": "This audit describes whether 2024 rating-feature values and category mix remain within or near 2022 development support. It uses no 2024 claim/loss outcomes and does not measure predictive performance, causal effects, fairness, customer premiums or commercial impact. Shape gap from v0.51 and support/mix shift are kept side-by-side rather than combined into a subjective score."
        },
        "persisted_row_level_data": False,
    }
    (OUTDIR / "rating_factor_support_summary_v52.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": summary["status"],
        "development_rows": summary["source"]["development_rows"],
        "current_rows": summary["source"]["current_rows"],
        "top_numeric_strict_extrapolation": [
            {"feature": f, "share": numeric_summary[f]["current_outside_development_observed_range_exposure_share"]}
            for f in ranked_numeric_extrapolation[:4]
        ],
        "top_numeric_q05_q95_tail_shift": [
            {"feature": f, "share": numeric_summary[f]["current_outside_development_q05_q95_exposure_share"]}
            for f in ranked_numeric_tail_shift[:4]
        ],
        "top_categorical_unseen": [
            {"feature": f, "share": categorical_summary[f]["current_unseen_nonmissing_exposure_share"]}
            for f in ranked_categorical_unseen[:4]
        ],
        "top_categorical_mix_shift": [
            {"feature": f, "tv": categorical_summary[f]["total_variation_distance_2022_vs_2024"], "level": categorical_summary[f]["max_shift_level"]}
            for f in ranked_categorical_mix_shift[:4]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
