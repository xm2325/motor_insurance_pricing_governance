from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_deployment_bundle_v21 import canonicalise_features, model_definitions
from deployment.contracts import FEATURES, feature_contract_hash
from run_rating_factor_relativity_audit_v51 import read_2022_development, score_profile

OUTDIR = Path("results_v55")
PROTOCOL_PATH = Path("governance/rating_shape_stability_protocol_v55.json")
V51_SUMMARY_PATH = Path("action_results/v51/rating_factor_relativity_summary_v51.json")
V51_NUMERIC_PATH = Path("action_results/v51/numeric_rating_factor_relativities_v51.csv")
V51_CATEGORICAL_PATH = Path("action_results/v51/categorical_rating_factor_relativities_v51.csv")
EXPECTED_MODELS = {"poisson_glm_frequency", "xgb_poisson_frequency"}
ZERO_TOL = 1e-12


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_locked_inputs() -> tuple[dict, dict, pd.DataFrame, pd.DataFrame]:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol["status"] != "V55_DEVELOPMENT_RATING_SHAPE_STABILITY_PROTOCOL_LOCKED":
        raise RuntimeError("v0.55 protocol is not locked")
    if protocol["fold_design"]["fold_count"] != 5 or protocol["fold_design"]["seed"] != 20260824:
        raise RuntimeError("v0.55 fold design changed")
    if protocol["fold_design"]["outcome_stratification"]:
        raise RuntimeError("v0.55 fold assignment must remain outcome-unstratified")
    if protocol["models"]["names"] != ["poisson_glm_frequency", "xgb_poisson_frequency"]:
        raise RuntimeError("v0.55 model set changed")
    if protocol["evaluation_grid"]["grid_reestimated_per_fold"]:
        raise RuntimeError("v0.55 grid must remain frozen across folds")
    if protocol["evaluation_grid"]["reference_profile_reestimated_per_fold"]:
        raise RuntimeError("v0.55 reference profile must remain frozen across folds")

    v51 = json.loads(V51_SUMMARY_PATH.read_text(encoding="utf-8"))
    if v51["status"] != "V51_DEVELOPMENT_RATING_FACTOR_RELATIVITY_AUDIT_COMPLETE":
        raise RuntimeError("Unexpected v0.51 lineage")
    if v51["source"]["years_read"] != [2022]:
        raise RuntimeError("v0.51 source role changed")

    numeric = pd.read_csv(V51_NUMERIC_PATH)
    categorical = pd.read_csv(V51_CATEGORICAL_PATH, keep_default_na=False)
    return protocol, v51, numeric, categorical


def deterministic_fold_ids(n_rows: int, fold_count: int, seed: int) -> np.ndarray:
    if n_rows < fold_count:
        raise RuntimeError("Not enough development rows for registered fold count")
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(n_rows)
    fold_ids = np.empty(n_rows, dtype=np.int16)
    fold_ids[permutation] = np.arange(n_rows, dtype=np.int64) % fold_count
    return fold_ids


def fit_frequency_models(frame: pd.DataFrame) -> tuple[dict, float, float]:
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
    if set(fitted) != EXPECTED_MODELS:
        raise RuntimeError(f"Unexpected frozen frequency model set: {sorted(fitted)}")
    return fitted, float(np.sum(exposure)), float(frame["total_claims"].sum())


def score_relativity(profile: dict, models: dict, base_scores: dict[str, float]) -> tuple[float, float, float]:
    scores = score_profile(profile, models)
    glm_rel = float(scores["poisson_glm_frequency"] / base_scores["poisson_glm_frequency"])
    xgb_rel = float(scores["xgb_poisson_frequency"] / base_scores["xgb_poisson_frequency"])
    if glm_rel <= 0 or xgb_rel <= 0:
        raise RuntimeError("Non-positive fold relativity")
    return glm_rel, xgb_rel, float(np.log(xgb_rel / glm_rel))


def evaluate_fold(
    fold_id: int,
    training: pd.DataFrame,
    reference: dict,
    numeric_grid: pd.DataFrame,
    categorical_grid: pd.DataFrame,
) -> tuple[list[dict], dict]:
    models, train_exposure, train_claims = fit_frequency_models(training)
    base_scores = score_profile(reference, models)
    if set(base_scores) != EXPECTED_MODELS:
        raise RuntimeError("Unexpected base-score model set")

    rows: list[dict] = []
    for grid_row in numeric_grid.to_dict(orient="records"):
        profile = dict(reference)
        profile[str(grid_row["feature"])] = float(grid_row["value"])
        glm_rel, xgb_rel, log_gap = score_relativity(profile, models, base_scores)
        rows.append({
            "fold_id": fold_id,
            "feature": str(grid_row["feature"]),
            "point_type": "numeric",
            "point_key": f"q{float(grid_row['quantile']):.2f}",
            "value_or_level": str(float(grid_row["value"])),
            "glm_frequency_relativity": glm_rel,
            "xgb_frequency_relativity": xgb_rel,
            "log_xgb_over_glm_relativity": log_gap,
            "v51_full_fit_log_gap": float(grid_row["log_xgb_over_glm_relativity"]),
        })

    for grid_row in categorical_grid.to_dict(orient="records"):
        profile = dict(reference)
        profile[str(grid_row["feature"])] = str(grid_row["level"])
        glm_rel, xgb_rel, log_gap = score_relativity(profile, models, base_scores)
        rows.append({
            "fold_id": fold_id,
            "feature": str(grid_row["feature"]),
            "point_type": "categorical",
            "point_key": str(grid_row["level"]),
            "value_or_level": str(grid_row["level"]),
            "glm_frequency_relativity": glm_rel,
            "xgb_frequency_relativity": xgb_rel,
            "log_xgb_over_glm_relativity": log_gap,
            "v51_full_fit_log_gap": float(grid_row["log_xgb_over_glm_relativity"]),
        })

    metadata = {
        "fold_id": fold_id,
        "train_rows": int(len(training)),
        "train_exposure": train_exposure,
        "train_claims": train_claims,
        "reference_profile_scores": {k: float(v) for k, v in base_scores.items()},
    }
    return rows, metadata


