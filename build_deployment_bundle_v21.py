from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from xgboost import XGBRegressor

from deployment.bundle import ShadowModelBundle, sha256_file
from deployment.contracts import (
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    SHADOW_GOVERNANCE_STATUS,
    feature_contract_hash,
)
from deployment.drift import build_monitoring_baseline
from deployment.environment import capture_model_environment
from run_spanish_oot_2024 import DATA_PATH, load_data, locked_scale, make_pipeline

OUTDIR = Path("deployment_artifacts")
PARITY_FIELDS = [
    "reference_frequency",
    "challenger_frequency",
    "reference_pure_premium",
    "challenger_pure_premium",
]


def canonicalise_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame[FEATURES].copy()
    for col in NUMERIC_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in CATEGORICAL_FEATURES:
        values = out[col]
        out[col] = values.map(lambda value: str(value) if pd.notna(value) else np.nan)
    return out


def model_definitions() -> dict[str, dict]:
    return {
        "poisson_glm_frequency": {
            "target": "frequency",
            "role": "reference",
            "model": make_pipeline(PoissonRegressor(alpha=1e-4, max_iter=600)),
        },
        "xgb_poisson_frequency": {
            "target": "frequency",
            "role": "challenger",
            "model": make_pipeline(
                XGBRegressor(
                    objective="count:poisson",
                    n_estimators=450,
                    max_depth=4,
                    learning_rate=0.035,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    min_child_weight=5,
                    reg_lambda=1.0,
                    n_jobs=2,
                    random_state=42,
                )
            ),
        },
        "tweedie_glm_pure_premium": {
            "target": "pure_premium",
            "role": "reference",
            "model": make_pipeline(
                TweedieRegressor(power=1.5, alpha=1e-4, link="log", max_iter=900)
            ),
        },
        "xgb_tweedie_pure_premium": {
            "target": "pure_premium",
            "role": "challenger",
            "model": make_pipeline(
                XGBRegressor(
                    objective="reg:tweedie",
                    tweedie_variance_power=1.5,
                    n_estimators=500,
                    max_depth=4,
                    learning_rate=0.03,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    min_child_weight=5,
                    reg_lambda=1.0,
                    n_jobs=2,
                    random_state=42,
                )
            ),
        },
    }


def records_from_frame(frame: pd.DataFrame) -> list[dict]:
    records = []
    for row in frame.to_dict(orient="records"):
        cleaned = {}
        for key, value in row.items():
            if pd.isna(value):
                cleaned[key] = None
            elif key in NUMERIC_FEATURES:
                cleaned[key] = float(value)
            else:
                cleaned[key] = str(value)
        records.append(cleaned)
    return records


def persist_model(name: str, model, spec: dict, locked_scale: float) -> dict:
    metadata = {
        "target": spec["target"],
        "role": spec["role"],
        "locked_scale": float(locked_scale),
    }
    fitted_estimator = model.named_steps["model"]

    if isinstance(fitted_estimator, XGBRegressor):
        prep_name = f"{name}.preprocessor.joblib"
        native_name = f"{name}.ubj"
        prep_path = OUTDIR / prep_name
        native_path = OUTDIR / native_name
        joblib.dump(model.named_steps["prep"], prep_path, compress=3)
        fitted_estimator.save_model(str(native_path))
        metadata.update(
            {
                "serialization": "sklearn_preprocessor_plus_xgboost_ubj",
                "preprocessor_artifact": prep_name,
                "preprocessor_sha256": sha256_file(prep_path),
                "native_model_artifact": native_name,
                "native_model_sha256": sha256_file(native_path),
            }
        )
        return metadata

    artifact_name = f"{name}.joblib"
    artifact_path = OUTDIR / artifact_name
    joblib.dump(model, artifact_path, compress=3)
    metadata.update(
        {
            "serialization": "joblib_pipeline",
            "artifact": artifact_name,
            "sha256": sha256_file(artifact_path),
        }
    )
    return metadata


