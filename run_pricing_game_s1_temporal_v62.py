from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
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
from validate_prospective_request_registration_v61 import canonical_sha256, validate

REGISTRATION = Path("governance/prospective_request_registration_v61.json")
IMPLEMENTATION = Path("governance/s1_execution_implementation_v62.json")
V61_STATUS = Path("action_results/v61/origin/32793349122/ACTION_V61_STATUS.json")
DATA_PATH = Path("data_external_v62/pg15training.rda")
SOURCE_AUDIT_PATH = Path("results_v62/pricing_game_source_binary_audit.json")
OUTDIR = Path("results_v62")
EXPECTED_PROTOCOL_SHA256 = "80533141f88b042a02618d609f77d355f32c9d81ce53569aece27aab207a58c9"
EXPECTED_V61_EVIDENCE_COMMIT = "9a4520d9647eb7a1c51ff1d8e49345fd783def10"


def _load_locked_protocol() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    validate(registration)
    if canonical_sha256(registration) != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.61 protocol changed before S1 execution")
    implementation = json.loads(IMPLEMENTATION.read_text(encoding="utf-8"))
    if implementation["parent_registration"]["canonical_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.62 implementation seal parent digest changed")
    if implementation["parent_registration"]["main_evidence_commit"] != EXPECTED_V61_EVIDENCE_COMMIT:
        raise RuntimeError("v0.62 implementation seal parent evidence commit changed")
    status = json.loads(V61_STATUS.read_text(encoding="utf-8"))
    if status["status"] != "success" or status["request_id"] != registration["request_id"]:
        raise RuntimeError("v0.61 immutable registration status invalid")
    if status["protocol_canonical_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.61 immutable registration protocol digest changed")
    if status["request_lifecycle"] != "REGISTERED_SEALED_BEFORE_S1":
        raise RuntimeError("v0.61 lifecycle no longer authorises first S1 execution")
    for key in ("s1_open", "s2_open", "s3_open", "new_rda_downloaded", "new_rda_decoded", "row_level_new_source_accessed", "new_outcome_values_accessed", "model_fit_executed", "performance_metrics_computed"):
        if status[key] is not False:
            raise RuntimeError(f"v0.61 pre-access state drift: {key}")
    if status["s3_reserve_sealed"] is not True:
        raise RuntimeError("S3 reserve was unsealed before S1")
    return registration, implementation, status


def canonical_policy_id(value: Any) -> str:
    if pd.isna(value):
        raise RuntimeError("PolNum contains missing value")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number) or not number.is_integer():
            raise RuntimeError(f"numeric PolNum must be finite integer-valued: {value!r}")
        return str(int(number))
    text = str(value).strip()
    if not text:
        raise RuntimeError("PolNum contains empty string")
    match = re.fullmatch(r"([+-]?\d+)\.0+", text)
    if match:
        return str(int(match.group(1)))
    return text


def canonical_calendar_year(value: Any) -> int:
    if pd.isna(value):
        raise RuntimeError("CalYear contains missing value")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"CalYear is not numeric: {value!r}") from exc
    if not math.isfinite(number) or not number.is_integer():
        raise RuntimeError(f"CalYear must be finite integer-valued: {value!r}")
    return int(number)


def pre_outcome_cross_year_filter(keys: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    if list(keys.columns) != ["PolNum", "CalYear"]:
        raise RuntimeError("pre-outcome barrier accepts only PolNum and CalYear")
    canonical_ids = keys["PolNum"].map(canonical_policy_id).to_numpy(dtype=object)
    years = keys["CalYear"].map(canonical_calendar_year).to_numpy(dtype=int)
    year_set = sorted(set(int(x) for x in years.tolist()))
    if year_set != [2009, 2010]:
        raise RuntimeError(f"S1 temporal year contract failed before outcome access: {year_set}")
    key_table = pd.DataFrame({"policy_id": canonical_ids, "year": years})
    year_counts = key_table.groupby("policy_id", sort=False)["year"].nunique()
    cross_year_ids = set(year_counts[year_counts > 1].index.astype(str).tolist())
    keep = np.array([policy_id not in cross_year_ids for policy_id in canonical_ids], dtype=bool)
    kept_ids = canonical_ids[keep]
    kept_years = years[keep]
    post = pd.DataFrame({"policy_id": kept_ids, "year": kept_years})
    if (post.groupby("policy_id", sort=False)["year"].nunique() > 1).any():
        raise RuntimeError("cross-year policy leakage remains after registered removal")
    metadata = {
        "decoded_rows_before_registered_cross_year_removal": int(len(keys)),
        "observed_calendar_years_before_outcome_access": year_set,
        "cross_year_policy_ids_observed": int(len(cross_year_ids)),
        "rows_removed_for_cross_year_policies": int((~keep).sum()),
        "rows_remaining_before_outcome_access": int(keep.sum()),
        "public_expected_cross_year_count_used_as_gate": False,
        "outcome_columns_accessed_during_barrier": [],
    }
    return keep, kept_ids, kept_years, metadata


def policy_bucket(policy_id: str) -> int:
    payload = ("v61|S1|20260825|" + policy_id).encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest(), 16) % 10000


