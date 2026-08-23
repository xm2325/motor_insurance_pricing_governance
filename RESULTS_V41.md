# v0.41 — Belgian external replication: first execution

## Purpose

Execute the v0.40 preregistered `beMTPL97` protocol for the first time after the preregistration has been merged and persisted on `main`.

This version deliberately does **not** permit a positive external-support conclusion from one run. v0.40 requires at least two independent GitHub Actions executions, matching registered decisions and preregistered point-metric reproducibility, before any positive external-support label can stand.

## Frozen lineage

- v0.40 preregistration canonical SHA-256: `19658e3a6b12e55ffaa564585bf69dd09ad1371b567f0c1b03c7d17103796822`
- v0.40 main source SHA: `833e861ee797d3751090e4d08a512d9f340b5378`
- CASdatasets source commit: `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`
- row-level data were not accessed by v0.40.

## Execution safeguards

The workflow first verifies the persisted v0.40 lock, then downloads the commit-pinned Belgian source into an untracked working directory. It audits the exact preregistered schema/row count, unique policy ids, exposure in `(0, 1]`, non-negative integer claim counts, non-negative aggregate claim amounts and finite modelling inputs.

The frozen preprocessing is fitted on training only: `StandardScaler` for numeric features and dense `OneHotEncoder(handle_unknown='ignore')` for categorical features.

Poisson and Tweedie GLMs use the preregistered `newton-cholesky` solver with `tol=1e-10`; convergence warnings or any warning indicating L-BFGS/fallback invalidate the execution. GLM/XGBoost predictions must be finite and strictly positive; v0.41 does not silently clip invalid predictions.

The job runs with single-thread OpenMP/OpenBLAS/MKL settings and the preregistered package versions.

## Decision boundary

Whatever the first-execution metrics are:

- model-family decision remains `HOLD`;
- serving remains `HOLD_SHADOW_ONLY`;
- model promotion is not authorised;
- pricing changes are not authorised;
- `positive_external_support_authorised=false` after execution ordinal 1.

If neither registered gate passes, there is no positive result to reproduce. If either gate passes, an independent second execution is required before any positive external-support conclusion.

Authoritative aggregate metrics are written by the v0.41 GitHub Actions workflow; raw Belgian data are never persisted to the repository.
