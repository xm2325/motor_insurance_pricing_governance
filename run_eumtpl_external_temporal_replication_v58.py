from __future__ import annotations

import gc
import json
import os
import platform
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pyreadr
import scipy
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from external_validation.replication import (
    aggregate_calibration,
    evaluate_replication_gate,
    multiplicative_calibration_scale,
    paired_bootstrap_relative_improvement,
    percentile_interval,
    poisson_deviance,
    top_exposure_capture,
    tweedie_deviance_p15,
)

PREREG_PATH = Path("governance/external_temporal_prereg_v57.json")
V57_LOCK_PATH = Path("action_results/v57/eumtpl_external_temporal_prereg_lock.json")
V57_STATUS_PATH = Path("action_results/v57/ACTION_V57_STATUS.json")
SOURCE_AUDIT_PATH = Path("results_v58/eumtpl_source_binary_audit.json")
DATA_PATH = Path("data_external_v58/euMTPL.rda")
OUTDIR = Path("results_v58")
EXPECTED_PROTOCOL_SHA256 = "a2b49e26aeca619323129ee4b56ff39d110cf68a08bfe0064fbd3f5886f74ff5"
EXPECTED_V57_MAIN_SHA = "cacb55a039c6132b7c2466f6356903250dc624d3"


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_verified_protocol() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    lock = json.loads(V57_LOCK_PATH.read_text(encoding="utf-8"))
    status = json.loads(V57_STATUS_PATH.read_text(encoding="utf-8"))
    digest = _sha256(PREREG_PATH)
    if digest != EXPECTED_PROTOCOL_SHA256 or lock["protocol_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.57 preregistration digest changed")
    if status["status"] != "success" or status["sha"] != EXPECTED_V57_MAIN_SHA:
        raise RuntimeError("v0.57 main lock changed")
    if status["row_level_external_data_accessed"] is not False or status["outcomes_inspected"] is not False:
        raise RuntimeError("v0.57 no-data evidence changed")
    return prereg, lock, status


def _load_frame(prereg: dict[str, Any]):
    audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    source = prereg["source"]
    if audit["status"] != "V58_PINNED_EUMTPL_BINARY_VERIFIED_BEFORE_DECODE":
        raise RuntimeError("euMTPL binary identity audit did not pass")
    if audit["git_blob_sha1"] != source["upstream_git_blob_sha"] or audit["file_bytes"] != source["upstream_blob_size_bytes"]:
        raise RuntimeError("euMTPL binary identity differs from preregistration")

    payload = pyreadr.read_r(str(DATA_PATH))
    if "euMTPL" not in payload:
        raise RuntimeError(f"Expected euMTPL object; found {sorted(str(k) for k in payload)}")
    frame = payload["euMTPL"].copy()
    contract = prereg["data_contract_for_future_execution"]
    required_columns = contract["required_columns_exactly"]
    if list(frame.columns) != required_columns:
        raise RuntimeError(f"euMTPL columns/order differ from preregistration: {list(frame.columns)}")
    if len(frame) != int(contract["required_rows"]):
        raise RuntimeError(f"euMTPL row count differs from preregistration: {len(frame)}")
    if frame[contract["required_nonmissing"]].isna().any().any():
        raise RuntimeError("euMTPL has missing values in preregistered required fields")

    exposure = frame["exposure"].astype(float).to_numpy()
    if np.any(~np.isfinite(exposure)) or np.any(exposure <= 0) or np.any(exposure > 1):
        raise RuntimeError("euMTPL exposure violates registered (0,1] contract")
    for column in prereg["source"]["known_from_public_documentation_before_row_level_access"]["claim_count_components"]:
        values = frame[column].astype(float).to_numpy()
        if np.any(~np.isfinite(values)) or np.any(values < 0) or np.any(np.abs(values - np.round(values)) > 1e-12):
            raise RuntimeError(f"euMTPL claim-count component violates contract: {column}")
    for column in prereg["source"]["known_from_public_documentation_before_row_level_access"]["claim_cost_components"]:
        values = frame[column].astype(float).to_numpy()
        if np.any(~np.isfinite(values)) or np.any(values < 0):
            raise RuntimeError(f"euMTPL claim-cost component violates contract: {column}")
    for column in prereg["features"]["numeric"]:
        values = frame[column].astype(float).to_numpy()
        if np.any(~np.isfinite(values)):
            raise RuntimeError(f"euMTPL numeric predictor is non-finite: {column}")
    return frame


