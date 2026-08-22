# v0.31 — Delayed-outcome Maturity & Segment Calibration Review

## Decision

**PASS — delayed-label controls and mature-outcome review are verified; the model-family decision remains `HOLD` and serving remains `HOLD_SHADOW_ONLY`.**

v0.31 closes the operational loop from the v0.22/v0.23 portfolio-mix review to later observed claims outcomes. It replays the real 2024 `total_claims` and `total_incurred` outcomes through a freshly rebuilt, v0.27 integrity-verified shadow bundle.

The claim/loss outcomes are observed historical data. The partial label-arrival timing is deliberately synthetic and tests whether the monitoring process refuses to make a performance judgement before enough exposure has mature outcomes.

## Outcome-maturity gate

The review requires at least **95% of exposure** to have mature outcomes before label-based model performance is calculated.

| Replay state | Mature rows | Mature exposure | Mature exposure share | Result |
|---|---:|---:|---:|---|
| Synthetic early arrival | 100,567 / 168,085 | 75,608.69 | **60.0001%** | `WAIT_FOR_OUTCOME_MATURITY`; no performance conclusion |
| Fully mature 2024 | 168,085 / 168,085 | 126,014.36 | **100%** | `OUTCOME_PERFORMANCE_EVALUATED` |

At the early checkpoint the code does not calculate or expose frequency/pure-premium performance metrics. It records `NO_PERFORMANCE_CONCLUSION`, and neither pricing change nor model promotion is authorised.

## Fully mature 2024 performance

Once all 2024 outcomes are available, the shadow bundle reproduces the locked OOT evidence:

| Target | GLM reference | XGBoost challenger | GLM minus XGB deviance |
|---|---:|---:|---:|
| Frequency Poisson deviance | **1.118536** | 1.118835 | **-0.000299** |
| Frequency calibration, predicted / actual | 0.963088 | 0.960085 | — |
| Pure-premium Tweedie deviance | **93.931806** | 93.951316 | **-0.019510** |
| Pure-premium calibration, predicted / actual | **0.953069** | 0.933593 | — |

Observed 2024 totals used in the mature review are **39,276 claims** and **38,106,351.28 incurred**, across **168,085 policy-years**.

The result does not create new evidence for challenger promotion. On both primary deviance measures the GLM remains slightly better in the mature 2024 replay, consistent with the existing `HOLD` decision.

## `business_type` calibration review

`business_type` drove the large v0.22 temporal PSI signal, so v0.31 evaluates mature label-based calibration separately for the two observed groups.

| Group | Exposure share | GLM frequency cal. | XGB frequency cal. | GLM pure-premium cal. | XGB pure-premium cal. |
|---|---:|---:|---:|---:|---:|
| NB | 48.18% | 0.9953 | **1.0025** | 0.8610 | **0.9165** |
| P | 51.82% | **0.9364** | 0.9249 | **1.0366** | 0.9491 |

There is no single model that is better across both groups and both targets. The challenger is closer to 1.0 for NB frequency and pure premium, while the GLM is closer for P frequency and pure premium. This is direct outcome evidence that the portfolio-mix drift should be reviewed by segment rather than interpreted as a reason for automatic global model replacement.

## Historical OOT reconciliation

The freshly rebuilt bundle is compared with the registered 2024 OOT evidence for eight values: reference/challenger frequency deviance, frequency calibration, pure-premium deviance and pure-premium calibration.

All eight values match exactly in this GitHub Actions run:

- maximum absolute difference: **0.0**;
- maximum relative difference: **0.0**;
- allowed regression-diagnostic relative tolerance: **0.2%**.

This is a fresh-training regression check against the same historical outcomes. It is separate from the v0.26 same-fit serialization parity contract.

## Verified workflow

PR validation run `32604899147` performed the full sequence on a GitHub-hosted runner:

1. run the v0.31 numeric maturity contracts;
2. discover, download/cache-check and audit Mendeley `sw4jmdb2sm` v1;
3. rebuild the current four-model shadow bundle;
4. seal and verify the v0.27 content-addressed bundle;
5. score the 168,085-row 2024 cohort;
6. run early and fully mature outcome reviews;
7. run `business_type` aggregate segment calibration;
8. reconcile the mature metrics against the registered OOT evidence;
9. assert that no automatic serving, pricing or model-family change occurred.

The separate lightweight governance CI also passes on the v0.31 branch after keeping dependency-heavy numeric tests in the heavy workflow and adding a standard-library static contract to the lightweight suite.

## Interpretation boundary

This is not a live claims-development study and does not estimate incurred-but-not-reported reserves or settlement curves. The 60% maturity checkpoint is synthetic and exists only to validate the delayed-label decision rule.

The 2024 outcomes themselves are observed historical data from the public Spanish motor portfolio. The review demonstrates how a shadow pricing model can wait for sufficiently mature labels and then connect input-drift investigation to realised claims/loss calibration. It does not establish post-deployment production performance, approve customer pricing, or establish transfer to FIRST CENTRAL or the UK motor market.
