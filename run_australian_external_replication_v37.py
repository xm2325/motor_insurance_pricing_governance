from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pyreadr
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.preprocessing import OneHotEncoder
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
from validate_external_validation_prereg_v36 import canonical_sha256, validate_prereg


PREREG_PATH = Path("governance/external_validation_prereg_v36.json")
V36_LOCK_PATH = Path("action_results/v36/external_validation_prereg_lock.json")
V36_STATUS_PATH = Path("action_results/v36/ACTION_V36_STATUS.json")
DATA_PATH = Path("data_external_v37/ausprivauto0405.rda")
SOURCE_AUDIT_PATH = Path("results_v37/australian_source_audit.json")
OUTDIR = Path("results_v37")
EXPECTED_V36_PREREG_SHA256 = "b20d38b51f767761fe4b4f85d58988f7032dbcc7d7afc96041f3858c0165e3c1"
EXPECTED_V36_MAIN_SHA = "49339232a6b913e111b6e4e66dfa4517d9396bc9"


def _load_verified_protocol() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    validate_prereg(prereg)
    lock = json.loads(V36_LOCK_PATH.read_text(encoding="utf-8"))
    status = json.loads(V36_STATUS_PATH.read_text(encoding="utf-8"))
    digest = canonical_sha256(prereg)
    if digest != EXPECTED_V36_PREREG_SHA256:
        raise RuntimeError(f"v0.36 preregistration digest changed: {digest}")
    if lock["preregistration_sha256"] != EXPECTED_V36_PREREG_SHA256:
        raise RuntimeError("persisted v0.36 lock does not match registered digest")
    if status["sha"] != EXPECTED_V36_MAIN_SHA or status["status"] != "success":
        raise RuntimeError("v0.36 main preregistration status is not the registered successful commit")
    if status["row_level_external_data_accessed"] is not False:
        raise RuntimeError("v0.36 does not prove pre-access registration")
    return prereg, lock, status


def _load_external_frame(prereg: dict[str, Any]):
    if not DATA_PATH.is_file():
        raise FileNotFoundError(DATA_PATH)
    payload = pyreadr.read_r(str(DATA_PATH))
    if "ausprivauto0405" not in payload:
        raise RuntimeError("ausprivauto0405 object missing from pinned source")
    frame = payload["ausprivauto0405"].copy()
    required = prereg["data_contract"]["required_columns"]
    if list(frame.columns) != required or len(frame) != prereg["data_contract"]["required_rows"]:
        raise RuntimeError("external frame no longer matches preregistered source contract")
    if frame[required].isna().any().any():
        raise RuntimeError("missing required value in locked external execution")
    exposure = frame["Exposure"].astype(float).to_numpy()
    claim_nb = frame["ClaimNb"].astype(float).to_numpy()
    claim_amount = frame["ClaimAmount"].astype(float).to_numpy()
    if np.any(exposure <= 0):
        raise RuntimeError("non-positive exposure violates preregistration")
    if np.any(claim_nb < 0) or np.any(np.abs(claim_nb - np.round(claim_nb)) > 1e-12):
        raise RuntimeError("claim count violates preregistration")
    if np.any(claim_amount < 0):
        raise RuntimeError("claim amount violates preregistration")
    return frame


def _model_kwargs(spec: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in spec.items() if key != "estimator"}


def _split_summary(frame, index: np.ndarray) -> dict[str, float | int]:
    part = frame.iloc[index]
    return {
        "rows": int(len(part)),
        "exposure": float(part["Exposure"].astype(float).sum()),
        "claims": int(part["ClaimNb"].astype(float).sum()),
        "claim_amount": float(part["ClaimAmount"].astype(float).sum()),
        "claiming_policies": int((part["ClaimNb"].astype(float) > 0).sum()),
    }


