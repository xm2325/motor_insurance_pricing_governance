# Motor Insurance Pricing & Model Governance Workbench

A reproducible insurance data-science case study asking one practical question:

> **Does a more flexible ML challenger improve the pricing target reliably enough, across time and customer cohorts, to justify replacing a GLM — and can the models be deployed, monitored and reviewed safely in shadow mode without confusing deployability with approval?**

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
| v0.23 review lifecycle | **2 breach windows open review / 2 green windows close it**; real 2024 drift opens a portfolio-mix review, with no automatic model/pricing change |
| v0.25 runtime slimming | CPU-only serving image **960.27 MB → 488.78 MB (-49.10%)**; full-vs-runtime and runtime-vs-offline locked parity max error **0.0** |
| v0.26 model IO portability | XGBoost challengers use native UBJSON plus sklearn preprocessor; **100 same-fit comparisons, max error 0.0**, including training XGBoost 3.4.1 → runtime 3.4.0 |
| v0.27 bundle integrity | **9 locked artifacts / 1,604,579 bytes**; content-addressed verification and corruption/missing-artifact tests pass before model deserialisation |
| v0.28 release/rollback control | A/B shadow releases registered; unauthorised rollback rejected; operator-authorised rollback returns to last-known-good with **100/100 parity comparisons at error 0.0** |
| v0.29–v0.30 build provenance/admission | GitHub/Sigstore attestation verifies the sealed archive; admission is restricted to **`ADMIT_TO_SHADOW_REGISTRY_ONLY`** and rejects tampered/wrong-identity cases |
| v0.31 delayed-outcome review | **60.0001% mature exposure** is below the **95%** gate so metrics are withheld; at full maturity, all **8 OOT regression checks match exactly** and segment review still retains HOLD |
| Model-family decision | **HOLD / NO PROMOTION**; serving status is **HOLD_SHADOW_ONLY** |

The project separates model evidence from operational controls. A challenger can rank risk differently, be technically deployable, pass bundle integrity and provenance checks, and still fail the evidence required for customer-pricing promotion. Likewise, monitoring drift can open a review without proving predictive deterioration, and later claims outcomes can be held back until enough exposure has mature labels.

The current evidence chain covers:

1. predictive/ranking uplift;
2. model-family change evidence;
3. locked temporal and rolling-origin validation;
4. transport and segment calibration;
5. shadow deployment and monitoring;
6. review lifecycle and recovery;
7. runtime/model-IO compatibility;
8. content-addressed release integrity and rollback;
9. build provenance and shadow-only admission;
10. delayed-outcome maturity and realised claims/loss review.

**Start here:** [Interview Evidence Pack](INTERVIEW_EVIDENCE_PACK.md) | [Evidence Registry](EVIDENCE_REGISTRY.md) | [Model Card](MODEL_CARD.md) | [v0.20 approval results](RESULTS_V20.md) | [v0.21 deployment](DEPLOYMENT_V21.md) | [v0.22 monitoring](RESULTS_V22.md) | [v0.23 review lifecycle](RESULTS_V23.md) | [v0.25 runtime](RESULTS_V25.md) | [v0.26 model IO](RESULTS_V26.md) | [v0.27 integrity](RESULTS_V27.md) | [v0.28 release control](RESULTS_V28.md) | [v0.29 attestation](RESULTS_V29.md) | [v0.30 admission](RESULTS_V30.md) | [v0.31 outcome review](RESULTS_V31.md)

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

## Evidence track 7 — v0.23 monitoring-to-review lifecycle

v0.23 consumes only persisted aggregate v0.22 evidence and adds hysteresis around monitoring alerts. Two consecutive breach windows are required to open a review, and two consecutive green windows are required to close it.

The verified replay is:

```text
HEALTHY → WATCH → REVIEW_REQUIRED → RECOVERING → HEALTHY → WATCH → REVIEW_REQUIRED
```

For the real 2024 temporal replay, the persistent alert is **feature drift only**. The review is classified **MEDIUM** and recommends `REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION`. After two green windows the review closes and returns to `HEALTHY`.

The final synthetic stress creates a separate **HIGH** review with `INVESTIGATE_SERVING_DATA_AND_MODEL`. It is a controller-validation scenario, not a production incident.

Every window is reduced to aggregate evidence with a SHA-256 digest. The controller is deterministic and recommendation-only: it does **not** automatically change pricing, model approval, rollback state or serving configuration.

