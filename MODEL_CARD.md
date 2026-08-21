# Model Card — Motor Pricing Decision Workbench

## Intended use

Portfolio demonstration of insurance data-science reasoning: claim frequency, severity, expected loss, calibration, segment checks, incremental-data testing and model-promotion decisions.

## Not intended for

- setting real customer premiums;
- underwriting decisions;
- regulatory or actuarial sign-off;
- inference about First Central production models or thresholds.

## Data

Public freMTPL2 French Motor Third-Party Liability policy and claim data, plus a separate Spanish motor portfolio used for the v0.11 calendar OOT track.

## Target definitions

- Frequency: claim count / exposure.
- Severity: positive claim amount, with explicit sensitivity to heavy-tail handling.
- Expected loss / pure premium: modelled annual claim cost per exposure-year.

## Main model families

Poisson GLM, Gamma GLM, Tweedie GLM, Random Forest frequency challenger and XGBoost Poisson / Gamma challengers.

## Key risks

- claim severity is heavy-tailed;
- frequency and severity source tables can contain reconciliation inconsistencies;
- aggregate calibration can hide segment-level error;
- public portfolios may not transfer to a UK insurer;
- model-selection thresholds are illustrative, not company policy;
- repeated use of one final test set can become test-set tuning.

## Current decision through v0.10

**HOLD / REQUIRE NEW OUT-OF-TIME EVIDENCE.**

The locked freMTPL2 final-test portfolio did not provide a stable expected-loss winner between the reference and challenger, even though XGBoost improved claim-frequency ranking. Model disagreement was broad at policy level and could not be removed by scalar recalibration or clipping without masking structural differences.

## v0.11 validation rule

A second Spanish motor dataset with explicit renewal dates is used only for a calendar OOT check. The GitHub Actions workflow must verify date coverage and create non-overlapping earlier-year train and later-year test partitions. If the source cannot support that split, the workflow fails and no OOT claim is made.

## Required work before any production-like claim

Time-based validation, tail sensitivity, fairness/proxy review, pricing-actuarial review, data lineage, operational monitoring, company-specific acceptance criteria and business-owner approval.