def temporal_split(canonical_ids: np.ndarray, years: np.ndarray) -> dict[str, np.ndarray]:
    if len(canonical_ids) != len(years):
        raise RuntimeError("split keys have inconsistent lengths")
    development = years == 2009
    locked_test = years == 2010
    buckets = np.array([policy_bucket(str(policy_id)) for policy_id in canonical_ids], dtype=int)
    train = np.flatnonzero(development & (buckets < 8000))
    calibration = np.flatnonzero(development & (buckets >= 8000))
    test = np.flatnonzero(locked_test)
    if not len(train) or not len(calibration) or not len(test):
        raise RuntimeError("registered S1 split produced an empty partition")
    train_ids = set(canonical_ids[train].tolist())
    cal_ids = set(canonical_ids[calibration].tolist())
    test_ids = set(canonical_ids[test].tolist())
    if train_ids & cal_ids or train_ids & test_ids or cal_ids & test_ids:
        raise RuntimeError("policy identity leaked across registered partitions")
    return {"train": train, "calibration": calibration, "test": test}


def _assert_runtime(implementation: dict[str, Any]) -> dict[str, Any]:
    expected = implementation["runtime"]
    actual = {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "xgboost": xgboost.__version__,
        "pyreadr": getattr(pyreadr, "__version__", "unknown"),
    }
    if ".".join(actual["python"].split(".")[:2]) != expected["python_major_minor"]:
        raise RuntimeError(f"Python runtime drift: {actual['python']}")
    for key in ("pandas", "numpy", "scipy", "scikit_learn", "xgboost", "pyreadr"):
        if actual[key] != expected[key]:
            raise RuntimeError(f"runtime drift {key}: {actual[key]} != {expected[key]}")
    for key, value in expected["thread_environment"].items():
        if os.environ.get(key) != value:
            raise RuntimeError(f"thread environment drift {key}: {os.environ.get(key)} != {value}")
    return {"versions": actual, "thread_environment": expected["thread_environment"]}


def _fit_glm(estimator, X, y, weight, *, label: str) -> dict[str, Any]:
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


def _assert_predictions(label: str, values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values <= 0):
        raise RuntimeError(f"{label} produced non-positive/non-finite predictions")
    return values


def _split_summary(frame: pd.DataFrame, index: np.ndarray, exposure: np.ndarray, claims: np.ndarray, amount: np.ndarray, ids: np.ndarray) -> dict[str, Any]:
    return {
        "rows": int(len(index)),
        "unique_policy_ids": int(len(set(ids[index].tolist()))),
        "exposure_years": float(exposure[index].sum()),
        "claim_count": int(round(float(claims[index].sum()))),
        "claim_amount": float(amount[index].sum()),
        "claiming_rows": int(np.sum(claims[index] > 0)),
    }


