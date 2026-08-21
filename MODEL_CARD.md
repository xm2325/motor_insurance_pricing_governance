# Model Card - Motor Pricing Decision Workbench

## Intended use

Portfolio demonstration of insurance data-science reasoning across claim frequency, severity, expected loss, calibration, temporal validation, model-change governance, shadow deployment and operational monitoring.

## Not intended for

- setting real customer premiums;
- underwriting decisions;
- regulatory or actuarial sign-off;
- inference about FIRST CENTRAL production models, SLAs or thresholds;
- claiming transfer from a Spanish or French public portfolio to the UK market.

## Data

Two public motor-insurance sources have different roles.

1. `freMTPL2` is the detailed cross-sectional governance benchmark used for model architecture, calibration, disagreement analysis and stress tests.
2. Mendeley dataset `sw4jmdb2sm`, version 1, supplies the main temporal evidence: **354,140 Spanish motor policy-year observations and 47 variables covering 2022, 2023 and 2024**.

The Mendeley source is downloaded in GitHub Actions rather than committed. The verified main CSV is 94,710,312 bytes with SHA-256 `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4`.

## Target definitions

- Frequency: `total_claims / total_exposure`.
- Expected loss / pure premium: `total_incurred / total_exposure`.
- Exposure is used as a modelling weight / denominator rather than a predictive feature.

## Feature policy

The temporal models use 14 selected driver, vehicle and policy characteristics.

Numeric:

- driver age;
- vehicle age;
- age at driving licence;
- vehicle value;
- seats;
- power-to-weight ratio.

Categorical:

- policy type;
- business type;
- payment frequency;
- bonus score;
- fuel type;
- vehicle brand;
- municipality type;
- circulation area.

The following are intentionally excluded from predictive features and are rejected by the v0.21/v0.22 online schema:

- `insured_id` and `year`;
- `policy_status`, because its timing within the calendar observation period can be post-period;
- current premium fields;
- current claim-count fields;
- current incurred-loss fields;
- exposure itself as a feature.

## Locked temporal design

The deployment-style OOT design is:

- **2022:** training;
- **2023:** aggregate scaling / calibration only;
- **2024:** untouched final OOT evaluation.

No 2024 outcome is used to fit the model or calibration scale.

## Model families

- Poisson GLM frequency reference;
- XGBoost Poisson frequency challenger;
- Tweedie GLM pure-premium reference;
- XGBoost Tweedie pure-premium challenger.

## Verified locked 2024 OOT results

### Frequency

- Poisson GLM locked deviance: **1.11854**
- XGBoost locked deviance: **1.11884**
- Poisson GLM locked calibration ratio: **0.963**
- XGBoost locked calibration ratio: **0.960**
- top-10% exposure claim capture: **26.62% GLM vs 27.04% XGBoost**

The XGBoost ranking gain is small and does not improve locked OOT deviance. The 250-resample GLM-minus-XGBoost Poisson-deviance difference has a 95% interval of **[-0.00155, 0.00083]**.

### Pure premium

- Tweedie GLM locked deviance: **93.9318**
- XGBoost Tweedie locked deviance: **93.9513**
- Tweedie GLM locked calibration ratio: **0.953**
- XGBoost locked calibration ratio: **0.934**
- top-10% exposure loss capture: **20.44% GLM vs 21.13% XGBoost**

The 250-resample GLM-minus-XGBoost Tweedie-deviance difference has a 95% interval of **[-0.988, 0.856]**.

## Rolling-origin stability

The rolling-origin audit is a **model-family stability check**, not a replacement for the locked OOT gate.

### 2022 train -> 2023 test

- frequency deviance: **1.13619 GLM vs 1.13646 XGBoost**;
- frequency bootstrap interval: **[-0.00189, 0.00095]**;
- pure-premium deviance: **92.6970 GLM vs 93.2707 XGBoost**;
- pure-premium bootstrap interval: **[-2.149, 0.880]**.

No stable XGBoost advantage is present.

### 2022+2023 train -> 2024 test

- frequency deviance: **1.11199 GLM vs 1.10843 XGBoost**;
- frequency top-10% claim capture: **26.98% vs 27.42%**;
- frequency bootstrap interval: **[0.00236, 0.00513]**, supporting a small XGBoost frequency gain;
- pure-premium deviance: **92.8213 GLM vs 93.1606 XGBoost**;
- pure-premium calibration: **0.948 GLM vs 0.842 XGBoost**;
- pure-premium bootstrap interval: **[-0.793, 0.160]**.

The frequency advantage appears after adding 2023 to the training window, but the expected-loss challenger still does not show stable superiority.

