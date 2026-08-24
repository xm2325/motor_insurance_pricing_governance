# Motor Insurance Pricing & Model Governance Workbench

A reproducible insurance data-science case study asking a deliberately difficult model-risk question:

> **Does a more flexible ML challenger improve the pricing target reliably enough, across time and independent portfolios, to justify replacing a GLM — and can rating structure, portfolio drift, deployment readiness and model impact be reviewed without confusing any of them with approval?**

## 30-second result

| Evidence | Result |
|---|---|
| Cross-sectional development signal | XGBoost reduced Poisson deviance by **5.43%** and increased top-10% exposure claim capture **20.59% → 31.17%** on freMTPL2; this is development evidence, not pricing uplift |
| Spanish calendar OOT | **2022 train → 2023 calibration → 2024 locked first-use OOT**; GLM retained slightly lower 2024 frequency and pure-premium deviance, so the registered model-family decision stayed **HOLD** |
| Validation lifecycle | Spanish 2024 is now **`CONSUMED_RETROSPECTIVE_VALIDATION`**; Australia and Belgium are also consumed external validation assets rather than reusable independent confirmation samples |
| Preregistered external replication | Australia + Belgium contribute **4 preregistered target gates and 0 passes**; mixed/favourable point metrics are retained, but no gate is relaxed after outcomes are seen |
| Model Change Committee gate | Request `MCR-XGB-MOTOR-001` is **`EVIDENCE_GAP_HOLD`**: **5/8** required gates pass; blockers remain locked temporal support, preregistered external support and fresh independent evidence |
| Rating-factor response shape | v0.51 development-only reference-profile audit: `driver_age` and `vehicle_age` show large GLM/XGB frequency shape gaps (**0.26866 / 0.26771**). At driver age 68, GLM/XGB relativities are **1.172 / 0.896** around the same 2022 reference profile |
| Support vs mix | v0.52 reads 2022/2024 rating features + exposure only. Maximum strict numeric extrapolation is only **0.00227% exposure**, while `business_type` mix TV is **48.60%** with **0% unseen business-type exposure** — known cells reweighted rather than becoming unfamiliar |
| Portfolio-neutral impact | On all **168,085** positive-exposure 2024 feature rows, aggregate GLM/XGB technical-risk totals are forced equal first. **36.81%** of exposure moves by >±10% for frequency; pure premium has **78.26% >±10%** and **58.17% >±20%** |
| Rating-factor review pack | v0.53 joins **response shape → strict support → portfolio mix → technical-risk redistribution → evidence adequacy → separate pricing governance**, without a composite risk score or new promotion threshold |
| Operational controls | FastAPI/Docker shadow scoring, monitoring, content-addressed bundles, manual rollback, GitHub/Sigstore provenance and attested **shadow-only** admission are demonstrated — without converting deployability into approval |
| Current decision | **HOLD / HOLD_SHADOW_ONLY**; `promotion_review_status=NOT_OPEN`; no model promotion or customer-pricing change is authorised |

The central result is not that “XGBoost is bad”. A strong development signal did **not** become a stable promotion case across calendar time and independent portfolios. The later rating-factor work adds a more insurance-specific lesson: **model response-shape disagreement, feature support, portfolio mix and technical-risk redistribution are different risks**. `driver_age` has a large model-family shape gap while remaining well inside development support; `business_type` has a much smaller frequency shape gap but a **48.60%** portfolio-mix shift. Those diagnostics improve review quality, but they do not repair missing validation evidence or become customer premiums.

## Evidence story

1. **Build the challenger:** freMTPL2 shows a material XGBoost frequency signal worth investigating.
2. **Challenge it in time:** the original Spanish 2024 locked OOT does not support a global model-family switch.
3. **Do not recycle the holdout:** later use is recorded and Spanish 2024 becomes consumed retrospective validation.
4. **Replicate externally:** Australian and Belgian protocols are merged before row-level access; registered gates are not relaxed after outcomes.
5. **Protect numerical evidence:** external replication separates stable decisions from point-metric reproducibility and adds prospective numerical controls.
6. **Synthesize without score-shopping:** heterogeneous portfolios keep their original evidence classes and decisions; **0/4** external target gates pass.
7. **Separate evidence from operations:** shadow deployment, monitoring, rollback and attested admission can pass while model promotion remains blocked.
8. **Explain frozen-model disagreement without reusing outcomes:** v0.47 reads consumed 2024 rating features/exposure only and identifies descriptive disagreement sensitivities.
9. **Translate disagreement into impact:** v0.48 forces aggregate technical-risk totals equal, then measures portfolio and major-segment relativity redistribution without reading 2024 outcomes or actual premiums.
10. **Put review steps in the right order:** v0.49 requires evidence adequacy first, impact review second and separate commercial/customer-pricing governance last.
11. **Inspect rating structure on development data:** v0.51 compares frozen Poisson-GLM/XGBoost frequency relativities across supported 2022 rating-factor grids; it is interpretability, not validation.
12. **Separate extrapolation from mix drift:** v0.52 shows strict numeric/unseen-category support remains strong while `business_type` exposure shares almost reverse.
13. **Package the insurance review logic:** v0.53 joins rating structure, support, mix and technical-risk impact but refuses a composite score and leaves the 5/8, 0/4 HOLD state controlling.