def _target_result(*, name: str, observed_test: np.ndarray, exposure_test: np.ndarray,
                   reference_pred_test: np.ndarray, challenger_pred_test: np.ndarray,
                   reference_scale: float, challenger_scale: float,
                   registration: dict[str, Any], implementation: dict[str, Any]) -> dict[str, Any]:
    reference_pred = _assert_predictions(f"{name}_reference_calibrated", reference_pred_test * reference_scale)
    challenger_pred = _assert_predictions(f"{name}_challenger_calibrated", challenger_pred_test * challenger_scale)
    if name == "frequency":
        metric = poisson_deviance
        capture_key = "top_10_percent_exposure_claim_capture"
        pass_label = implementation["stage_decision_labels"]["frequency_pass"]
        fail_label = implementation["stage_decision_labels"]["frequency_fail"]
    else:
        metric = tweedie_deviance_p15
        capture_key = "top_10_percent_exposure_loss_capture"
        pass_label = implementation["stage_decision_labels"]["pure_premium_pass"]
        fail_label = implementation["stage_decision_labels"]["pure_premium_fail"]
    ref_dev = metric(observed_test, reference_pred, exposure_test)
    ch_dev = metric(observed_test, challenger_pred, exposure_test)
    ref_cal = aggregate_calibration(observed_test, reference_pred, exposure_test)
    ch_cal = aggregate_calibration(observed_test, challenger_pred, exposure_test)
    bootstrap_spec = registration["bootstrap"]
    bootstrap_values = paired_bootstrap_relative_improvement(
        observed_test,
        reference_pred,
        challenger_pred,
        exposure_test,
        metric=metric,
        draws=int(bootstrap_spec["draws"]),
        seed=int(bootstrap_spec["stage_seeds"]["S1_TEMPORAL_QUALIFICATION"]),
    )
    interval = percentile_interval(bootstrap_values)
    calibration = registration["calibration"]
    scale_valid = all(calibration["lower_guard"] <= value <= calibration["upper_guard"] for value in (reference_scale, challenger_scale))
    gate = registration["target_gate"]
    registered = evaluate_replication_gate(
        reference_deviance=ref_dev,
        challenger_deviance=ch_dev,
        reference_abs_log_calibration_error=ref_cal["abs_log_calibration_error"],
        challenger_abs_log_calibration_error=ch_cal["abs_log_calibration_error"],
        bootstrap_interval=interval,
        minimum_relative_deviance_improvement=float(gate["point_relative_deviance_improvement_min"]),
        bootstrap_ci_lower_bound_must_exceed=float(gate["bootstrap_relative_deviance_improvement_q025_must_be_strictly_greater_than"]),
        maximum_additional_abs_log_calibration_error=float(gate["challenger_absolute_log_calibration_error_must_be_lte_reference_plus"]),
        calibration_scales_valid=scale_valid,
        pass_label=pass_label,
        fail_label=fail_label,
    )
    return {
        "calibration_scales": {
            "reference": float(reference_scale),
            "challenger": float(challenger_scale),
            "guardrails": [calibration["lower_guard"], calibration["upper_guard"]],
            "both_valid": bool(scale_valid),
            "clipped": False,
        },
        "locked_temporal_test": {
            "reference_deviance": float(ref_dev),
            "challenger_deviance": float(ch_dev),
            "relative_deviance_improvement": float(1.0 - ch_dev / ref_dev),
            "reference_calibration": ref_cal,
            "challenger_calibration": ch_cal,
            "reference_" + capture_key: float(top_exposure_capture(observed_test, reference_pred, exposure_test)),
            "challenger_" + capture_key: float(top_exposure_capture(observed_test, challenger_pred, exposure_test)),
        },
        "paired_bootstrap_relative_deviance_improvement": {
            "draws": int(bootstrap_spec["draws"]),
            "seed": int(bootstrap_spec["stage_seeds"]["S1_TEMPORAL_QUALIFICATION"]),
            **interval,
            "positive_draw_rate": float(np.mean(bootstrap_values > 0)),
        },
        "registered_gate": registered,
    }


