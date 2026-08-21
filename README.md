# Motor Insurance Pricing & Model Governance Workbench

A reproducible insurance data-science case study asking one practical question:

> **Does a more flexible ML challenger improve the pricing target reliably enough, across time and customer cohorts, to justify replacing a GLM — and can the models be deployed and monitored safely in shadow mode without confusing deployability with approval?**

## 30-second result

| Evidence | Result |
|---|---|
| Cross-sectional frequency benchmark | XGBoost reduced Poisson deviance by **5.43%** and increased top-10% claim capture from **20.59% to 31.17%** |
| Real longitudinal source | **354,140 Spanish motor policy-years**, 47 variables, 2022–2024 |
| Locked temporal design | **2022 train → 2023 calibration → 2024 untouched OOT** |
| 2024 frequency result | XGBoost top-10% claim capture **26.62% → 27.04%**, but deviance **1.11884 vs GLM 1.11854** |
| 2024 uncertainty | 250-bootstrap GLM-minus-XGB deviance CI **[-0.00155, 0.00083]** |
| Rolling-origin result | With 2022+2023 training, XGBoost frequency deviance improved by only **~0.32%** |
| Pure-premium result | No stable XGBoost advantage; rolling-origin Tweedie deviance **93.1606 vs GLM 92.8213** |
| v0.20 model-change pack | Tail, transport uncertainty and value-for-complexity checks all retain **HOLD** |
| v0.21 shadow deployment | FastAPI + Docker; **25-record parity error 0.0**, deterministic 1,000-policy batch, container HTTP parity **pass** |
| v0.22 shadow monitoring | Real 2024 replay: feature PSI **1.4116** (`business_type`) while model-disagreement p95 stayed near baseline; Docker `/monitoring` **pass** |
| Model-family decision | **HOLD / NO PROMOTION**; serving status is **HOLD_SHADOW_ONLY** |

The project deliberately separates four ideas that are often conflated:

1. **predictive/ranking uplift**;
2. **evidence for a model-family change**;
3. **technical deployability**;
4. **operational monitoring after deployment to shadow mode**.

A challenger can be deployable and observable in shadow mode while still failing the statistical / pricing evidence required for promotion.

**Start here:** [Interview Evidence Pack](INTERVIEW_EVIDENCE_PACK.md) | [Evidence Registry](EVIDENCE_REGISTRY.md) | [Model Card](MODEL_CARD.md) | [v0.20 approval results](RESULTS_V20.md) | [v0.21 deployment evidence](DEPLOYMENT_V21.md) | [v0.22 monitoring evidence](RESULTS_V22.md)

---

## Evidence track 1 — freMTPL2 governance benchmark

The public French `freMTPL2` portfolio is used for the detailed model-governance workbench:

- Poisson GLM vs XGBoost claim-frequency modelling;
- Gamma severity and Tweedie / two-part expected-loss modelling;
- locked train / calibration / final-test separation;
- calibration, lift, segment stability and paired bootstrap uncertainty;
- external/geographic data-value gates;
- shadow monitoring, PSI, unseen-category and severity-inflation stress tests;
- model-change disagreement, exact attribution and high-disagreement cohort investigation;
- explicitly synthetic Pricing & Proposition simulations kept separate from observed outcomes.

On the full frequency benchmark, XGBoost reduced weighted Poisson deviance by **5.43%** relative to the comparable Poisson GLM and increased claims captured in the highest-risk 10% of exposure by **10.58 percentage points**.

That justified building a challenger. It did not justify deployment.

## Evidence track 2 — real 2022–2024 calendar OOT

The main temporal track uses public Mendeley dataset `sw4jmdb2sm` (version 1): **354,140 policy-year rows and 47 variables** from one Spanish motor insurer.

GitHub Actions downloads the 94.7 MB source, records SHA-256, verifies schema/year coverage and runs the locked design:

- **2022:** model training;
- **2023:** aggregate calibration only;
- **2024:** untouched OOT evaluation.

The predictive feature set intentionally excludes customer ID, year, policy status, current premiums, current claim counts, current incurred losses and exposure as a predictor.

### Locked 2024 results

| Target | GLM reference | XGBoost challenger | Interpretation |
|---|---:|---:|---|
| Frequency Poisson deviance | **1.11854** | 1.11884 | no deviance gain |
| Frequency calibration ratio | 0.963 | 0.960 | both close in aggregate |
| Top-10% claim capture | 26.62% | **27.04%** | +0.42 pp ranking gain |
| Pure-premium Tweedie deviance | **93.9318** | 93.9513 | no deviance gain |
| Pure-premium calibration ratio | **0.953** | 0.934 | GLM closer in aggregate |
| Top-10% loss capture | 20.44% | **21.13%** | +0.69 pp ranking gain |

The 250-resample bootstrap intervals cross zero for both frequency and pure-premium deviance differences. Automatic decision: **HOLD**.

## Evidence track 3 — rolling-origin and transport

Rolling-origin evaluation is a stability diagnostic, not a replacement for the locked 2024 test.

- **2022 → 2023:** no stable XGBoost frequency or pure-premium advantage.
- **2022+2023 → 2024:** XGBoost frequency deviance improves by only **~0.32%** with a positive bootstrap interval; pure premium still does not improve.

The 2024 portfolio also transports differently by customer cohort:

- returning-policy pure-premium calibration: GLM **0.994**, XGBoost **0.950**;
- new-policy calibration: GLM **0.825**, XGBoost **0.881**.

