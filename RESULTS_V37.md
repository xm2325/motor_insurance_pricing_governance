# v0.37 — Preregistered Australian external motor replication

## Why this result matters

v0.37 is the first model-family evidence added after the v0.35 validation firewall. Unlike v0.32–v0.34, it does not interrogate the already-consumed Spanish 2024 period again.

The complete modelling protocol was merged to main in v0.36 **before row-level Australian data were accessed**. The persisted preregistration has SHA-256:

`b20d38b51f767761fe4b4f85d58988f7032dbcc7d7afc96041f3858c0165e3c1`

The first row-level execution then used that protocol without changing the split, features, model hyperparameters, calibration rules, bootstrap or decision thresholds.

**Evidence convention after v0.38 audit:** the post-merge main run is the authoritative persisted v0.37 result. Earlier PR runs are retained as numerical-reproducibility comparators. The registered decisions agree, but the pure-premium Tweedie GLM point deviance did not reproduce exactly across hosted runners. See `RESULTS_V38.md`.

## Source audit

Pinned source:

- dataset: CASdatasets `ausprivauto0405`;
- upstream commit: `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`;
- rows: **67,856**;
- columns: **9**;
- policies with at least one claim: **4,624**;
- downloaded `.rda` size: **268,505 bytes**;
- downloaded file SHA-256: `c8aeabd0b75e16a2b9a7452cfb3e8e2b3ec36a27171d35c2862bc8278777461c`.

The raw `.rda` is used only in the Actions workspace. It is not committed or persisted as project evidence.

## Locked split

The preregistered source-order permutation with seed `20260823` produced:

| Split | Rows | Exposure | Claims | Claim amount | Claiming policies |
|---|---:|---:|---:|---:|---:|
| Train | 40,713 | 19,126.845 | 2,934 | 5,501,513.53 | 2,736 |
| Calibration | 13,571 | 6,333.202 | 992 | 1,845,284.86 | 940 |
| Locked test | 13,572 | 6,340.772 | 1,011 | 1,967,806.05 | 948 |

The split was not outcome-stratified and was not changed after outcomes were inspected.

Primary predictors were exactly the preregistered `VehValue`, `VehAge`, `VehBody` and `DrivAge`. `Exposure`, `Gender`, outcome-derived `ClaimOcc`, `ClaimNb` and `ClaimAmount` were excluded from model features. The training-only encoder produced 24 model columns.

## Primary endpoint — claim frequency

Calibration scales were within the preregistered `[0.5, 2.0]` range and were not clipped:

- GLM: **1.02080**;
- XGBoost: **1.01795**.

Authoritative main locked-test results:

| Metric | Poisson GLM | XGBoost |
|---|---:|---:|
| Poisson deviance | **0.814742** | 0.817878 |
| Aggregate calibration | **0.98377** | 0.98138 |
| Absolute log-calibration error | **0.01636** | 0.01879 |
| Top-10% exposure claim capture | 12.66% | **13.25%** |

The XGBoost relative deviance improvement is therefore **-0.3849%**: on the preregistered primary loss function it is worse, despite a small ranking/capture increase.

The 500-draw paired locked-test bootstrap gives relative-improvement interval:

> **95% CI [-0.7799%, -0.0381%]**

with median **-0.3837%** and only **1.8%** of draws above zero.

Registered decision:

> **`NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT`**

The calibration non-inferiority check passes, but both the required >=0.5% point improvement and positive bootstrap lower bound fail.

## Secondary confirmatory endpoint — pure premium

Authoritative main calibration scales are valid and unclipped:

- GLM: **1.01377**;
- XGBoost: **1.10226**.

Authoritative main locked-test results from run **32633520755**:

| Metric | Tweedie GLM | XGBoost |
|---|---:|---:|
| Tweedie deviance, p=1.5 | 129.8409 | **114.9561** |
| Aggregate calibration | 0.93933 | **0.94033** |
| Absolute log-calibration error | 0.06259 | **0.06153** |
| Top-10% exposure loss capture | **18.48%** | 11.09% |

The authoritative main point deviance improvement is **+11.4639%**. It is not treated as confirmatory because the preregistered paired bootstrap remains much less stable:

> **95% CI [-10.6885%, +33.8421%]**

with median **+10.4135%** and **61.8%** of draws above zero.

Registered decision:

> **`NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT`**

The point-improvement and calibration checks pass, but the required positive bootstrap lower bound fails. The large deterioration in top-10% loss capture is also retained as a descriptive trade-off rather than hidden, although ranking capture was not part of the preregistered pass gate.

### Numerical reproducibility note

The final PR execution and a later rerun of the exact same PR job, on two different hosted-runner allocations, both produced Tweedie GLM deviance **126.220469** and XGBoost point improvement **+8.9244%**. The post-merge main execution produced GLM deviance **129.840909** and point improvement **+11.4639%** while the XGBoost deviance, source audit, split, package versions, bootstrap conclusion and registered decision remained stable.

Therefore v0.37 must **not** be described as having exact pure-premium point-metric reproducibility across runners. `RESULTS_V38.md` records the three-run reconciliation and prospective safeguards.

## Interpretation across Spain and Australia

This external portfolio does **not** support a simple story that XGBoost should replace the GLM globally:

- the primary Australian frequency endpoint favours the GLM on deviance, with the entire registered bootstrap interval below zero;
- the Australian pure-premium point estimate favours XGBoost strongly, but uncertainty spans material harm to material benefit and the tail-ranking result moves in the opposite direction;
- the pure-premium GLM point metric also exposed cross-run numerical sensitivity, further strengthening the case for conservative external-evidence governance;
- this contrasts with some later Spanish XGBoost frequency recalibration evidence, showing why repeated success on one reused historical period would have been insufficient evidence for promotion.

That non-uniformity is the useful result.

## Governance decision

Neither preregistered external endpoint passes its XGBoost replication gate. No rule was relaxed after observing the results.

Project status remains:

- model-family decision: **`HOLD`**;
- serving status: **`HOLD_SHADOW_ONLY`**;
- model promotion authorised: **false**;
- customer-pricing change authorised: **false**.

This is an external portfolio model-family replication, not direct validation of the Spanish fitted models and not evidence of transfer to FIRST CENTRAL or the UK motor market.