def _year_contract(frame, prereg: dict[str, Any]):
    raw_year = frame["year"]
    numeric = np.asarray(raw_year.astype(float), dtype=float)
    if np.any(~np.isfinite(numeric)) or np.any(np.abs(numeric - np.round(numeric)) > 1e-12):
        raise RuntimeError("year must be finite integer-valued calendar labels")
    years = sorted(int(x) for x in np.unique(numeric))
    if len(years) != 3 or prereg["data_contract_for_future_execution"]["require_exactly_three_distinct_years"] is not True:
        raise RuntimeError(f"registered exactly-three-year contract failed: {years}")
    year_int = np.round(numeric).astype(int)
    masks = {
        "train": year_int == years[0],
        "calibration": year_int == years[1],
        "test": year_int == years[2],
    }
    if any(int(mask.sum()) < int(prereg["temporal_split"]["minimum_nonempty_rows_per_period"]) for mask in masks.values()):
        raise RuntimeError("one registered temporal period is empty")
    return years, masks


def _aggregate_outcomes(frame, prereg: dict[str, Any]):
    count_cols = prereg["source"]["known_from_public_documentation_before_row_level_access"]["claim_count_components"]
    cost_cols = prereg["source"]["known_from_public_documentation_before_row_level_access"]["claim_cost_components"]
    claims = frame[count_cols].astype(float).sum(axis=1).to_numpy(dtype=float)
    amount = frame[cost_cols].astype(float).sum(axis=1).to_numpy(dtype=float)
    return claims, amount


def _split_summary(frame, mask: np.ndarray, exposure: np.ndarray, claims: np.ndarray, amount: np.ndarray) -> dict[str, Any]:
    idx = np.flatnonzero(mask)
    return {
        "rows": int(len(idx)),
        "exposure": float(exposure[idx].sum()),
        "claims": int(claims[idx].sum()),
        "claim_amount": float(amount[idx].sum()),
        "claiming_policy_rows": int(np.sum(claims[idx] > 0)),
        "unique_policy_ids": int(frame.loc[mask, "policy_id"].nunique()),
    }


def _feature_frame(frame, mask: np.ndarray, numeric: list[str], categorical: list[str]):
    x = frame.loc[mask, numeric + categorical].copy()
    for column in numeric:
        x[column] = x[column].astype(float)
    for column in categorical:
        x[column] = x[column].astype(str)
    return x


def _fit_glm(estimator, X, y, weight, *, label: str):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        estimator.fit(X, y, sample_weight=weight)
    messages = [str(item.message) for item in caught]
    if any(issubclass(item.category, ConvergenceWarning) for item in caught):
        raise RuntimeError(f"{label} convergence warning: {messages}")
    if any("lbfgs" in message.lower() or "fallback" in message.lower() for message in messages):
        raise RuntimeError(f"{label} attempted forbidden solver fallback: {messages}")
    if not np.all(np.isfinite(estimator.coef_)) or not np.isfinite(estimator.intercept_):
        raise RuntimeError(f"{label} produced non-finite coefficients")
    return {"n_iter": int(estimator.n_iter_), "warnings": messages}


def _assert_predictions(name: str, values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values <= 0):
        raise RuntimeError(f"{name} produced non-positive/non-finite predictions")
    return values


