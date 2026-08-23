# v0.47 — Frozen-model disagreement attribution

## Purpose

v0.47 explains **where the frozen GLM and XGBoost shadow scores differ** without turning the already-consumed Spanish 2024 validation period back into model-selection evidence.

The analysis is a post-hoc model-sensitivity diagnostic only. It does **not** refit a new candidate family, tune hyperparameters, read 2024 claim-count/incurred-loss labels, change any historical gate, or authorise model promotion or customer pricing.

## Diagnostic design

The workflow reuses the frozen v0.21 model definitions:

- 2022: fit the same four GLM/XGBoost reference/challenger models;
- 2023: estimate the same locked aggregate calibration scales;
- 2024: read **rating features + exposure only** for disagreement diagnostics.

From 168,085 positive-exposure 2024 rows, the workflow draws a deterministic **20,000-row** sample with seed **20260823**, without outcome stratification.

For each registered rating factor, it replaces that factor only with its 2022 training reference value:

- numeric factor → 2022 training median;
- categorical factor → 2022 training mode.

All other features remain fixed. It then recomputes the exposure-weighted absolute log score disagreement:

`|log(challenger / reference)|`.

A positive reduction means that replacing the observed factor with the 2022 reference makes the GLM and XGBoost scores more similar on this diagnostic sample.

This is **not causal attribution**, **not SHAP**, and **not predictive feature importance**. One-factor effects are non-additive because the fitted models contain nonlinearities and interactions; the reductions must not be summed to 100%.

## Baseline model-family disagreement

### Frequency

Exposure-weighted `log(XGB / GLM)` on the 20,000-row diagnostic sample:

- mean: **-0.00212**;
- mean absolute disagreement: **0.09926**;
- q05: **-0.19861**;
- median: **-0.01021**;
- q95: **+0.22425**;
- XGBoost above GLM on **46.25%** of exposure.

The near-zero mean masks material bidirectional row-level disagreement: XGBoost is not simply above or below the GLM everywhere.

### Pure premium

Exposure-weighted `log(XGB / GLM)`:

- mean: **-0.06765**;
- mean absolute disagreement: **0.31708**;
- q05: **-0.76105**;
- median: **-0.04247**;
- q95: **+0.53378**;
- XGBoost above GLM on **45.61%** of exposure.

Pure-premium model-family divergence is substantially wider than frequency divergence on this diagnostic sample. This is a score-difference observation, not evidence that either model is more accurate.

## Factor-level disagreement sensitivity

### Frequency — largest reductions in mean absolute log disagreement

| Rating factor | Absolute reduction | Fraction of baseline reduced | Exposure-weighted sign-flip rate |
|---|---:|---:|---:|
| `vehicle_brand` | **0.01068** | **10.75%** | 21.23% |
| `policy_type` | **0.01051** | **10.58%** | 13.38% |
| `vehicle_value` | **0.00596** | **6.00%** | 12.17% |
| `payment_frequency` | **0.00328** | **3.30%** | 4.43% |
| `power_to_weight_ratio` | **0.00235** | **2.37%** | 8.30% |

The strongest frequency sensitivity is concentrated in vehicle brand and policy type. Replacing either factor alone with its 2022 reference reduces mean absolute GLM-vs-XGBoost disagreement by about one tenth.

That does **not** mean these factors explain 21% in total; the one-factor diagnostics overlap through interactions and are deliberately not additive.

### Pure premium — largest reductions

| Rating factor | Absolute reduction | Fraction of baseline reduced | Exposure-weighted sign-flip rate |
|---|---:|---:|---:|
| `business_type` | **0.01974** | **6.23%** | 12.37% |
| `power_to_weight_ratio` | **0.01073** | **3.39%** | 16.82% |
| `vehicle_value` | **0.01052** | **3.32%** | 12.04% |
| `circulation_area` | **0.00913** | **2.88%** | 6.31% |
| `payment_frequency` | **0.00704** | **2.22%** | 4.96% |

`business_type` is the largest single pure-premium sensitivity driver, but replacing it alone reduces baseline absolute disagreement by only **6.23%**. Together with the much larger pure-premium baseline disagreement, this suggests the divergence is more diffuse / interaction-heavy than the frequency disagreement.

This is consistent with earlier evidence that `business_type` mix changed materially across calendar years, but v0.47 does **not** claim that portfolio mix caused predictive deterioration or caused the model-performance difference. It only measures score sensitivity under a one-factor substitution.

## Segment output

The workflow also persists aggregate, label-free disagreement summaries across:

- `business_type`;
- `policy_type`;
- `payment_frequency`;
- driver-age band.

No insured IDs, claim counts, incurred losses, premiums or row-level predictions are persisted.

## Numerical limitation retained

The pure-premium Tweedie GLM rebuild emitted a scikit-learn convergence warning because the frozen v0.21 specification reached its registered `max_iter=900` limit.

v0.47 deliberately **does not change `max_iter`, solver, model family or hyperparameters after seeing the diagnostic result**. Changing the frozen estimator solely to remove the warning would create a different model specification and undermine the purpose of this diagnostic.

The warning therefore remains a documented limitation. v0.47 is a model-disagreement sensitivity analysis, not a new point-metric reproducibility claim.

## Governance boundary

Spanish 2024 remains `CONSUMED_RETROSPECTIVE_VALIDATION`. Its allowed role here is `post_hoc_diagnostics` only.

The v0.47 result does not change:

- model-family decision: **HOLD**;
- serving status: **HOLD_SHADOW_ONLY**;
- Model Change Committee state: **EVIDENCE_GAP_HOLD**;
- promotion review: **NOT_OPEN**;
- model promotion authorised: **No**;
- customer-pricing change authorised: **No**.

The highest-value use of this evidence is diagnostic: it tells a pricing/model-risk reviewer where GLM and XGBoost behaviour diverges and which rating-factor dimensions deserve closer review, without recycling the consumed validation period into another model-selection exercise.