def verify_same_fit_serialization_parity(
    parity_records: list[dict], parity_scores: list[dict]
) -> dict:
    reloaded = ShadowModelBundle.load(OUTDIR)
    reloaded_scores = reloaded.score_records(parity_records)
    max_abs_error = 0.0
    per_field = {field: 0.0 for field in PARITY_FIELDS}
    for record_index, (expected, observed) in enumerate(zip(parity_scores, reloaded_scores)):
        for field in PARITY_FIELDS:
            expected_value = float(expected[field])
            observed_value = float(observed[field])
            error = abs(observed_value - expected_value)
            max_abs_error = max(max_abs_error, error)
            per_field[field] = max(per_field[field], error)
            if not np.isclose(observed_value, expected_value, rtol=1e-12, atol=1e-12):
                raise AssertionError(
                    f"Same-fit serialization parity failed record={record_index} field={field} "
                    f"before={expected_value} after={observed_value} abs_error={error}"
                )
    return {
        "status": "SAME_FIT_SERIALIZATION_PARITY_PASS",
        "records_tested": len(parity_records),
        "fields_per_record": len(PARITY_FIELDS),
        "comparisons": len(parity_records) * len(PARITY_FIELDS),
        "max_absolute_error": max_abs_error,
        "max_absolute_error_by_field": per_field,
        "acceptance_tolerance": {"rtol": 1e-12, "atol": 1e-12},
        "interpretation": (
            "This is a serialization migration gate on one fitted model set. It is not a "
            "retraining-reproducibility claim."
        ),
    }


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for stale in OUTDIR.glob("*"):
        if stale.is_file():
            stale.unlink()

    df = load_data()
    train = df[df["year"] == 2022].copy().reset_index(drop=True)
    calibration = df[df["year"] == 2023].copy().reset_index(drop=True)
    test = df[df["year"] == 2024].copy().reset_index(drop=True)

    x_train = canonicalise_features(train)
    x_calibration = canonicalise_features(calibration)
    x_test = canonicalise_features(test)

    e_train = train["total_exposure"].to_numpy(float)
    e_calibration = calibration["total_exposure"].to_numpy(float)
    claims_train = train["total_claims"].to_numpy(float)
    claims_calibration = calibration["total_claims"].to_numpy(float)
    loss_train = train["total_incurred"].to_numpy(float)
    loss_calibration = calibration["total_incurred"].to_numpy(float)

    y_train = {
        "frequency": claims_train / e_train,
        "pure_premium": loss_train / e_train,
    }
    actual_calibration = {
        "frequency": claims_calibration,
        "pure_premium": loss_calibration,
    }

    definitions = model_definitions()
    manifest_models = {}
    fitted_models = {}

    for name, spec in definitions.items():
        model = spec["model"]
        target = spec["target"]
        model.fit(x_train, y_train[target], model__sample_weight=e_train)
        pred_calibration = np.clip(model.predict(x_calibration), 1e-12, None)
        scale = locked_scale(actual_calibration[target], pred_calibration, e_calibration)
        fitted_models[name] = model
        manifest_models[name] = persist_model(name, model, spec, scale)

    categorical_levels = {
        col: sorted(x_train[col].dropna().astype(str).unique().tolist())
        for col in CATEGORICAL_FEATURES
    }
    monitoring_baseline = build_monitoring_baseline(x_train)

    parity_frame = x_test.head(25).copy()
    parity_records = records_from_frame(parity_frame)
    parity_scores = []
    direct = {
        name: np.clip(model.predict(parity_frame), 1e-12, None)
        * manifest_models[name]["locked_scale"]
        for name, model in fitted_models.items()
    }
    for idx in range(len(parity_frame)):
        parity_scores.append(
            {
                "reference_frequency": float(direct["poisson_glm_frequency"][idx]),
                "challenger_frequency": float(direct["xgb_poisson_frequency"][idx]),
                "reference_pure_premium": float(direct["tweedie_glm_pure_premium"][idx]),
                "challenger_pure_premium": float(direct["xgb_tweedie_pure_premium"][idx]),
            }
        )

    training_environment = capture_model_environment()
    manifest = {
        "bundle_contract_version": "0.26",
        "model_version": "v0.21-shadow-2022-train-2023-calibration",
        "governance_status": SHADOW_GOVERNANCE_STATUS,
        "source_dataset": str(DATA_PATH),
        "train_year": 2022,
        "calibration_year": 2023,
        "evaluation_year": 2024,
        "feature_contract_hash": feature_contract_hash(),
        "features": FEATURES,
        "categorical_levels": categorical_levels,
        "monitoring_baseline": monitoring_baseline,
        "training_environment": training_environment,
        "serialization": {
            "format": "hybrid_sklearn_joblib_plus_xgboost_native_ubj",
            "pickle_compatibility_policy": "exact_match_for_joblib_pickle_stack",
            "xgboost_compatibility_policy": "same_major_minor_for_native_model_io",
            "environment_check_before_deserialization": True,
            "xgboost_removed_from_pickle": True,
        },
        "models": manifest_models,
        "interpretation_boundary": (
            "Shadow comparison only. The v0.20 global model-family decision is HOLD. "
            "Scores are risk-model outputs, not customer premiums, underwriting decisions, "
            "or evidence of transfer to FIRST CENTRAL / the UK motor market."
        ),
    }

    (OUTDIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUTDIR / "parity_reference.json").write_text(
        json.dumps({"records": parity_records, "scores": parity_scores}, indent=2),
        encoding="utf-8",
    )
    serialization_parity = verify_same_fit_serialization_parity(
        parity_records, parity_scores
    )
    (OUTDIR / "serialization_parity_summary.json").write_text(
        json.dumps(serialization_parity, indent=2), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "bundle": str(OUTDIR),
                "bundle_contract_version": manifest["bundle_contract_version"],
                "model_version": manifest["model_version"],
                "governance_status": manifest["governance_status"],
                "models": list(manifest_models),
                "parity_records": len(parity_records),
                "monitoring_baseline_source": monitoring_baseline["source"],
                "training_environment": training_environment,
                "serialization_parity": serialization_parity,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
