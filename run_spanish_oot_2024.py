from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

DATA_PATH = Path("data_spanish_2022_2024/Dataset_of_motor_insurance_portfolio.csv")
OUTDIR = Path("results_oot_2024")

# Rating variables available without using current premium, current outcomes, or
# end-of-year policy status. policy_status is excluded because it describes whether
# the policy is active/cancelled during the calendar year and may be post-period.
CATEGORICAL = [
    "policy_type", "business_type", "payment_frequency", "bonus_score",
    "fuel_type", "vehicle_brand", "municipality_type", "circulation_area",
]
NUMERIC = [
    "driver_age", "vehicle_age", "age_driving_licence", "vehicle_value",
    "seats", "power_to_weight_ratio",
]
FEATURES = NUMERIC + CATEGORICAL


def make_pipeline(model) -> Pipeline:
    prep = ColumnTransformer([
        ("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), NUMERIC),
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAL),
    ])
    return Pipeline([("prep", prep), ("model", model)])


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, sep=";", low_memory=False)
    numeric = NUMERIC + ["year", "total_claims", "total_incurred", "total_exposure", "total_premium"]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[
        df["year"].isin([2022, 2023, 2024])
        & df["total_exposure"].notna()
        & (df["total_exposure"] > 0)
        & df["total_claims"].notna()
        & (df["total_claims"] >= 0)
        & df["total_incurred"].notna()
        & (df["total_incurred"] >= 0)
    ].copy()
    return df


def top_capture(outcome: np.ndarray, score: np.ndarray, exposure: np.ndarray, fraction: float = 0.10) -> float:
    order = np.argsort(-score)
    outcome = outcome[order]
    exposure = exposure[order]
    cumulative = np.cumsum(exposure) / max(np.sum(exposure), 1e-12)
    mask = cumulative <= fraction
    if not np.any(mask):
        mask[0] = True
    return float(np.sum(outcome[mask]) / max(np.sum(outcome), 1e-12))


def locked_scale(actual: np.ndarray, pred_rate: np.ndarray, exposure: np.ndarray) -> float:
    actual_total = float(np.sum(actual))
    pred_total = float(np.sum(pred_rate * exposure))
    return actual_total / max(pred_total, 1e-12)


def calibration_ratio(actual: np.ndarray, pred_rate: np.ndarray, exposure: np.ndarray) -> float:
    return float(np.sum(pred_rate * exposure) / max(np.sum(actual), 1e-12))


def year_summary(df: pd.DataFrame) -> dict:
    result = {}
    for year, g in df.groupby("year"):
        exposure = float(g["total_exposure"].sum())
        claims = float(g["total_claims"].sum())
        incurred = float(g["total_incurred"].sum())
        premium = float(g["total_premium"].sum())
        result[str(int(year))] = {
            "rows": int(len(g)),
            "unique_ids": int(g["insured_id"].nunique()),
            "exposure": exposure,
            "claims": claims,
            "claim_frequency": claims / max(exposure, 1e-12),
            "incurred": incurred,
            "pure_premium": incurred / max(exposure, 1e-12),
            "premium": premium,
            "observed_loss_ratio": incurred / max(premium, 1e-12),
        }
    return result


def frequency_metrics(y_rate, claims, pred, exposure) -> dict:
    return {
        "poisson_deviance": float(mean_poisson_deviance(y_rate, pred, sample_weight=exposure)),
        "calibration_ratio_pred_over_actual": calibration_ratio(claims, pred, exposure),
        "top10_claim_capture": top_capture(claims, pred, exposure),
    }


def loss_metrics(y_rate, loss, pred, exposure) -> dict:
    return {
        "tweedie_deviance_p1_5": float(mean_tweedie_deviance(y_rate, pred, sample_weight=exposure, power=1.5)),
        "calibration_ratio_pred_over_actual": calibration_ratio(loss, pred, exposure),
        "top10_loss_capture": top_capture(loss, pred, exposure),
    }