def _target_result(
    *,
    target_name: str,
    observed_test: np.ndarray,
    exposure_test: np.ndarray,
    reference_pred_test: np.ndarray,
    challenger_pred_test: np.ndarray,
    reference_scale: float,
    challenger_scale: float,
    scale_guardrails: list[float],
    gate: dict[str, Any],
    bootstrap: dict[str, Any],
) -> dict[str, Any]:
    reference_pred = np.clip(reference_pred_test * reference_scale, 1e-12, None)
    challenger_pred = np.clip(challenger_pred_test * challenger_scale, 1e-12, None)
    if target_name == "frequency":
        metric = poisson_deviance
        reference_deviance = metric(observed_test, reference_pred, exposure_test)
        challenger_deviance = metric(observed_test, challenger_pred, exposure_test)
        reference_capture = top_exposure_capture(observed_test, reference_pred, exposure_test)
        challenger_capture = top_exposure_capture(observed_test, challenger_pred, exposure_test)
        pass_label = gate["frequency_pass_label"]
        fail_label = gate["frequency_fail_label"]
        capture_name = "top_10_percent_exposure_claim_capture"
    elif target_name == "pure_premium":
        metric = tweedie_deviance_p15
        reference_deviance = metric(observed_test, reference_pred, exposure_test)
        challenger_deviance = metric(observed_test, challenger_pred, exposure_test)
        reference_capture = top_exposure_capture(observed_test, reference_pred, exposure_test)
        challenger_capture = top_exposure_capture(observed_test, challenger_pred, exposure_test)
        pass_label = gate["pure_premium_pass_label"]
        fail_label = gate["pure_premium_fail_label"]
        capture_name = "top_10_percent_exposure_loss_capture"
    else:
        raise ValueError(target_name)

    reference_calibration = aggregate_calibration(observed_test, reference_pred, exposure_test)
    challenger_calibration = aggregate_calibration(observed_test, challenger_pred, exposure_test)
    bootstrap_values = paired_bootstrap_relative_improvement(
        observed_test,
        reference_pred,
        challenger_pred,
        exposure_test,
        metric=metric,
        draws=int(bootstrap["draws"]),
        seed=int(bootstrap["seed"]),
    )
    interval = percentile_interval(bootstrap_values)
    scale_valid = all(
        float(scale_guardrails[0]) <= scale <= float(scale_guardrails[1])
        for scale in (reference_scale, challenger_scale)
    )
    decision = evaluate_replication_gate(
        reference_deviance=reference_deviance,
        challenger_deviance=challenger_deviance,
        reference_abs_log_calibration_error=reference_calibration["abs_log_calibration_error"],
        challenger_abs_log_calibration_error=challenger_calibration["abs_log_calibration_error"],
        bootstrap_interval=interval,
        minimum_relative_deviance_improvement=float(gate["minimum_relative_deviance_improvement"]),
        bootstrap_ci_lower_bound_must_exceed=float(
            gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"]
        ),
        maximum_additional_abs_log_calibration_error=float(
            gate["maximum_additional_abs_log_aggregate_calibration_error"]
        ),
        calibration_scales_valid=scale_valid,
        pass_label=pass_label,
        fail_label=fail_label,
    )
    return {
        "calibration_scales": {
            "reference": reference_scale,
            "challenger": challenger_scale,
            "guardrails": scale_guardrails,
            "both_valid": scale_valid,
            "clipped": False,
        },
        "locked_test": {
            "reference_deviance": reference_deviance,
            "challenger_deviance": challenger_deviance,
            "relative_deviance_improvement": 1.0 - challenger_deviance / reference_deviance,
            "reference_calibration": reference_calibration,
            "challenger_calibration": challenger_calibration,
            "reference_" + capture_name: reference_capture,
            "challenger_" + capture_name: challenger_capture,
        },
        "paired_bootstrap_relative_deviance_improvement": {
            "draws": int(bootstrap["draws"]),
            "seed": int(bootstrap["seed"]),
            **interval,
            "positive_draw_rate": float(np.mean(bootstrap_values > 0)),
        },
        "registered_gate": decision,
    }