def _target_result(*, target_name: str, observed_test: np.ndarray, exposure_test: np.ndarray,
                   reference_pred_test: np.ndarray, challenger_pred_test: np.ndarray,
                   reference_scale: float, challenger_scale: float, scale_guardrails: list[float],
                   gate: dict[str, Any], bootstrap: dict[str, Any]) -> dict[str, Any]:
    reference_pred = _assert_predictions("calibrated reference", reference_pred_test * reference_scale)
    challenger_pred = _assert_predictions("calibrated challenger", challenger_pred_test * challenger_scale)
    if target_name == "frequency":
        metric = poisson_deviance
        capture_name = "top_10_percent_exposure_claim_capture"
        pass_label, fail_label = gate["frequency_pass_label"], gate["frequency_fail_label"]
    else:
        metric = tweedie_deviance_p15
        capture_name = "top_10_percent_exposure_loss_capture"
        pass_label, fail_label = gate["pure_premium_pass_label"], gate["pure_premium_fail_label"]
    ref_dev = metric(observed_test, reference_pred, exposure_test)
    ch_dev = metric(observed_test, challenger_pred, exposure_test)
    ref_cal = aggregate_calibration(observed_test, reference_pred, exposure_test)
    ch_cal = aggregate_calibration(observed_test, challenger_pred, exposure_test)
    bootstrap_values = paired_bootstrap_relative_improvement(
        observed_test, reference_pred, challenger_pred, exposure_test, metric=metric,
        draws=int(bootstrap["draws"]), seed=int(bootstrap["seed"]),
    )
    interval = percentile_interval(bootstrap_values)
    scale_valid = all(float(scale_guardrails[0]) <= value <= float(scale_guardrails[1]) for value in (reference_scale, challenger_scale))
    registered = evaluate_replication_gate(
        reference_deviance=ref_dev,
        challenger_deviance=ch_dev,
        reference_abs_log_calibration_error=ref_cal["abs_log_calibration_error"],
        challenger_abs_log_calibration_error=ch_cal["abs_log_calibration_error"],
        bootstrap_interval=interval,
        minimum_relative_deviance_improvement=float(gate["minimum_relative_deviance_improvement"]),
        bootstrap_ci_lower_bound_must_exceed=float(gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"]),
        maximum_additional_abs_log_calibration_error=float(gate["maximum_additional_abs_log_aggregate_calibration_error"]),
        calibration_scales_valid=scale_valid,
        pass_label=pass_label,
        fail_label=fail_label,
    )
    return {
        "calibration_scales": {"reference": reference_scale, "challenger": challenger_scale, "guardrails": scale_guardrails, "both_valid": scale_valid, "clipped": False},
        "locked_test": {
            "reference_deviance": ref_dev,
            "challenger_deviance": ch_dev,
            "relative_deviance_improvement": 1.0 - ch_dev / ref_dev,
            "reference_calibration": ref_cal,
            "challenger_calibration": ch_cal,
            "reference_" + capture_name: top_exposure_capture(observed_test, reference_pred, exposure_test),
            "challenger_" + capture_name: top_exposure_capture(observed_test, challenger_pred, exposure_test),
        },
        "paired_bootstrap_relative_deviance_improvement": {"draws": int(bootstrap["draws"]), "seed": int(bootstrap["seed"]), **interval, "positive_draw_rate": float(np.mean(bootstrap_values > 0))},
        "registered_gate": registered,
    }


def main() -> None:
    prereg, lock, v57_status = _load_verified_protocol()
    frame = _load_frame(prereg)
    years, masks = _year_contract(frame, prereg)
    exposure = frame["exposure"].astype(float).to_numpy()
    claims, amount = _aggregate_outcomes(frame, prereg)

    runtime = prereg["runtime_reproducibility"]
    actual_versions = {
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "scikit_learn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        "pyreadr_version": getattr(pyreadr, "__version__", "unknown"),
    }
    if ".".join(actual_versions["python_version"].split(".")[:2]) != runtime["python_version"]:
        raise RuntimeError("Python major.minor differs from preregistration")
    for key, expected in runtime.items():
        if key.endswith("_version") and key != "python_version" and actual_versions[key] != expected:
            raise RuntimeError(f"runtime version mismatch {key}: {actual_versions[key]} != {expected}")
    for key, expected in runtime["thread_environment"].items():
        if os.environ.get(key) != expected:
            raise RuntimeError(f"thread environment mismatch {key}: {os.environ.get(key)} != {expected}")

    numeric = prereg["features"]["numeric"]
    categorical = prereg["features"]["categorical"]
    if set(numeric + categorical) & set(prereg["features"]["excluded_from_predictors"]):
        raise RuntimeError("excluded predictor entered registered feature set")
    preprocessor = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ], remainder="drop", sparse_threshold=0.0, verbose_feature_names_out=False)

    x_train_df = _feature_frame(frame, masks["train"], numeric, categorical)
    X_train = preprocessor.fit_transform(x_train_df)
    del x_train_df
    train_idx = np.flatnonzero(masks["train"])
    cal_idx = np.flatnonzero(masks["calibration"])
    test_idx = np.flatnonzero(masks["test"])

    models = prereg["models"]
    freq_glm_spec = {k: v for k, v in models["frequency_glm"].items() if k not in {"estimator", "convergence_required", "fallback_solver_allowed"}}
    pp_glm_spec = {k: v for k, v in models["pure_premium_glm"].items() if k not in {"estimator", "convergence_required", "fallback_solver_allowed"}}
    freq_xgb_spec = {k: v for k, v in models["frequency_xgb"].items() if k != "estimator"}
    pp_xgb_spec = {k: v for k, v in models["pure_premium_xgb"].items() if k != "estimator"}
    freq_ref = PoissonRegressor(**freq_glm_spec)
    freq_ch = XGBRegressor(**freq_xgb_spec)
    pp_ref = TweedieRegressor(**pp_glm_spec)
    pp_ch = XGBRegressor(**pp_xgb_spec)

    freq_rate_train = claims[train_idx] / exposure[train_idx]
    pp_rate_train = amount[train_idx] / exposure[train_idx]
    glm_fit = {
        "frequency": _fit_glm(freq_ref, X_train, freq_rate_train, exposure[train_idx], label="frequency_glm"),
        "pure_premium": _fit_glm(pp_ref, X_train, pp_rate_train, exposure[train_idx], label="pure_premium_glm"),
    }
    freq_ch.fit(X_train, freq_rate_train, sample_weight=exposure[train_idx])
    pp_ch.fit(X_train, pp_rate_train, sample_weight=exposure[train_idx])
    del X_train, freq_rate_train, pp_rate_train
    gc.collect()

    x_cal_df = _feature_frame(frame, masks["calibration"], numeric, categorical)
    X_cal = preprocessor.transform(x_cal_df)
    del x_cal_df
    predictions_cal = {
        "freq_ref": _assert_predictions("freq_ref_cal", freq_ref.predict(X_cal)),
        "freq_ch": _assert_predictions("freq_ch_cal", freq_ch.predict(X_cal)),
        "pp_ref": _assert_predictions("pp_ref_cal", pp_ref.predict(X_cal)),
        "pp_ch": _assert_predictions("pp_ch_cal", pp_ch.predict(X_cal)),
    }
    del X_cal
    gc.collect()

    scales = {
        "freq_ref": multiplicative_calibration_scale(claims[cal_idx], predictions_cal["freq_ref"], exposure[cal_idx]),
        "freq_ch": multiplicative_calibration_scale(claims[cal_idx], predictions_cal["freq_ch"], exposure[cal_idx]),
        "pp_ref": multiplicative_calibration_scale(amount[cal_idx], predictions_cal["pp_ref"], exposure[cal_idx]),
        "pp_ch": multiplicative_calibration_scale(amount[cal_idx], predictions_cal["pp_ch"], exposure[cal_idx]),
    }
    del predictions_cal
    gc.collect()

    x_test_df = _feature_frame(frame, masks["test"], numeric, categorical)
    X_test = preprocessor.transform(x_test_df)
    del x_test_df
    predictions_test = {
        "freq_ref": _assert_predictions("freq_ref_test", freq_ref.predict(X_test)),
        "freq_ch": _assert_predictions("freq_ch_test", freq_ch.predict(X_test)),
        "pp_ref": _assert_predictions("pp_ref_test", pp_ref.predict(X_test)),
        "pp_ch": _assert_predictions("pp_ch_test", pp_ch.predict(X_test)),
    }
    encoded_feature_count = int(X_test.shape[1])
    del X_test
    gc.collect()

    gate = prereg["registered_external_temporal_gate"]
    bootstrap = prereg["paired_bootstrap"]
    guardrails = prereg["calibration"]["scale_guardrails"]
    frequency = _target_result(
        target_name="frequency", observed_test=claims[test_idx], exposure_test=exposure[test_idx],
        reference_pred_test=predictions_test["freq_ref"], challenger_pred_test=predictions_test["freq_ch"],
        reference_scale=scales["freq_ref"], challenger_scale=scales["freq_ch"],
        scale_guardrails=guardrails, gate=gate, bootstrap=bootstrap,
    )
    pure_premium = _target_result(
        target_name="pure_premium", observed_test=amount[test_idx], exposure_test=exposure[test_idx],
        reference_pred_test=predictions_test["pp_ref"], challenger_pred_test=predictions_test["pp_ch"],
        reference_scale=scales["pp_ref"], challenger_scale=scales["pp_ch"],
        scale_guardrails=guardrails, gate=gate, bootstrap=bootstrap,
    )

    source_audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    policy_year_counts = frame.groupby("policy_id", observed=True)["year"].nunique(dropna=False)
    cross_year_policy_ids = int((policy_year_counts > 1).sum())
    result = {
        "status": "V58_EUMTPL_EXTERNAL_TEMPORAL_FIRST_EXECUTION_COMPLETE",
        "preregistration": {
            "sha256": EXPECTED_PROTOCOL_SHA256,
            "v57_main_sha": EXPECTED_V57_MAIN_SHA,
            "registered_before_row_level_access": lock["registered_before_row_level_access"],
            "rules_changed_after_registration": False,
        },
        "source": {
            "dataset": "euMTPL",
            "source_commit": prereg["source"]["upstream_commit"],
            "source_git_blob_sha": source_audit["git_blob_sha1"],
            "file_sha256": source_audit["file_sha256"],
            "file_bytes": source_audit["file_bytes"],
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "year_labels": years,
            "row_level_data_accessed": True,
            "outcomes_inspected": True,
            "raw_data_persisted_to_repository": False,
        },
        "split": {
            "method": prereg["temporal_split"]["method"],
            "train_year": years[0],
            "calibration_year": years[1],
            "locked_test_year": years[2],
            "source_group_used": False,
            "outcome_stratified": False,
            "resplit_after_outcome_inspection": False,
            "train": _split_summary(frame, masks["train"], exposure, claims, amount),
            "calibration": _split_summary(frame, masks["calibration"], exposure, claims, amount),
            "locked_test": _split_summary(frame, masks["test"], exposure, claims, amount),
            "cross_year_policy_ids": cross_year_policy_ids,
            "cross_year_policy_id_overlap_changed_split": False,
        },
        "targets": {
            "frequency": prereg["targets"]["frequency"]["observed_count"],
            "pure_premium": prereg["targets"]["pure_premium"]["observed_amount"],
        },
        "features": {
            "numeric": numeric,
            "categorical": categorical,
            "encoded_feature_count": encoded_feature_count,
            "preprocessor_fit_on_train_year_only": True,
            "policy_id_used_as_predictor": False,
            "year_used_as_predictor": False,
            "source_group_used_as_predictor": False,
            "gender_used_as_predictor": False,
        },
        "runtime": {
            "versions": actual_versions,
            "thread_environment": {k: os.environ.get(k) for k in runtime["thread_environment"]},
            "glm_fit": glm_fit,
        },
        "frequency": frequency,
        "pure_premium": pure_premium,
        "reproducibility": {
            "registered_minimum_independent_executions_for_positive_support": runtime["minimum_independent_actions_executions_for_positive_external_support"],
            "executions_completed_for_this_new_portfolio": 1,
            "status": "FIRST_EXECUTION_ONLY_REPRODUCIBILITY_NOT_YET_SATISFIED",
            "positive_external_support_authorised": False,
            "second_independent_execution_required_if_any_registered_gate_is_positive": True,
        },
        "decision": {
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "promotion_review_status": "NOT_OPEN",
            "model_promotion_authorised": False,
            "pricing_change_authorised": False,
            "committee_gate_count_changed_by_first_execution": False,
        },
        "persisted_row_level_data": False,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "eumtpl_external_temporal_first_execution.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "years": years,
        "split_rows": {k: result["split"][k]["rows"] for k in ("train", "calibration", "locked_test")},
        "frequency_decision": frequency["registered_gate"]["decision"],
        "frequency_relative_improvement": frequency["registered_gate"]["relative_deviance_improvement"],
        "frequency_bootstrap_q025": frequency["paired_bootstrap_relative_deviance_improvement"]["q025"],
        "pure_premium_decision": pure_premium["registered_gate"]["decision"],
        "pure_premium_relative_improvement": pure_premium["registered_gate"]["relative_deviance_improvement"],
        "pure_premium_bootstrap_q025": pure_premium["paired_bootstrap_relative_deviance_improvement"]["q025"],
        "positive_support_authorised": False,
    }, indent=2))


if __name__ == "__main__":
    main()
