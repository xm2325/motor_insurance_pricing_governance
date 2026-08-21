# Model Card — Motor Pricing Decision Workbench

## Intended use

Portfolio demonstration of insurance data-science reasoning: claim frequency, severity, expected loss, calibration, segment checks, temporal validation, incremental-data testing and model-promotion decisions.

## Not intended for

- setting real customer premiums;
- underwriting decisions;
- regulatory or actuarial sign-off;
- inference about FIRST CENTRAL production models or thresholds;
- claiming transfer from a Spanish or French public portfolio to the UK market.

## Data

Two public motor-insurance sources have different roles.

1. `freMTPL2` is the detailed cross-sectional governance benchmark used for model architecture, calibration, monitoring, disagreement analysis and stress tests.
2. Mendeley dataset `sw4jmdb2sm`, version 1, supplies the main temporal evidence: 354,140 Spanish motor policy-year observations and 47 variables covering 2022, 2023 and 2024.

The Mendeley source is downloaded in GitHub Actions rather than committed. The verified main CSV is 94,710,312 bytes with SHA-256 `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4`.

## Target definitions

- Frequency: `total_claims / total_exposure`.
- Expected loss / pure premium: `total_incurred / total_exposure`.
- Exposure is used as a modelling weight / denominator rather than a predictive feature.

## 2022–2024 OOT feature policy

The OOT model uses only selected driver, vehicle and policy characteristics:

- numeric: driver age, vehicle age, age at driving licence, vehicle value, seats, power-to-weight ratio;
- categorical: policy type, business type, payment frequency, bonus score, fuel type, vehicle brand, municipality type, circulation area.

The following are intentionally excluded from predictive features:

- `insured_id` and `year`;
- `policy_status`, because its timing within the calendar observation period can be post-period;
- current premium fields;
- current claim-count fields;
- current incurred-loss fields;
- exposure itself as a feature.

## Temporal design

The locked OOT design is:

- **2022:** training;
- **2023:** aggregate scaling / calibration only;
- **2024:** untouched final OOT evaluation.

No 2024 outcome is used to fit the model or calibration scale.

## OOT model families

- Poisson GLM frequency reference;
- XGBoost Poisson frequency challenger;
- Tweedie GLM pure-premium reference;
- XGBoost Tweedie pure-premium challenger.

## Verified 2024 OOT results

### Frequency

- Poisson GLM locked deviance: **1.11854**
- XGBoost locked deviance: **1.11884**
- Poisson GLM locked calibration ratio: **0.963**
- XGBoost locked calibration ratio: **0.960**
- top-10% exposure claim capture: **26.62% GLM vs 27.04% XGBoost**

The XGBoost ranking gain is small and does not improve OOT deviance. The 250-resample GLM-minus-XGBoost Poisson-deviance difference has a 95% interval of **[-0.00155, 0.00083]**.

### Pure premium

- Tweedie GLM locked deviance: **93.9318**
- XGBoost Tweedie locked deviance: **93.9513**
- Tweedie GLM locked calibration ratio: **0.953**
- XGBoost locked calibration ratio: **0.934**
- top-10% exposure loss capture: **20.44% GLM vs 21.13% XGBoost**

The 250-resample GLM-minus-XGBoost Tweedie-deviance difference has a 95% interval of **[-0.988, 0.856]**.

## Transport checks

The 2024 evaluation includes both returning and new policy IDs:

- 105,307 test IDs were seen in 2022 or 2023;
- 62,778 were unseen before 2024.

Pure-premium calibration differs by transport cohort:

- seen IDs: GLM **0.994**, XGBoost **0.950**;
- unseen IDs: GLM **0.825**, XGBoost **0.881**.

This means the aggregate result is not sufficient for a segment-level model-family decision.

## Current decision

**HOLD.**

The automatic rule requires both:

1. 2024 locked aggregate calibration ratio in `[0.90, 1.10]`; and
2. a strictly positive 95% bootstrap interval for GLM-minus-XGBoost deviance.

Both XGBoost challengers satisfy the broad aggregate-calibration condition but fail the evidence condition. The model family is therefore not promoted merely because top-risk capture is slightly higher.

## Key risks and limits

- claim severity remains heavy-tailed;
- aggregate calibration can hide transport-segment error;
- the public Spanish portfolio represents one insurer and does not establish UK-market transport;
- policy-year data do not provide the full operational data lineage of a production insurer;
- bonus score is treated as an available rating characteristic, but its exact production as-of construction is source-specific;
- model-selection thresholds in this repository are demonstration rules, not insurer policy;
- synthetic proposition simulations are not observed business outcomes.

## Required work before any production-like claim

UK/company-specific data validation, rating-factor lineage, fairness/proxy review, actuarial review, pricing governance, operational monitoring, expense/reinsurance treatment, regulatory review, business-owner approval and prospective validation on the target portfolio.
