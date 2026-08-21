from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance
from xgboost import XGBRegressor

from run_spanish_oot_2024 import (
    FEATURES,
    calibration_ratio,
    load_data,
    make_pipeline,
    top_capture,
)

OUTDIR = Path("results_oot_2024")


def bootstrap_diff(y, exposure, pred_glm, pred_xgb, metric: str, reps: int = 200, seed: int = 20260821):
    rng = np.random.default_rng(seed)
    n = len(y)
    diffs = np.empty(reps, dtype=float)
    for b in range(reps):
        idx = rng.integers(0, n, size=n)
        if metric == "poisson":
            diffs[b] = mean_poisson_deviance(y[idx], pred_glm[idx], sample_weight=exposure[idx]) - mean_poisson_deviance(y[idx], pred_xgb[idx], sample_weight=exposure[idx])
        else:
            diffs[b] = mean_tweedie_deviance(y[idx], pred_glm[idx], sample_weight=exposure[idx], power=1.5) - mean_tweedie_deviance(y[idx], pred_xgb[idx], sample_weight=exposure[idx], power=1.5)
    return {
        "mean": float(diffs.mean()),
        "ci95_low": float(np.quantile(diffs, 0.025)),
        "ci95_high": float(np.quantile(diffs, 0.975)),
        "p_gt_0": float(np.mean(diffs > 0)),
    }


def fit_window(df: pd.DataFrame, train_years: list[int], test_year: int) -> dict:
    train = df[df["year"].isin(train_years)].copy().reset_index(drop=True)
    test = df[df["year"] == test_year].copy().reset_index(drop=True)
    x_train, x_test = train[FEATURES], test[FEATURES]
    e_train = train["total_exposure"].to_numpy(float)
    e_test = test["total_exposure"].to_numpy(float)

    claims_train = train["total_claims"].to_numpy(float)
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
    freq_pred = {}
    freq_rows = []
    for name, model in freq_models.items():
        model.fit(x_train, y_freq_train, model__sample_weight=e_train)
        pred = np.clip(model.predict(x_test), 1e-9, None)
        freq_pred[name] = pred
        freq_rows.append({
            "model": name,
            "deviance": float(mean_poisson_deviance(y_freq_test, pred, sample_weight=e_test)),
            "calibration_ratio": calibration_ratio(claims_test, pred, e_test),
            "top10_capture": top_capture(claims_test, pred, e_test),
        })

    loss_train = train["total_incurred"].to_numpy(float)
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
    loss_pred = {}
    loss_rows = []
    for name, model in loss_models.items():
        model.fit(x_train, y_loss_train, model__sample_weight=e_train)
        pred = np.clip(model.predict(x_test), 1e-9, None)
        loss_pred[name] = pred
        loss_rows.append({
            "model": name,
            "deviance": float(mean_tweedie_deviance(y_loss_test, pred, sample_weight=e_test, power=1.5)),
            "calibration_ratio": calibration_ratio(loss_test, pred, e_test),
            "top10_capture": top_capture(loss_test, pred, e_test),
        })

    return {
        "train_years": train_years,
        "test_year": test_year,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "frequency": freq_rows,
        "pure_premium": loss_rows,
        "frequency_bootstrap_glm_minus_xgb": bootstrap_diff(
            y_freq_test, e_test, freq_pred["Poisson_GLM"], freq_pred["XGBoost_Poisson"], "poisson"
        ),
        "pure_premium_bootstrap_glm_minus_xgb": bootstrap_diff(
            y_loss_test, e_test, loss_pred["Tweedie_GLM"], loss_pred["XGBoost_Tweedie"], "tweedie"
        ),
    }


def cohort_gate_from_v13() -> dict:
    path = OUTDIR / "oot_2024_transport_segment_calibration.csv"
    if not path.exists():
        return {"status": "NOT_AVAILABLE"}
    seg = pd.read_csv(path)
    seen = seg[seg["dimension"] == "seen_before_2024"].set_index("group")
    threshold = [0.85, 1.15]
    rows = {}
    for group in ["seen", "unseen"]:
        if group not in seen.index:
            continue
        r = seen.loc[group]
        rows[group] = {
            "glm_loss_calibration": float(r["glm_loss_calibration_ratio"]),
            "xgb_loss_calibration": float(r["xgb_loss_calibration_ratio"]),
            "glm_within_illustrative_0_85_1_15": bool(threshold[0] <= r["glm_loss_calibration_ratio"] <= threshold[1]),
            "xgb_within_illustrative_0_85_1_15": bool(threshold[0] <= r["xgb_loss_calibration_ratio"] <= threshold[1]),
        }
    return {
        "status": "DIAGNOSTIC_ONLY",
        "threshold_note": "Illustrative portfolio diagnostic only; not a FIRST CENTRAL or regulatory threshold.",
        "cohorts": rows,
    }


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    windows = [
        fit_window(df, [2022], 2023),
        fit_window(df, [2022, 2023], 2024),
    ]

    rows = []
    for w in windows:
        for target in ["frequency", "pure_premium"]:
            for model in w[target]:
                rows.append({
                    "target": target,
                    "train_years": ",".join(map(str, w["train_years"])),
                    "test_year": w["test_year"],
                    "n_train": w["n_train"],
                    "n_test": w["n_test"],
                    **model,
                })
    pd.DataFrame(rows).to_csv(OUTDIR / "rolling_origin_v14_model_comparison.csv", index=False)

    summary = {
        "status": "COMPLETED_ROLLING_ORIGIN_V14",
        "purpose": "Model-family temporal stability check. This does not replace the locked 2022 train -> 2023 calibration -> 2024 untouched OOT deployment gate.",
        "windows": windows,
        "new_vs_existing_business_gate": cohort_gate_from_v13(),
        "decision_rule": "Do not promote a challenger unless directionally better performance is repeatable across temporal windows and the locked 2024 gate is cleared.",
    }
    (OUTDIR / "rolling_origin_v14_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
