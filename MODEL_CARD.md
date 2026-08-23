# Model Card — Motor Insurance Pricing & Model Governance Workbench

## Purpose

This project is a reproducible model-risk workbench for one question:

> **Does an XGBoost challenger improve motor-insurance claim-frequency and pure-premium targets reliably enough, across calendar time and independent portfolios, to justify advancing beyond GLM reference models?**

The project deliberately separates **development signal**, **validation evidence**, **operational readiness** and **approval authority**. A model can be technically deployable in shadow mode while still lacking enough evidence for promotion.

## Current status

| Item | Current state |
|---|---|
| Model-family decision | **HOLD** |
| Serving boundary | **HOLD_SHADOW_ONLY** |
| Promotion review | **NOT_OPEN** |
| Model promotion authorised | **No** |
| Customer-pricing change authorised | **No** |
| Preregistered external target gates | **0 / 4 pass** |
| Model Change Committee readiness | **EVIDENCE_GAP_HOLD — 5 / 8 gates pass** |

The three current committee blockers are:

1. `G2_LOCKED_TEMPORAL_SUPPORT` — the original Spanish locked OOT result did not support a global model-family switch;
2. `G3_PREREGISTERED_EXTERNAL_SUPPORT` — Australia and Belgium provide four preregistered external target gates, with zero passes;
3. `G4_FRESH_INDEPENDENT_EVIDENCE` — the Spanish, Australian and Belgian validation datasets have already been used and are now consumed for fresh candidate selection.

A human-signoff flag cannot override failed evidence gates. Even a future all-pass machine state can only open a human review; this repository never authorises customer pricing automatically.

## Model inventory

The shadow bundle contains four reference/challenger models:

- Poisson GLM frequency reference;
- XGBoost Poisson frequency challenger;
- Tweedie GLM pure-premium reference;
- XGBoost Tweedie pure-premium challenger.

The v0.21 manifest records the model artifacts, locked calibration scales, feature-contract digest and artifact SHA-256 values. The API exposes side-by-side risk scores for shadow comparison and deliberately exposes no `/quote` or `/price` endpoint.

## Target definitions

- **Claim frequency:** claim count per unit exposure.
- **Pure premium / expected loss:** incurred claim amount per unit exposure.
- Exposure is used as an offset/weight or denominator as appropriate, not as a predictive feature.

## Evidence and data lineage

Different datasets have deliberately different evidence roles.

| Portfolio | Role at first use | Current role | Can support new candidate selection now? |
|---|---|---|---|
| French `freMTPL2` | Cross-sectional development benchmark | Development benchmark | **No — not promotion evidence** |
| Spanish `sw4jmdb2sm` 2024 | `LOCKED_OOT_FIRST_USE` | `CONSUMED_RETROSPECTIVE_VALIDATION` | **No** |
| Australian `ausprivauto0405` | `INDEPENDENT_EXTERNAL_VALIDATION_FIRST_USE` | `CONSUMED_EXTERNAL_VALIDATION_DATASET` | **No** |
| Belgian `beMTPL97` | `INDEPENDENT_EXTERNAL_VALIDATION_FIRST_USE` | `CONSUMED_EXTERNAL_VALIDATION_DATASET` | **No** |

The distinction matters: rerunning, resplitting or retuning on an already inspected validation portfolio cannot make it independent again.

## Development benchmark

On the French `freMTPL2` frequency benchmark, the comparable XGBoost Poisson model reduced weighted Poisson deviance by **5.43%** relative to the Poisson GLM with geography and increased top-10% exposure claim capture from **20.59% to 31.17%**.

This is strong **challenger-development evidence**. It is not an out-of-time pricing uplift, observed commercial impact or promotion decision.

## Spanish calendar validation

The Spanish public motor portfolio contains **354,140 policy-year observations and 47 variables** covering 2022–2024. The original prospective roles were:

- **2022:** model training;
- **2023:** aggregate calibration;
- **2024:** locked OOT evaluation at **first use**.

The feature contract excludes current premiums, current claim counts, current incurred losses, policy status, year and customer ID from predictive inputs.

### First-use locked 2024 results

Frequency:

- GLM Poisson deviance: **1.118536**;
- XGBoost Poisson deviance: **1.118835**;
- top-10% exposure claim capture: **26.62% GLM vs 27.04% XGBoost**;
- paired bootstrap GLM-minus-XGB deviance interval: **[-0.00155, 0.00083]**.

Pure premium:

- GLM Tweedie deviance: **93.931806**;
- XGBoost Tweedie deviance: **93.951316**;
- aggregate calibration: **0.953 GLM vs 0.934 XGBoost**;
- the paired bootstrap interval crossed zero.

The registered decision remained **HOLD**. Later monitoring, outcome review, recalibration, cohort and uncertainty work reused 2024, so v0.35 now records the period as `CONSUMED_RETROSPECTIVE_VALIDATION` for future decision-making while preserving the historical fact that it was independent at first locked use.

## Australian preregistered external replication

`ausprivauto0405` contains **67,856** policies. Source, split, features, models, calibration, metrics, bootstrap and support gates were merged on main **before row-level access**.

Registered external results:

### Frequency