def same_sign_fraction(values: np.ndarray, reference: float) -> float | None:
    if abs(reference) <= ZERO_TOL:
        return None
    target_sign = 1 if reference > 0 else -1
    signs = np.sign(values)
    return float(np.mean(signs == target_sign))


def summarise_points(fold_points: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict] = []
    keys = ["feature", "point_type", "point_key", "value_or_level"]
    for key_values, group in fold_points.groupby(keys, sort=True, dropna=False):
        full_values = group["v51_full_fit_log_gap"].to_numpy(float)
        if np.max(full_values) - np.min(full_values) > 1e-15:
            raise RuntimeError(f"v0.51 full-fit gap changed across fold rows for {key_values}")
        full_gap = float(full_values[0])
        gaps = group["log_xgb_over_glm_relativity"].to_numpy(float)
        if len(gaps) != 5:
            raise RuntimeError(f"Expected 5 fold values for {key_values}, found {len(gaps)}")
        fold_min = float(np.min(gaps))
        fold_max = float(np.max(gaps))
        summary_rows.append({
            "feature": key_values[0],
            "point_type": key_values[1],
            "point_key": key_values[2],
            "value_or_level": key_values[3],
            "v51_full_fit_log_gap": full_gap,
            "fold_mean_log_gap": float(np.mean(gaps)),
            "fold_min_log_gap": fold_min,
            "fold_max_log_gap": fold_max,
            "fold_log_gap_range": float(fold_max - fold_min),
            "fold_std_log_gap": float(np.std(gaps, ddof=0)),
            "fraction_folds_same_sign_as_v51_full_fit": same_sign_fraction(gaps, full_gap),
            "v51_full_fit_gap_inside_fold_min_max": bool(fold_min - 1e-12 <= full_gap <= fold_max + 1e-12),
        })
    return pd.DataFrame(summary_rows)


def summarise_features(point_summary: pd.DataFrame, v51: dict) -> dict:
    output: dict[str, dict] = {}
    for feature, group in point_summary.groupby("feature", sort=True):
        if feature in v51["numeric_grid"]["features"]:
            full_max = float(v51["numeric_grid"]["features"][feature]["max_absolute_log_relativity_gap"])
            point_type = "numeric"
        elif feature in v51["categorical_grid"]["features"]:
            full_max = float(v51["categorical_grid"]["features"][feature]["max_absolute_log_relativity_gap"])
            point_type = "categorical"
        else:
            raise RuntimeError(f"Unknown v0.51 feature in point summary: {feature}")

        nonzero = group[np.abs(group["v51_full_fit_log_gap"].astype(float)) > ZERO_TOL]
        sign_values = [
            float(value)
            for value in nonzero["fraction_folds_same_sign_as_v51_full_fit"].tolist()
            if value is not None and not pd.isna(value)
        ]
        output[str(feature)] = {
            "point_type": point_type,
            "v51_max_absolute_log_gap": full_max,
            "max_fold_log_gap_range_over_registered_points": float(group["fold_log_gap_range"].max()),
            "minimum_same_sign_fraction_over_nonzero_v51_points": float(min(sign_values)) if sign_values else None,
            "registered_point_count": int(len(group)),
        }
    return output


def select_registered_review_points(point_summary: pd.DataFrame, protocol: dict) -> list[dict]:
    selected: list[dict] = []
    for spec in protocol["preselected_review_points"]:
        feature = spec["feature"]
        if spec["point_type"] != "numeric":
            raise RuntimeError("Current v0.55 preregistered review points must be numeric")
        point_key = f"q{float(spec['quantile']):.2f}"
        rows = point_summary[
            (point_summary["feature"] == feature)
            & (point_summary["point_type"] == "numeric")
            & (point_summary["point_key"] == point_key)
        ]
        if len(rows) != 1:
            raise RuntimeError(f"Missing preregistered review point {feature} {point_key}")
        item = rows.iloc[0].to_dict()
        item["reason"] = spec["reason"]
        selected.append(item)
    return selected


