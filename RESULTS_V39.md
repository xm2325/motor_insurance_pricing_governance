# v0.39 — External validation reuse firewall

## Purpose

v0.39 prevents the Australian `ausprivauto0405` portfolio from being reused as if it were a fresh independent validation dataset after v0.37/v0.38.

The dataset was legitimately independent at the first preregistered v0.37 execution. That independence is now consumed: the registered train/calibration/test split has been used, the locked-test outcomes have been inspected, and the same frozen protocol has been rerun for numerical-reproducibility auditing.

## Registered source

- CASdatasets `ausprivauto0405`;
- pinned upstream commit `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`;
- source file SHA-256 `c8aeabd0b75e16a2b9a7452cfb3e8e2b3ec36a27171d35c2862bc8278777461c`;
- **67,856** rows;
- v0.37 locked test: **13,572** rows;
- v0.36 preregistration SHA-256 `b20d38b51f767761fe4b4f85d58988f7032dbcc7d7afc96041f3858c0165e3c1`.

Current evidence role:

> **`CONSUMED_EXTERNAL_VALIDATION_DATASET`**

## Use history

| Version | Role | Row-level access | Outcomes inspected | Independent at time of use |
|---|---|---|---|---|
| v0.36 | preregistration before data access | no | no | yes |
| v0.37 | first external model-family replication | yes | yes | yes |
| v0.38 | numerical reproducibility/governance audit | yes | yes | no |

The immutable v0.37 origin-main evidence is retained under `action_results/v37/origin_main_32633520755/`. Top-level v0.37 evidence is rolling regression evidence and is not a new validation sample.

## Allowed future use of the Australian portfolio

The consumed portfolio may still be used for:

- exact regression reproduction of the frozen v0.37 protocol;
- numerical reproducibility auditing;
- explicitly post-hoc diagnostics that cannot inform candidate selection;
- governance-contract testing.

Every such use is classified as `CONSUMED_EXTERNAL_VALIDATION_REUSE`, never independent confirmation.

## Uses that now fail closed

The Australian portfolio cannot be used for:

- fitting new model parameters;
- fitting new calibration parameters;
- hyperparameter search;
- selecting a new candidate policy;
- a new claim of independent confirmation;
- authorising model-family promotion;
- authorising customer pricing.

Unknown or newly invented purposes also fail closed.

## Entry rule for the next external dataset

An unseen external dataset may enter the project only through a preregistration-only state in which **row-level access is still forbidden**.

Before row-level access, a future protocol must be registered on main and fix the source, split, features, model specifications, metrics, gates and numerical-reproducibility rules.

Prospective positive external support also inherits the v0.38 reproducibility controls:

- at least **two independent GitHub Actions executions**;
- identical locked source/split/features/models/gate;
- matching registered decisions;
- point metrics inside the preregistered numerical tolerance;
- explicit solver/tolerance for iterative estimators;
- recorded numerical environment, with default `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `MKL_NUM_THREADS=1` unless preregistered otherwise.

## Next independent evidence requirement

> A genuinely new external dataset or new independent period whose row-level outcomes have not been inspected in this project, with its protocol merged before row-level access.

The Australian results can strengthen retrospective understanding and reproducibility engineering, but they cannot become independent again by rerunning, resplitting or changing candidate models after the test outcomes have been seen.

## Governance result

v0.39 is a data-use and evidence-governance control. It does not change the model decision:

- model-family decision: **`HOLD`**;
- serving status: **`HOLD_SHADOW_ONLY`**;
- model promotion authorised: **false**;
- customer-pricing change authorised: **false**.

All thresholds and workflow rules are project governance rules, not insurer or regulatory standards. Nothing in this external portfolio establishes transfer to FIRST CENTRAL or the UK motor market.