## Start here

- **Short interview story:** [Interview Evidence Pack](INTERVIEW_EVIDENCE_PACK.md)
- **Rating-factor model review:** [Rating Factor Review Pack](RATING_FACTOR_REVIEW_PACK.md)
- **Decision-ready impact assessment:** [Model Change Impact Assessment](MODEL_CHANGE_IMPACT_ASSESSMENT.md)
- **Trace every headline claim:** [Evidence Registry](EVIDENCE_REGISTRY.md)
- **Current model scope and consumed-validation roles:** [Model Card](MODEL_CARD.md)
- **Rating-factor chain:** [v0.51 response shapes](RESULTS_V51.md) → [v0.52 support/mix](RESULTS_V52.md) → [v0.53 review pack](RESULTS_V53.md)
- **Why the frozen models disagree:** [v0.47 results](RESULTS_V47.md)
- **Portfolio-neutral technical relativity migration:** [v0.48 results](RESULTS_V48.md)
- **Committee-ready synthesis:** [v0.49 results](RESULTS_V49.md)
- **Model-family evidence / committee gate:** [v0.43 results](RESULTS_V43.md) → [v0.44 results](RESULTS_V44.md)
- **External-validation chain:** [v0.36 preregistration](RESULTS_V36.md) → [v0.37 Australia](RESULTS_V37.md) → [v0.38 reproducibility](RESULTS_V38.md) → [v0.39 firewall](RESULTS_V39.md) → [v0.40 Belgian preregistration](RESULTS_V40.md) → [v0.41 Belgium](RESULTS_V41.md) → [v0.42 closeout](RESULTS_V42.md)
- **Deployment/governance chain:** [v0.21 deployment](DEPLOYMENT_V21.md) → [v0.22 monitoring](RESULTS_V22.md) → [v0.28 rollback](RESULTS_V28.md) → [v0.30 admission](RESULTS_V30.md)

## Current evidence boundaries

- The **5.43%** number is a cross-sectional frequency-deviance benchmark result, not observed pricing/profit uplift.
- Spanish 2024 was independent at its **first** locked OOT use; it is no longer fresh evidence for candidate selection. Australia and Belgium are likewise consumed for new independent-confirmation claims.
- Australian and Belgian results replicate a **GLM-vs-XGBoost model-family question** in different portfolio contexts; they are not direct validation of the fitted Spanish models.
- `0/4` refers specifically to the four preregistered Australian/Belgian target gates; it does not mean every XGBoost metric is worse.
- v0.47/v0.48 are **post-hoc diagnostics on consumed validation features**; v0.51 is **development interpretability**; v0.52 is a **label-free feature support/mix audit**; v0.53 is an **aggregate synthesis/navigation pack**. None is fresh performance evidence or a way to clear G2/G3/G4.
- v0.51 response profiles hold other factors at a common 2022 reference profile. They are not population-average PDPs, causal rating effects or pricing recommendations.
- v0.52 distinguishes strict observed-range/unseen-category support from q05–q95 tail exposure and portfolio mix; tail exposure is not automatically extrapolation.
- v0.48/v0.53 technical-relativity percentages are **score redistribution after aggregate neutralisation**, not customer premium, quote or realised commercial impact.
- The frozen Tweedie GLM `max_iter=900` warning remains registered; descriptive v0.48 headlines are reported only at precision supported by the repeat-run envelope.
- `EVIDENCE_GAP_HOLD`, `HOLD_SHADOW_ONLY`, `NOT_OPEN` and `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN` are project governance states, not FIRST CENTRAL or regulatory approval states.
- No result establishes transport to FIRST CENTRAL, the current UK motor market, production safety, customer-pricing impact, profit or conversion uplift.
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

GitHub Actions downloads the 94.7 MB source, records SHA-256, verifies schema/year coverage and runs the original locked design:

- **2022:** model training;
- **2023:** aggregate calibration only;
- **2024:** untouched at the **first** locked OOT evaluation.

The predictive feature set intentionally excludes customer ID, year, policy status, current premiums, current claim counts, current incurred losses and exposure as a predictor.

The first-use independence is a historical fact. Later v0.22/v0.23/v0.31–v0.34 analyses repeatedly reuse 2024 for monitoring, realised-outcome review, recalibration evaluation, cohort transport and uncertainty analysis. v0.35 therefore prevents 2024 from being described as a fresh independent holdout for any future candidate-selection or promotion claim.

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

Rolling-origin evaluation is a stability diagnostic, not a replacement for the first locked 2024 test.

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

## Evidence track 14 — v0.32 2023-only business-type recalibration

v0.32 asks whether the large `business_type` drift can be addressed without leaking 2024 outcomes into factor fitting. Incremental NB/P multipliers are fitted from **2023 only** on top of the existing global calibration, then evaluated on 2024.