## Transport and tail checks

The 2024 evaluation includes both returning and new policy IDs:

- 105,307 test IDs were seen in 2022 or 2023;
- 62,778 were unseen before 2024.

Pure-premium calibration differs by transport cohort:

- returning IDs: GLM **0.994**, XGBoost **0.950**;
- new IDs: GLM **0.825**, XGBoost **0.881**.

v0.18 adds bootstrap intervals around these cohort estimates. v0.17 separately shows that the highest-loss 1% of positive-loss 2024 policy rows contribute **20.52%** of incurred, so severity-tail behaviour is treated as a model-risk issue rather than hidden by one cap.

## Value for complexity

On the measured GitHub runner, XGBoost Tweedie is approximately **111x larger** on disk and about **3.65x slower** for 2024 inference than the Tweedie GLM while not improving locked OOT Tweedie deviance. These are environment-specific diagnostics, not universal model benchmarks.

## Current model-family decision

**KEEP HOLD / NO MODEL-FAMILY PROMOTION.**

The promotion gate requires stable expected-loss evidence, calibration, temporal repeatability, transport and acceptable value for additional complexity. The current evidence does not satisfy that standard.

## v0.21 shadow deployment boundary

Technical deployability is separated from approval. v0.21 packages the four locked reference/challenger models into a versioned FastAPI/Docker shadow-scoring service.

Serving status is:

**`HOLD_SHADOW_ONLY`**

The API exposes `/health`, `/model-info`, `/score` and `/batch-score`; it deliberately exposes no `/quote` or `/price` route. The model bundle records the feature-contract hash, locked calibration scales and SHA-256 digests for every serialised model artifact.

Verified deployment controls include:

- exact 25-record offline-online prediction parity (max absolute error **0.0**);
- deterministic 1,000-policy batch scoring;
- rejection of forbidden current-outcome fields;
- unseen-category warnings;
- Docker build and live HTTP scoring parity.

These controls establish a deployable shadow demonstration, not approval for customer pricing.

## v0.22 monitoring boundary

v0.22 adds aggregate operational monitoring to the shadow service. Monitoring stores no raw request payloads, customer identifiers or policy rows.

It tracks:

- request/error rates;
- latency and batch size;
- unseen-category rate;
- reference/challenger disagreement distributions;
- feature-distribution PSI against an aggregate 2022 training baseline.

The training baseline stores numeric quantile bins and categorical proportions only. Feature-drift alerts require at least **500 records**.

A seeded 5,000-record 2022 control replay is GREEN with max PSI **0.00973**. A seeded real 5,000-record 2024 replay triggers feature drift with max PSI **1.4116** on `business_type`, while reference/challenger disagreement p95 remains near the 2022 control (**0.94x** frequency, **1.04x** pure premium).

Full-year business-type mix shifts from **97.91% new business / 2.09% existing-renewal** in 2022 to **57.35% / 42.65%** in 2024. This identifies a portfolio-composition change; it does not by itself establish predictive deterioration.

An explicitly synthetic stress replay verifies error-rate, unseen-category, feature-drift and relative disagreement alerts. These are monitoring-behaviour tests, not observed production incidents.

Monitoring thresholds, including PSI 0.25 and the 500-record minimum, are project demonstration rules rather than insurer/regulatory limits.

## Key risks and limits

- claim severity remains heavy-tailed;
- aggregate calibration can hide transport-segment error;
- feature drift can occur without an immediate model-disagreement shift and requires later outcome monitoring;
- the public Spanish portfolio represents one insurer and does not establish UK-market transport;
- policy-year data do not provide the full operational data lineage of a production insurer;
- bonus score is treated as an available rating characteristic, but its exact production as-of construction is source-specific;
- model-selection and monitoring thresholds in this repository are demonstration rules, not insurer policy;
- synthetic proposition and monitoring-stress simulations are not observed business outcomes/incidents.

## Engineering controls

The repository tests and GitHub Actions workflows protect:

- forbidden current premium/outcome/post-period fields;
- the locked 2022/2023/2024 temporal roles;
- evidence-registry headline values;
- model-bundle hashes and offline-online parity;
- batch determinism and unknown-category handling;
- aggregate-only monitoring telemetry;
- feature PSI alert behaviour and minimum sample gating;
- Docker/network serving and monitoring endpoints.

## Required work before any production-like claim

UK/company-specific data validation, rating-factor lineage, fairness/proxy review, actuarial review, pricing governance, external telemetry storage/aggregation design, outcome-linked monitoring, expense/reinsurance treatment, security review, regulatory review, business-owner approval and prospective validation on the target portfolio.
