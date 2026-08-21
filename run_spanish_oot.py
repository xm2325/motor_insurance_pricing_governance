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

# Strict pre-outcome feature set. Claim-history fields are intentionally excluded
# because their as-of timing relative to the current-year outcome is ambiguous in
# the source data and the original modelling code also removes them.
CATEGORICAL = ["Distribution_channel", "Payment", "Type_risk", "Area", "Second_driver", "Type_fuel"]
NUMERIC = [
    "Seniority", "Policies_in_force", "Max_policies", "Max_products",
    "Power", "Cylinder_capacity", "Value_vehicle", "N_doors", "Length", "Weight",
]


def load_data(path: str) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, sep=";", low_memory=False)
    source_rows = len(raw)
    df = raw.copy()
    df["renewal_date"] = pd.to_datetime(df["Date_last_renewal"], dayfirst=True, errors="coerce")
    df["renewal_year"] = df["renewal_date"].dt.year
    next_renewal = pd.to_datetime(df["Date_next_renewal"], dayfirst=True, errors="coerce")

    if "Date_lapse" in df:
        lapse = pd.to_datetime(df["Date_lapse"], dayfirst=True, errors="coerce")
        end = next_renewal.where(lapse.isna() | (next_renewal < lapse), lapse)
    else:
        end = next_renewal

    raw_exposure = (end - df["renewal_date"]).dt.days / 365.25
    df["Exposure"] = raw_exposure.clip(upper=1.0)
    nonpositive_exposure = int((df["Exposure"].fillna(0) <= 0).sum())
    missing_year = int(df["renewal_year"].isna().sum())

    df["N_claims_year"] = pd.to_numeric(df["N_claims_year"], errors="coerce").fillna(0).clip(lower=0)
    df["Cost_claims_year"] = pd.to_numeric(df["Cost_claims_year"], errors="coerce").fillna(0).clip(lower=0)
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Match the source project's exposure rule: cap at one year, then remove
    # zero/negative exposure rather than converting it to a one-day exposure.
    df = df[df["renewal_year"].notna() & df["Exposure"].notna() & (df["Exposure"] > 0)].copy()

    audit = {
        "source_rows": int(source_rows),
        "valid_rows_after_exposure_filter": int(len(df)),
        "removed_nonpositive_or_missing_exposure": int(source_rows - len(df) - missing_year),
        "rows_with_missing_renewal_year": missing_year,
        "raw_nonpositive_exposure_rows": nonpositive_exposure,
        "feature_policy": "strict_pre_outcome_excludes_N_claims_history_and_R_Claims_history",
    }
    return df, audit


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


def year_summary(df: pd.DataFrame) -> dict:
    out = {}
    for year, g in df.groupby("renewal_year"):
        exposure = float(g["Exposure"].sum())
        claims = float(g["N_claims_year"].sum())
        loss = float(g["Cost_claims_year"].sum())
        out[str(int(year))] = {
            "rows": int(len(g)),
            "unique_ids": int(g["ID"].nunique()),
            "exposure": exposure,
            "claims": claims,
            "claim_frequency": claims / max(exposure, 1e-12),
            "loss": loss,
            "pure_premium": loss / max(exposure, 1e-12),
        }
    return out


def aggregate_scale(actual_total: float, pred_rate: np.ndarray, exposure: np.ndarray) -> float:
    predicted_total = float(np.sum(pred_rate * exposure))
    return float(actual_total / max(predicted_total, 1e-12))