See [RESULTS_V23.md](RESULTS_V23.md).

## Evidence track 8 — v0.25 CPU-only runtime

v0.25 separates training/development dependencies from the container used for shadow serving. The historical full image and the new CPU-only image are built in the same Actions benchmark from the same commit and mounted with the same locked v0.21 bundle.

Verified results:

- full baseline image: **960,271,925 bytes**;
- CPU-only runtime image: **488,778,419 bytes**;
- reduction: **471,493,506 bytes / 49.10%**;
- runtime uses `xgboost-cpu 3.4.0` and excludes `httpx`, `matplotlib`, `nvidia-nccl-cu13`, `pytest` and `tabulate`;
- **25 records × 6 numeric fields** match full-vs-runtime with max absolute error **0.0**;
- the same 25 records × 4 core prediction fields match the persisted offline reference with max absolute error **0.0**.

This does not remove the model-governance HOLD. It also does not claim arbitrary cross-version portability: the joblib/pickle bundle emitted an XGBoost version-serialization warning even though the locked parity test was exact. v0.26 addresses that model-IO boundary rather than hiding the warning.

See [RESULTS_V25.md](RESULTS_V25.md).

## Evidence track 9 — v0.26 native XGBoost model IO

v0.26 removes the XGBoost estimator from pickle/joblib persistence. The sklearn preprocessing pipeline remains joblib-serialised, while each XGBoost challenger is stored using native UBJSON model IO.

The same-fit migration is checked over **25 records × 4 prediction fields = 100 comparisons**, with max absolute error **0.0**. The CPU runtime then loads a model trained under XGBoost **3.4.1** using `xgboost-cpu 3.4.0`, again with **100 HTTP comparisons at max error 0.0** and no cross-version pickle warning.

A separate historical retrain diagnostic has maximum relative difference **0.0874%**. That is not used as a serialization acceptance threshold: same-fit parity and fresh-retrain reproducibility are different tests.

See [RESULTS_V26.md](RESULTS_V26.md).

## Evidence track 10 — v0.27 content-addressed bundle integrity

v0.27 seals the shadow bundle before deserialisation. The registered build contains **9 locked artifacts / 1,604,579 bytes**, a canonical lock digest, model/artifact hashes and public-source provenance.

Negative checks reject:

- a byte change in a model artifact;
- a missing GLM artifact;
- a modified lock self-digest.

The verified container status is `CONTENT_ADDRESSED_BUNDLE_VERIFIED` plus `HYBRID_MODEL_IO_COMPATIBLE`, followed by **100 serving comparisons at max error 0.0**.

This is a repository-local content integrity contract, not a signature. v0.29 adds external build provenance.

See [RESULTS_V27.md](RESULTS_V27.md).

## Evidence track 11 — v0.28 shadow release registry and rollback

v0.28 turns sealed bundles into explicit shadow releases. Candidate A and B have distinct release/lock identities while sharing identical hashes for the nine locked model artifacts in the controlled replay.

The controller verifies that:

- opening a synthetic review does **not** automatically switch serving;
- an unauthorised rollback is rejected;
- an explicitly operator-authorised rollback selects last-known-good A;
- the release registry carries a verified **7-event SHA-256 chain**;
- candidate B and rollback A each reproduce **100 predictions at max error 0.0** in the same runtime image;
- switching releases performs no retraining and no customer-pricing change.

`operator_authorised=True` is a project control flag, not an IAM or production authentication system.

See [RESULTS_V28.md](RESULTS_V28.md).

## Evidence track 12 — v0.29/v0.30 provenance and shadow admission

v0.29 packages a sealed release archive and generates GitHub Artifact Attestation / Sigstore provenance. `gh attestation verify` independently verifies the archive against the repository/workflow identity.

v0.30 then converts provenance from descriptive metadata into an admission policy. A release must have the expected repository, workflow, SLSA provenance predicate and GitHub Actions build type, and its inner v0.27 bundle must pass integrity verification. The current persisted result is:

> **`V30_ATTESTED_RELEASE_ADMISSION_PASS` → `ADMIT_TO_SHADOW_REGISTRY_ONLY`**

The admitted archive contains **0 raw source-data members**. Negative cases for archive tampering, wrong repository and wrong workflow identity all fail closed.

Admission remains shadow-only. It does not approve the challenger or customer pricing.