Both frequency outputs improve under the registered candidate gate. The GLM frequency candidate changes Poisson deviance by about **-0.0398%** and the XGBoost frequency candidate by about **-0.0640%**. Neither pure-premium candidate passes all calibration/deviance rules, so global pure-premium calibration is retained.

The mix decomposition also shows why PSI alone is insufficient: the within-segment/time component dominates the registered calibration changes rather than portfolio mix explaining the full deterioration.

See [RESULTS_V32.md](RESULTS_V32.md).

## Evidence track 15 — v0.33 orthogonal cohort transport

v0.33 does not refit the v0.32 factors. It applies the fixed 2023-only frequency multipliers across 2024 cohorts defined by `seen_before_2024`, driver age, policy type and payment frequency.

For both frequency outputs, **13 major cohorts** meet the support rules and **0 breach** the pre-specified calibration/deviance guardrails. The analysis still retains small adverse trade-offs: quarterly payment (`Q`) has the largest calibration deterioration and `policy_type=TPG` the largest deviance worsening.

This is a slice/transport stability analysis inside the already-used 2024 year, not a second independent temporal validation period.

See [RESULTS_V33.md](RESULTS_V33.md).

## Evidence track 16 — v0.34 factor-estimation uncertainty

v0.34 performs **500 deterministic, business-type-stratified 2023 row-bootstrap draws** of the incremental frequency factors. The same draw indices are paired across GLM/XGBoost, factor draws are not clipped, and 2024 outcomes are used only after each 2023 factor draw is fixed.

The pre-registered strong gate produces a useful non-all-green result:

- **XGBoost frequency:** 499/500 (**99.8%**) draws improve deviance, 424/500 (**84.8%**) do not worsen aggregate calibration, 500/500 improve worst-segment calibration and 500/500 pass the original v0.32 deviance guardrail → `ROBUST_TO_2023_FACTOR_ESTIMATION_FOR_FURTHER_SHADOW_TESTING`.
- **GLM frequency:** 485/500 (**97.0%**) improve deviance and 497/500 improve worst-segment calibration, but only 398/500 (**79.6%**) do not worsen aggregate calibration → `FACTOR_UNCERTAINTY_REVIEW_REQUIRED` because the registered rule was **80%**.

The 79.6% result is not rounded or threshold-adjusted after inspection.

See [RESULTS_V34.md](RESULTS_V34.md).

## Evidence track 17 — v0.35 validation-use firewall

v0.35 stops repeated 2024 analysis from silently turning into pseudo-independent confirmation. A machine-readable ledger preserves the historical fact that 2024 was independent at first locked OOT use, while setting its current role to `CONSUMED_RETROSPECTIVE_VALIDATION`.

The fail-closed validator permits 2024 for regression reproduction, monitoring replay, post-hoc diagnostics and governance testing. It rejects new model/calibration fitting, new candidate selection, independent-confirmation claims, model-family promotion and customer-pricing authorisation. Unknown 2024 purposes also fail closed.

A future promotion claim therefore requires a genuinely new independent calendar period or external validation dataset with analysis rules fixed before outcomes are inspected.

See [RESULTS_V35.md](RESULTS_V35.md) and `governance/validation_use_ledger_v35.json`.

## Auditable claims and CI

`EVIDENCE_REGISTRY.md` maps headline CV/README/interview claims to persisted result files. Lightweight CI verifies modelling evidence, temporal/leakage contracts, deployment/monitoring/review controls, runtime and model-IO compatibility, bundle/release integrity, attestation/admission evidence, delayed-outcome review, v0.32 recalibration, v0.33 cohort transport, v0.34 factor uncertainty, concurrent evidence writes and the v0.35 validation-use firewall. Heavy workflows rebuild public data/models only when the corresponding source paths change.

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
RESULTS_V32.md                         2023-only business-type recalibration review
RESULTS_V33.md                         fixed-factor orthogonal cohort transport
RESULTS_V34.md                         conditional factor-estimation uncertainty
RESULTS_V35.md                         validation-use firewall and holdout-reuse policy
governance/validation_firewall.py      fail-closed validation-use classifier
governance/validation_use_ledger_v35.json machine-readable 2024 reuse history
deployment/                            FastAPI, bundle, monitoring, review and outcome-monitoring code
build_deployment_bundle_v21.py         reproducible model bundle + aggregate monitoring baseline
build_bundle_lock_v27.py               content-addressed bundle lock
verify_bundle_v27.py                   fail-closed bundle integrity verifier
verify_release_admission_v30.py        attested shadow release admission policy
run_outcome_review_v31.py              real-2024 delayed-outcome replay and segment review
run_validation_firewall_v35.py         aggregate validation-reuse evidence runner
scripts/push_evidence_with_rebase.sh   bounded race-safe evidence persistence helper
Dockerfile                             CPU-only containerised shadow service
requirements-runtime.txt               serving-only dependency boundary
action_results/v21/ ... v35/           persisted non-binary workflow evidence
.github/workflows/                     data, governance, deployment, release and evidence workflows
tests/                                 leakage, evidence, model, serving, release, validation and persistence contracts
```
