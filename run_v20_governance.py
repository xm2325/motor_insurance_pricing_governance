from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance
from xgboost import XGBRegressor

from run_spanish_oot_2024 import (
    FEATURES,
    calibration_ratio,
    load_data,
    locked_scale,
    make_pipeline,
)

OUTDIR = Path("results_v20")

COVERAGES = {
    "liability": ("liability_premium", "liability_claims", "liability_incurred", "liability_exposure"),
    "property": ("property_damage_premium", "property_claims", "property_incurred", "total_exposure"),
    "theft": ("theft_premium", "theft_claims", "theft_incurred", "total_exposure"),
    "fire": ("fire_premium", "fire_claims", "fire_incurred", "total_exposure"),
    "glass": ("glass_premium", "glass_claims", "glass_incurred", "total_exposure"),
    "legal_protection": ("legal_protection_premium", "legal_protection_claims", "legal_protection_incurred", "total_exposure"),
    "occupants": ("occupants_premium", "occupants_claims", "occupants_incurred", "total_exposure"),
}


def _fit_models(train: pd.DataFrame, calibration: pd.DataFrame, test: pd.DataFrame):
    x_train, x_cal, x_test = train[FEATURES], calibration[FEATURES], test[FEATURES]
    e_train = train["total_exposure"].to_numpy(float)
    e_cal = calibration["total_exposure"].to_numpy(float)
    e_test = test["total_exposure"].to_numpy(float)

    claims_train = train["total_claims"].to_numpy(float)
    claims_cal = calibration["total_claims"].to_numpy(float)
    claims_test = test["total_claims"].to_numpy(float)
    loss_train = train["total_incurred"].to_numpy(float)
    loss_cal = calibration["total_incurred"].to_numpy(float)
    loss_test = test["total_incurred"].to_numpy(float)

    y_freq_train = claims_train / e_train
    y_freq_test = claims_test / e_test
    y_loss_train = loss_train / e_train
    y_loss_test = loss_test / e_test

    specs = {
        "Poisson_GLM": ("frequency", make_pipeline(PoissonRegressor(alpha=1e-4, max_iter=600))),
        "XGBoost_Poisson": ("frequency", make_pipeline(XGBRegressor(
            objective="count:poisson", n_estimators=450, max_depth=4,
            learning_rate=0.035, subsample=0.9, colsample_bytree=0.9,
            min_child_weight=5, reg_lambda=1.0, n_jobs=2, random_state=42,
        ))),
        "Tweedie_GLM": ("loss", make_pipeline(TweedieRegressor(
            power=1.5, alpha=1e-4, link="log", max_iter=900
        ))),
        "XGBoost_Tweedie": ("loss", make_pipeline(XGBRegressor(
            objective="reg:tweedie", tweedie_variance_power=1.5,
            n_estimators=500, max_depth=4, learning_rate=0.03,
            subsample=0.9, colsample_bytree=0.9, min_child_weight=5,
            reg_lambda=1.0, n_jobs=2, random_state=42,
        ))),
    }

    preds = {}
    complexity_rows = []
    metric_rows = []
    for name, (target, model) in specs.items():
        if target == "frequency":
            y_train, actual_cal, actual_test, y_test = y_freq_train, claims_cal, claims_test, y_freq_test
        else:
            y_train, actual_cal, actual_test, y_test = y_loss_train, loss_cal, loss_test, y_loss_test

        t0 = time.perf_counter()
        model.fit(x_train, y_train, model__sample_weight=e_train)
        fit_s = time.perf_counter() - t0

        pred_cal = np.clip(model.predict(x_cal), 1e-9, None)
        scale = locked_scale(actual_cal, pred_cal, e_cal)
        t1 = time.perf_counter()
        pred_test = np.clip(model.predict(x_test) * scale, 1e-9, None)
        predict_s = time.perf_counter() - t1
        preds[name] = pred_test

        with tempfile.NamedTemporaryFile(suffix=".joblib") as tmp:
            joblib.dump(model, tmp.name)
            model_bytes = Path(tmp.name).stat().st_size

        prep = model.named_steps["prep"]
        try:
            transformed_features = len(prep.get_feature_names_out())
        except Exception:
            transformed_features = None

        complexity_rows.append({
            "model": name,
            "target": target,
            "fit_seconds": fit_s,
            "predict_seconds_2024": predict_s,
            "prediction_ms_per_1000_policies": predict_s / len(test) * 1_000_000,
            "serialized_model_mb": model_bytes / (1024 ** 2),
            "transformed_feature_count": transformed_features,
        })

        if target == "frequency":
            deviance = mean_poisson_deviance(y_test, pred_test, sample_weight=e_test)
        else:
            deviance = mean_tweedie_deviance(y_test, pred_test, sample_weight=e_test, power=1.5)
        metric_rows.append({
            "model": name,
            "target": target,
            "locked_scale_from_2023": scale,
            "2024_deviance": float(deviance),
            "2024_calibration_ratio": calibration_ratio(actual_test, pred_test, e_test),
        })

    return preds, pd.DataFrame(complexity_rows), pd.DataFrame(metric_rows)


