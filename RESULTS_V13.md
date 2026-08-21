# v0.13 Results — 2022–2024 Calendar OOT Validation

## Question

Does the stronger nonlinear challenger from the earlier motor-insurance workbench retain a meaningful advantage when evaluated on a genuine later calendar period?

The validation is intentionally designed to stop repeated reuse of the freMTPL2 final test set.

## Data and audit

Source: public Mendeley dataset `sw4jmdb2sm`, version 1.

The GitHub Actions download/audit produced:

- 354,140 policy-year rows;
- 47 columns;
- 67,172 rows in 2022;
- 118,835 rows in 2023;
- 168,133 rows in 2024;
- main CSV size 94,710,312 bytes;
- SHA-256 `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4`.

After requiring positive exposure and valid outcomes, 354,091 rows remain for modelling.

The observed portfolio is reasonably stable in claim frequency but changes in loss level:

| Year | Exposure | Claim frequency | Pure premium | Observed loss ratio |
|---|---:|---:|---:|---:|
| 2022 | 41,912.50 | 0.3022 | 292.75 | 65.62% |
| 2023 | 82,399.04 | 0.3053 | 285.06 | 66.46% |
| 2024 | 126,014.36 | 0.3117 | 302.40 | 74.66% |

## Leakage controls

The model does not use current premium, current claim count, current incurred loss or policy status as predictive features. Exposure is only a weight / denominator. `insured_id` and `year` are also excluded.

The split is fixed before model fitting:

- training: 2022;
- calibration: 2023;
- final OOT test: 2024.

The 2023 aggregate calibration factor is locked before any 2024 outcome is evaluated.

## Claim-frequency OOT result

| Metric | Poisson GLM | XGBoost Poisson |
|---|---:|---:|
| 2023 raw calibration ratio | 0.988 | 0.973 |
| locked scale from 2023 | 1.0124 | 1.0278 |
| 2024 raw Poisson deviance | 1.11887 | 1.11974 |
| 2024 locked Poisson deviance | **1.11854** | 1.11884 |
| 2024 locked calibration ratio | 0.9631 | 0.9601 |
| 2024 top-10% exposure claim capture | 26.62% | **27.04%** |

XGBoost captures about **0.42 percentage points** more claims in the top-risk 10% of exposure, but its locked Poisson deviance is marginally worse than the GLM.

Across 250 policy-row bootstrap resamples, the GLM-minus-XGBoost Poisson-deviance difference is:

- mean: `-0.000349`;
- 95% interval: **[-0.001553, 0.000830]**;
- probability difference > 0: **0.308**.

The interval crosses zero. There is no stable OOT evidence that the XGBoost frequency model improves deviance.

## Pure-premium OOT result

| Metric | Tweedie GLM | XGBoost Tweedie |
|---|---:|---:|
| 2023 raw calibration ratio | 1.094 | 0.828 |
| locked scale from 2023 | 0.9141 | 1.2076 |
| 2024 raw Tweedie deviance | **93.8344** | 95.3400 |
| 2024 locked Tweedie deviance | **93.9318** | 93.9513 |
| 2024 locked calibration ratio | **0.9531** | 0.9336 |
| 2024 top-10% exposure loss capture | 20.44% | **21.13%** |

Again, the nonlinear challenger has slightly higher top-risk capture, but it does not improve locked OOT deviance and is less well calibrated at portfolio level.

Across 250 bootstrap resamples, the GLM-minus-XGBoost Tweedie-deviance difference is:

- mean: `-0.01699`;
- 95% interval: **[-0.9884, 0.8556]**;
- probability difference > 0: **0.480**.

There is no stable OOT deviance advantage for the challenger.

## Policy transport

The 2024 test set contains:

- 105,307 policy IDs previously observed in 2022 or 2023;
- 62,778 policy IDs not previously observed;
- 62.65% of 2024 test IDs had prior observations.

Pure-premium calibration differs materially by this transport status:

| 2024 cohort | Tweedie GLM | XGBoost Tweedie |
|---|---:|---:|
| Seen before 2024 | **0.994** | 0.950 |
| Unseen before 2024 | 0.825 | **0.881** |

The challenger is closer for new policies, while the GLM is closer for returning policies. This prevents a simple claim that one model family transports better in every business cohort.

Other segment checks also show heterogeneous behaviour. For example, XGBoost improves pure-premium calibration for ages 25–34 but is materially worse for age 65+. The `<25` group is very small and is not used to make a model-change decision.

## Model-change decision

The predeclared demonstration gate is:

1. locked 2024 aggregate calibration ratio must be within `[0.90, 1.10]`; and
2. the 95% bootstrap interval for GLM-minus-XGBoost deviance must be strictly above zero.

Result:

- frequency challenger: **HOLD**;
- pure-premium challenger: **HOLD**;
- overall: **HOLD**.

The challengers pass the broad aggregate-calibration check but fail the statistical evidence check.

## Interpretation

This OOT experiment changes the project story in an important way. Earlier cross-sectional experiments showed that XGBoost can improve claim-frequency ranking. The calendar test shows that this does not automatically justify replacing the GLM in a later portfolio. In 2024, XGBoost captures slightly more high-risk claims and losses, but the gain is too small and uncertain to offset the absence of a deviance advantage and the mixed transport-segment calibration.

The result therefore supports a model-governance decision, not a model leaderboard: **retain the reference model family and keep the challenger in evaluation rather than promote it from a small ranking gain.**

## Boundary

This is real calendar OOT evidence within one public Spanish insurer dataset. It does not show that either model transfers to FIRST CENTRAL, the UK motor market or any production pricing system. A production decision would require company-specific rating-factor lineage, actuarial review, pricing governance and prospective validation.
