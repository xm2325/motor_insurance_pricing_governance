# v0.55 — Development rating-shape stability audit

## Scope

v0.55 asks a narrow interpretability question left open by v0.51:

> When the 2022 development sample is perturbed in a preregistered way, do the displayed GLM/XGBoost frequency response-shape differences keep the same direction and approximate magnitude?

This is **not** a predictive-validation experiment. The protocol was committed before the first execution and fixes five deterministic, outcome-unstratified folds (`seed=20260824`). Each fold refits the exact frozen v0.21 frequency specifications on the remaining 80% of **2022 development rows only**. The v0.51 reference profile and all v0.51 numeric/categorical evaluation points remain fixed; they are not re-estimated inside folds.

No 2023 or 2024 rows, incurred-loss outcomes, actual premium, customer ID or policy-status fields are read. No held-out performance metric, confidence interval, candidate-selection rule, promotion gate, composite score or customer-pricing authority is created.

Protocol: `governance/rating_shape_stability_protocol_v55.json`  
Locked protocol SHA-256: `16f96d57e10e0445c014d6fce1cd8dbfdabbd04c4c82b826a13d18899d298f48`

## Development population and fold design

- 2022 valid development rows: **67,171**
- exposure: **41,912.495890410966**
- claims used for frequency fitting: **12,664**
- folds: **5**
- training rows per fold: **53,736–53,737**
- excluded rows summed across folds: **67,171** exactly
- outcome stratification: **none**
- reference/grid re-estimation per fold: **none**
- calibration inside folds: **none**
- held-out fold performance scoring: **none**

The output is therefore a fixed-design **development fit sensitivity** analysis. Fold min/max values are not sampling confidence intervals.

## Preselected review points

The protocol selected three review points before the first v0.55 execution: two large v0.51 tail disagreements and one deliberately small-gap counterexample.

| Preselected point | v0.51 full-fit log(XGB/GLM relativity) gap | Five-fold mean | Fold min → max | Range | Folds with same sign as v0.51 |
|---|---:|---:|---:|---:|---:|
| `driver_age` q95 = 68 | **-0.268660** | -0.246722 | **-0.356179 → -0.122047** | 0.234132 | **5/5** |
| `vehicle_age` q95 = 44 | **+0.267706** | +0.255565 | **+0.156786 → +0.346264** | 0.189478 | **5/5** |
| `vehicle_value` q95 = 49,666.33455 | **-0.021964** | -0.005070 | **-0.059073 → +0.028179** | 0.087251 | **2/5** |

For both large preselected tail gaps, every fold retains the same direction as the v0.51 full-development fit. Their magnitude is nevertheless development-sample-sensitive: the driver-age q95 range is about 0.234 log-relativity units and the vehicle-age q95 range about 0.189.

The deliberately smaller `vehicle_value` counterexample changes sign across folds. This is useful negative evidence against over-generalising the response-shape story: a displayed small difference can be dominated by ordinary development-sample perturbation.

## The whole feature is not automatically “stable”

The audit retains all registered v0.51 points rather than reporting only the three examples. That matters because local behaviour can differ within one feature.

Examples:

- `driver_age`: minimum same-sign fraction across non-zero v0.51 registered points is **1.0**. In this fixed-fold audit, the displayed driver-age differences retain their direction across all five folds at every non-reference registered point.
- `vehicle_age`: minimum same-sign fraction is only **0.6**. The q95 old-vehicle point is directionally persistent, but the q05 point can change sign; therefore v0.55 does **not** support the statement that the entire vehicle-age curve is stable.
- `vehicle_value`: minimum same-sign fraction is **0.2** and maximum fold gap range across its registered points is **0.08725**. Small local differences are visibly sensitive.
- several categorical/smaller effects are also sensitive: `payment_frequency` has a minimum same-sign fraction **0.4**, `policy_type` **0.2**, and `power_to_weight_ratio` **0.2**.

So the defensible conclusion is local and graded, not binary.

## Interpretation

The new evidence supports this statement:

> **Some of the larger development tail disagreements identified in v0.51 — especially driver age q95 and vehicle age q95 — retain their direction under the preregistered five-fold development perturbation, while their magnitude remains sample-sensitive and smaller/local response differences can reverse sign.**

It does **not** establish that XGBoost is more accurate, that either response curve is causal, that a customer should receive a different premium, or that the Spanish 2024 / external validation evidence has changed.

v0.55 also does not create a post-hoc “stability threshold”. The fold range and same-sign fractions are descriptive audit outputs under the protocol fixed before execution.

## Governance boundary

Nothing in v0.55 clears or modifies the existing evidence blockers. Current project state remains:

- model-family decision: **`HOLD`**;
- serving: **`HOLD_SHADOW_ONLY`**;
- promotion review: **`NOT_OPEN`**;
- committee evidence status: **`EVIDENCE_GAP_HOLD`**, **5/8** machine gates pass;
- preregistered Australian/Belgian external target gates: **0/4**;
- customer pricing authorised: **false**.

This is project evidence about development response-shape sensitivity, not a FIRST CENTRAL/current-UK transport claim or insurer/regulatory standard.

## Cross-region numerical repeat

The exact computational head `cc6babb828680fef050a1267055373e3cc8ae455` was executed twice before closeout:

- GitHub Actions run **32703117264**, attempt 1 / job **97358535042**, Azure **westus** — SUCCESS;
- the same run/head was explicitly re-run as attempt 2 / job **97585065220**, Azure **eastus2** — SUCCESS.

Both used Ubuntu 24.04 image `20260816.277.1`, Python 3.12.14, NumPy 2.5.2, SciPy 1.18.0, scikit-learn 1.9.0 and XGBoost 3.4.1 with `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `MKL_NUM_THREADS=1` for the audit execution.

The three aggregate files are **not byte-identical**, so v0.55 does not claim bitwise or exact-metric reproducibility. The observed hosted numerical differences are instead extremely small:

- maximum absolute GLM frequency-relativity difference: **3.50×10⁻⁹**;
- maximum absolute `log(XGB/GLM)` relativity-gap difference: **3.47×10⁻⁹**;
- maximum absolute difference in a point-summary fold-gap range: **2.73×10⁻⁹**;
- XGBoost fold frequency relativities: **exactly equal** across the two artifacts;
- all row/key structure and all preselected same-sign fractions are unchanged.

The registered fold perturbation ranges are approximately **0.087–0.234** at the three preselected points and reach **0.342** elsewhere, so the hosted GLM numerical drift is many orders of magnitude smaller than the sample-perturbation variation being audited. This is descriptive numerical context, not a newly invented acceptance threshold.

The repeat therefore supports a narrower claim: **the qualitative v0.55 interpretation is numerically robust across these two hosted regions, while the persisted floating-point outputs are not bitwise identical.** Exact provenance, artifact IDs, hashes and comparison values are recorded in `governance/rating_shape_repeat_evidence_v55.json`.

## CI evidence

The first and second locked-head executions both passed protocol locking, the five-fold audit, **10 contracts**, and the development-only/non-validation boundary. No protocol, fold rule, evaluation grid, model specification or interpretation rule was changed between the two attempts.