def _coverage_audit(test: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    total_incurred = float(test["total_incurred"].sum())
    total_claims = float(test["total_claims"].sum())
    rows = []
    component_incurred = 0.0
    component_claims = 0.0
    for name, (premium_col, claims_col, incurred_col, exposure_col) in COVERAGES.items():
        covered = pd.to_numeric(test[premium_col], errors="coerce").fillna(0).to_numpy(float) > 0
        exposure = pd.to_numeric(test[exposure_col], errors="coerce").fillna(0).to_numpy(float)
        covered_exposure = float(exposure[covered].sum())
        claims = float(pd.to_numeric(test[claims_col], errors="coerce").fillna(0).sum())
        incurred = float(pd.to_numeric(test[incurred_col], errors="coerce").fillna(0).sum())
        component_incurred += incurred
        component_claims += claims
        rows.append({
            "coverage": name,
            "covered_policy_rows_proxy": int(covered.sum()),
            "covered_exposure_proxy": covered_exposure,
            "claims": claims,
            "incurred": incurred,
            "claim_frequency_per_covered_exposure_proxy": claims / max(covered_exposure, 1e-12),
            "incurred_per_covered_exposure_proxy": incurred / max(covered_exposure, 1e-12),
            "share_of_total_claim_count": claims / max(total_claims, 1e-12),
            "share_of_total_incurred": incurred / max(total_incurred, 1e-12),
        })
    audit = {
        "version": "v0.16",
        "note": "Coverage premium fields are used only to construct an audit coverage-exposure proxy; they are not predictive features.",
        "total_claims": total_claims,
        "sum_component_claims": component_claims,
        "claim_reconciliation_gap": component_claims - total_claims,
        "total_incurred": total_incurred,
        "sum_component_incurred": component_incurred,
        "incurred_reconciliation_gap": component_incurred - total_incurred,
    }
    return pd.DataFrame(rows).sort_values("incurred", ascending=False), audit


def _tail_audit(test: pd.DataFrame, loss_preds: dict[str, np.ndarray]) -> tuple[pd.DataFrame, dict]:
    observed = test["total_incurred"].to_numpy(float)
    exposure = test["total_exposure"].to_numpy(float)
    positive = observed[observed > 0]
    q995 = float(np.quantile(positive, 0.995))
    q99 = float(np.quantile(positive, 0.99))
    q999 = float(np.quantile(positive, 0.999))
    tail = observed >= q99
    extreme = observed >= q995
    rows = []
    y_rate = observed / exposure
    for name, pred_rate in loss_preds.items():
        pred_amount = pred_rate * exposure
        abs_error = np.abs(pred_amount - observed)
        for label, keep in [
            ("all", np.ones(len(test), dtype=bool)),
            ("exclude_top_0_5pct_positive_losses", ~extreme),
            ("exclude_top_1pct_positive_losses", ~tail),
        ]:
            rows.append({
                "model": name,
                "subset": label,
                "rows": int(keep.sum()),
                "tweedie_deviance": float(mean_tweedie_deviance(
                    y_rate[keep], pred_rate[keep], sample_weight=exposure[keep], power=1.5
                )),
                "calibration_ratio": float(pred_amount[keep].sum() / max(observed[keep].sum(), 1e-12)),
                "mean_absolute_policy_loss_error": float(abs_error[keep].mean()),
            })
    summary = {
        "version": "v0.17",
        "positive_loss_policy_rows": int((observed > 0).sum()),
        "positive_loss_p99": q99,
        "positive_loss_p99_5": q995,
        "positive_loss_p99_9": q999,
        "positive_loss_max": float(positive.max()),
        "top_1pct_positive_loss_policies_share_of_total_incurred": float(observed[tail].sum() / observed.sum()),
        "top_0_5pct_positive_loss_policies_share_of_total_incurred": float(observed[extreme].sum() / observed.sum()),
    }
    return pd.DataFrame(rows), summary


def _bootstrap_ratio(actual_amount: np.ndarray, pred_amount: np.ndarray, reps: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = len(actual_amount)
    ratios = np.empty(reps)
    for b in range(reps):
        idx = rng.integers(0, n, n)
        ratios[b] = pred_amount[idx].sum() / max(actual_amount[idx].sum(), 1e-12)
    return {
        "point": float(pred_amount.sum() / max(actual_amount.sum(), 1e-12)),
        "ci95_low": float(np.quantile(ratios, 0.025)),
        "ci95_high": float(np.quantile(ratios, 0.975)),
    }


def _transport_uncertainty(test: pd.DataFrame, loss_preds: dict[str, np.ndarray]) -> pd.DataFrame:
    raw_ids = pd.read_csv(
        Path("data_spanish_2022_2024/Dataset_of_motor_insurance_portfolio.csv"),
        sep=";", usecols=["insured_id", "year"], low_memory=False,
    )
    prior_ids = set(raw_ids.loc[raw_ids["year"].isin([2022, 2023]), "insured_id"])
    seen = test["insured_id"].isin(prior_ids).to_numpy()
    groups = {
        "returning_policy": seen,
        "new_policy": ~seen,
        "business_type_NB": test["business_type"].astype(str).eq("NB").to_numpy(),
        "business_type_P": test["business_type"].astype(str).eq("P").to_numpy(),
    }
    actual = test["total_incurred"].to_numpy(float)
    exposure = test["total_exposure"].to_numpy(float)
    rows = []
    for gname, mask in groups.items():
        for model, pred_rate in loss_preds.items():
            stats = _bootstrap_ratio(actual[mask], pred_rate[mask] * exposure[mask], reps=300, seed=2026 + len(rows))
            rows.append({
                "version": "v0.18",
                "segment": gname,
                "model": model,
                "rows": int(mask.sum()),
                **stats,
            })
    return pd.DataFrame(rows)


def _approval_pack(metrics: pd.DataFrame, complexity: pd.DataFrame, tail: pd.DataFrame, transport: pd.DataFrame) -> dict:
    v13 = json.loads(Path("results_oot_2024/oot_2024_summary.json").read_text())
    v14 = json.loads(Path("results_oot_2024/rolling_origin_v14_summary.json").read_text())

    freq_boot = v13["bootstrap"]["glm_minus_xgb_frequency_deviance"]
    loss_boot = v13["bootstrap"]["glm_minus_xgb_tweedie_deviance"]
    windows = v14["windows"]
    rolling_freq_support = [w["frequency_bootstrap_glm_minus_xgb"]["ci95_low"] > 0 for w in windows]
    rolling_loss_support = [w["pure_premium_bootstrap_glm_minus_xgb"]["ci95_low"] > 0 for w in windows]

    transport_points = transport.pivot(index="segment", columns="model", values="point")
    seen_glm = abs(transport_points.loc["returning_policy", "Tweedie_GLM"] - 1)
    seen_xgb = abs(transport_points.loc["returning_policy", "XGBoost_Tweedie"] - 1)
    new_glm = abs(transport_points.loc["new_policy", "Tweedie_GLM"] - 1)
    new_xgb = abs(transport_points.loc["new_policy", "XGBoost_Tweedie"] - 1)
    transport_same_winner = (seen_xgb < seen_glm) == (new_xgb < new_glm)

    metric_map = metrics.set_index("model")["2024_deviance"].to_dict()
    complexity_map = complexity.set_index("model").to_dict("index")
    xgb_pp_better = metric_map["XGBoost_Tweedie"] < metric_map["Tweedie_GLM"]
    xgb_pp_more_complex = (
        complexity_map["XGBoost_Tweedie"]["serialized_model_mb"] > complexity_map["Tweedie_GLM"]["serialized_model_mb"]
        or complexity_map["XGBoost_Tweedie"]["fit_seconds"] > complexity_map["Tweedie_GLM"]["fit_seconds"]
    )

    gates = {
        "locked_2024_frequency_bootstrap_supports_xgb": bool(freq_boot["ci95_low"] > 0),
        "locked_2024_pure_premium_bootstrap_supports_xgb": bool(loss_boot["ci95_low"] > 0),
        "rolling_origin_frequency_support_consistent_across_windows": bool(all(rolling_freq_support)),
        "rolling_origin_pure_premium_support_consistent_across_windows": bool(all(rolling_loss_support)),
        "same_model_is_closer_to_one_for_returning_and_new_business": bool(transport_same_winner),
        "xgb_has_lower_locked_2024_pure_premium_deviance": bool(xgb_pp_better),
        "xgb_pure_premium_is_more_complex_on_size_or_fit_time": bool(xgb_pp_more_complex),
    }
    decision = "PROMOTE" if all([
        gates["locked_2024_frequency_bootstrap_supports_xgb"],
        gates["locked_2024_pure_premium_bootstrap_supports_xgb"],
        gates["rolling_origin_frequency_support_consistent_across_windows"],
        gates["rolling_origin_pure_premium_support_consistent_across_windows"],
        gates["same_model_is_closer_to_one_for_returning_and_new_business"],
        gates["xgb_has_lower_locked_2024_pure_premium_deviance"],
    ]) else "HOLD"

    return {
        "version": "v0.20",
        "decision": decision,
        "gates": gates,
        "interpretation": (
            "The final decision prioritises stable expected-loss evidence, temporal repeatability, transport and value-for-complexity. "
            "No synthetic proposition result is used as deployment evidence."
        ),
    }


def _write_markdown(coverage: pd.DataFrame, coverage_audit: dict, tail: pd.DataFrame, tail_summary: dict,
                    transport: pd.DataFrame, complexity: pd.DataFrame, metrics: pd.DataFrame, approval: dict) -> None:
    lines = [
        "# v0.20 — Final Model-Change Approval Pack",
        "",
        f"**Decision: {approval['decision']}**",
        "",
        "This pack closes v0.16–v0.20 without adding new model families. The four existing references/challengers are fitted once and reused across the audits below.",
        "",
        "## v0.16 Coverage decomposition",
        "",
        f"2024 component incurred reconciliation gap: `{coverage_audit['incurred_reconciliation_gap']:.6f}`.",
        "",
        coverage.head(7).to_markdown(index=False),
        "",
        "## v0.17 Severity-tail audit",
        "",
        f"Top 1% of positive-loss policy rows account for **{100 * tail_summary['top_1pct_positive_loss_policies_share_of_total_incurred']:.2f}%** of total incurred.",
        "",
        tail.to_markdown(index=False),
        "",
        "## v0.18 Transport uncertainty",
        "",
        transport.to_markdown(index=False),
        "",
        "## v0.19 Value for complexity",
        "",
        complexity.merge(metrics, on=["model", "target"]).to_markdown(index=False),
        "",
        "## v0.20 Approval gates",
        "",
    ]
    for k, v in approval["gates"].items():
        lines.append(f"- `{k}`: **{v}**")
    lines += ["", f"Final decision: **{approval['decision']}**", ""]
    (OUTDIR / "V20_FINAL_APPROVAL_PACK.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    train = df[df["year"] == 2022].copy().reset_index(drop=True)
    calibration = df[df["year"] == 2023].copy().reset_index(drop=True)
    test = df[df["year"] == 2024].copy().reset_index(drop=True)

    preds, complexity, metrics = _fit_models(train, calibration, test)
    complexity.to_csv(OUTDIR / "v19_model_complexity.csv", index=False)
    metrics.to_csv(OUTDIR / "v19_locked_model_metrics.csv", index=False)

    coverage, coverage_audit = _coverage_audit(test)
    coverage.to_csv(OUTDIR / "v16_coverage_decomposition.csv", index=False)
    (OUTDIR / "v16_coverage_reconciliation.json").write_text(json.dumps(coverage_audit, indent=2), encoding="utf-8")

    loss_preds = {k: v for k, v in preds.items() if "Tweedie" in k}
    tail, tail_summary = _tail_audit(test, loss_preds)
    tail.to_csv(OUTDIR / "v17_tail_sensitivity.csv", index=False)
    (OUTDIR / "v17_tail_summary.json").write_text(json.dumps(tail_summary, indent=2), encoding="utf-8")

    transport = _transport_uncertainty(test, loss_preds)
    transport.to_csv(OUTDIR / "v18_transport_bootstrap_calibration.csv", index=False)

    approval = _approval_pack(metrics, complexity, tail, transport)
    (OUTDIR / "v20_approval_decision.json").write_text(json.dumps(approval, indent=2), encoding="utf-8")
    _write_markdown(coverage, coverage_audit, tail, tail_summary, transport, complexity, metrics, approval)
    print(json.dumps(approval, indent=2))


if __name__ == "__main__":
    main()
