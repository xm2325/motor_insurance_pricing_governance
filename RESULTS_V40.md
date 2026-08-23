# v0.40 — Belgian external validation preregistration

## Status

`PREREGISTRATION ONLY — NO BELGIAN ROW-LEVEL OUTCOMES ACCESSED`

The second independent external portfolio is CASdatasets `beMTPL97`, a Belgian motor third-party liability portfolio observed in 1997. v0.40 freezes the protocol before any row-level source file is downloaded, converted or inspected by this repository.

## Public metadata frozen before access

Public CASdatasets documentation describes 163,212 unique policyholders and 18 fields. Exposure is documented as a fraction of a year; claim information is represented by claim count and aggregate claim amount. The upstream source is pinned to CASdatasets commit `227fb56b8734bdb7c0327a41180e01d2ddaeaf26` and path `data/beMTPL97.rda`.

The public documentation identifies the insurer as unknown/anonymised. This provenance limitation remains explicit: the portfolio is useful as an independent actuarial replication dataset, not as evidence about a named insurer or the present UK market.

## Frozen modelling scope

Primary predictors:

- numeric: `ageph`, `bm`, `power`, `agec`;
- categorical: `coverage`, `fuel`, `use`, `fleet`.

Excluded from predictors:

- identifiers/exposure/outcomes: `id`, `expo`, `claim`, `nclaims`, `amount`, `average`;
- `sex` by registered project-design choice, not as a legal conclusion;
- `postcode`, `long`, `lat` to avoid geography-specific feature engineering and spatial proxy effects in this cross-portfolio replication.

`claim` and `average` are explicitly treated as outcome-derived leakage fields. Preprocessing is fitted on training only. No target encoding, category pooling, outcome-based row filtering, winsorisation or clipping is allowed.

## Frozen split and targets

A source-row-index permutation with seed `20260825` creates 60% training, 20% calibration and 20% locked test partitions without outcome stratification. Calibration and locked test cannot be used for hyperparameter selection, and no resplitting is permitted after outcome inspection.

The primary target is claim frequency (`nclaims / expo`, exposure-weighted Poisson deviance). The secondary confirmatory target is pure premium (`amount / expo`, exposure-weighted Tweedie deviance at power 1.5).

## Numerical reproducibility upgrade after v0.38

v0.37/v0.38 showed that a governance decision can reproduce while an iterative GLM point metric does not. v0.40 therefore preregisters:

- Python 3.12, NumPy 2.5.2, SciPy 1.18.0, scikit-learn 1.9.0, XGBoost 3.4.1 and pyreadr 0.5.3;
- `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`;
- Poisson and Tweedie GLMs with `solver='newton-cholesky'`, `tol=1e-10`, `max_iter=500`;
- convergence is required and fallback solver changes are forbidden;
- XGBoost uses `n_jobs=1` and fixed seeds;
- at least two independent GitHub Actions executions are required before any positive external-support label can stand;
- positive support also requires matching registered decisions and point metrics within relative tolerance `1e-8` / absolute tolerance `1e-10`.

A decision match with point-metric failure is labelled `METRIC_NUMERICAL_REPRODUCIBILITY_REVIEW`; a positive gate that fails independent reproduction becomes `NO_EXTERNAL_REPLICATION_SUPPORT`.

## Frozen gate

For frequency and pure premium separately:

1. point relative deviance improvement must be at least 0.5%;
2. the paired 500-draw bootstrap 95% percentile interval for relative deviance improvement must have lower bound above zero;
3. XGBoost aggregate absolute-log calibration error may be at most 0.01 worse than the GLM reference;
4. calibration scales must remain inside `[0.5, 2.0]` without clipping;
5. any positive result must satisfy the two-execution numerical reproducibility rule above.

The bootstrap seed is `20260826`. Registered thresholds are intentionally unchanged from the first external replication; the project is not loosening gates after seeing the Australian result.

## Governance boundary

v0.40 remains:

- model-family decision: `HOLD`;
- serving status: `HOLD_SHADOW_ONLY`;
- model promotion authorised: no;
- pricing change authorised: no.

Even a reproduced positive Belgian result would support further validation only. It cannot override the Spanish or Australian evidence, validate the fitted Spanish/Australian parameters, establish FIRST CENTRAL transfer, or authorise customer pricing.

The row-level Belgian execution is allowed only after this preregistration has been merged and persisted on `main`.
