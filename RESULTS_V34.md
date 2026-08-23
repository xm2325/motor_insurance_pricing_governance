# v0.34 — 2023 frequency recalibration factor uncertainty

## Question

v0.32 found that 2023-only `business_type` recalibration improved both frequency outputs on the 2024 OOT year, and v0.33 found no material breach across 13 orthogonal major cohorts. v0.34 asks whether those point estimates are stable to sampling variation in the **2023 factor-estimation rows**.

This is deliberately narrower than a full model uncertainty analysis. It bootstraps only the incremental `business_type` frequency factors conditional on the rebuilt globally calibrated prediction functions.

## Leakage and sampling boundary

- Public source: Mendeley `sw4jmdb2sm` v1.
- Model train year: 2022.
- Global calibration year: 2023.
- Incremental factor bootstrap year: 2023.
- Evaluation year: 2024.
- 500 deterministic row-bootstrap draws, seed `20260823`.
- Resampling is stratified by `business_type` and preserves the original NB/P row counts within every draw.
- The same sampled row indices are used for GLM and XGBoost in each replicate, preserving a paired comparison.
- 2024 outcomes are **not** used to estimate a bootstrap factor.
- Bootstrap factor draws are **not clipped**; excursions outside operational guardrails would remain visible.

The sufficient-statistics Poisson-deviance implementation is unit-tested against direct `sklearn.metrics.mean_poisson_deviance` evaluation.

## Pre-registered strong robustness gate

A frequency candidate is marked `ROBUST_TO_2023_FACTOR_ESTIMATION_FOR_FURTHER_SHADOW_TESTING` only if all conditions hold:

1. every NB/P factor 95% percentile interval does not cross 1;
2. all 500 factor draws remain within the project [0.5, 2.0] factor guardrails;
3. at least 80% of draws improve 2024 Poisson deviance;
4. at least 80% of draws do not worsen aggregate 2024 calibration error;
5. at least 80% of draws improve the worst NB/P calibration error;
6. at least 95% of draws satisfy the original v0.32 `<= 0.1%` relative-deviance-worsening guardrail.

These are project retrospective shadow-review rules, not insurer or regulatory thresholds. The thresholds were fixed before the bootstrap result was read.

## Fresh-rebuild reconciliation

The fresh v0.34 point factors and v0.32 aggregate metrics reconcile well inside the existing 0.2% fresh-retrain diagnostic tolerance.

- GLM factor maximum relative difference versus persisted v0.32: **3.39e-9**.
- GLM 2024 metric maximum relative difference: **7.03e-10**.
- XGBoost factor maximum relative difference: **2.12e-16**.
- XGBoost 2024 metric maximum relative difference: **2.29e-16**.

These are fresh-retraining diagnostics, not the same-fit serialization parity contract from v0.26.

## Factor uncertainty

| Output | Segment | v0.32 point factor | Bootstrap median | 95% percentile interval | Crosses 1? |
|---|---|---:|---:|---:|---|
| GLM reference | NB | 0.976356 | 0.976905 | [0.955804, 0.996788] | No |
| GLM reference | P | 1.035197 | 1.036236 | [1.004908, 1.063408] | No |
| XGBoost challenger | NB | 0.969608 | 0.970342 | [0.949049, 0.989880] | No |
| XGBoost challenger | P | 1.046035 | 1.047231 | [1.015465, 1.074819] | No |

All four 95% intervals preserve the point-estimate direction. All 500 draws for all four factor series remain inside [0.5, 2.0]. Individual extreme draws can cross 1 for some GLM/XGBoost NB/P series; this is retained in evidence rather than clipped away. The registered gate is based on the 95% interval direction, not on requiring every draw to stay on one side of 1.

## GLM reference frequency — narrow failure retained

The GLM factor directions are stable, and most bootstrap metrics support the v0.32 point result:

- Poisson deviance improves in **485/500 = 97.0%** of draws.
- Aggregate calibration is not worse in **398/500 = 79.6%** of draws.
- Worst NB/P calibration improves in **497/500 = 99.4%** of draws.
- The original v0.32 deviance guardrail passes in **500/500 = 100%** of draws.

The pre-registered aggregate-calibration requirement is **80%**. The observed **79.6%** is below it, so the GLM result is:

`FACTOR_UNCERTAINTY_REVIEW_REQUIRED`

The threshold is not rounded or relaxed after seeing the result. In count terms, the GLM candidate is only **two successful draws short** of the 400/500 requirement, which is useful sensitivity information but does not convert the registered failure into a pass.

## XGBoost challenger frequency — strong robustness pass

The XGBoost factor directions and downstream 2024 metrics satisfy every registered condition:

- Poisson deviance improves in **499/500 = 99.8%** of draws.
- Aggregate calibration is not worse in **424/500 = 84.8%** of draws.
- Worst NB/P calibration improves in **500/500 = 100%** of draws.
- The original v0.32 deviance guardrail passes in **500/500 = 100%** of draws.

Decision:

`ROBUST_TO_2023_FACTOR_ESTIMATION_FOR_FURTHER_SHADOW_TESTING`

This is stronger evidence for the XGBoost incremental frequency recalibration than for the GLM recalibration under the registered conditional-bootstrap sensitivity analysis.

## What v0.34 does not establish

This bootstrap does **not** resample or refit:

- the underlying 2022 GLM/XGBoost models;
- the existing global 2023 calibration layer;
- claim-development or reserve uncertainty;
- a new temporal evaluation period.

Therefore the bootstrap percentages should not be described as the probability that a production pricing change will improve performance. They are conditional sensitivity rates for the incremental 2023 segment factors under this retrospective design.

## Governance decision

v0.34 authorises no serving or pricing change. Project status remains:

- model-family decision: `HOLD`;
- serving status: `HOLD_SHADOW_ONLY`;
- bundle change authorised: **false**;
- pricing change authorised: **false**;
- model promotion authorised: **false**.

The evidence comes from one public Spanish motor-insurance dataset and does not establish transfer to FIRST CENTRAL or the UK motor market.