def main() -> None:
    prereg, lock, v36_status = _load_verified_protocol()
    source_audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    if source_audit["status"] != "V37_PINNED_AUSTRALIAN_SOURCE_VERIFIED":
        raise RuntimeError("pinned source audit did not pass")
    if source_audit["source_commit"] != prereg["source"]["upstream_commit"]:
        raise RuntimeError("downloaded source commit differs from preregistration")

    frame = _load_external_frame(prereg)
    split_spec = prereg["split"]
    splits = deterministic_split_indices(
        len(frame),
        seed=int(split_spec["seed"]),
        train_fraction=float(split_spec["train_fraction"]),
        calibration_fraction=float(split_spec["calibration_fraction"]),
    )

    numeric = prereg["features"]["numeric"]
    categorical = prereg["features"]["categorical"]
    model_features = numeric + categorical
    if any(feature in model_features for feature in prereg["features"]["excluded_from_predictors"]):
        raise RuntimeError("excluded predictor entered external feature set")

    X = frame[model_features].copy()
    for column in categorical:
        X[column] = X[column].astype(str)
    exposure = frame["Exposure"].astype(float).to_numpy()
    claim_nb = frame["ClaimNb"].astype(float).to_numpy()
    claim_amount = frame["ClaimAmount"].astype(float).to_numpy()

    train, calibration, test = splits["train"], splits["calibration"], splits["test"]
    preprocessor = ColumnTransformer(
        [
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
            ("numeric", "passthrough", numeric),
        ],
        remainder="drop",
        sparse_threshold=0.0,
        verbose_feature_names_out=False,
    )
    X_train = preprocessor.fit_transform(X.iloc[train])
    X_calibration = preprocessor.transform(X.iloc[calibration])
    X_test = preprocessor.transform(X.iloc[test])

    models = prereg["models"]
    frequency_reference = PoissonRegressor(**_model_kwargs(models["frequency_glm"]))
    frequency_challenger = XGBRegressor(**_model_kwargs(models["frequency_xgb"]))
    pure_premium_reference = TweedieRegressor(**_model_kwargs(models["pure_premium_glm"]))
    pure_premium_challenger = XGBRegressor(**_model_kwargs(models["pure_premium_xgb"]))

    frequency_rate_train = claim_nb[train] / exposure[train]
    pure_premium_rate_train = claim_amount[train] / exposure[train]
    frequency_reference.fit(X_train, frequency_rate_train, sample_weight=exposure[train])
    frequency_challenger.fit(X_train, frequency_rate_train, sample_weight=exposure[train])
    pure_premium_reference.fit(X_train, pure_premium_rate_train, sample_weight=exposure[train])
    pure_premium_challenger.fit(X_train, pure_premium_rate_train, sample_weight=exposure[train])

    predictions = {
        "frequency_reference_cal": np.clip(frequency_reference.predict(X_calibration), 1e-12, None),
        "frequency_challenger_cal": np.clip(frequency_challenger.predict(X_calibration), 1e-12, None),
        "frequency_reference_test": np.clip(frequency_reference.predict(X_test), 1e-12, None),
        "frequency_challenger_test": np.clip(frequency_challenger.predict(X_test), 1e-12, None),
        "pure_premium_reference_cal": np.clip(pure_premium_reference.predict(X_calibration), 1e-12, None),
        "pure_premium_challenger_cal": np.clip(pure_premium_challenger.predict(X_calibration), 1e-12, None),
        "pure_premium_reference_test": np.clip(pure_premium_reference.predict(X_test), 1e-12, None),
        "pure_premium_challenger_test": np.clip(pure_premium_challenger.predict(X_test), 1e-12, None),
    }

    scales = {
        "frequency_reference": multiplicative_calibration_scale(
            claim_nb[calibration], predictions["frequency_reference_cal"], exposure[calibration]
        ),
        "frequency_challenger": multiplicative_calibration_scale(
            claim_nb[calibration], predictions["frequency_challenger_cal"], exposure[calibration]
        ),
        "pure_premium_reference": multiplicative_calibration_scale(
            claim_amount[calibration], predictions["pure_premium_reference_cal"], exposure[calibration]
        ),
        "pure_premium_challenger": multiplicative_calibration_scale(
            claim_amount[calibration], predictions["pure_premium_challenger_cal"], exposure[calibration]
        ),
    }

    gate = prereg["registered_external_replication_gate"]
    bootstrap = prereg["paired_bootstrap"]
    scale_guardrails = prereg["calibration"]["scale_guardrails"]
    frequency = _target_result(
        target_name="frequency",
        observed_test=claim_nb[test],
        exposure_test=exposure[test],
        reference_pred_test=predictions["frequency_reference_test"],
        challenger_pred_test=predictions["frequency_challenger_test"],
        reference_scale=scales["frequency_reference"],
        challenger_scale=scales["frequency_challenger"],
        scale_guardrails=scale_guardrails,
        gate=gate,
        bootstrap=bootstrap,
    )
    pure_premium = _target_result(
        target_name="pure_premium",
        observed_test=claim_amount[test],
        exposure_test=exposure[test],
        reference_pred_test=predictions["pure_premium_reference_test"],
        challenger_pred_test=predictions["pure_premium_challenger_test"],
        reference_scale=scales["pure_premium_reference"],
        challenger_scale=scales["pure_premium_challenger"],
        scale_guardrails=scale_guardrails,
        gate=gate,
        bootstrap=bootstrap,
    )

    result = {
        "status": "V37_AUSTRALIAN_EXTERNAL_REPLICATION_COMPLETE",
        "evidence_class": prereg["independence_statement"]["evidence_class"],
        "preregistration": {
            "sha256": lock["preregistration_sha256"],
            "v36_main_sha": v36_status["sha"],
            "registered_before_row_level_access": True,
            "rules_changed_after_registration": False,
        },
        "source": source_audit,
        "split": {
            "method": split_spec["method"],
            "seed": split_spec["seed"],
            "train": _split_summary(frame, train),
            "calibration": _split_summary(frame, calibration),
            "locked_test": _split_summary(frame, test),
            "outcome_stratified": False,
            "resplit_after_outcome_inspection": False,
        },
        "features": {
            "used": model_features,
            "excluded": prereg["features"]["excluded_from_predictors"],
            "preprocessor_fit_on_train_only": True,
            "encoded_feature_count": int(X_train.shape[1]),
        },
        "frequency": frequency,
        "pure_premium": pure_premium,
        "decision": {
            "primary_frequency_external_replication_passed": bool(frequency["registered_gate"]["passed"]),
            "secondary_pure_premium_external_replication_passed": bool(pure_premium["registered_gate"]["passed"]),
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "model_promotion_authorised": False,
            "pricing_change_authorised": False,
        },
        "interpretation_boundary": prereg["independence_statement"]["limitation"],
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "australian_external_replication_summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
