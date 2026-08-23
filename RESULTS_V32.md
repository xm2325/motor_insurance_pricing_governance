# v0.32 — 2023-only `business_type` Recalibration Review

## Decision

**PASS as a review workflow; only the two frequency recalibration candidates are supported for further shadow testing. Pure-premium recalibration is rejected.**

The global model-family decision remains **`HOLD`**, serving remains **`HOLD_SHADOW_ONLY`**, and v0.32 authorises **no bundle change, pricing change or model promotion**.

v0.32 follows the v0.22/v0.23 `business_type` portfolio-mix alert and the v0.31 mature-outcome review. The question is narrower than model replacement:

> Can a simple `business_type` calibration adjustment, fitted only from the 2023 calibration period, improve untouched 2024 calibration without giving up predictive fit?

## Leakage boundary

The model family is unchanged. The four base outputs are still trained on 2022 data and globally calibrated on 2023 data.

The additional v0.32 segment multipliers use only:

- 2023 `business_type`;
- 2023 exposure;
- 2023 `total_claims` for frequency or 2023 `total_incurred` for pure premium;
- predictions that already contain the existing global 2023 calibration scale.

**No 2024 claim or incurred value is used to fit a multiplier.** The locked candidate is evaluated on 2024 only after its factors are fixed.

The mix-only decomposition uses 2024 `business_type` exposure shares, but not 2024 claims/incurred values, to ask how much calibration change would arise from portfolio composition alone if 2023 segment rates stayed fixed.

## 2023 locked multipliers

All NB/P groups pass the pre-set minimum support rules: at least 500 rows and at least 1% of calibration exposure. No multiplier hits the pre-set `[0.50, 2.00]` bounds.

| Output | NB multiplier | P multiplier |
|---|---:|---:|
| GLM frequency | **0.97636** | **1.03520** |
| XGBoost frequency | **0.96961** | **1.04603** |
| GLM pure premium | **1.03370** | **0.95703** |
| XGBoost pure premium | **0.96886** | **1.04632** |

These are modest adjustments around the existing global scale, rather than a new model fit.

## Untouched 2024 candidate results

The field-level support rule was fixed before reading the 2024 outcome result:

1. every 2023 segment must pass support rules;
2. the worst 2024 segment absolute log-calibration error must improve;
3. aggregate 2024 calibration must not move farther from 1.0;
4. relative 2024 deviance worsening must be no more than **0.1%**.

| Output | Baseline deviance | Candidate deviance | Baseline aggregate calibration | Candidate aggregate calibration | Worst segment log-error, baseline → candidate | Decision |
|---|---:|---:|---:|---:|---:|---|
| GLM frequency | 1.118536 | **1.118091** | 0.96309 | **0.97045** | 0.06574 → **0.03115** | `SUPPORTED_FOR_FURTHER_SHADOW_TESTING` |
| XGBoost frequency | 1.118835 | **1.118119** | 0.96009 | **0.96956** | 0.07805 → **0.03304** | `SUPPORTED_FOR_FURTHER_SHADOW_TESTING` |
| GLM pure premium | 93.931806 | **93.845803** | **0.95307** | 0.94352 | 0.14960 → **0.11645** | `RETAIN_GLOBAL_CALIBRATION` |
| XGBoost pure premium | **93.951316** | 93.957534 | 0.93359 | **0.94306** | **0.08715** → 0.11879 | `RETAIN_GLOBAL_CALIBRATION` |

The two frequency candidates satisfy all four rules. Their deviance also decreases slightly rather than merely staying inside the 0.1% guardrail:

- GLM frequency relative deviance change: **−0.0398%**;
- XGBoost frequency relative deviance change: **−0.0640%**.

That result supports a future **shadow-only frequency recalibration experiment**, not an immediate serving change.

The pure-premium results show why the gate is multi-part rather than based on one metric:

- **GLM pure premium:** segment error and deviance improve, but aggregate calibration moves from **0.95307 to 0.94352**, farther from 1.0, so the candidate is rejected.
- **XGBoost pure premium:** aggregate calibration improves from **0.93359 to 0.94306**, but the worst segment log-error worsens from **0.08715 to 0.11879** and deviance rises slightly, so the candidate is rejected.

The same `business_type` correction therefore should **not** be applied mechanically across pricing targets.

## What explains the 2024 calibration change?

The exact log-ratio decomposition separates the effect of changing `business_type` exposure shares from the remaining within-segment/time change.

| Output | Total log calibration change | Portfolio-mix component | Within-segment/time component |
|---|---:|---:|---:|
| GLM frequency | −0.03761 | −0.00731 | **−0.03030** |
| XGBoost frequency | −0.04073 | −0.00947 | **−0.03127** |
| GLM pure premium | −0.04807 | **+0.00965** | **−0.05772** |
| XGBoost pure premium | −0.06871 | −0.00961 | **−0.05911** |

For both frequency models, changing NB/P mix explains only part of the observed move away from calibration 1.0; the larger component remains within segments over time.

For GLM pure premium the result is stronger: the 2024 mix-only counterfactual moves the calibration ratio slightly **above** 1.0 (`1.00970`), while the actual 2024 ratio is `0.95307`. In this case the changed NB/P mix would have offset part of the observed underprediction rather than caused it.

This changes how the earlier v0.22 PSI alert should be read. The large `business_type` PSI correctly identified a material input-distribution change, but it did **not** establish that portfolio composition was the main cause of realised calibration deterioration. Label-based follow-up is needed before assigning a cause or changing calibration.

## Baseline regression check

The final GitHub Actions run rebuilds the four-model bundle before v0.32. Its baseline 2024 deviance values match the persisted v0.31 values exactly in this run for all four outputs; maximum relative difference is **0.0**.

The contract allows a **0.2%** relative tolerance because this is a fresh-training regression diagnostic, not the v0.26 same-fit serialization parity test.

## Verified workflow

PR validation run `32606767378`, head `6946881b68dc65e1dd2de229d59312657281e644`, completed successfully and performed:

1. v0.32 numerical recalibration contracts;
2. Mendeley source discovery/download-cache verification and schema audit;
3. fresh rebuild of the four globally calibrated shadow models;
4. v0.27 content-addressed seal and verification;
5. scoring of the 2023 calibration cohort and 2024 OOT cohort;
6. 2023-only NB/P multiplier fit;
7. untouched 2024 baseline/candidate comparison;
8. portfolio-mix vs within-segment/time decomposition;
9. v0.31 baseline regression check;
10. leakage and governance assertions.

On the same final PR head, the lightweight governance CI and the existing v0.30 attested-release-admission regression also passed.

## Interpretation boundary

The 2024 evaluation uses real historical claims/incurred outcomes from one Spanish motor-insurance portfolio. This is not production evidence and does not establish transfer to FIRST CENTRAL or the UK motor market.

`SUPPORTED_FOR_FURTHER_SHADOW_TESTING` means that the frequency recalibration rule passed the fixed v0.32 retrospective gate. It does **not** authorise adding those factors to the sealed serving bundle. A further prospective or rolling temporal test is required before considering a bundle-level calibration change.

The pure-premium result remains **retain global calibration**. The overall model-family decision remains **HOLD**.
