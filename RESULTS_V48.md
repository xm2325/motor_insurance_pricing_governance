# v0.48 — Portfolio-neutral technical relativity migration

## Decision

**Diagnostic complete; model-family decision remains `HOLD`, serving remains `HOLD_SHADOW_ONLY`, and committee readiness remains `EVIDENCE_GAP_HOLD`.**

v0.48 does not estimate a customer premium or a commercial rate change. It asks a narrower model-risk question: if the frozen XGBoost challenger and GLM reference are forced to have the same aggregate predicted technical-risk total, how differently do they distribute relative risk indications across the already-consumed Spanish 2024 feature population?

## Data and governance boundary

- Source: Mendeley `sw4jmdb2sm` v1, SHA-256 `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4`.
- Frozen training/calibration design: 2022 model fit, 2023 locked aggregate calibration.
- Diagnostic population: all **168,085** 2024 rows with positive exposure.
- 2024 fields read by the diagnostic: registered rating features plus exposure only.
- 2024 claim counts, incurred losses and actual premiums are not read.
- Spanish 2024 remains `CONSUMED_RETROSPECTIVE_VALIDATION`; this is an allowed `post_hoc_diagnostics` use under v0.35, not fresh independent evidence.
- No candidate selection, model/calibration parameter change, promotion evidence, customer-pricing authority or row-level output persistence is created.

## Portfolio-neutralisation

For each target, the challenger is rescaled only for this diagnostic:

`normalised_challenger = raw_challenger * sum(reference * exposure) / sum(raw_challenger * exposure)`

The calculation is explicitly performed in float64. On the successful registered run, both targets satisfy:

- `normalised_total_over_reference = 1.0`
- `absolute_total_difference_after_neutralisation = 0.0`

This removes the aggregate level difference before studying redistribution. It does not change the stored model, calibration or serving bundle.

## Full-population redistribution

### Frequency

Successful float64 run:

- GLM aggregate predicted total: **37,826.2453**
- raw XGBoost aggregate total: **37,708.2998**
- raw XGBoost / GLM: **0.996882**
- neutralisation scale applied to XGBoost: **1.003128**
- exposure-weighted mean absolute relativity change: **10.18%**
- exposure with `|change| > 5%`: **64.96%**
- exposure with `|change| > 10%`: **36.81%**
- exposure with `|change| > 20%`: **10.98%**
- median change: approximately **-0.61%**
- 5th / 95th percentiles: approximately **-17.76% / +25.23%**

The frequency redistribution is material but comparatively moderate: about 35.0% of exposure remains within ±5% after the aggregate totals are forced equal.

### Pure premium

Successful float64 run:

- GLM aggregate predicted total: approximately **36.32 million**
- raw XGBoost aggregate total: approximately **35.58 million**
- raw XGBoost / GLM: approximately **0.9796**
- neutralisation scale applied to XGBoost: approximately **1.0208**
- exposure-weighted mean absolute relativity change: approximately **32.3%**
- exposure with `|change| > 5%`: approximately **89.04%**
- exposure with `|change| > 10%`: approximately **78.26%**
- exposure with `|change| > 20%`: approximately **58.16%**
- median change: approximately **-2.69%**
- 5th / 95th percentiles: approximately **-52.18% / +73.5%**

The pure-premium model families therefore redistribute technical risk much more strongly than the frequency models even after their aggregate totals are matched.

## Major-segment pattern

The main descriptive pure-premium segment shifts are stable in direction across the repeat-run audit:

| Segment | Exposure share | Portfolio-neutral XGB vs GLM aggregate technical relativity |
|---|---:|---:|
| business type NB | 48.18% | about **+8.65%** |
| business type P | 51.82% | about **-6.52% to -6.53%** |
| policy type COMP_E | 27.16% | about **+13.68%** |
| policy type CC | 56.93% | about **-9.27%** |
| driver age 35–49 | 42.01% | about **+5.20%** |
| driver age 50–64 | 34.48% | about **-5.49%** |

These are differences between frozen technical-risk score families, not segment accuracy, fairness, causality or realised customer-price effects.

The `<25` age band shows a much larger positive pure-premium shift, but it represents only about **0.15% of exposure**. It is therefore retained in the aggregate diagnostic file rather than promoted to a headline finding.

## Numerical reproducibility audit

The frozen Tweedie GLM continues to emit its existing `max_iter=900` convergence warning. v0.48 does not change that frozen specification after observing the diagnostic.

Two successful float64 executions on the same head (`3492c6a72db69a47a7708f4dc4ea1420e366616f`) were compared using GitHub Actions artifacts:

- workflow run: `32643619315`
- jobs: `97204386862` and `97282171330`
- artifact IDs: `9494274481` and `9502479141`
- artifact SHA-256: `6bdeebfa...a7e29c2` and `3cfb9501...701af25`

Observed envelope:

- frequency `>10%` and `>20%` exposure shares: **identical** across the two executions;
- pure-premium GLM aggregate total relative range: **0.00411%**;
- pure-premium mean-absolute-change range: **0.001096** in ratio units;
- pure-premium `>10%` exposure-share range: **0.00447 percentage points**;
- pure-premium `>20%` exposure-share range: **0.00977 pp**;
- largest range among the six major segment headline shifts: about **0.0159 pp**.

Conclusion: `DESCRIPTIVE_REDISTRIBUTION_HEADLINES_STABLE_WITH_REGISTERED_TWEEDIE_GLM_NUMERICAL_LIMITATION`.

This is not a claim of bitwise model reproducibility or performance reproducibility. Pure-premium values are deliberately reported at modest precision.

## Engineering failure retained

The first v0.48 workflow execution exposed a useful implementation defect: NumPy operations involving the original prediction arrays left aggregate-neutralisation residuals around `10^-8`, which violated the 12-decimal neutralisation contract. The test was **not relaxed**. `portfolio_neutralise` was changed to use explicit float64 arrays, after which both aggregate totals match exactly in the registered calculation.

This failure is retained as evidence that the contract caught a numerical implementation issue rather than being weakened to accommodate it.

## Interpretation boundary

The v0.48 outputs are **technical risk-score relativity diagnostics only**. They do not include expenses, commission, reinsurance, profit, tax, demand/elasticity, underwriting actions or regulatory pricing constraints. The fixed ±5% / ±10% / ±20% bands are project diagnostic bins, not insurer or regulatory thresholds.

No result here establishes model promotion, actual premium movement, commercial uplift, fairness, transport to FIRST CENTRAL, or transfer to the current UK motor market.
