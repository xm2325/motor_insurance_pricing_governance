# v0.56 — Development rating-context sensitivity audit

## Question

v0.51 measured one-factor GLM/XGBoost frequency response shapes at one synthetic reference profile. v0.55 then showed that some large tail disagreements retain direction under fixed development-sample perturbations, but it still did not answer whether the response shape itself depends on the other rating-factor context.

v0.56 therefore asks:

> **Do the large `driver_age` and `vehicle_age` development response-shape disagreements remain visible when one preselected high-exposure categorical context is changed at a time?**

This remains a **2022 development-only interpretability audit**. It is not predictive validation, a causal interaction analysis, an observed segment comparison or a pricing test.

## Protocol locked before first scoring

Protocol: `governance/rating_context_sensitivity_protocol_v56.json`  
Protocol SHA-256: `fc4b1f228c260f5480bb12be8f559e17faa3ade3cd3e61830fecfad905cb504d`

The protocol was committed at `5bf450c1fcca8cd65d349d2ed3ba649ff1da813b` before the first v0.56 scoring run.

Frozen design:

- fit the exact v0.21 Poisson GLM and XGBoost frequency specifications once on all valid 2022 development rows;
- target only `driver_age` and `vehicle_age` using the exact persisted v0.51 11-point grids;
- use the original v0.51 reference profile;
- evaluate five fixed synthetic reference-profile contexts;
- change exactly one categorical field from the reference at a time;
- normalise each model/feature/context curve to that model's own score at the registered target-feature reference value;
- no context-specific refitting and no calibration;
- no post-result context selection or stability threshold.

## Preselected contexts

The non-reference levels were selected from persisted v0.51 evidence **before v0.56 scores existed**: for four preselected dimensions, use the highest-2022-exposure non-reference level.

| Context | Change from v0.51 reference | v0.51 marginal 2022 exposure share of changed level |
|---|---|---:|
| `BASE` | none | — |
| `BUSINESS_TYPE_P` | `business_type: NB → P` | **3.22%** |
| `POLICY_TYPE_COMP_E` | `policy_type: CC → COMP_E` | **23.75%** |
| `FUEL_TYPE_G` | `fuel_type: D → G` | **36.07%** |
| `CIRCULATION_AREA_R` | `circulation_area: U → R` | **45.98%** |

These percentages are **marginal exposure shares of the changed level**, not prevalence of the complete synthetic profile. v0.56 does not claim that these five profiles are observed customer cells.

## Why within-context normalisation matters

For every target feature, context and model, the curve is divided by that same model/context score at the registered reference value (`driver_age=47`, `vehicle_age=23`). This removes the categorical context's main score level and isolates response shape.

That creates a useful implementation control. The Poisson GLM specification is additive with no registered feature interactions, so its normalised age response should be context-invariant. In the first execution the maximum GLM log-relativity spread across contexts is only **6.38×10⁻¹⁶**, far inside the preregistered `1e-8` computational tolerance. The context variation below is therefore driven by the XGBoost response, not by a normalisation bug in the GLM curve.

## Preselected q95 results

### Driver age q95 = 68

The original BASE gap is approximately **−0.26866**. Across the five preregistered contexts:

| Context | log(XGB/GLM relativity) gap |
|---|---:|
| BASE | **−0.268660** |
| BUSINESS_TYPE_P | **−0.268660** |
| POLICY_TYPE_COMP_E | **−0.187245** |
| FUEL_TYPE_G | **−0.278505** |
| CIRCULATION_AREA_R | **−0.244803** |

Range: **−0.278505 to −0.187245**, width **0.091260**.  
All **5/5 contexts retain the BASE negative sign**.

So the high-driver-age disagreement is not unique to the original reference profile, but its magnitude is context-dependent. In particular, `POLICY_TYPE_COMP_E` makes the q95 gap smaller in this synthetic-profile diagnostic.

### Vehicle age q95 = 44

BASE is approximately **+0.267706**. Across contexts:

| Context | log(XGB/GLM relativity) gap |
|---|---:|
| BASE | **+0.267706** |
| BUSINESS_TYPE_P | **+0.267706** |
| POLICY_TYPE_COMP_E | **+0.307804** |
| FUEL_TYPE_G | **+0.263880** |
| CIRCULATION_AREA_R | **+0.316662** |

Range: **+0.263880 to +0.316662**, width **0.052782**.  
All **5/5 contexts retain the BASE positive sign**.

The old-vehicle tail disagreement is therefore directionally persistent across these fixed profiles, while its magnitude still changes.

## Whole-grid context dependence

The q95 result must not be generalised to the full curve.

### Driver age

