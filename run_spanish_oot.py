from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

CATEGORICAL = ["Distribution_channel", "Payment", "Type_risk", "Area", "Second_driver", "Type_fuel"]
NUMERIC = [
    "Seniority", "Policies_in_force", "Max_policies", "Max_products",
    "N_claims_history", "R_Claims_history", "Power", "Cylinder_capacity",
    "Value_vehicle", "N_doors", "Length", "Weight",
]


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", low_memory=False)
    df["renewal_date"] = pd.to_datetime(df["Date_last_renewal"], dayfirst=True, errors="coerce")
    df["renewal_year"] = df["renewal_date"].dt.year
    next_renewal = pd.to_datetime(df["Date_next_renewal"], dayfirst=True, errors="coerce")
    if "Date_lapse" in df:
        lapse = pd.to_datetime(df["Date_lapse"], dayfirst=True, errors="coerce")
        end = next_renewal.where(lapse.isna() | (next_renewal < lapse), lapse)
    else:
        end = next_renewal
    df["Exposure"] = ((end - df["renewal_date"]).dt.days / 365.25).clip(lower=1 / 365.25, upper=1.0)
    df["N_claims_year"] = pd.to_numeric(df["N_claims_year"], errors="coerce").fillna(0).clip(lower=0)
    df["Cost_claims_year"] = pd.to_numeric(df["Cost_claims_year"], errors="coerce").fillna(0).clip(lower=0)
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["renewal_year", "Exposure"])


def top_capture(outcome, score, exposure, fraction: float = 0.10) -> float:
    frame = pd.DataFrame({"outcome": outcome, "score": score, "exposure": exposure}).sort_values("score", ascending=False)
    frame["cum_exposure"] = frame["exposure"].cumsum() / frame["exposure"].sum()
    selected = frame[frame["cum_exposure"] <= fraction]
    if selected.empty:
        selected = frame.iloc[:1]
    return float(selected["outcome"].sum() / max(frame["outcome"].sum(), 1e-12))


def make_pipeline(model) -> Pipeline:
    prep = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore"))]), CATEGORICAL),
    ])
    return Pipeline([("prep", prep), ("model", model)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data_spanish/Motor_vehicle_insurance_data.csv")
    parser.add_argument("--outdir", default="results_oot")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    df = load_data(args.data)
    rows_by_year = df.groupby("renewal_year").size().sort_index()
    usable_years = [int(year) for year, n in rows_by_year.items() if n >= 1000]
    if len(usable_years) < 2:
        raise SystemExit(f"Need at least two calendar years with >=1000 rows; got {rows_by_year.to_dict()}")

    test_year = max(usable_years)
    train_years = [year for year in usable_years if year < test_year]
    train = df[df["renewal_year"].isin(train_years)].copy()
    test = df[df["renewal_year"] == test_year].copy()
    if train.empty or test.empty:
        raise SystemExit("Calendar OOT split produced an empty partition")

    features = NUMERIC + CATEGORICAL
    x_train, x_test = train[features], test[features]
    exposure_train = train["Exposure"].to_numpy()
    exposure_test = test["Exposure"].to_numpy()
    y_frequency_train = (train["N_claims_year"] / train["Exposure"]).to_numpy()
    y_frequency_test = (test["N_claims_year"] / test["Exposure"]).to_numpy()

    models = {
        "Poisson_GLM": make_pipeline(PoissonRegressor(alpha=1e-4, max_iter=400)),
        "XGBoost_Poisson": make_pipeline(XGBRegressor(
            objective="count:poisson", n_estimators=250, max_depth=4,
            learning_rate=0.05, subsample=0.9, colsample_bytree=0.9,
            n_jobs=2, random_state=42,
        )),
    }

    frequency_rows = []
    for name, model in models.items():
        model.fit(x_train, y_frequency_train, model__sample_weight=exposure_train)
        pred = np.clip(model.predict(x_test), 1e-9, None)
        frequency_rows.append({
            "model": name,
            "train_years": ",".join(map(str, train_years)),
            "test_year": test_year,
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "poisson_deviance": float(mean_poisson_deviance(y_frequency_test, pred, sample_weight=exposure_test)),
            "claim_calibration_ratio": float(np.sum(pred * exposure_test) / max(test["N_claims_year"].sum(), 1e-12)),
            "top10_claim_capture": top_capture(test["N_claims_year"], pred, exposure_test),
        })
    pd.DataFrame(frequency_rows).to_csv(outdir / "oot_frequency_model_comparison.csv", index=False)

    y_loss_train = (train["Cost_claims_year"] / train["Exposure"]).to_numpy()
    y_loss_test = (test["Cost_claims_year"] / test["Exposure"]).to_numpy()
    tweedie = make_pipeline(TweedieRegressor(power=1.5, alpha=1e-4, link="log", max_iter=500))
    tweedie.fit(x_train, y_loss_train, model__sample_weight=exposure_train)
    pure_premium_pred = np.clip(tweedie.predict(x_test), 1e-9, None)
    pure_premium_row = {
        "model": "Tweedie_GLM",
        "train_years": ",".join(map(str, train_years)),
        "test_year": test_year,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "tweedie_deviance_p1_5": float(mean_tweedie_deviance(y_loss_test, pure_premium_pred, sample_weight=exposure_test, power=1.5)),
        "loss_calibration_ratio": float(np.sum(pure_premium_pred * exposure_test) / max(test["Cost_claims_year"].sum(), 1e-12)),
        "top10_loss_capture": top_capture(test["Cost_claims_year"], pure_premium_pred, exposure_test),
    }
    pd.DataFrame([pure_premium_row]).to_csv(outdir / "oot_pure_premium_model_comparison.csv", index=False)

    summary = {
        "status": "COMPLETED_REAL_CALENDAR_OOT",
        "train_years": train_years,
        "test_year": test_year,
        "rows_by_year": {str(int(k)): int(v) for k, v in rows_by_year.items()},
        "frequency_results": frequency_rows,
        "pure_premium_result": pure_premium_row,
    }
    (outdir / "oot_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
