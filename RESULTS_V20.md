# v0.20 — Final model-change approval results

v0.20 closes the current motor-insurance pricing workbench without adding a new model family. The four existing models are fitted once on the same temporal design and then reused for coverage, tail, transport and complexity audits.

**Final decision: HOLD / NO MODEL-FAMILY PROMOTION.**

## v0.16 — Coverage decomposition and reconciliation

The 2024 total loss target reconciles exactly to the coverage-level incurred components (floating-point reconciliation gap approximately `7.45e-09`). The main shares of 2024 incurred loss are:

- liability: **64.05%**;
- property damage: **25.84%**;
- glass: **5.99%**;
- theft: **1.86%**;
- legal protection: **1.52%**;
- occupants: **0.39%**;
- fire: **0.35%**.

Coverage-premium fields are used only to construct an audit coverage-exposure proxy; they remain excluded from the predictive feature set.

## v0.17 — Severity-tail audit

There are **21,264** positive-loss 2024 policy rows. Positive policy-loss quantiles are:

- p99: **15,522.76**;
- p99.5: **22,542.85**;
- p99.9: **59,641.99**;
- maximum: **571,128.32**.

The top 1% of positive-loss policy rows account for **20.52%** of total incurred; the top 0.5% account for **15.39%**. Removing these observations changes both deviance and aggregate calibration materially, so the project treats tail performance as a separate model-risk issue rather than hiding it through a single severity cap.

On the full untouched 2024 cohort:

- Tweedie GLM deviance **93.9318**, calibration **0.9531**;
- XGBoost Tweedie deviance **93.9513**, calibration **0.9336**.

## v0.18 — Transport uncertainty

300 policy bootstrap resamples quantify aggregate pure-premium calibration uncertainty by cohort.

| Cohort | GLM calibration (95% CI) | XGBoost calibration (95% CI) |
|---|---:|---:|
| Returning policies | 0.994 [0.954, 1.037] | 0.950 [0.910, 0.996] |
| New policies | 0.825 [0.703, 0.948] | 0.881 [0.748, 1.005] |
| New business (`NB`) | 0.861 [0.789, 0.938] | 0.917 [0.840, 0.997] |
| Existing/renewal business (`P`) | 1.037 [0.983, 1.086] | 0.949 [0.905, 0.991] |

The relative model advantage changes by cohort. The same model is not consistently closer to aggregate calibration 1.0 for both returning and new policies.

## v0.19 — Value for complexity

The GitHub-hosted runner measured fit time, 2024 inference time and serialised model size under the same run.

| Model | Fit seconds | Prediction ms / 1,000 policies | Serialised MB | 2024 deviance |
|---|---:|---:|---:|---:|
| Poisson GLM | 0.52 | 1.37 | 0.007 | 1.11854 |
| XGBoost Poisson | 1.26 | 4.61 | 0.724 | 1.11884 |
| Tweedie GLM | 6.76 | 1.36 | 0.007 | 93.9318 |
| XGBoost Tweedie | 1.48 | 4.96 | 0.799 | 93.9513 |

XGBoost Tweedie fits faster in this implementation, but it is approximately **111x larger** on disk and about **3.65x slower** for 2024 inference than the Tweedie GLM, while not improving locked OOT Tweedie deviance.

These timings are environment-specific diagnostics, not universal model benchmarks.

## v0.20 — Approval gates

All of the following are considered before a global model-family change:

- locked 2024 frequency bootstrap supports XGBoost: **false**;
- locked 2024 pure-premium bootstrap supports XGBoost: **false**;
- rolling-origin frequency support is consistent across windows: **false**;
- rolling-origin pure-premium support is consistent across windows: **false**;
- the same model is closer to calibration 1.0 for returning and new policies: **false**;
- XGBoost has lower locked 2024 pure-premium deviance: **false**;
- XGBoost pure-premium is more complex on model size or fit time: **true**.

Therefore:

> **HOLD / NO MODEL-FAMILY PROMOTION**

The decision prioritises stable expected-loss evidence, temporal repeatability, transport and value-for-complexity. Synthetic quote-conversion/proposition experiments are explicitly excluded from deployment evidence.

## Reproducibility

The network-enabled workflow `.github/workflows/v20-governance.yml` downloads and verifies the 354k-policy-year Mendeley source, rebuilds the locked OOT and rolling-origin evidence, runs v0.16–v0.20, and uploads the final artifact. Contract tests protect the temporal/leakage rules and prevent synthetic proposition metrics from entering the final approval rule.
