from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_deployment_bundle_v21 import canonicalise_features, model_definitions
from deployment.contracts import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, feature_contract_hash
from run_spanish_oot_2024 import DATA_PATH

OUTDIR = Path("results_v51")
QUANTILES = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
MAX_CATEGORICAL_LEVELS = 10


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_2022_development() -> pd.DataFrame:
    # Development-only interpretability rebuild. Deliberately reads no 2023/2024
    # rows, incurred-loss outcomes, premium fields, IDs or policy status.
    cols = FEATURES + ["year", "total_exposure", "total_claims"]
    frame = pd.read_csv(DATA_PATH, sep=";", usecols=cols, low_memory=False)
    for col in [*NUMERIC_FEATURES, "year", "total_exposure", "total_claims"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    valid = (
        (frame["year"] == 2022)
        & frame["total_exposure"].notna()
        & (frame["total_exposure"] > 0)
        & frame["total_claims"].notna()
        & (frame["total_claims"] >= 0)
    )
    return frame.loc[valid].reset_index(drop=True)


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


def exposure_weighted_reference(x: pd.DataFrame, exposure: np.ndarray) -> dict:
    reference: dict[str, float | str] = {}
    for feature in NUMERIC_FEATURES:
        values = pd.to_numeric(x[feature], errors="coerce").to_numpy(float)
        reference[feature] = weighted_quantile(values, exposure, 0.50)
    for feature in CATEGORICAL_FEATURES:
        values = x[feature]
        table = (
            pd.DataFrame({"level": values, "exposure": exposure})
            .dropna(subset=["level"])
            .assign(level=lambda d: d["level"].astype(str))
            .groupby("level", as_index=False)["exposure"].sum()
            .sort_values(["exposure", "level"], ascending=[False, True])
        )
        if table.empty:
            raise RuntimeError(f"No non-missing exposure-supported level for {feature}")
        reference[feature] = str(table.iloc[0]["level"])
    return reference


def fit_frozen_frequency_models(frame: pd.DataFrame) -> tuple[dict, pd.DataFrame, np.ndarray]:
    x = canonicalise_features(frame)
    exposure = frame["total_exposure"].to_numpy(float)
    y = frame["total_claims"].to_numpy(float) / exposure
    fitted = {}
    for name, spec in model_definitions().items():
        if spec["target"] != "frequency":
            continue
        model = spec["model"]
        model.fit(x, y, model__sample_weight=exposure)
        fitted[name] = model
    expected = {"poisson_glm_frequency", "xgb_poisson_frequency"}
    if set(fitted) != expected:
        raise RuntimeError(f"Unexpected frozen frequency model set: {sorted(fitted)}")
    return fitted, x, exposure


def score_profile(profile: dict, models: dict) -> dict[str, float]:
    row = canonicalise_features(pd.DataFrame([profile], columns=FEATURES))
    scores = {
        name: float(np.clip(model.predict(row)[0], 1e-12, None))
        for name, model in models.items()
    }
    return scores


def count_direction_changes(values: list[float], tolerance: float = 1e-10) -> int:
    diffs = np.diff(np.asarray(values, dtype=float))
    signs = np.sign(diffs[np.abs(diffs) > tolerance])
    if len(signs) < 2:
        return 0
    return int(np.sum(signs[1:] != signs[:-1]))


def numeric_audit(
    x: pd.DataFrame,
    exposure: np.ndarray,
    models: dict,
    reference: dict,
    base_scores: dict,
) -> tuple[pd.DataFrame, dict]:
    rows = []
    summaries = {}
    for feature in NUMERIC_FEATURES:
        values = pd.to_numeric(x[feature], errors="coerce").to_numpy(float)
        feature_rows = []
        for q in QUANTILES:
            value = weighted_quantile(values, exposure, q)
            profile = dict(reference)
            profile[feature] = value
            scores = score_profile(profile, models)
            glm_rel = scores["poisson_glm_frequency"] / base_scores["poisson_glm_frequency"]
            xgb_rel = scores["xgb_poisson_frequency"] / base_scores["xgb_poisson_frequency"]
            item = {
                "feature": feature,
                "quantile": q,
                "value": value,
                "glm_frequency_relativity": glm_rel,
                "xgb_frequency_relativity": xgb_rel,
                "log_xgb_over_glm_relativity": float(np.log(xgb_rel / glm_rel)),
            }
            rows.append(item)
            feature_rows.append(item)

        gaps = np.abs([r["log_xgb_over_glm_relativity"] for r in feature_rows])
        max_index = int(np.argmax(gaps))
        max_row = feature_rows[max_index]
        glm_values = [r["glm_frequency_relativity"] for r in feature_rows]
        xgb_values = [r["xgb_frequency_relativity"] for r in feature_rows]
        summaries[feature] = {
            "grid_points": len(feature_rows),
            "min_grid_value": float(min(r["value"] for r in feature_rows)),
            "max_grid_value": float(max(r["value"] for r in feature_rows)),
            "glm_relativity_min": float(min(glm_values)),
            "glm_relativity_max": float(max(glm_values)),
            "xgb_relativity_min": float(min(xgb_values)),
            "xgb_relativity_max": float(max(xgb_values)),
            "glm_direction_changes_over_quantile_grid": count_direction_changes(glm_values),
            "xgb_direction_changes_over_quantile_grid": count_direction_changes(xgb_values),
            "max_absolute_log_relativity_gap": float(gaps[max_index]),
            "max_gap_quantile": float(max_row["quantile"]),
            "max_gap_value": float(max_row["value"]),
            "interpretation": "Reference-profile sensitivity over exposure-weighted 2022 support. A larger gap means the frozen development GLM and XGBoost imply different one-factor technical-risk relativities at that supported value. This is not a causal effect or customer premium.",
        }
    return pd.DataFrame(rows), summaries


def categorical_levels(x: pd.DataFrame, exposure: np.ndarray, feature: str, reference_level: str) -> pd.DataFrame:
    table = (
        pd.DataFrame({"level": x[feature], "exposure": exposure})
        .dropna(subset=["level"])
        .assign(level=lambda d: d["level"].astype(str))
        .groupby("level", as_index=False)["exposure"].sum()
    )
    total = float(table["exposure"].sum())
    table["exposure_share"] = table["exposure"] / total
    table = table.sort_values(["exposure", "level"], ascending=[False, True]).reset_index(drop=True)
    selected = table.head(MAX_CATEGORICAL_LEVELS).copy()
    if reference_level not in set(selected["level"]):
        ref_row = table[table["level"] == reference_level]
        if ref_row.empty:
            raise RuntimeError(f"Reference level {reference_level!r} absent for {feature}")
        selected = pd.concat([selected, ref_row], ignore_index=True).drop_duplicates("level")
    return selected.sort_values(["exposure", "level"], ascending=[False, True]).reset_index(drop=True)


def categorical_audit(
    x: pd.DataFrame,
    exposure: np.ndarray,
    models: dict,
    reference: dict,
    base_scores: dict,
) -> tuple[pd.DataFrame, dict]:
    rows = []
    summaries = {}
    for feature in CATEGORICAL_FEATURES:
        levels = categorical_levels(x, exposure, feature, str(reference[feature]))
        feature_rows = []
        for row in levels.itertuples(index=False):
            profile = dict(reference)
            profile[feature] = str(row.level)
            scores = score_profile(profile, models)
            glm_rel = scores["poisson_glm_frequency"] / base_scores["poisson_glm_frequency"]
            xgb_rel = scores["xgb_poisson_frequency"] / base_scores["xgb_poisson_frequency"]
            item = {
                "feature": feature,
                "level": str(row.level),
                "exposure_share": float(row.exposure_share),
                "is_reference_level": str(row.level) == str(reference[feature]),
                "glm_frequency_relativity": glm_rel,
                "xgb_frequency_relativity": xgb_rel,
                "log_xgb_over_glm_relativity": float(np.log(xgb_rel / glm_rel)),
            }
            rows.append(item)
            feature_rows.append(item)

        gaps = np.abs([r["log_xgb_over_glm_relativity"] for r in feature_rows])
        max_index = int(np.argmax(gaps))
        max_row = feature_rows[max_index]
        summaries[feature] = {
            "displayed_levels": len(feature_rows),
            "displayed_exposure_share": float(sum(r["exposure_share"] for r in feature_rows)),
            "reference_level": str(reference[feature]),
            "max_absolute_log_relativity_gap": float(gaps[max_index]),
            "max_gap_level": str(max_row["level"]),
            "max_gap_level_exposure_share": float(max_row["exposure_share"]),
            "interpretation": "Reference-profile categorical sensitivity for the highest-exposure 2022 levels (plus the reference level if needed). It is not an exhaustive category effect estimate, causal effect or premium change.",
        }
    return pd.DataFrame(rows), summaries


def main() -> None:
    OUTDIR.mkdir(exist_ok=True)
    frame = read_2022_development()
    models, x, exposure = fit_frozen_frequency_models(frame)
    reference = exposure_weighted_reference(x, exposure)
    base_scores = score_profile(reference, models)

    numeric, numeric_summary = numeric_audit(x, exposure, models, reference, base_scores)
    categorical, categorical_summary = categorical_audit(x, exposure, models, reference, base_scores)

    numeric.to_csv(OUTDIR / "numeric_rating_factor_relativities_v51.csv", index=False)
    categorical.to_csv(OUTDIR / "categorical_rating_factor_relativities_v51.csv", index=False)

    ranked_numeric = sorted(
        ({"feature": k, **v} for k, v in numeric_summary.items()),
        key=lambda r: r["max_absolute_log_relativity_gap"],
        reverse=True,
    )
    ranked_categorical = sorted(
        ({"feature": k, **v} for k, v in categorical_summary.items()),
        key=lambda r: r["max_absolute_log_relativity_gap"],
        reverse=True,
    )

    summary = {
        "status": "V51_DEVELOPMENT_RATING_FACTOR_RELATIVITY_AUDIT_COMPLETE",
        "analysis_role": "DEVELOPMENT_ONLY_REFERENCE_PROFILE_INTERPRETABILITY_AUDIT",
        "source": {
            "dataset": "Mendeley sw4jmdb2sm v1",
            "source_file_sha256": sha256_file(DATA_PATH),
            "years_read": [2022],
            "rows": int(len(frame)),
            "exposure": float(frame["total_exposure"].sum()),
            "claims": float(frame["total_claims"].sum()),
            "2023_rows_read": False,
            "2024_rows_read": False,
            "incurred_loss_read": False,
            "actual_premium_read": False,
            "customer_id_read": False,
        },
        "frozen_frequency_definition": {
            "source": "build_deployment_bundle_v21.py::model_definitions",
            "feature_contract_hash": feature_contract_hash(),
            "models": ["poisson_glm_frequency", "xgb_poisson_frequency"],
            "model_fit_executed": True,
            "calibration_applied": False,
            "reason_calibration_not_needed": "Each model's factor sweep is normalised to its own 2022 reference-profile score, so an aggregate multiplicative calibration scale would cancel from the relativity.",
        },
        "reference_profile": reference,
        "reference_profile_scores": base_scores,
        "numeric_grid": {
            "quantiles": QUANTILES,
            "exposure_weighted": True,
            "features": numeric_summary,
        },
        "categorical_grid": {
            "selection": f"top {MAX_CATEGORICAL_LEVELS} levels by 2022 exposure, plus reference level if needed",
            "features": categorical_summary,
        },
        "ranked_numeric_shape_gaps": ranked_numeric,
        "ranked_categorical_shape_gaps": ranked_categorical,
        "interpretation_boundary": {
            "reference_profile_not_population_average_pdp": True,
            "causal_interpretation_claimed": False,
            "validation_performance_evidence_created": False,
            "candidate_selection_allowed": False,
            "model_promotion_evidence_created": False,
            "customer_pricing_authorised": False,
            "actual_premium_or_quote": False,
            "interpretation": "The audit compares one-factor technical-risk relativities implied by frozen development frequency model specifications around one exposure-weighted 2022 reference profile. It is a development interpretability diagnostic, not a population-average PDP, validation result, causal effect, customer premium or model-promotion gate.",
        },
        "persisted_row_level_data": False,
    }
    (OUTDIR / "rating_factor_relativity_summary_v51.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "status": summary["status"],
        "rows": summary["source"]["rows"],
        "reference_profile": reference,
        "top_numeric_shape_gaps": [
            {"feature": r["feature"], "max_absolute_log_relativity_gap": r["max_absolute_log_relativity_gap"], "xgb_direction_changes": r["xgb_direction_changes_over_quantile_grid"]}
            for r in ranked_numeric[:4]
        ],
        "top_categorical_shape_gaps": [
            {"feature": r["feature"], "max_absolute_log_relativity_gap": r["max_absolute_log_relativity_gap"], "level": r["max_gap_level"], "level_exposure_share": r["max_gap_level_exposure_share"]}
            for r in ranked_categorical[:4]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