v0.18 adds bootstrap intervals around these cohort calibration estimates rather than treating point estimates as certain.

## Evidence track 4 — v0.20 final model-change pack

v0.16–v0.20 close the offline governance case without adding another model family:

- **coverage decomposition:** 2024 total incurred reconciles to coverage components;
- **severity tail:** the highest-loss 1% of positive-loss policies contribute **20.52%** of incurred;
- **transport uncertainty:** model calibration advantage changes across new/returning/business-type cohorts;
- **value for complexity:** XGBoost Tweedie is about **111× larger** on disk and about **3.65× slower** for inference in the measured GitHub runner while not improving locked OOT Tweedie deviance;
- **approval pack:** frequency, pure-premium, temporal consistency, transport and value-for-complexity gates do not support a global model-family change.

Decision remains:

> **HOLD / NO MODEL-FAMILY PROMOTION.**

## Evidence track 5 — v0.21 shadow deployment bridge

v0.21 demonstrates deployability **without overriding the HOLD decision**.

The FastAPI service exposes:

- `GET /health`;
- `GET /model-info`;
- `POST /score`;
- `POST /batch-score` (maximum 1,000 policies).

It deliberately exposes **no `/quote` or `/price` endpoint**. Each request returns GLM reference and XGBoost challenger frequency / pure-premium risk scores side by side for shadow comparison.

Verified deployment evidence includes:

- feature/leakage/deployment contracts: pass;
- public data download and schema audit: pass;
- four-model bundle rebuild: pass;
- **25-record direct-vs-API max absolute error: 0.0**;
- current-outcome field rejected: pass;
- unseen-category warning: pass;
- deterministic **1,000-policy** batch: pass;
- Docker image build: pass;
- live container `/health` and HTTP `/score` parity: pass.

The model manifest records training/calibration/evaluation years, feature-contract SHA-256 and SHA-256 hashes for every binary model artifact. The binary bundle is kept as an Actions artifact rather than committed.

See [DEPLOYMENT_V21.md](DEPLOYMENT_V21.md) for the serving contract.

## Evidence track 6 — v0.22 shadow monitoring telemetry

v0.22 adds operational observability without storing raw policy requests. `/monitoring` exposes aggregate, non-PII request/error/latency/batch statistics, unseen-category rate, reference/challenger disagreement and feature-distribution PSI.

The monitoring baseline is stored as aggregate 2022 training histograms/category proportions in the model manifest. A feature-drift alert requires at least **500 scored records** so tiny smoke tests do not produce unstable PSI alerts.

The replay distinguishes three cases:

- **2022 control, 5,000 records:** GREEN; max PSI **0.00973**;
- **real 2024 temporal replay, 5,000 records:** max PSI **1.4116**, driven by `business_type`; full-year mix changes from **97.91% NB / 2.09% P** in 2022 to **57.35% NB / 42.65% P** in 2024;
- **synthetic stress, 5,000 scored records plus schema-invalid requests:** error, unseen-category and feature-drift alerts fire; reference/challenger disagreement p95 rises by **2.54×** for frequency and **2.87×** for pure premium.

The real 2024 population drift does **not** coincide with a large change in reference/challenger disagreement: frequency disagreement p95 is **0.94×** the 2022 control and pure-premium disagreement p95 is **1.04×**. That separation is intentional: input drift and model disagreement are monitored as different risks.

The Docker workflow also verifies `/monitoring` over HTTP. Five valid smoke-test requests remain **GREEN**, confirming the minimum-sample guard.

See [RESULTS_V22.md](RESULTS_V22.md) for exact monitoring scope, caveats and replay evidence.

## Auditable claims and CI

`EVIDENCE_REGISTRY.md` maps headline CV/README/interview claims to persisted result files. Automated tests verify modelling results, temporal/leakage contracts, v0.21 deployment evidence and v0.22 monitoring evidence.

## Repository map

```text
README.md                         recruiter / reviewer entry point
INTERVIEW_EVIDENCE_PACK.md        short explanation and likely interview questions
EVIDENCE_REGISTRY.md              headline claims -> persisted evidence
MODEL_CARD.md                     intended use, limits and decision rules
RESULTS_V20.md                    final offline model-change approval results
DEPLOYMENT_V21.md                 shadow serving contract and verified deployment gates
RESULTS_V22.md                    shadow monitoring, temporal drift and stress evidence
deployment/                       FastAPI contracts, bundle loader, drift and telemetry code
build_deployment_bundle_v21.py    reproducible locked model bundle + monitoring baseline
replay_monitoring_v22.py          2022 control / real 2024 / synthetic stress replay
Dockerfile                        containerised shadow service
action_results/v21/               persisted non-binary deployment evidence
action_results/v22/               persisted non-binary monitoring evidence
.github/workflows/                data, governance, deployment and monitoring workflows
tests/                            leakage, evidence, governance, deployment and monitoring contracts
```

## Scope

This is a portfolio model-governance, shadow-deployment and monitoring project, not a production pricing engine. It does not set real customer premiums and does not establish transfer to FIRST CENTRAL or the UK motor market. Pure-premium estimates do not include company-specific expenses, reinsurance, commercial adjustments or regulatory approval. Monitoring thresholds are demonstration rules rather than insurer/regulatory limits, and synthetic stress replays are labelled separately from observed temporal data.