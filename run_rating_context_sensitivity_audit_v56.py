from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_rating_factor_relativity_audit_v51 import (
    read_2022_development,
    fit_frozen_frequency_models,
    score_profile,
)

ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "governance/rating_context_sensitivity_protocol_v56.json"
OUTDIR = ROOT / "results_v56"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sign_fraction(values: list[float], reference: float) -> float:
    if reference == 0:
        raise RuntimeError("Registered reference sign cannot be zero")
    return float(np.mean([np.sign(v) == np.sign(reference) for v in values]))


def direction_changes(values: list[float], tolerance: float = 1e-10) -> int:
    diffs = np.diff(np.asarray(values, dtype=float))
    signs = np.sign(diffs[np.abs(diffs) > tolerance])
    if len(signs) < 2:
        return 0
    return int(np.sum(signs[1:] != signs[:-1]))


def build_context_profile(reference: dict, change: dict) -> dict:
    overlap = set(change) - set(reference)
    if overlap:
        raise RuntimeError(f"Unknown context fields: {sorted(overlap)}")
    profile = dict(reference)
    profile.update(change)
    return profile


def score_curves(protocol: dict, models: dict) -> pd.DataFrame:
    rows: list[dict] = []
    reference = protocol["v51_reference_profile"]
    contexts = protocol["context_selection"]["contexts"]

    for feature, feature_spec in protocol["target_features"].items():
        ref_value = feature_spec["reference_value"]
        quantiles = feature_spec["grid_quantiles"]
        values = feature_spec["grid_values"]
        if len(quantiles) != len(values):
            raise RuntimeError(f"Grid length mismatch for {feature}")

        for context in contexts:
            context_id = context["context_id"]
            context_profile = build_context_profile(
                reference, context["change_from_v51_reference"]
            )
            normalisation_profile = dict(context_profile)
            normalisation_profile[feature] = ref_value
            normalisation_scores = score_profile(normalisation_profile, models)

            for q, value in zip(quantiles, values):
                profile = dict(context_profile)
                profile[feature] = value
                scores = score_profile(profile, models)
                glm_rel = (
                    scores["poisson_glm_frequency"]
                    / normalisation_scores["poisson_glm_frequency"]
                )
                xgb_rel = (
                    scores["xgb_poisson_frequency"]
                    / normalisation_scores["xgb_poisson_frequency"]
                )
                rows.append(
                    {
                        "feature": feature,
                        "context_id": context_id,
                        "context_change": json.dumps(
                            context["change_from_v51_reference"],
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        "context_changed_level_v51_marginal_exposure_share": context[
                            "v51_marginal_exposure_share_of_changed_level"
                        ],
                        "quantile": q,
                        "value": value,
                        "glm_frequency_relativity": glm_rel,
                        "xgb_frequency_relativity": xgb_rel,
                        "log_xgb_over_glm_relativity": float(np.log(xgb_rel / glm_rel)),
                    }
                )
    return pd.DataFrame(rows)


def context_feature_summary(curves: pd.DataFrame, protocol: dict) -> pd.DataFrame:
    rows: list[dict] = []
    for feature, feature_spec in protocol["target_features"].items():
        for context in protocol["context_selection"]["contexts"]:
            context_id = context["context_id"]
            part = curves[
                (curves["feature"] == feature)
                & (curves["context_id"] == context_id)
            ].sort_values("quantile")
            if len(part) != len(feature_spec["grid_values"]):
                raise RuntimeError(f"Incomplete curve for {feature}/{context_id}")
            q05 = part.loc[np.isclose(part["quantile"], 0.05)].iloc[0]
            q95 = part.loc[np.isclose(part["quantile"], 0.95)].iloc[0]
            abs_gap = part["log_xgb_over_glm_relativity"].abs()
            max_row = part.loc[abs_gap.idxmax()]
            rows.append(
                {
                    "feature": feature,
                    "context_id": context_id,
                    "context_change": q95["context_change"],
                    "context_changed_level_v51_marginal_exposure_share": q95[
                        "context_changed_level_v51_marginal_exposure_share"
                    ],
                    "q05_log_gap": float(q05["log_xgb_over_glm_relativity"]),
                    "q95_log_gap": float(q95["log_xgb_over_glm_relativity"]),
                    "max_absolute_log_gap": float(max_row["log_xgb_over_glm_relativity"] if max_row["log_xgb_over_glm_relativity"] >= 0 else -max_row["log_xgb_over_glm_relativity"]),
                    "max_gap_quantile": float(max_row["quantile"]),
                    "max_gap_value": float(max_row["value"]),
                    "glm_direction_changes": direction_changes(part["glm_frequency_relativity"].tolist()),
                    "xgb_direction_changes": direction_changes(part["xgb_frequency_relativity"].tolist()),
                }
            )
    return pd.DataFrame(rows)


def cross_context_summary(curves: pd.DataFrame, summary: pd.DataFrame, protocol: dict) -> pd.DataFrame:
    rows: list[dict] = []
    for feature, feature_spec in protocol["target_features"].items():
        feature_curves = curves[curves["feature"] == feature].copy()
        feature_summary = summary[summary["feature"] == feature].copy()
        base_summary = feature_summary[feature_summary["context_id"] == "BASE"].iloc[0]
        base_q95 = float(base_summary["q95_log_gap"])
        q95_values = feature_summary["q95_log_gap"].astype(float).tolist()

        base_curve = (
            feature_curves[feature_curves["context_id"] == "BASE"]
            .set_index("quantile")["log_xgb_over_glm_relativity"]
        )
        max_delta = -1.0
        max_delta_context = None
        max_delta_quantile = None
        for context_id in feature_summary["context_id"]:
            curve = (
                feature_curves[feature_curves["context_id"] == context_id]
                .set_index("quantile")["log_xgb_over_glm_relativity"]
            )
            delta = (curve - base_curve).abs()
            idx = float(delta.idxmax())
            val = float(delta.loc[idx])
            if val > max_delta:
                max_delta = val
                max_delta_context = context_id
                max_delta_quantile = idx

        xgb_ranges = []
        glm_ranges = []
        for q in feature_spec["grid_quantiles"]:
            point = feature_curves[np.isclose(feature_curves["quantile"], q)]
            xgb_logs = np.log(point["xgb_frequency_relativity"].astype(float).to_numpy())
            glm_logs = np.log(point["glm_frequency_relativity"].astype(float).to_numpy())
            xgb_ranges.append(float(np.max(xgb_logs) - np.min(xgb_logs)))
            glm_ranges.append(float(np.max(glm_logs) - np.min(glm_logs)))

        min_idx = int(np.argmin(q95_values))
        max_idx = int(np.argmax(q95_values))
        context_ids = feature_summary["context_id"].tolist()
        rows.append(
            {
                "feature": feature,
                "base_q95_log_gap": base_q95,
                "v51_registered_base_q95_log_gap": feature_spec["v51_base_q95_log_gap"],
                "base_q95_minus_v51_registered": base_q95 - feature_spec["v51_base_q95_log_gap"],
                "q95_log_gap_min": float(min(q95_values)),
                "q95_log_gap_min_context": context_ids[min_idx],
                "q95_log_gap_max": float(max(q95_values)),
                "q95_log_gap_max_context": context_ids[max_idx],
                "q95_log_gap_range": float(max(q95_values) - min(q95_values)),
                "fraction_contexts_same_q95_sign_as_base": sign_fraction(q95_values, base_q95),
                "max_absolute_context_minus_base_log_gap_over_registered_grid": max_delta,
                "max_context_minus_base_context": max_delta_context,
                "max_context_minus_base_quantile": max_delta_quantile,
                "max_xgb_log_relativity_range_across_contexts_over_registered_grid": float(max(xgb_ranges)),
                "max_glm_log_relativity_range_across_contexts_over_registered_grid": float(max(glm_ranges)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol["status"] != "V56_DEVELOPMENT_RATING_CONTEXT_SENSITIVITY_PROTOCOL_LOCKED":
        raise RuntimeError("v0.56 protocol is not locked")

    frame = read_2022_development()
    models, _, exposure = fit_frozen_frequency_models(frame)
    curves = score_curves(protocol, models)
    feature_context = context_feature_summary(curves, protocol)
    cross_context = cross_context_summary(curves, feature_context, protocol)

    tol_ref = protocol["numerical_contracts"]["normalised_reference_point_absolute_tolerance_from_one"]
    for feature, spec in protocol["target_features"].items():
        ref_rows = curves[
            (curves["feature"] == feature)
            & np.isclose(curves["value"], spec["reference_value"])
        ]
        if len(ref_rows) != len(protocol["context_selection"]["contexts"]):
            raise RuntimeError(f"Missing normalised reference rows for {feature}")
        for col in ["glm_frequency_relativity", "xgb_frequency_relativity"]:
            if float((ref_rows[col] - 1.0).abs().max()) > tol_ref:
                raise RuntimeError(f"Reference normalisation contract failed for {feature}/{col}")

    glm_tol = protocol["numerical_contracts"]["glm_context_invariance_absolute_tolerance"]
    max_glm_context_range = float(
        cross_context["max_glm_log_relativity_range_across_contexts_over_registered_grid"].max()
    )
    if max_glm_context_range > glm_tol:
        raise RuntimeError(
            f"GLM context-invariance computational contract failed: {max_glm_context_range} > {glm_tol}"
        )

    OUTDIR.mkdir(exist_ok=True)
    curves.to_csv(OUTDIR / "rating_context_curve_points_v56.csv", index=False)
    feature_context.to_csv(OUTDIR / "rating_context_feature_summary_v56.csv", index=False)
    cross_context.to_csv(OUTDIR / "rating_context_cross_context_summary_v56.csv", index=False)

    context_rows = []
    for context in protocol["context_selection"]["contexts"]:
        context_rows.append(
            {
                "context_id": context["context_id"],
                "change_from_v51_reference": context["change_from_v51_reference"],
                "v51_marginal_exposure_share_of_changed_level": context[
                    "v51_marginal_exposure_share_of_changed_level"
                ],
                "observed_joint_cell_claimed": False,
            }
        )

    preselected = []
    for point in protocol["preselected_review_points"]:
        part = curves[
            (curves["feature"] == point["feature"])
            & np.isclose(curves["quantile"], point["quantile"])
        ].copy()
        base = float(part.loc[part["context_id"] == "BASE", "log_xgb_over_glm_relativity"].iloc[0])
        vals = part["log_xgb_over_glm_relativity"].astype(float)
        preselected.append(
            {
                "feature": point["feature"],
                "quantile": point["quantile"],
                "value": point["value"],
                "base_log_gap": base,
                "context_min_log_gap": float(vals.min()),
                "context_max_log_gap": float(vals.max()),
                "context_log_gap_range": float(vals.max() - vals.min()),
                "fraction_contexts_same_sign_as_base": sign_fraction(vals.tolist(), base),
                "by_context": {
                    row.context_id: float(row.log_xgb_over_glm_relativity)
                    for row in part.itertuples(index=False)
                },
            }
        )

    result = {
        "status": "V56_DEVELOPMENT_RATING_CONTEXT_SENSITIVITY_AUDIT_COMPLETE",
        "analysis_role": protocol["evidence_class"],
        "protocol": {
            "path": str(PROTOCOL_PATH.relative_to(ROOT)),
            "sha256": sha256_file(PROTOCOL_PATH),
            "locked_before_first_execution": protocol["protocol_locked_before_first_v56_execution"],
        },
        "source": {
            "dataset": protocol["source"]["dataset"],
            "years_read": [2022],
            "rows": int(len(frame)),
            "exposure": float(np.sum(exposure)),
            "2023_rows_read": False,
            "2024_rows_read": False,
            "incurred_loss_read": False,
            "actual_premium_read": False,
            "customer_id_read": False,
            "policy_status_read": False,
        },
        "models": {
            "models": sorted(models),
            "model_fit_executed": True,
            "model_refit_per_context": False,
            "calibration_applied": False,
            "hyperparameter_search": False,
        },
        "contexts": context_rows,
        "context_count": len(context_rows),
        "contexts_are_synthetic_reference_profiles": True,
        "marginal_exposure_share_is_not_joint_profile_prevalence": True,
        "target_features": list(protocol["target_features"]),
        "registered_curve_point_count": int(len(curves)),
        "registered_feature_context_summary_count": int(len(feature_context)),
        "preselected_review_points": preselected,
        "cross_context_summary": {
            row.feature: {
                key: getattr(row, key)
                for key in cross_context.columns
                if key != "feature"
            }
            for row in cross_context.itertuples(index=False)
        },
        "computational_contracts": {
            "normalised_reference_points_equal_one_within_registered_tolerance": True,
            "max_glm_log_relativity_range_across_contexts": max_glm_context_range,
            "glm_context_invariance_tolerance": glm_tol,
            "glm_context_invariance_contract_pass": True,
        },
        "interpretation_boundary": protocol["interpretation_rules"],
        "governance_state_unchanged": protocol["governance_state_must_remain"],
        "persisted_row_level_data": False,
    }
    (OUTDIR / "rating_context_sensitivity_summary_v56.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "status": result["status"],
                "rows": result["source"]["rows"],
                "contexts": result["context_count"],
                "preselected_review_points": preselected,
                "cross_context_summary": result["cross_context_summary"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
