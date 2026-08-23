from __future__ import annotations

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
    deterministic_split_indices,
    evaluate_replication_gate,
    multiplicative_calibration_scale,
    paired_bootstrap_relative_improvement,
    percentile_interval,
    poisson_deviance,
    top_exposure_capture,
    tweedie_deviance_p15,
)
from validate_external_validation_prereg_v40 import canonical_sha256, validate_prereg

PREREG_PATH = Path("governance/external_validation_prereg_v40.json")
V40_LOCK_PATH = Path("action_results/v40/belgian_external_validation_prereg_lock.json")
V40_STATUS_PATH = Path("action_results/v40/ACTION_V40_STATUS.json")
DATA_PATH = Path("data_external_v41/beMTPL97.rda")
SOURCE_AUDIT_PATH = Path("results_v41/belgian_source_audit.json")
OUTDIR = Path("results_v41")
EXPECTED_V40_PREREG_SHA256 = "19658e3a6b12e55ffaa564585bf69dd09ad1371b567f0c1b03c7d17103796822"
EXPECTED_V40_MAIN_SHA = "833e861ee797d3751090e4d08a512d9f340b5378"


def _load_verified_protocol() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    validate_prereg(prereg)
    lock = json.loads(V40_LOCK_PATH.read_text(encoding="utf-8"))
    status = json.loads(V40_STATUS_PATH.read_text(encoding="utf-8"))
    digest = canonical_sha256(prereg)
    if digest != EXPECTED_V40_PREREG_SHA256 or lock["preregistration_sha256"] != EXPECTED_V40_PREREG_SHA256:
        raise RuntimeError("v0.40 preregistration digest changed")
    if status["sha"] != EXPECTED_V40_MAIN_SHA or status["status"] != "success":
        raise RuntimeError("v0.40 main preregistration status changed")
    if status["row_level_external_data_accessed"] is not False:
        raise RuntimeError("v0.40 no longer proves pre-access registration")
    if status["positive_support_minimum_independent_executions"] != 2:
        raise RuntimeError("v0.40 two-execution rule changed")
    return prereg, lock, status


def _load_frame(prereg: dict[str, Any]):
    payload = pyreadr.read_r(str(DATA_PATH))
    if "beMTPL97" not in payload:
        raise RuntimeError("beMTPL97 object missing")
    frame = payload["beMTPL97"].copy()
    contract = prereg["data_contract"]
    if list(frame.columns) != contract["required_columns"] or len(frame) != contract["required_rows"]:
        raise RuntimeError("Belgian frame differs from preregistered schema/dimensions")
    if frame[contract["required_nonmissing_for_model"]].isna().any().any():
        raise RuntimeError("missing value in preregistered modelling field")
    if frame["id"].duplicated().any():
        raise RuntimeError("duplicate id violates preregistration")
    exposure = frame["expo"].astype(float).to_numpy()
    claims = frame["nclaims"].astype(float).to_numpy()
    amount = frame["amount"].astype(float).to_numpy()
    if np.any(~np.isfinite(exposure)) or np.any(exposure <= 0) or np.any(exposure > 1):
        raise RuntimeError("exposure violates preregistration")
    if np.any(~np.isfinite(claims)) or np.any(claims < 0) or np.any(np.abs(claims - np.round(claims)) > 1e-12):
        raise RuntimeError("claim count violates preregistration")
    if np.any(~np.isfinite(amount)) or np.any(amount < 0):
        raise RuntimeError("claim amount violates preregistration")
    return frame