def main() -> None:
    OUTDIR.mkdir(exist_ok=True)
    protocol, v51, numeric_grid, categorical_grid = load_locked_inputs()
    frame = read_2022_development()
    if len(frame) != int(v51["source"]["rows"]):
        raise RuntimeError("v0.55 eligible 2022 row count does not match v0.51 lineage")

    fold_count = int(protocol["fold_design"]["fold_count"])
    seed = int(protocol["fold_design"]["seed"])
    fold_ids = deterministic_fold_ids(len(frame), fold_count, seed)
    reference = dict(v51["reference_profile"])

    fold_rows: list[dict] = []
    fold_metadata: list[dict] = []
    for fold_id in range(fold_count):
        excluded = fold_ids == fold_id
        training = frame.loc[~excluded].reset_index(drop=True)
        rows, metadata = evaluate_fold(fold_id, training, reference, numeric_grid, categorical_grid)
        metadata.update({
            "excluded_rows": int(np.sum(excluded)),
            "excluded_exposure": float(frame.loc[excluded, "total_exposure"].sum()),
            "excluded_claims": float(frame.loc[excluded, "total_claims"].sum()),
        })
        fold_rows.extend(rows)
        fold_metadata.append(metadata)

    fold_points = pd.DataFrame(fold_rows)
    point_summary = summarise_points(fold_points)
    feature_summary = summarise_features(point_summary, v51)
    preselected = select_registered_review_points(point_summary, protocol)

    fold_points.to_csv(OUTDIR / "rating_shape_stability_fold_points_v55.csv", index=False)
    point_summary.to_csv(OUTDIR / "rating_shape_stability_point_summary_v55.csv", index=False)

    summary = {
        "status": "V55_DEVELOPMENT_RATING_SHAPE_STABILITY_AUDIT_COMPLETE",
        "analysis_role": protocol["analysis_role"],
        "protocol": {
            "path": str(PROTOCOL_PATH),
            "sha256": sha256_file(PROTOCOL_PATH),
            "locked_before_first_execution": True,
        },
        "lineage": {
            "v51_summary_sha256": sha256_file(V51_SUMMARY_PATH),
            "v51_numeric_grid_sha256": sha256_file(V51_NUMERIC_PATH),
            "v51_categorical_grid_sha256": sha256_file(V51_CATEGORICAL_PATH),
            "feature_contract_hash": feature_contract_hash(),
            "reference_profile": reference,
        },
        "source": {
            "dataset": v51["source"]["dataset"],
            "source_file_sha256": v51["source"]["source_file_sha256"],
            "years_read": [2022],
            "rows": int(len(frame)),
            "exposure": float(frame["total_exposure"].sum()),
            "claims": float(frame["total_claims"].sum()),
            "2023_rows_read": False,
            "2024_rows_read": False,
            "incurred_loss_read": False,
            "actual_premium_read": False,
            "customer_id_read": False,
            "policy_status_read": False,
        },
        "fold_design": {
            "fold_count": fold_count,
            "seed": seed,
            "outcome_stratification": False,
            "held_out_performance_metric_computed": False,
            "folds": fold_metadata,
            "excluded_row_count_sum": int(sum(item["excluded_rows"] for item in fold_metadata)),
        },
        "models": {
            "names": sorted(EXPECTED_MODELS),
            "target": "frequency",
            "definition_source": protocol["lineage"]["frozen_model_definition_source"],
            "model_fit_executed": True,
            "fit_scope": "five deterministic 80-percent development subsets only",
            "calibration_applied": False,
            "grid_reestimated_per_fold": False,
            "reference_profile_reestimated_per_fold": False,
        },
        "registered_grid": {
            "numeric_point_count": int(len(numeric_grid)),
            "categorical_point_count": int(len(categorical_grid)),
            "fold_point_row_count": int(len(fold_points)),
            "point_summary_row_count": int(len(point_summary)),
        },
        "feature_summary": feature_summary,
        "preselected_review_points": preselected,
        "interpretation_boundary": {
            **protocol["interpretation_rules"],
            "interpretation": "The five fixed folds perturb only which 2022 development rows are used to refit the frozen frequency specifications while holding the v0.51 reference profile and evaluation grid fixed. Fold ranges and standard deviations describe development response-shape sensitivity; they are not confidence intervals, held-out predictive validation, causal effects, population-average PDPs, candidate-selection evidence or customer-pricing authority.",
        },
        "persisted_row_level_data": False,
    }
    (OUTDIR / "rating_shape_stability_summary_v55.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "status": summary["status"],
        "protocol_sha256": summary["protocol"]["sha256"],
        "rows": summary["source"]["rows"],
        "fold_rows": [item["excluded_rows"] for item in fold_metadata],
        "preselected_review_points": [
            {
                "feature": item["feature"],
                "point_key": item["point_key"],
                "v51_full_fit_log_gap": item["v51_full_fit_log_gap"],
                "fold_min_log_gap": item["fold_min_log_gap"],
                "fold_max_log_gap": item["fold_max_log_gap"],
                "fold_log_gap_range": item["fold_log_gap_range"],
                "fraction_same_sign": item["fraction_folds_same_sign_as_v51_full_fit"],
            }
            for item in preselected
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