See [RESULTS_V29.md](RESULTS_V29.md) and [RESULTS_V30.md](RESULTS_V30.md).

## Evidence track 13 — v0.31 delayed-outcome maturity review

v0.31 connects the v0.23 portfolio-mix review to realised 2024 claims/loss outcomes. It rebuilds and integrity-verifies the current shadow bundle, scores the **168,085-row** 2024 cohort, and then applies an outcome-maturity gate before computing label-based performance.

At a deterministic synthetic early-arrival checkpoint, **60.0001% of exposure** has outcomes marked mature. Because this is below the project gate of **95%**, the result is `WAIT_FOR_OUTCOME_MATURITY`: frequency and pure-premium performance metrics are deliberately withheld and no model/pricing change is authorised.

At full maturity, the observed 2024 totals are **39,276 claims** and **38,106,351.28 incurred**. The rebuilt bundle reproduces all eight registered 2024 OOT values exactly:

| Target | GLM reference | XGBoost challenger | Result |
|---|---:|---:|---|
| Frequency Poisson deviance | **1.118536** | 1.118835 | GLM lower by 0.000299 |
| Frequency calibration | 0.963088 | 0.960085 | both below 1.0 |
| Pure-premium Tweedie deviance | **93.931806** | 93.951316 | GLM lower by 0.019510 |
| Pure-premium calibration | **0.953069** | 0.933593 | GLM closer in aggregate |

The `business_type` review is deliberately aggregate-only. NB contributes **48.18%** of exposure and P **51.82%**. XGBoost is closer to calibration 1.0 for NB frequency/pure premium, while GLM is closer for P frequency/pure premium. There is therefore no segment evidence for an automatic global challenger replacement.

The 2024 outcome values are real historical values; the partial label-arrival timing is synthetic. This is not a claims-development/IBNR study and not post-deployment production evidence.

Decision remains:

> **HOLD / HOLD_SHADOW_ONLY.**

See [RESULTS_V31.md](RESULTS_V31.md) and `action_results/v31/`.

## Auditable claims and CI

`EVIDENCE_REGISTRY.md` maps headline CV/README/interview claims to persisted result files. Lightweight CI verifies modelling evidence, temporal/leakage contracts, deployment/monitoring/review controls, runtime and model-IO compatibility, bundle/release integrity, attestation/admission evidence, the v0.31 persisted outcome review and the concurrent evidence-write contract. Heavy workflows rebuild public data/models when the corresponding source paths change.

## Repository map

```text
README.md                              recruiter / reviewer entry point
INTERVIEW_EVIDENCE_PACK.md             short explanation and likely interview questions
EVIDENCE_REGISTRY.md                   headline claims -> persisted evidence
MODEL_CARD.md                          intended use, limits and decision rules
RESULTS_V20.md                         final offline model-change approval results
DEPLOYMENT_V21.md                      shadow serving contract and verified deployment gates
RESULTS_V22.md                         shadow monitoring, temporal drift and stress evidence
RESULTS_V23.md                         persistent-alert review and recovery lifecycle
RESULTS_V25.md                         CPU-only runtime size and parity evidence
RESULTS_V26.md                         native XGBoost model IO and environment compatibility
RESULTS_V27.md                         content-addressed bundle integrity
RESULTS_V28.md                         shadow release registry and rollback replay
RESULTS_V29.md                         GitHub/Sigstore artifact attestation
RESULTS_V30.md                         attestation-aware shadow release admission
RESULTS_V31.md                         delayed-outcome maturity and segment calibration review
deployment/                            FastAPI, bundle, monitoring, review and outcome-monitoring code
build_deployment_bundle_v21.py         reproducible model bundle + aggregate monitoring baseline
build_bundle_lock_v27.py               content-addressed bundle lock
verify_bundle_v27.py                   fail-closed bundle integrity verifier
verify_release_admission_v30.py        attested shadow release admission policy
run_outcome_review_v31.py              real-2024 delayed-outcome replay and segment review
scripts/push_evidence_with_rebase.sh   bounded race-safe evidence persistence helper
Dockerfile                             CPU-only containerised shadow service
requirements-runtime.txt               serving-only dependency boundary
action_results/v21/ ... v31/           persisted non-binary workflow evidence
.github/workflows/                     data, governance, deployment, release and evidence workflows
tests/                                 leakage, evidence, model, serving, release and persistence contracts
```
