# v0.38 — External-validation numerical reproducibility audit

## Why this audit exists

v0.37 deliberately executed a protocol that had been frozen on main before row-level Australian data were accessed. The scientific gate itself was stable: both the primary frequency endpoint and secondary pure-premium endpoint returned `NO_EXTERNAL_*_REPLICATION_SUPPORT`.

During closeout, however, the persisted main execution exposed a numerical-reproducibility issue that should not be hidden. The pure-premium **Tweedie GLM reference deviance** differed materially from the final PR execution even though the source, split, feature contract, dependency versions and runner image version were unchanged.

v0.38 records that discrepancy instead of selecting whichever point estimate looks preferable.

## Three observed executions

All three executions used:

- v0.36 preregistration SHA-256 `b20d38b51f767761fe4b4f85d58988f7032dbcc7d7afc96041f3858c0165e3c1`;
- pinned Australian source SHA-256 `c8aeabd0b75e16a2b9a7452cfb3e8e2b3ec36a27171d35c2862bc8278777461c`;
- the same 60/20/20 split and feature contract;
- Python 3.12.14, NumPy 2.5.2, SciPy 1.18.0, scikit-learn 1.9.0 and XGBoost 3.4.1;
- the same Ubuntu 24.04 runner-image release.

| Execution | Runner region | Summary SHA-256 | Pure-premium GLM deviance | XGB deviance | XGB point improvement | Pure-premium decision |
|---|---|---|---:|---:|---:|---|
| final PR | centralus | `6f3fd009...` | **126.220469** | 114.956067 | +8.9244% | `NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT` |
| exact PR rerun | westcentralus | `6f3fd009...` | **126.220469** | 114.956067 | +8.9244% | `NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT` |
| post-merge main | northcentralus | `da7c30ae...` | **129.840909** | 114.956067 | +11.4639% | `NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT` |

The PR execution and a later manually requested rerun on a different runner allocation produced byte-identical aggregate summaries. The main execution differed in the Tweedie GLM point fit.

The relative difference between the two observed GLM reference deviances is about **2.87%** using the PR value as denominator. This is far too large to describe as exact point-metric reproducibility.

## What remained stable

The discrepancy does **not** reverse the registered scientific decision.

### Frequency

Frequency is effectively stable across the observed executions:

- GLM deviance approximately **0.814742**;
- XGBoost deviance **0.817878**;
- XGBoost relative improvement approximately **-0.3849%**;
- bootstrap 97.5th percentile remains below zero;
- decision remains `NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT`.

### Pure premium

The XGBoost pure-premium deviance is unchanged at **114.956067**. The GLM point estimate changes, so the apparent XGBoost point improvement changes from **+8.9244%** to **+11.4639%**.

But the preregistered paired bootstrap remains non-confirmatory in every observed execution:

- PR/rerun lower 95% bound: about **-10.687%**;
- main lower 95% bound: about **-10.688%**;
- positive-draw rate: **61.8%** in both result families;
- registered decision: `NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT` throughout.

Thus the correct statement is:

> **The v0.37 governance decision is reproducible across the observed executions; the pure-premium GLM point metric is not exactly numerically reproducible.**

## Cause boundary

The repeated runs used the same source and package versions but different hosted-runner regions/hardware allocations. The observed pattern is **consistent with numerical convergence sensitivity in the iterative Tweedie GLM**, but the audit does not establish a unique causal mechanism.

The project therefore does not attribute the discrepancy to a particular BLAS library, CPU instruction set, solver implementation detail or runner region without direct evidence.

## Authoritative v0.37 record

For repository evidence, the post-merge main execution remains authoritative because it is the result persisted under `action_results/v37/`:

- workflow run: **32633520755**;
- source commit: `1e975b5258f3442da5c72dd9794fad2bf5303ae6`;
- summary SHA-256: `da7c30aef7e5e810755b9fb15a4749757c25af79ff4d553ed775d71be0f71017`;
- main pure-premium GLM deviance: **129.840909**;
- main XGBoost deviance: **114.956067**;
- main point improvement: **+11.4639%**;
- main bootstrap 95% interval approximately **[-10.69%, +33.84%]**;
- registered pure-premium decision still **NO SUPPORT**.

The earlier PR result is retained as reproducibility evidence; it is not silently substituted for main.

## New rule for future external validation

For protocols registered after v0.38, a **positive** external-support claim will require more than a single successful run:

1. at least **two independent GitHub Actions executions** using the identical locked source, split, features, model specifications and gate;
2. identical registered decision labels across the executions;
3. key point metrics within the preregistered numerical-reproducibility tolerance;
4. environment, runner-image, dependency and thread settings recorded;
5. iterative estimators must preregister their solver and tolerance explicitly and record available convergence metadata;
6. future numerical workflows default to `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `MKL_NUM_THREADS=1` unless a preregistration explicitly justifies another setting.

The default future project review tolerance for claiming **exact metric reproducibility** is **0.1% relative difference**. This is a project rule, not an insurer or regulatory threshold, and future protocols may register a stricter rule before data access.

If decisions disagree across runs, the result becomes `NUMERICAL_REPRODUCIBILITY_REVIEW_REQUIRED` and no positive external claim is permitted. If decisions agree but point metrics exceed the registered tolerance, the evidence is labelled `METRIC_NUMERICAL_REPRODUCIBILITY_REVIEW` rather than exact reproducibility.

These rules are prospective. They do **not** retroactively alter v0.36 after the Australian outcomes were observed.

## Governance result

v0.38 does not promote either model family and does not change serving or pricing:

- frequency external support: **false**;
- pure-premium external support: **false**;
- decision reproducible across observed runs: **true**;
- exact pure-premium point-metric reproducibility claim allowed: **false**;
- model-family decision: **`HOLD`**;
- serving status: **`HOLD_SHADOW_ONLY`**;
- model promotion authorised: **false**;
- customer-pricing change authorised: **false**.
