from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from xgboost import XGBRegressor

from deployment.bundle import sha256_file
from deployment.contracts import (
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    SHADOW_GOVERNANCE_STATUS,
    feature_contract_hash,
)
from deployment.drift import build_monitoring_baseline
from run_spanish_oot_2024 import DATA_PATH, load_data, locked_scale, make_pipeline

OUTDIR = Path("deployment_artifacts")


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


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
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
        artifact_name = f"{name}.joblib"
        artifact_path = OUTDIR / artifact_name
        joblib.dump(model, artifact_path, compress=3)
        fitted_models[name] = model
        manifest_models[name] = {
            "target": target,
            "role": spec["role"],
            "artifact": artifact_name,
            "locked_scale": float(scale),
            "sha256": sha256_file(artifact_path),
        }

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

    manifest = {
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
    print(json.dumps({
        "bundle": str(OUTDIR),
        "model_version": manifest["model_version"],
        "governance_status": manifest["governance_status"],
        "models": list(manifest_models),
        "parity_records": len(parity_records),
        "monitoring_baseline_source": monitoring_baseline["source"],
    }, indent=2))


if __name__ == "__main__":
    main()
