# v0.22 — Shadow Monitoring Telemetry

v0.22 extends the v0.21 shadow-scoring service with aggregate monitoring and alerting. It does **not** change the v0.20 model-family decision: the service remains `HOLD_SHADOW_ONLY` and exposes risk scores for shadow comparison rather than customer prices.

## Monitoring boundary

The `/monitoring` endpoint records only aggregate, non-PII telemetry:

- request and error counts;
- latency and batch-size summaries;
- unseen-category rate;
- reference/challenger disagreement distributions;
- aggregate feature-bin/category counts converted to PSI.

It does not retain request payloads, policy rows, customer identifiers or raw feature values.

The monitoring thresholds are project demonstration rules, not insurer SLAs, regulatory limits or FIRST CENTRAL thresholds.

## Feature-drift baseline

The model manifest now contains an aggregate 2022 training-feature baseline:

- numeric features: quantile cut-points and expected bin proportions;
- categorical features: expected category proportions plus missing/unseen buckets;
- no row-level training data are stored in the baseline.

Feature-drift alerts require at least **500 scored records**. This prevents tiny smoke-test samples from producing misleading PSI alerts.

## Replay design

The GitHub Actions replay separates three cases, each using 5,000 policy records where applicable:

1. **2022 control replay** — a seeded sample from the model-training year;
2. **2024 temporal replay** — a seeded sample from the real later-year portfolio;
3. **synthetic stress replay** — deliberately perturbed features, an unseen vehicle brand and schema-invalid requests.

Model cold start is exercised separately and is excluded from the steady-state latency baseline.

## 2022 control replay

The 2022 control is GREEN.

- maximum feature PSI: **0.00973** (`vehicle_brand`);
- unseen-category rate: **0%**;
- frequency reference/challenger absolute log-ratio p95: **0.2901**;
- pure-premium absolute log-ratio p95: **0.7919**;
- no error, latency, disagreement or feature-drift alert fires.

The measured TestClient latency is a GitHub-runner diagnostic, not a production SLA.

## Real 2024 temporal replay

The 2024 replay triggers a **feature-drift alert** but does not trigger error, unseen-category, latency or model-disagreement alerts.

- maximum feature PSI: **1.4116**;
- feature with maximum PSI: **`business_type`**;
- driver-age PSI: **0.0534**;
- vehicle-age PSI: **0.0408**;
- unseen-category rate: **0%**.

The full-year business-type mix provides context for the drift signal:

| Year | New business (`NB`) | Existing/renewal (`P`) |
|---|---:|---:|
| 2022 | **97.91%** | 2.09% |
| 2024 | **57.35%** | **42.65%** |

At the same time, the reference/challenger disagreement distribution remains comparatively stable:

- frequency disagreement p95: **0.2901 → 0.2715** (**0.94×** baseline);
- pure-premium disagreement p95: **0.7919 → 0.8257** (**1.04×** baseline).

This is a useful monitoring distinction: **portfolio mix can move materially even when reference/challenger disagreement does not**. Feature drift and model disagreement therefore remain separate alert channels.

This finding is consistent with the earlier transport analysis, which showed different calibration behaviour for new and returning policies. It does not by itself establish model deterioration; it identifies a population change that requires performance monitoring once outcomes mature.

## Synthetic stress replay

The synthetic stress is explicitly a test of alert behaviour, not an observed incident.

It intentionally:

- changes several numeric rating features;
- introduces `V22_UNSEEN_BRAND`;
- sends 20 requests containing the forbidden current-outcome field `total_claims`.

The stress produces:

- error rate: **80%** across the combined error/scoring request set;
- unseen-category rate: **100%** of scored stress records;
- maximum feature PSI: **24.58** (`vehicle_brand`);
- frequency disagreement p95: **2.54×** the 2022 control;
- pure-premium disagreement p95: **2.87×** the 2022 control.

Error-rate, unseen-category and feature-drift alerts fire. The absolute pure-premium disagreement alert fires, and both relative disagreement-shift checks fire.

## Container monitoring check

The v0.22 Docker image is started in GitHub Actions and queried over HTTP. Five valid `/score` requests are followed by `/monitoring`.

Verified result:

- HTTP monitoring endpoint: **pass**;
- privacy boundary: `aggregate_non_pii_only`;
- request count: **5**;
- records scored: **5**;
- alert status: **GREEN**.

The last result verifies the minimum-sample gate: a five-record container smoke test does not generate a feature-drift alert from unstable small-sample PSI.

## Governance interpretation

v0.22 closes another gap between offline modelling and operational model governance:

> **A technically deployable shadow model still needs population, service, data-quality and reference/challenger monitoring before any model-change decision can be reconsidered.**

The current model-family decision remains:

> **HOLD / NO MODEL-FAMILY PROMOTION**

and the serving status remains:

> **HOLD_SHADOW_ONLY**

No quote or price endpoint is added.

## Reproducibility

`.github/workflows/v22-monitoring.yml` rebuilds the public-data model bundle, runs monitoring/governance contracts, executes the 2022/2024/stress replays, builds the Docker image and verifies the `/monitoring` endpoint over the container network.

Persisted evidence is stored under `action_results/v22/`; the complete run is also uploaded as a GitHub Actions artifact.
