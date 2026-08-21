# v0.10 — Held-out model-change investigation

v0.10 asks a narrower question than v0.8-v0.9: after explaining **why** the reference and challenger disagree, do the already locked final-test outcomes show **which direction is more credible**?

The analysis reuses the 23,675-policy final-test predictions from v0.6-v0.9. It does **not** refit, recalibrate, select a threshold, or change either model using final-test outcomes.

## Risk-decile ordering

| Diagnostic | Reference | Candidate |
|---|---:|---:|
| Spearman correlation between decile order and observed pure premium | 0.818 | 0.770 |
| Actual loss captured in highest-risk 10% exposure | 17.886% | 17.891% |

The candidate does not produce a clear expected-loss ranking gain over the reference on this final-test portfolio. This differs from the earlier claim-frequency result, where XGBoost clearly improved frequency deviance and claim capture.

## Non-overlapping top-risk selections

The two models share only 35.3% weighted overlap in their top-risk selections.

| Cohort | Observed pure premium |
|---|---:|
| Both models' top-risk set | 267.52 |
| Candidate-only top-risk | 195.18 |
| Reference-only top-risk | 195.12 |
| Neither | 114.48 |

The point difference between candidate-only and reference-only is only +0.06. Across 1,000 policy bootstrap resamples, the 95% interval is [-94.80, 94.79].

## Extreme disagreement

For the 10% of exposure with the largest absolute candidate/reference log prediction ratio:

- reference Tweedie deviance: 79.87;
- candidate Tweedie deviance: 80.35;
- point delta (reference minus candidate): -0.48;
- 500-bootstrap 95% interval: [-9.36, 11.01].

## Outcome evidence within attribution-dominant cohorts

| Dominant disagreement component | Reference - candidate deviance | 95% bootstrap interval |
|---|---:|---:|
| Direct-vs-two-part baseline | +1.93 | [-0.39, 4.82] |
| Frequency model | -2.46 | [-5.81, 0.89] |
| Severity relativity | -0.21 | [-1.86, 1.28] |

Every interval crosses zero. The diagnostics are useful, but they are not evidence for selecting a new global model using the same final-test sample.

## Decision

**KEEP HOLD / REQUIRE NEW OUT-OF-TIME EVIDENCE.**

The next valid evidence should come from a genuinely later portfolio, a separate frozen holdout, or production shadow data collected under a pre-specified validation plan. v0.11 implements the first of these using a second public Spanish motor portfolio with renewal dates and a GitHub Actions calendar OOT workflow.