- maximum absolute context-minus-BASE log-gap difference anywhere on the registered grid: **0.081415**;
- this occurs for `POLICY_TYPE_COMP_E` around q90;
- maximum XGBoost log-relativity range across contexts: **0.091260**;
- maximum GLM log-relativity range across contexts in the first run: **6.38×10⁻¹⁶**.

The driver-age curve therefore has non-zero XGBoost context dependence, even though the large q95 disagreement remains negative in all five profiles.

### Vehicle age

Context dependence is stronger locally:

- maximum absolute context-minus-BASE log-gap difference: **0.141793**;
- it occurs at **q05** for `POLICY_TYPE_COMP_E`;
- maximum XGBoost log-relativity range across contexts: **0.141793**;
- maximum GLM spread in the first run remains only **6.38×10⁻¹⁶**.

At vehicle-age q05, the model-family gap **changes sign across contexts**: BASE is about **+0.02210**, while `POLICY_TYPE_COMP_E` is about **−0.11969**. `FUEL_TYPE_G` and `CIRCULATION_AREA_R` are also slightly negative.

This is an important negative result against an over-broad interpretation: the q95 old-vehicle tail disagreement is directionally persistent, but **the entire vehicle-age response-shape disagreement is not context-invariant**.

## What v0.56 supports

A defensible summary is:

> **The large q95 `driver_age` and `vehicle_age` GLM/XGBoost development disagreements retain their direction across five preregistered synthetic reference-profile contexts, but XGBoost response shape is context-dependent in magnitude, and local vehicle-age differences can reverse sign across contexts.**

This complements v0.55:

- v0.55: large tail gaps can persist under development-sample perturbation, while small/local differences may be unstable;
- v0.56: large tail gaps can also persist across selected rating contexts, while local XGBoost response shape can depend materially on context.

Neither result says that XGBoost is more accurate or that either curve is the true pricing relationship.

## Hosted numerical repeat

The exact scoring head `a1d4dbe60e79bf4f1967a4bf6e34d00fcaa122e1` was executed twice before closeout:

- run **32776747130**, attempt 1 / job **97589429492**, Azure **centralus** — SUCCESS;
- the same run/head, attempt 2 / job **97590009549**, Azure **northcentralus** — SUCCESS.

Both used Ubuntu 24.04 image `20260816.277.1`, Python 3.12.14, NumPy 2.5.2, SciPy 1.18.0, scikit-learn 1.9.0 and XGBoost 3.4.1, with the registered single-thread environment for scoring.

The artifacts are **not byte-identical**, so v0.56 does not claim bitwise or exact-metric reproducibility. The observed hosted numerical differences are:

- maximum GLM frequency-relativity difference: **8.02×10⁻⁸**;
- maximum `log(XGB/GLM)` gap difference: **6.92×10⁻⁸**;
- maximum feature/context q95-gap difference: **6.92×10⁻⁸**;
- difference in the reported driver/vehicle q95 context-range widths: at most **5.97×10⁻¹⁶**;
- XGBoost frequency relativities: **exactly equal** across both artifacts.

Every qualitative context result is unchanged: both q95 points remain 5/5 same sign as BASE; the same contexts define q95 minima/maxima; the same locations produce the largest whole-grid context delta; and vehicle-age q05 is positive for `BASE`/`BUSINESS_TYPE_P` but negative for `POLICY_TYPE_COMP_E`/`FUEL_TYPE_G`/`CIRCULATION_AREA_R` in both executions.

The numerical drift is therefore tiny relative to the observed registered context-dependent log-gap ranges (**0.0528–0.1418**) and does not explain the context result. This is descriptive numerical context, not a new acceptance threshold. Exact artifact IDs, hashes and comparisons are in `governance/rating_context_repeat_evidence_v56.json`.

## Evidence boundary

v0.56 reads only valid 2022 development features, exposure and frequency claim counts required to rebuild the frozen development models. It reads no 2023/2024 rows, incurred loss, actual premium, customer ID or policy status.

It creates:

- no held-out predictive performance metric;
- no confidence interval;
- no context-stability acceptance threshold;
- no causal interaction estimate;
- no observed segment effect;
- no fairness conclusion;
- no customer premium effect;
- no candidate-selection or model-promotion evidence;
- no FIRST CENTRAL/current-UK transport claim.

Current governance state remains **`EVIDENCE_GAP_HOLD`**, **5/8** machine gates, external target support **0/4**, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, with customer pricing unauthorised.

## CI evidence

Both locked-head executions passed:

- protocol lock before scoring;
- source verification;
- 110 registered curve points;
- 10 feature/context summaries;
- GLM context-invariance computational control;
- 10 v0.56 contracts;
- synthetic-context / non-validation boundary;
- aggregate-only artifact upload.

No protocol, context, target feature, grid, model specification or interpretation rule changed between attempts.