def main() -> None:
    registration, implementation, v61_status = _load_locked_protocol()
    audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["status"] != "V62_PINNED_PG15TRAINING_BINARY_VERIFIED_BEFORE_DECODE":
        raise RuntimeError("S1 binary identity was not verified before decode")
    if audit["git_blob_sha1"] != registration["sources"]["S1_TEMPORAL_QUALIFICATION"]["rda_files"][0]["git_blob_sha1"]:
        raise RuntimeError("S1 source audit does not match registered blob identity")
    runtime = _assert_runtime(implementation)

    payload = pyreadr.read_r(str(DATA_PATH))
    object_name = implementation["source_decode"]["expected_r_object_name"]
    if object_name not in payload:
        raise RuntimeError(f"registered R object {object_name!r} missing; found {sorted(payload)}")
    frame = payload[object_name]
    s1 = registration["sources"]["S1_TEMPORAL_QUALIFICATION"]
    actual_columns = list(frame.columns)
    required_columns = s1["required_columns"]
    if len(actual_columns) != len(set(actual_columns)) or set(actual_columns) != set(required_columns):
        raise RuntimeError(f"S1 semantic column-name contract failed: {actual_columns}")

    # The first value-level access after semantic schema validation is restricted to these two keys.
    key_frame = frame[["PolNum", "CalYear"]].copy()
    keep, canonical_ids, years, barrier = pre_outcome_cross_year_filter(key_frame)

    # Outcome/exposure/feature access starts only after the registered cross-year removal barrier completed.
    clean = frame.loc[keep].reset_index(drop=True)
    required_nonmissing = implementation["post_barrier_data_quality"]["required_nonmissing_fields"]
    if clean[required_nonmissing].isna().any().any():
        missing = clean[required_nonmissing].isna().sum()
        raise RuntimeError(f"S1 contains missing registered modelling values after barrier: {missing[missing > 0].to_dict()}")
    for column in implementation["post_barrier_data_quality"]["numeric_feature_fields_must_be_finite"]:
        values = clean[column].astype(float).to_numpy()
        if np.any(~np.isfinite(values)):
            raise RuntimeError(f"S1 numeric feature contains non-finite values: {column}")

    expdays = clean["Expdays"].astype(float).to_numpy()
    if np.any(~np.isfinite(expdays)) or np.any(expdays <= 0):
        raise RuntimeError("S1 Expdays violates registered finite strictly-positive contract")
    exposure = expdays / 365.0
    count_components = [clean["Numtppd"].astype(float).to_numpy(), clean["Numtpbi"].astype(float).to_numpy()]
    for label, values in zip(("Numtppd", "Numtpbi"), count_components):
        if np.any(~np.isfinite(values)) or np.any(values < 0) or np.any(np.abs(values - np.round(values)) > 1e-12):
            raise RuntimeError(f"S1 claim-count component violates contract: {label}")
    amount_components = [clean["Indtppd"].astype(float).to_numpy(), clean["Indtpbi"].astype(float).to_numpy()]
    for label, values in zip(("Indtppd", "Indtpbi"), amount_components):
        if np.any(~np.isfinite(values)) or np.any(values < 0):
            raise RuntimeError(f"S1 claim-cost component violates contract: {label}")
    claims = count_components[0] + count_components[1]
    amount = amount_components[0] + amount_components[1]

    splits = temporal_split(canonical_ids, years)
    train, calibration, test = splits["train"], splits["calibration"], splits["test"]
    numeric = s1["features"]["numeric"]
    categorical = s1["features"]["categorical"]
    model_features = numeric + categorical
    X = clean[model_features].copy()
    for column in categorical:
        X[column] = X[column].astype(str)
    preprocessor = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ], remainder="drop", sparse_threshold=0.0, verbose_feature_names_out=False)
    X_train = preprocessor.fit_transform(X.iloc[train])
    X_cal = preprocessor.transform(X.iloc[calibration])
    X_test = preprocessor.transform(X.iloc[test])

    model = registration["registered_model_family"]
    freq_ref_spec = {k: v for k, v in model["frequency_reference"].items() if k != "estimator"}
    pp_ref_spec = {k: v for k, v in model["pure_premium_reference"].items() if k != "estimator"}
    freq_ch_spec = {k: v for k, v in model["frequency_challenger"].items() if k != "estimator"}
    pp_ch_spec = {k: v for k, v in model["pure_premium_challenger"].items() if k != "estimator"}
    freq_ref = PoissonRegressor(**freq_ref_spec)
    pp_ref = TweedieRegressor(**pp_ref_spec)
    freq_ch = XGBRegressor(**freq_ch_spec)
    pp_ch = XGBRegressor(**pp_ch_spec)

    freq_rate_train = claims[train] / exposure[train]
    pp_rate_train = amount[train] / exposure[train]
    glm_fit = {
        "frequency": _fit_glm(freq_ref, X_train, freq_rate_train, exposure[train], label="frequency_glm"),
        "pure_premium": _fit_glm(pp_ref, X_train, pp_rate_train, exposure[train], label="pure_premium_glm"),
    }
    freq_ch.fit(X_train, freq_rate_train, sample_weight=exposure[train])
    pp_ch.fit(X_train, pp_rate_train, sample_weight=exposure[train])

    pred = {
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
        "freq_ref": multiplicative_calibration_scale(claims[calibration], pred["freq_ref_cal"], exposure[calibration]),
        "freq_ch": multiplicative_calibration_scale(claims[calibration], pred["freq_ch_cal"], exposure[calibration]),
        "pp_ref": multiplicative_calibration_scale(amount[calibration], pred["pp_ref_cal"], exposure[calibration]),
        "pp_ch": multiplicative_calibration_scale(amount[calibration], pred["pp_ch_cal"], exposure[calibration]),
    }
    frequency = _target_result(
        name="frequency", observed_test=claims[test], exposure_test=exposure[test],
        reference_pred_test=pred["freq_ref_test"], challenger_pred_test=pred["freq_ch_test"],
        reference_scale=scales["freq_ref"], challenger_scale=scales["freq_ch"],
        registration=registration, implementation=implementation,
    )
    pure_premium = _target_result(
        name="pure_premium", observed_test=amount[test], exposure_test=exposure[test],
        reference_pred_test=pred["pp_ref_test"], challenger_pred_test=pred["pp_ch_test"],
        reference_scale=scales["pp_ref"], challenger_scale=scales["pp_ch"],
        registration=registration, implementation=implementation,
    )
    both_pass = bool(frequency["registered_gate"]["passed"] and pure_premium["registered_gate"]["passed"])
    if both_pass:
        stage_status = implementation["stage_decision_labels"]["first_execution_both_targets_pass"]
        request_state = "S1_POSITIVE_REPRODUCIBILITY_EXECUTION_REQUIRED"
        second_execution_allowed = True
    else:
        stage_status = implementation["stage_decision_labels"]["any_target_fails"]
        request_state = "TERMINAL_HOLD_FOR_MCR_XGB_MOTOR_002"
        second_execution_allowed = False

    result = {
        "status": "V62_S1_FIRST_EXECUTION_COMPLETE",
        "request_id": registration["request_id"],
        "stage": "S1_TEMPORAL_QUALIFICATION",
        "programme_scope": registration["activation"]["programme_scope"],
        "registration": {
            "protocol_canonical_sha256": EXPECTED_PROTOCOL_SHA256,
            "v61_main_evidence_commit": EXPECTED_V61_EVIDENCE_COMMIT,
            "v61_main_run_id": v61_status["run_id"],
            "registered_before_s1_row_access": True,
            "rules_changed_after_registration": False,
        },
        "source": audit,
        "access_sequence": {
            "binary_identity_verified_before_decode": True,
            "semantic_column_names_verified_before_key_values": True,
            "pre_outcome_value_columns": ["PolNum", "CalYear"],
            "cross_year_removal_completed_before_outcome_access": True,
            "outcome_access_started_after_barrier": True,
            "s2_accessed": False,
            "s3_accessed": False,
            **barrier,
        },
        "runtime": {**runtime, "glm_fit": glm_fit},
        "split": {
            "method": "2009 deterministic SHA256 policy-id train/calibration split; 2010 locked temporal test",
            "outcome_stratified": False,
            "resplit_after_outcome_inspection": False,
            "train": _split_summary(clean, train, exposure, claims, amount, canonical_ids),
            "calibration": _split_summary(clean, calibration, exposure, claims, amount, canonical_ids),
            "locked_temporal_test": _split_summary(clean, test, exposure, claims, amount, canonical_ids),
        },
        "features": {
            "numeric": numeric,
            "categorical": categorical,
            "used": model_features,
            "preprocessor_fit_on_train_only": True,
            "numeric_transform": "StandardScaler",
            "categorical_transform": "OneHotEncoder(handle_unknown='ignore', sparse_output=False)",
            "encoded_feature_count": int(X_train.shape[1]),
        },
        "frequency": frequency,
        "pure_premium": pure_premium,
        "stage_decision": {
            "both_registered_targets_pass_first_execution": both_pass,
            "status": stage_status,
            "request_state": request_state,
            "independent_second_execution_allowed": second_execution_allowed,
            "s2_open_authorised": False,
            "s3_open_authorised": False,
            "reserve_can_rescue_failure": False,
        },
        "reproducibility": {
            "executions_completed": 1,
            "positive_stage_requires_executions": 2,
            "decision_labels_must_match": True,
            "point_metric_relative_tolerance": registration["stage_gate"]["point_metric_relative_reproducibility_tolerance_max"],
            "positive_s1_support_authorised": False,
        },
        "governance": {
            "historical_request_MCR_XGB_MOTOR_001_unchanged": True,
            "project_model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "promotion_review_status": "NOT_OPEN",
            "model_promotion_authorised": False,
            "customer_pricing_authorised": False,
            "s2_remains_sealed": True,
            "s3_remains_sealed": True,
            "raw_external_data_persisted": False,
            "row_level_predictions_persisted": False,
        },
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "pricing_game_s1_first_execution.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