def bootstrap_deviance_differences(
    y_freq: np.ndarray,
    y_loss: np.ndarray,
    exposure: np.ndarray,
    glm_freq: np.ndarray,
    xgb_freq: np.ndarray,
    glm_loss: np.ndarray,
    xgb_loss: np.ndarray,
    reps: int = 250,
    seed: int = 2026,
) -> tuple[dict, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n = len(y_freq)
    rows = []
    for b in range(reps):
        idx = rng.integers(0, n, size=n)
        w = exposure[idx]
        freq_diff = mean_poisson_deviance(y_freq[idx], glm_freq[idx], sample_weight=w) - mean_poisson_deviance(y_freq[idx], xgb_freq[idx], sample_weight=w)
        loss_diff = mean_tweedie_deviance(y_loss[idx], glm_loss[idx], sample_weight=w, power=1.5) - mean_tweedie_deviance(y_loss[idx], xgb_loss[idx], sample_weight=w, power=1.5)
        rows.append({"rep": b, "glm_minus_xgb_frequency_deviance": freq_diff, "glm_minus_xgb_tweedie_deviance": loss_diff})
    frame = pd.DataFrame(rows)
    summary = {}
    for col in ["glm_minus_xgb_frequency_deviance", "glm_minus_xgb_tweedie_deviance"]:
        vals = frame[col].to_numpy()
        summary[col] = {
            "mean": float(np.mean(vals)),
            "ci95_low": float(np.quantile(vals, 0.025)),
            "ci95_high": float(np.quantile(vals, 0.975)),
            "p_gt_0": float(np.mean(vals > 0)),
        }
    return summary, frame


def segment_metrics(test: pd.DataFrame, pred_map: dict[str, np.ndarray]) -> pd.DataFrame:
    prior_ids = set(pd.read_csv(DATA_PATH, sep=";", usecols=["insured_id", "year"], low_memory=False).query("year in [2022, 2023]")["insured_id"])
    seen = test["insured_id"].isin(prior_ids).to_numpy()
    driver_age = pd.to_numeric(test["driver_age"], errors="coerce")
    age_band = pd.cut(driver_age, bins=[0, 24, 34, 49, 64, 200], labels=["<25", "25-34", "35-49", "50-64", "65+"]).astype(str)

    base = test[["total_claims", "total_incurred", "total_exposure", "business_type"]].reset_index(drop=True).copy()
    base["seen_before_2024"] = np.where(seen, "seen", "unseen")
    base["driver_age_band"] = age_band.reset_index(drop=True)
    for name, values in pred_map.items():
        base[name] = values

    rows = []
    for dimension in ["seen_before_2024", "business_type", "driver_age_band"]:
        for group, g in base.groupby(dimension, dropna=False):
            idx = g.index.to_numpy()
            exposure = g["total_exposure"].to_numpy(float)
            claims = g["total_claims"].to_numpy(float)
            loss = g["total_incurred"].to_numpy(float)
            row = {
                "dimension": dimension,
                "group": str(group),
                "rows": int(len(g)),
                "exposure": float(exposure.sum()),
                "claims": float(claims.sum()),
                "incurred": float(loss.sum()),
            }
            for key, values in pred_map.items():
                pred = values[idx]
                actual = claims if "freq" in key else loss
                row[f"{key}_calibration_ratio"] = calibration_ratio(actual, pred, exposure)
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    yearly = year_summary(df)
    train = df[df["year"] == 2022].copy().reset_index(drop=True)
    calibration = df[df["year"] == 2023].copy().reset_index(drop=True)
    test = df[df["year"] == 2024].copy().reset_index(drop=True)

    if min(len(train), len(calibration), len(test)) == 0:
        raise RuntimeError("2022/2023/2024 split contains an empty partition")

    x_train = train[FEATURES]
    x_cal = calibration[FEATURES]
    x_test = test[FEATURES]
    e_train = train["total_exposure"].to_numpy(float)
    e_cal = calibration["total_exposure"].to_numpy(float)
    e_test = test["total_exposure"].to_numpy(float)

    claims_train = train["total_claims"].to_numpy(float)
    claims_cal = calibration["total_claims"].to_numpy(float)
    claims_test = test["total_claims"].to_numpy(float)
    y_freq_train = claims_train / e_train
    y_freq_test = claims_test / e_test

    freq_models = {
        "Poisson_GLM": make_pipeline(PoissonRegressor(alpha=1e-4, max_iter=600)),
        "XGBoost_Poisson": make_pipeline(XGBRegressor(
            objective="count:poisson", n_estimators=450, max_depth=4,
            learning_rate=0.035, subsample=0.9, colsample_bytree=0.9,
            min_child_weight=5, reg_lambda=1.0, n_jobs=2, random_state=42,
        )),
    }

    frequency_rows = []
    locked_freq_preds: dict[str, np.ndarray] = {}
    for name, model in freq_models.items():
        model.fit(x_train, y_freq_train, model__sample_weight=e_train)
        pred_cal = np.clip(model.predict(x_cal), 1e-9, None)
        pred_test_raw = np.clip(model.predict(x_test), 1e-9, None)
        scale = locked_scale(claims_cal, pred_cal, e_cal)
        pred_test = np.clip(pred_test_raw * scale, 1e-9, None)
        locked_freq_preds[name] = pred_test
        raw_metrics = frequency_metrics(y_freq_test, claims_test, pred_test_raw, e_test)
        locked_metrics = frequency_metrics(y_freq_test, claims_test, pred_test, e_test)
        frequency_rows.append({
            "model": name,
            "train_year": 2022,
            "calibration_year": 2023,
            "test_year": 2024,
            "n_train": len(train),
            "n_calibration": len(calibration),
            "n_test": len(test),
            "locked_scale_from_2023": scale,
            "calibration_2023_raw_ratio": calibration_ratio(claims_cal, pred_cal, e_cal),
            **{f"test_raw_{k}": v for k, v in raw_metrics.items()},
            **{f"test_locked_{k}": v for k, v in locked_metrics.items()},
        })
    frequency_frame = pd.DataFrame(frequency_rows)
    frequency_frame.to_csv(OUTDIR / "oot_2024_frequency_model_comparison.csv", index=False)

    loss_train = train["total_incurred"].to_numpy(float)
    loss_cal = calibration["total_incurred"].to_numpy(float)
    loss_test = test["total_incurred"].to_numpy(float)
    y_loss_train = loss_train / e_train
    y_loss_test = loss_test / e_test

    loss_models = {
        "Tweedie_GLM": make_pipeline(TweedieRegressor(power=1.5, alpha=1e-4, link="log", max_iter=900)),
        "XGBoost_Tweedie": make_pipeline(XGBRegressor(
            objective="reg:tweedie", tweedie_variance_power=1.5,
            n_estimators=500, max_depth=4, learning_rate=0.03,
            subsample=0.9, colsample_bytree=0.9, min_child_weight=5,
            reg_lambda=1.0, n_jobs=2, random_state=42,
        )),
    }

    loss_rows = []
    locked_loss_preds: dict[str, np.ndarray] = {}
    for name, model in loss_models.items():
        model.fit(x_train, y_loss_train, model__sample_weight=e_train)
        pred_cal = np.clip(model.predict(x_cal), 1e-9, None)
        pred_test_raw = np.clip(model.predict(x_test), 1e-9, None)
        scale = locked_scale(loss_cal, pred_cal, e_cal)
        pred_test = np.clip(pred_test_raw * scale, 1e-9, None)
        locked_loss_preds[name] = pred_test
        raw_metrics = loss_metrics(y_loss_test, loss_test, pred_test_raw, e_test)
        locked_metrics = loss_metrics(y_loss_test, loss_test, pred_test, e_test)
        loss_rows.append({
            "model": name,
            "train_year": 2022,
            "calibration_year": 2023,
            "test_year": 2024,
            "n_train": len(train),
            "n_calibration": len(calibration),
            "n_test": len(test),
            "locked_scale_from_2023": scale,
            "calibration_2023_raw_ratio": calibration_ratio(loss_cal, pred_cal, e_cal),
            **{f"test_raw_{k}": v for k, v in raw_metrics.items()},
            **{f"test_locked_{k}": v for k, v in locked_metrics.items()},
        })
    loss_frame = pd.DataFrame(loss_rows)
    loss_frame.to_csv(OUTDIR / "oot_2024_pure_premium_model_comparison.csv", index=False)

    bootstrap_summary, bootstrap_frame = bootstrap_deviance_differences(
        y_freq_test, y_loss_test, e_test,
        locked_freq_preds["Poisson_GLM"], locked_freq_preds["XGBoost_Poisson"],
        locked_loss_preds["Tweedie_GLM"], locked_loss_preds["XGBoost_Tweedie"],
    )
    bootstrap_frame.to_csv(OUTDIR / "oot_2024_bootstrap_deviance_differences.csv", index=False)

    pred_map = {
        "glm_freq": locked_freq_preds["Poisson_GLM"],
        "xgb_freq": locked_freq_preds["XGBoost_Poisson"],
        "glm_loss": locked_loss_preds["Tweedie_GLM"],
        "xgb_loss": locked_loss_preds["XGBoost_Tweedie"],
    }
    segments = segment_metrics(test, pred_map)
    segments.to_csv(OUTDIR / "oot_2024_transport_segment_calibration.csv", index=False)

    prior_ids = set(pd.concat([train["insured_id"], calibration["insured_id"]]))
    test_ids = set(test["insured_id"])
    id_transport = {
        "test_unique_ids": int(test["insured_id"].nunique()),
        "test_ids_seen_in_2022_or_2023": int(len(test_ids & prior_ids)),
        "test_ids_unseen_before_2024": int(len(test_ids - prior_ids)),
        "share_test_ids_seen_before": float(len(test_ids & prior_ids) / max(len(test_ids), 1)),
    }

    # Decision rules: challenger must have a positive 95% CI for deviance gain and
    # locked aggregate calibration within 10% of observed total on 2024.
    freq_xgb = frequency_frame.set_index("model").loc["XGBoost_Poisson"]
    loss_xgb = loss_frame.set_index("model").loc["XGBoost_Tweedie"]
    freq_boot = bootstrap_summary["glm_minus_xgb_frequency_deviance"]
    loss_boot = bootstrap_summary["glm_minus_xgb_tweedie_deviance"]
    freq_pass = (
        0.90 <= freq_xgb["test_locked_calibration_ratio_pred_over_actual"] <= 1.10
        and freq_boot["ci95_low"] > 0
    )
    loss_pass = (
        0.90 <= loss_xgb["test_locked_calibration_ratio_pred_over_actual"] <= 1.10
        and loss_boot["ci95_low"] > 0
    )
    decision = {
        "frequency_challenger": "PASS" if freq_pass else "HOLD",
        "pure_premium_challenger": "PASS" if loss_pass else "HOLD",
        "overall": "PROMOTE" if (freq_pass and loss_pass) else "HOLD",
        "rule": "2024 locked calibration ratio in [0.90,1.10] AND 95% bootstrap CI for GLM-minus-XGB deviance strictly above zero",
    }

    summary = {
        "status": "COMPLETED_2022_TRAIN_2023_CALIBRATION_2024_OOT",
        "data_source": {
            "dataset_id": "sw4jmdb2sm",
            "version": 1,
            "rows_used": int(len(df)),
            "features": FEATURES,
            "excluded_from_features": [
                "insured_id", "year", "policy_status", "total_premium",
                "all coverage premiums", "all current claim counts", "all current incurred losses",
                "total_exposure",
            ],
        },
        "year_summary": yearly,
        "split": {"train": 2022, "calibration": 2023, "test": 2024},
        "id_transport": id_transport,
        "frequency_results": frequency_rows,
        "pure_premium_results": loss_rows,
        "bootstrap": bootstrap_summary,
        "model_change_decision": decision,
        "interpretation_boundary": "Real calendar policy-year OOT within one Spanish insurer. It is not evidence of transport to FIRST CENTRAL or the UK motor market.",
    }
    (OUTDIR / "oot_2024_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTDIR / "oot_2024_model_decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