def _split_summary(frame, index: np.ndarray) -> dict[str, float | int]:
    part = frame.iloc[index]
    return {
        "rows": int(len(part)),
        "exposure": float(part["expo"].astype(float).sum()),
        "claims": int(part["nclaims"].astype(float).sum()),
        "claim_amount": float(part["amount"].astype(float).sum()),
        "claiming_policies": int((part["nclaims"].astype(float) > 0).sum()),
    }


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
    reference_pred = reference_pred_test * reference_scale
    challenger_pred = challenger_pred_test * challenger_scale
    _assert_predictions("calibrated reference", reference_pred)
    _assert_predictions("calibrated challenger", challenger_pred)
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
    prereg, lock, v40_status = _load_verified_protocol()
    audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["status"] != "V41_PINNED_BELGIAN_SOURCE_VERIFIED" or audit["source_commit"] != prereg["source"]["upstream_commit"]:
        raise RuntimeError("Belgian source audit did not pass registered source identity")
    frame = _load_frame(prereg)

    runtime = prereg["runtime_reproducibility"]
    actual_versions = {
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "scikit_learn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        "pyreadr_version": getattr(pyreadr, "__version__", "unknown"),
    }
    registered_python = runtime["python_version"]
    actual_python_major_minor = ".".join(actual_versions["python_version"].split(".")[:2])
    if actual_python_major_minor != registered_python:
        raise RuntimeError(
            f"runtime version mismatch python_version: {actual_versions['python_version']} "
            f"does not satisfy registered major.minor {registered_python}"
        )
    for key, expected in runtime.items():
        if key.endswith("_version") and key != "python_version" and actual_versions[key] != expected:
            raise RuntimeError(f"runtime version mismatch {key}: {actual_versions[key]} != {expected}")
    for key, expected in runtime["thread_environment"].items():
        if os.environ.get(key) != expected:
            raise RuntimeError(f"thread environment mismatch {key}: {os.environ.get(key)} != {expected}")

    split_spec = prereg["split"]
    splits = deterministic_split_indices(len(frame), seed=int(split_spec["seed"]), train_fraction=float(split_spec["train_fraction"]), calibration_fraction=float(split_spec["calibration_fraction"]))
    train, calibration, test = splits["train"], splits["calibration"], splits["test"]

    numeric = prereg["features"]["numeric"]
    categorical = prereg["features"]["categorical"]
    model_features = numeric + categorical
    if set(model_features) & set(prereg["features"]["excluded_from_predictors"]):
        raise RuntimeError("excluded predictor entered feature set")
    X = frame[model_features].copy()
    for column in categorical:
        X[column] = X[column].astype(str)
    exposure = frame["expo"].astype(float).to_numpy()
    claims = frame["nclaims"].astype(float).to_numpy()
    amount = frame["amount"].astype(float).to_numpy()

    preprocessor = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ], remainder="drop", sparse_threshold=0.0, verbose_feature_names_out=False)
    X_train = preprocessor.fit_transform(X.iloc[train])
    X_cal = preprocessor.transform(X.iloc[calibration])
    X_test = preprocessor.transform(X.iloc[test])

    models = prereg["models"]
    freq_glm_spec = {k: v for k, v in models["frequency_glm"].items() if k not in {"estimator", "convergence_required", "fallback_solver_allowed"}}
    pp_glm_spec = {k: v for k, v in models["pure_premium_glm"].items() if k not in {"estimator", "convergence_required", "fallback_solver_allowed"}}
    freq_xgb_spec = {k: v for k, v in models["frequency_xgb"].items() if k != "estimator"}
    pp_xgb_spec = {k: v for k, v in models["pure_premium_xgb"].items() if k != "estimator"}

    freq_ref = PoissonRegressor(**freq_glm_spec)
    freq_ch = XGBRegressor(**freq_xgb_spec)
    pp_ref = TweedieRegressor(**pp_glm_spec)
    pp_ch = XGBRegressor(**pp_xgb_spec)
    freq_rate_train = claims[train] / exposure[train]
    pp_rate_train = amount[train] / exposure[train]
    glm_fit = {
        "frequency": _fit_glm(freq_ref, X_train, freq_rate_train, exposure[train], label="frequency_glm"),
        "pure_premium": _fit_glm(pp_ref, X_train, pp_rate_train, exposure[train], label="pure_premium_glm"),
    }
    freq_ch.fit(X_train, freq_rate_train, sample_weight=exposure[train])
    pp_ch.fit(X_train, pp_rate_train, sample_weight=exposure[train])

    predictions = {
        "freq_ref_cal": _assert_predictions("freq_ref_cal", freq_ref.predict(X_cal)),
        "freq_ch_cal": _assert_predictions("freq_ch_cal", freq_ch.predict(X_cal)),
        "freq_ref_test": _assert_predictions("freq_ref_test", freq_ref.predict(X_test)),
        "freq_ch_test": _assert_predictions("freq_ch_test", freq_ch.predict(X_test)),
        "pp_ref_cal": _assert_predictions("pp_ref_cal", pp_ref.predict(X_cal)),
        "pp_ch_cal": _assert_predictions("pp_ch_cal", pp_ch.predict(X_cal)),
        "pp_ref_test": _assert_predictions("pp_ref_test", pp_ref.predict(X_test)),
        "pp_ch_test": _assert_predictions("pp_ch_test", pp_ch.predict(X_test)),
    }
    scales = {
        "freq_ref": multiplicative_calibration_scale(claims[calibration], predictions["freq_ref_cal"], exposure[calibration]),
        "freq_ch": multiplicative_calibration_scale(claims[calibration], predictions["freq_ch_cal"], exposure[calibration]),
        "pp_ref": multiplicative_calibration_scale(amount[calibration], predictions["pp_ref_cal"], exposure[calibration]),
        "pp_ch": multiplicative_calibration_scale(amount[calibration], predictions["pp_ch_cal"], exposure[calibration]),
    }
    gate = prereg["registered_external_replication_gate"]
    bootstrap = prereg["paired_bootstrap"]
    guardrails = prereg["calibration"]["scale_guardrails"]
    frequency = _target_result(target_name="frequency", observed_test=claims[test], exposure_test=exposure[test], reference_pred_test=predictions["freq_ref_test"], challenger_pred_test=predictions["freq_ch_test"], reference_scale=scales["freq_ref"], challenger_scale=scales["freq_ch"], scale_guardrails=guardrails, gate=gate, bootstrap=bootstrap)
    pure_premium = _target_result(target_name="pure_premium", observed_test=amount[test], exposure_test=exposure[test], reference_pred_test=predictions["pp_ref_test"], challenger_pred_test=predictions["pp_ch_test"], reference_scale=scales["pp_ref"], challenger_scale=scales["pp_ch"], scale_guardrails=guardrails, gate=gate, bootstrap=bootstrap)

    any_positive = bool(frequency["registered_gate"]["passed"] or pure_premium["registered_gate"]["passed"])
    result = {
        "status": "V41_BELGIAN_EXTERNAL_FIRST_EXECUTION_COMPLETE",
        "evidence_class": prereg["independence_statement"]["evidence_class"],
        "preregistration": {"sha256": lock["preregistration_sha256"], "v40_main_sha": v40_status["sha"], "registered_before_row_level_access": True, "rules_changed_after_registration": False},
        "source": audit,
        "runtime": {"versions": actual_versions, "registered_python_major_minor": registered_python, "thread_environment": runtime["thread_environment"], "glm_fit": glm_fit},
        "split": {"method": split_spec["method"], "seed": split_spec["seed"], "train": _split_summary(frame, train), "calibration": _split_summary(frame, calibration), "locked_test": _split_summary(frame, test), "outcome_stratified": False, "resplit_after_outcome_inspection": False},
        "features": {"used": model_features, "excluded": prereg["features"]["excluded_from_predictors"], "preprocessor_fit_on_train_only": True, "encoded_feature_count": int(X_train.shape[1])},
        "frequency": frequency,
        "pure_premium": pure_premium,
        "reproducibility": {
            "registered_minimum_independent_executions_for_positive_support": 2,
            "executions_completed_for_this_new_portfolio": 1,
            "any_first_execution_registered_gate_positive": any_positive,
            "positive_external_support_authorised": False,
            "status": "SECOND_EXECUTION_REQUIRED_BEFORE_ANY_POSITIVE_SUPPORT" if any_positive else "NO_POSITIVE_GATE_TO_REPRODUCE",
        },
        "decision": {"model_family_decision": "HOLD", "serving_status": "HOLD_SHADOW_ONLY", "model_promotion_authorised": False, "pricing_change_authorised": False},
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "belgian_external_replication_first_execution.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
