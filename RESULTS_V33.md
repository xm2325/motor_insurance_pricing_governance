# v0.33 — Fixed-frequency recalibration transport review

## Question

v0.32 found that 2023-only `business_type` recalibration improved both frequency outputs on untouched 2024 aggregate and NB/P calibration metrics. v0.33 asks a different question before any bundle change is considered:

> Do those already-locked frequency multipliers create material harm in 2024 cohorts defined by variables other than the fitted `business_type` segment?

The v0.32 multipliers are reused exactly. v0.33 does **not** refit them and does not use any 2024 claim outcome to estimate a multiplier.

## Data and evaluation boundary

- Public source: Mendeley `sw4jmdb2sm` v1.
- Evaluation cohort: 168,085 usable 2024 policy-years.
- Candidate source: persisted v0.32 2023-only `business_type` multipliers.
- Candidate factors are not refitted in v0.33.
- 2024 claims are used only to evaluate the already-locked candidate.
- The public source has calendar year but no intra-year policy date, so this is **not** represented as monthly or prospective validation.
- Transport dimensions are intentionally orthogonal to the fitted segment: `seen_before_2024`, `driver_age_band`, `policy_type`, and `payment_frequency`.

## Pre-specified major-cohort guardrails

A subgroup is treated as a major cohort only when it has all of:

- at least 2,000 rows;
- at least 2% of 2024 exposure;
- at least 100 observed claims.

For a major cohort, the candidate must not exceed either project review boundary:

- absolute log-calibration-error deterioration > 0.02;
- relative Poisson-deviance worsening > 0.5%.

These are project shadow-review rules, not insurer or regulatory thresholds.

## Fresh replay reconciliation

Before subgroup interpretation, the fresh v0.33 replay reconciled exactly to the persisted v0.32 aggregate frequency results.

| Frequency output | Baseline deviance | Candidate deviance | Baseline calibration | Candidate calibration | Max relative reconciliation difference |
|---|---:|---:|---:|---:|---:|
| GLM reference | 1.118536263 | 1.118090706 | 0.963088026 | 0.970446680 | 0.0 |
| XGBoost challenger | 1.118835276 | 1.118119032 | 0.960085035 | 0.969561756 | 0.0 |

## Transport results

### GLM reference frequency

- 13 major cohorts evaluated.
- 0 major-cohort gate breaches.
- Calibration improved in 8/13 major cohorts.
- Poisson deviance improved in 10/13 major cohorts.
- Worst calibration deterioration: 0.0109915, below the 0.02 review boundary.
- Worst relative deviance worsening: 0.1223%, below the 0.5% review boundary.
- Decision: `TRANSPORT_STABLE_FOR_FURTHER_SHADOW_TESTING`.

The largest observed calibration deterioration was quarterly payment frequency (`Q`): +0.0109915 absolute log-calibration error. The largest deviance deterioration was `policy_type=TPG`: +0.1223%. Both stayed inside the pre-specified major-cohort guardrails.

### XGBoost challenger frequency

- 13 major cohorts evaluated.
- 0 major-cohort gate breaches.
- Calibration improved in 9/13 major cohorts.
- Poisson deviance improved in 10/13 major cohorts.
- Worst calibration deterioration: 0.0146934, below the 0.02 review boundary.
- Worst relative deviance worsening: 0.1313%, below the 0.5% review boundary.
- Decision: `TRANSPORT_STABLE_FOR_FURTHER_SHADOW_TESTING`.

The largest observed calibration deterioration was again quarterly payment frequency (`Q`): +0.0146934. The largest deviance deterioration was again `policy_type=TPG`: +0.1313%.

## Seen vs unseen policyholders

The fixed candidate did not rely on a favourable result only among previously observed customers. Both seen and unseen 2024 cohorts improved calibration for both frequency outputs:

| Output | Cohort | Rows | Exposure share | Calibration-error change | Relative deviance change |
|---|---|---:|---:|---:|---:|
| GLM | seen | 105,307 | 76.06% | -0.01655 | -0.0487% |
| GLM | unseen | 62,778 | 23.94% | -0.02389 | -0.0145% |
| XGBoost | seen | 105,307 | 76.06% | -0.02150 | -0.0760% |
| XGBoost | unseen | 62,778 | 23.94% | -0.03082 | -0.0297% |

Negative values mean improvement versus the globally calibrated baseline.

## Interpretation

v0.33 strengthens the v0.32 frequency result because the improvement is not accompanied by a material breach across the tested orthogonal major cohorts. It does **not** show that every subgroup improves: some policy-type and payment-frequency cohorts have small trade-offs, which are retained in the evidence rather than hidden.

The result also does not create a new independent calendar period. The same 2024 OOT year is being interrogated more deeply, so this is a transport/slice-stability check, not another temporal validation sample.

## Governance decision

Both frequency candidates remain suitable only for **further shadow testing**. v0.33 does not authorise:

- a serving-bundle change;
- a customer pricing change;
- model-family promotion;
- replacement of the global calibration layer in production.

Project status remains:

- model-family decision: `HOLD`;
- serving status: `HOLD_SHADOW_ONLY`.

The results come from one public Spanish motor-insurance dataset and do not establish transfer to FIRST CENTRAL or the UK motor market.