def frequency_metrics(name: str, y_rate: np.ndarray, claims: np.ndarray, pred: np.ndarray, exposure: np.ndarray) -> dict:
    return {
        "model": name,
        "poisson_deviance": float(mean_poisson_deviance(y_rate, pred, sample_weight=exposure)),
        "claim_calibration_ratio_pred_over_actual": float(np.sum(pred * exposure) / max(np.sum(claims), 1e-12)),
        "top10_claim_capture": top_capture(claims, pred, exposure),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data_spanish/Motor_vehicle_insurance_data.csv")
    parser.add_argument("--outdir", default="results_oot")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    df, construction_audit = load_data(args.data)
    yearly = year_summary(df)
    usable_years = [int(year) for year, stats in yearly.items() if stats["rows"] >= 1000]
    usable_years = sorted(usable_years)
    if len(usable_years) < 3:
        raise SystemExit(f"Need at least three calendar years with >=1000 rows for train/calibration/OOT; got {yearly}")

    test_year = usable_years[-1]
    calibration_year = usable_years[-2]
    train_years = [year for year in usable_years if year < calibration_year]
    if not train_years:
        raise SystemExit("No pre-calibration training year available")

    train = df[df["renewal_year"].isin(train_years)].copy()
    calibration = df[df["renewal_year"] == calibration_year].copy()
    test = df[df["renewal_year"] == test_year].copy()
    if train.empty or calibration.empty or test.empty:
        raise SystemExit("Calendar OOT split produced an empty partition")

    features = NUMERIC + CATEGORICAL
    x_train = train[features]
    x_cal = calibration[features]
    x_test = test[features]
    exposure_train = train["Exposure"].to_numpy()
    exposure_cal = calibration["Exposure"].to_numpy()
    exposure_test = test["Exposure"].to_numpy()
    claims_train = train["N_claims_year"].to_numpy()
    claims_cal = calibration["N_claims_year"].to_numpy()
    claims_test = test["N_claims_year"].to_numpy()
    y_frequency_train = claims_train / exposure_train
    y_frequency_cal = claims_cal / exposure_cal
    y_frequency_test = claims_test / exposure_test

    models = {
        "Poisson_GLM": make_pipeline(PoissonRegressor(alpha=1e-4, max_iter=500)),
        "XGBoost_Poisson": make_pipeline(XGBRegressor(
            objective="count:poisson", n_estimators=300, max_depth=4,
            learning_rate=0.04, subsample=0.9, colsample_bytree=0.9,
            n_jobs=2, random_state=42,
        )),
    }

    frequency_rows = []
    for name, model in models.items():
        model.fit(x_train, y_frequency_train, model__sample_weight=exposure_train)
        pred_cal_raw = np.clip(model.predict(x_cal), 1e-9, None)
        pred_test_raw = np.clip(model.predict(x_test), 1e-9, None)
        locked_scale = aggregate_scale(float(claims_cal.sum()), pred_cal_raw, exposure_cal)
        pred_test_locked = np.clip(pred_test_raw * locked_scale, 1e-9, None)

        raw = frequency_metrics(name + "_raw", y_frequency_test, claims_test, pred_test_raw, exposure_test)
        locked = frequency_metrics(name + "_locked_calibration", y_frequency_test, claims_test, pred_test_locked, exposure_test)
        frequency_rows.append({
            "model": name,
            "train_years": ",".join(map(str, train_years)),
            "calibration_year": calibration_year,
            "test_year": test_year,
            "n_train": int(len(train)),
            "n_calibration": int(len(calibration)),
            "n_test": int(len(test)),
            "calibration_scale_from_prior_year": locked_scale,
            "calibration_year_raw_ratio_pred_over_actual": float(np.sum(pred_cal_raw * exposure_cal) / max(claims_cal.sum(), 1e-12)),
            "test_raw_poisson_deviance": raw["poisson_deviance"],
            "test_raw_calibration_ratio_pred_over_actual": raw["claim_calibration_ratio_pred_over_actual"],
            "test_locked_poisson_deviance": locked["poisson_deviance"],
            "test_locked_calibration_ratio_pred_over_actual": locked["claim_calibration_ratio_pred_over_actual"],
            "test_top10_claim_capture": locked["top10_claim_capture"],
        })
    pd.DataFrame(frequency_rows).to_csv(outdir / "oot_frequency_model_comparison.csv", index=False)

    loss_train = train["Cost_claims_year"].to_numpy()
    loss_cal = calibration["Cost_claims_year"].to_numpy()
    loss_test = test["Cost_claims_year"].to_numpy()
    y_loss_train = loss_train / exposure_train
    y_loss_cal = loss_cal / exposure_cal
    y_loss_test = loss_test / exposure_test

    tweedie = make_pipeline(TweedieRegressor(power=1.5, alpha=1e-4, link="log", max_iter=700))
    tweedie.fit(x_train, y_loss_train, model__sample_weight=exposure_train)
    pp_cal_raw = np.clip(tweedie.predict(x_cal), 1e-9, None)
    pp_test_raw = np.clip(tweedie.predict(x_test), 1e-9, None)
    pp_locked_scale = aggregate_scale(float(loss_cal.sum()), pp_cal_raw, exposure_cal)
    pp_test_locked = np.clip(pp_test_raw * pp_locked_scale, 1e-9, None)

    pure_premium_row = {
        "model": "Tweedie_GLM",
        "train_years": ",".join(map(str, train_years)),
        "calibration_year": calibration_year,
        "test_year": test_year,
        "n_train": int(len(train)),
        "n_calibration": int(len(calibration)),
        "n_test": int(len(test)),
        "calibration_scale_from_prior_year": pp_locked_scale,
        "calibration_year_raw_ratio_pred_over_actual": float(np.sum(pp_cal_raw * exposure_cal) / max(loss_cal.sum(), 1e-12)),
        "test_raw_tweedie_deviance_p1_5": float(mean_tweedie_deviance(y_loss_test, pp_test_raw, sample_weight=exposure_test, power=1.5)),
        "test_raw_loss_calibration_ratio_pred_over_actual": float(np.sum(pp_test_raw * exposure_test) / max(loss_test.sum(), 1e-12)),
        "test_locked_tweedie_deviance_p1_5": float(mean_tweedie_deviance(y_loss_test, pp_test_locked, sample_weight=exposure_test, power=1.5)),
        "test_locked_loss_calibration_ratio_pred_over_actual": float(np.sum(pp_test_locked * exposure_test) / max(loss_test.sum(), 1e-12)),
        "test_top10_loss_capture": top_capture(loss_test, pp_test_locked, exposure_test),
    }
    pd.DataFrame([pure_premium_row]).to_csv(outdir / "oot_pure_premium_model_comparison.csv", index=False)

    test_ids = set(test["ID"])
    prior_ids = set(pd.concat([train["ID"], calibration["ID"]]))
    id_transport = {
        "test_unique_ids": int(test["ID"].nunique()),
        "test_ids_seen_before": int(len(test_ids & prior_ids)),
        "test_ids_unseen_before": int(len(test_ids - prior_ids)),
        "share_test_ids_seen_before": float(len(test_ids & prior_ids) / max(len(test_ids), 1)),
    }

    summary = {
        "status": "COMPLETED_STRICT_CALENDAR_OOT_V2",
        "construction_audit": construction_audit,
        "feature_policy": {
            "included_numeric": NUMERIC,
            "included_categorical": CATEGORICAL,
            "excluded_ambiguous_claim_history": ["N_claims_history", "R_Claims_history"],
        },
        "year_summary": yearly,
        "train_years": train_years,
        "calibration_year": calibration_year,
        "test_year": test_year,
        "id_transport": id_transport,
        "frequency_results": frequency_rows,
        "pure_premium_result": pure_premium_row,
        "interpretation_boundary": "Calendar ordering is genuine, but Date_last_renewal defines policy-renewal cohorts rather than a guaranteed claim-occurrence timestamp. Treat as renewal-cohort OOT, not claim-date OOT.",
    }
    (outdir / "oot_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