- GLM deviance: **0.814742**;
- XGBoost deviance: **0.817878**;
- XGBoost relative deviance improvement: **-0.3849%**;
- bootstrap 95% interval for relative improvement: approximately **[-0.7799%, -0.0381%]**;
- decision: `NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT`.

### Pure premium

The immutable origin-main evidence records:

- GLM deviance: **129.840909**;
- XGBoost deviance: **114.956067**;
- favourable XGBoost point improvement: **+11.4639%**;
- bootstrap lower bound: approximately **-10.6885%**;
- top-10% exposure loss capture: **18.48% GLM vs 11.09% XGBoost**;
- decision: `NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT`.

The favourable point estimate was not promoted into a positive conclusion because the preregistered uncertainty gate failed and ranking performance moved adversely.

Repeated Australian executions also exposed that one iterative Tweedie GLM point metric was not exactly reproducible across hosted runs even though the registered decisions remained negative. That numerical issue was retained rather than hidden and led to stronger prospective reproducibility requirements.

## Belgian preregistered external replication

`beMTPL97` contains **163,212 unique policies**. The protocol was merged before row-level access and prospectively fixed solver, tolerance and single-thread numerical controls.

### Frequency

- GLM deviance: **0.604357**;
- XGBoost deviance: **0.602598**;
- XGBoost relative improvement: **+0.2910%**;
- bootstrap 95% interval: approximately **[+0.0987%, +0.4876%]**;
- registered decision: `NO_SECOND_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT`.

The uncertainty interval is positive, but the point improvement misses the fixed **0.5% project materiality threshold**. That threshold is a project demonstration rule, not an insurer or regulatory standard, and it was not relaxed after observing the result.

### Pure premium

- GLM deviance: **79.843311**;
- XGBoost deviance: **79.586308**;
- XGBoost relative improvement: **+0.3219%**;
- bootstrap 95% interval: approximately **[-0.7918%, +1.3082%]**;
- top-10% loss capture: **20.45% GLM vs 19.12% XGBoost**;
- registered decision: `NO_SECOND_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT`.

Two completed Actions executions in different observed Azure regions reproduced all registered aggregate metrics within the preregistered tolerances. Maximum absolute difference was **1.42×10⁻¹⁴** and maximum relative difference **6.90×10⁻¹⁴**. This strengthens confidence in the recorded negative decisions; it does not convert them into positive challenger support.

## Cross-portfolio evidence synthesis

v0.43 keeps the original evidence classes and decisions rather than constructing a pooled meta-analysis or subjective evidence-weighting score.

Across Australia and Belgium:

- external portfolios evaluated: **2**;
- preregistered target gates evaluated: **4**;
- preregistered target gates passed: **0**;
- fresh independent validation datasets currently available: **0**.

The correct conclusion is **not** “XGBoost is universally worse than GLM”. Some challenger point and ranking metrics are favourable. The conclusion is that the existing evidence is insufficient to open a global model-family promotion review.

## Operational readiness

Operational controls are deliberately evaluated separately from model evidence.

The repository demonstrates:

- FastAPI/Docker shadow scoring and offline/online parity;
- aggregate monitoring without raw request payload persistence;
- review hysteresis with no automatic pricing/model switch;
- CPU runtime packaging and native XGBoost model IO;
- content-addressed bundle integrity;
- manual release and rollback controls;
- GitHub/Sigstore build provenance;
- attested release admission restricted to `ADMIT_TO_SHADOW_REGISTRY_ONLY`;
- zero raw-source-data members in the admitted release archive.

The synthetic release-control replay rejects unauthorised rollback and requires explicit operator authorisation. These are project engineering controls, not production incidents, insurer approval or proof of pricing safety.

## Model Change Committee readiness

v0.44 converts the persisted evidence dossier into a fail-closed machine readiness gate for a hypothetical human model-change review.

Current request `MCR-XGB-MOTOR-001` is:

**`EVIDENCE_GAP_HOLD` — 5 of 8 required gates pass.**

Passing gates demonstrate development signal, prospective reproducibility controls, shadow deployment boundaries, release/rollback control and attested shadow admission. They cannot compensate for the three failed evidence gates.

## Intended use

Appropriate uses include:

- demonstrating insurance model-development and validation reasoning;
- comparing GLM references with ML challengers;
- showing preregistration, holdout-consumption controls and external replication;
- demonstrating model-risk, reproducibility and shadow-release governance;
- explaining why negative or mixed evidence can correctly lead to HOLD.

## Not intended for

This project must not be represented as:

- a real customer-pricing or underwriting system;
- evidence of profit, conversion or premium uplift;
- validation of FIRST CENTRAL models, thresholds or governance policy;
- proof of transfer to the current UK motor market;
- an insurer, actuarial or regulatory approval;
- a real Model Change Committee decision;
- production-safety evidence.

## Work required before any production-like claim

A production-like claim would require, at minimum, governed target-portfolio rating and claims data with as-of feature lineage, insurer-specific actuarial and pricing review, agreed acceptance thresholds, fairness/proxy and regulatory review, expense/reinsurance/commercial treatment, security and operational controls, prospective target-portfolio validation, outcome-linked monitoring and authorised business/model-risk approval.

For this public project specifically, reopening the challenger evidence review requires a **genuinely new independent external dataset or independent calendar period whose row-level outcomes have not already been inspected**, with the protocol merged before access and any positive result reproduced under the prospective multi-run numerical controls.
