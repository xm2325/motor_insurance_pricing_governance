# v0.36 — Australian external validation preregistration

## Purpose

v0.35 closes the repeatedly reused Spanish 2024 period to new candidate-selection and promotion claims. v0.36 therefore does **not** compute another 2024 metric and does **not** download a new outcome dataset.

Instead, it preregisters an independent external motor-insurance replication before row-level outcomes are accessed in this repository.

## External source selected

The registered source is CASdatasets `ausprivauto0405`, pinned to upstream repository commit:

`227fb56b8734bdb7c0327a41180e01d2ddaeaf26`

Public documentation available before row-level access states that the portfolio contains:

- 67,856 Australian private motor policies written in 2004 or 2005;
- 9 columns;
- exposure, vehicle value/age/body, policyholder gender/age, claim occurrence, claim count and aggregate claim amount;
- 4,624 policies with at least one claim.

Those public aggregate facts are recorded explicitly in the preregistration so they are not later presented as information that was unknown before the protocol was fixed.

The CASdatasets package documents GPL (>=2) and DOI `10.57745/P0KHAG`. The dataset documentation cites De Jong and Heller (2008), *Generalized Linear Models for Insurance Data*.

## Evidence class

This is preregistered as:

`EXTERNAL_PORTFOLIO_MODEL_FAMILY_REPLICATION`

It is **not** a direct transport test of the fitted Spanish parameters. The feature space and insurer/market context differ. A positive result would show that the GLM-vs-XGBoost question replicates on another public motor portfolio under fixed rules; it would not establish transfer to FIRST CENTRAL or the UK market.

## Frozen data and leakage contract

Primary features are fixed before download:

- numeric: `VehValue`;
- categorical: `VehAge`, `VehBody`, `DrivAge`.

Excluded predictors are:

- `Exposure` — weight only;
- `Gender` — deliberately excluded by project design;
- `ClaimOcc` — outcome-derived leakage;
- `ClaimNb` — frequency outcome;
- `ClaimAmount` — loss outcome.

`ClaimOcc` is explicitly prohibited from all preprocessing, fitting, calibration, ranking and scoring features.

The execution must fail rather than silently filter if the pinned source does not have exactly 67,856 rows and the expected columns, contains missing required values, non-positive exposure, negative/non-integer claim counts or negative claim amount.

## Frozen split

A single source-order row-index permutation is fixed with seed `20260823`:

- 60% train;
- 20% calibration;
- 20% locked test.

The split is **not outcome-stratified**. Test and calibration data may not be used for hyperparameter search, and the split may not be changed after outcomes are inspected.

## Frozen model families

### Frequency

Reference: `PoissonRegressor`, alpha `1e-8`, max_iter `2000`.

Challenger: fixed `XGBRegressor(objective='count:poisson')` with:

- 400 trees;
- depth 3;
- learning rate 0.05;
- subsample 0.8;
- column subsample 0.8;
- min child weight 20;
- L2 regularisation 5;
- random seed `20260823`.

### Pure premium

Reference: `TweedieRegressor(power=1.5, link='log')`, alpha `1e-6`, max_iter `3000`.

Challenger: fixed XGBoost Tweedie with the same tree controls and variance power 1.5.

No hyperparameter search and no early stopping are allowed in the external execution.

## Calibration

Each fitted model receives one multiplicative scale estimated on the 20% calibration split only.

Registered scale guardrails are `[0.5, 2.0]`. Scales are **not clipped**. A scale outside the range invalidates that external candidate and retains HOLD rather than forcing a plausible-looking factor.

## Locked-test endpoints

Primary endpoint: exposure-weighted Poisson deviance for claim frequency.

Secondary confirmatory endpoint: exposure-weighted Tweedie deviance, power 1.5, for pure premium.

Aggregate calibration and top-10%-of-exposure claim/loss capture are also reported.

## Frozen paired bootstrap

The locked test will use 500 paired policy-row bootstrap draws with seed `20260824`. GLM and XGBoost are evaluated on identical resampled rows.

The registered relative-improvement statistic is:

`1 - challenger_deviance / reference_deviance`

for each target.

## External replication gate

A target supports XGBoost for **further validation** only if all three conditions hold:

1. point relative deviance improvement is at least 0.5%;
2. the paired-bootstrap 95% percentile interval for relative improvement has lower bound > 0;
3. challenger aggregate absolute log-calibration error is no more than 0.01 worse than the reference.

No threshold may be relaxed after the locked-test result is known.

## Governance boundary

Even a fully positive Australian result cannot directly authorise:

- model-family promotion;
- a serving-bundle change;
- customer pricing;
- a claim of UK/FIRST CENTRAL transfer.

v0.36 itself changes no model and accesses no row-level external data. Status remains:

- model-family decision: `HOLD`;
- serving status: `HOLD_SHADOW_ONLY`.

The row-level execution is allowed only after this preregistration is merged to main and its canonical SHA-256 is persisted.
