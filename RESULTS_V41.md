# v0.41 — Belgian external replication: first execution

## Purpose

Execute the v0.40 preregistered `beMTPL97` protocol for the first time after the preregistration has been merged and persisted on `main`.

v0.40 required at least two independent GitHub Actions executions, matching registered decisions and preregistered point-metric reproducibility, before any **positive** external-support label could stand. The first completed Belgian execution did not pass either registered model-family gate, so no positive support was created.

## Frozen lineage

- v0.40 preregistration canonical SHA-256: `19658e3a6b12e55ffaa564585bf69dd09ad1371b567f0c1b03c7d17103796822`
- v0.40 main source SHA: `833e861ee797d3751090e4d08a512d9f340b5378`
- CASdatasets source commit: `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`
- Belgian source SHA-256 after first permitted access: `955a821a7a693bf18076c425e4d5a5a99889f3c89e1fbd99eca6239c11e963a6`
- raw Belgian data are never persisted to the repository.

## Execution chronology

The chronology is part of the evidence boundary:

1. Earlier CI attempts failed or were cancelled **before** Belgian row-level access.
2. Run `32637645586` passed the preregistration/source contract and became the first legal row-level source access. The pinned source audit passed, but execution then stopped **before any model fit or locked-test metric** because implementation code compared the registered Python major.minor string `3.12` to the exact hosted patch string `3.12.14`.
3. The implementation was corrected to interpret the already-registered `3.12` as a major.minor requirement. No split, feature, model, solver, tolerance, metric or gate changed after source access.
4. PR run `32637809066` (`eastus2`) was the first completed model execution.
5. Main run `32637884887` (`centralus`) independently reran the frozen implementation and persisted an immutable origin snapshot under `action_results/v41/origin/32637884887/`.

The aborted source-access run is not counted as a completed model execution and generated no result that could be used for model selection.

## Execution safeguards

The workflow verifies the persisted v0.40 lock before downloading the commit-pinned Belgian source into an untracked working directory. It audits the exact preregistered schema and 163,212-row count, unique policy ids, exposure in `(0, 1]`, non-negative integer claim counts, non-negative aggregate claim amounts and finite modelling inputs.

The frozen preprocessing is fitted on training only: `StandardScaler` for numeric features and dense `OneHotEncoder(handle_unknown='ignore')` for categorical features. The resulting design has 13 encoded features.

Poisson and Tweedie GLMs use the preregistered `newton-cholesky` solver with `tol=1e-10`; convergence warnings or any warning indicating L-BFGS/fallback invalidate the execution. In the authoritative main origin run, the Poisson GLM converged in 5 iterations and the Tweedie GLM in 4 iterations, both without warnings. GLM/XGBoost predictions must be finite and strictly positive; v0.41 does not silently clip invalid predictions.

The completed runs use Python 3.12.14 satisfying the registered Python 3.12 major.minor requirement, with exact NumPy 2.5.2, SciPy 1.18.0, scikit-learn 1.9.0, XGBoost 3.4.1 and pyreadr 0.5.3, plus `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `MKL_NUM_THREADS=1`.

## Frozen split realised on the pinned source

- train: 97,927 rows, exposure 87,175.7260, 12,153 claims, aggregate claim amount 16,025,532.07;
- calibration: 32,642 rows, exposure 29,001.2027, 3,969 claims, aggregate claim amount 5,012,321.75;
- locked test: 32,643 rows, exposure 29,039.8959, 4,093 claims, aggregate claim amount 5,427,116.11.

The split was not outcome-stratified and was not changed after outcome inspection.

## Authoritative main result — frequency

From immutable main run `32637884887`:

- GLM calibration scale: `0.9809032872120628`;
- XGBoost calibration scale: `0.9814338776666937`;
- GLM Poisson deviance: `0.604356714368424`;
- XGBoost Poisson deviance: `0.6025982649080157`;
- relative XGBoost improvement: **0.290962%**;
- bootstrap 95% interval for relative improvement: **[0.098721%, 0.487631%]**;
- bootstrap positive-draw rate: **99.8%**;
- aggregate calibration ratio: GLM `0.9703271`, XGBoost `0.9699975`;
- top-10% exposure claim capture: GLM **18.98%**, XGBoost **19.57%**.

The bootstrap lower bound is above zero, but the preregistered point-improvement threshold is **0.5%**. `0.290962% < 0.5%`, so the frequency gate fails exactly as registered:

`NO_SECOND_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT`

The threshold is not rounded or relaxed after observing the result.

## Authoritative main result — pure premium

From the same immutable main run:

- GLM calibration scale: `0.9394974339493479`;
- XGBoost calibration scale: `0.9959583115046144`;
- GLM Tweedie deviance: `79.84331051378416`;
- XGBoost Tweedie deviance: `79.58630762159916`;
- relative XGBoost improvement: **0.321884%**;
- bootstrap 95% interval: **[-0.791760%, 1.308226%]**;
- bootstrap positive-draw rate: **75.4%**;
- aggregate calibration ratio: GLM `0.9244734`, XGBoost `0.9181729`;
- top-10% exposure loss capture: GLM **20.45%**, XGBoost **19.12%**.

The point improvement is below 0.5% and the bootstrap lower bound is below zero. The pure-premium gate therefore fails:

`NO_SECOND_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT`

The adverse top-10 loss-capture movement is retained as descriptive evidence rather than hidden because the deviance point estimate is favourable.

## Decision boundary

The first completed execution has no positive registered gate, so its reproducibility state is `NO_POSITIVE_GATE_TO_REPRODUCE`. The independent main rerun is useful as a numerical reproducibility observation, but it cannot turn two failed gates into support.

The project remains:

- model-family decision `HOLD`;
- serving `HOLD_SHADOW_ONLY`;
- model promotion not authorised;
- customer pricing changes not authorised;
- no FIRST CENTRAL or current-UK transfer claim.

v0.42 separately audits the two completed executions against the preregistered numerical tolerance and closes `beMTPL97` as consumed external validation for future candidate selection.
