# Motor Insurance Pricing & Model Governance Workbench

A reproducible motor-insurance pricing project covering GLM and gradient-boosting benchmarks, expected-loss modelling, locked validation, monitoring, model-change governance, real calendar out-of-time (OOT) validation and rolling-origin temporal stability checks.

## Evidence tracks

### 1. freMTPL2 governance benchmark

The public French `freMTPL2` portfolio is used for the detailed model-governance workbench:

- Poisson GLM vs XGBoost claim-frequency modelling;
- Gamma severity and Tweedie / two-part expected-loss modelling;
- train / calibration / final-test separation;
- calibration, lift, segment stability and paired bootstrap uncertainty;
- shadow monitoring, PSI, unseen-category and severity-inflation stress tests;
- model-change disagreement, exact log-risk attribution and high-disagreement cohort investigation;
- explicitly synthetic Pricing & Proposition simulations kept separate from observed insurance outcomes.

The cross-sectional benchmark shows that XGBoost can improve claim-frequency ranking materially, but the detailed expected-loss evidence did not justify model-family promotion on that portfolio.

### 2. 2022-2024 Spanish motor real calendar OOT

The main temporal validation track uses public Mendeley dataset `sw4jmdb2sm` (version 1), a longitudinal Spanish motor portfolio with **354,140 policy-year rows and 47 variables** covering 2022-2024.

GitHub Actions downloads the source directly from Mendeley, records file hashes and sizes, verifies the 47-column schema, and runs the locked split:

- **2022:** model training;
- **2023:** aggregate calibration only;
- **2024:** untouched OOT evaluation.

The feature set uses selected driver, vehicle and policy characteristics. It intentionally excludes `insured_id`, `year`, `policy_status`, all current premiums, all current claim counts, all current incurred losses and exposure as a predictive feature. Exposure is used only as modelling weight / denominator.

#### Verified source audit

- Source rows: **354,140**
- Columns: **47**
- 2022 rows: **67,172**
- 2023 rows: **118,835**
- 2024 rows: **168,133**
- Main CSV: **94,710,312 bytes**
- SHA-256: `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4`

The locked model run uses 354,091 rows after requiring positive exposure and valid outcomes.

#### Locked 2024 OOT results

| Target | Reference | XGBoost challenger | Conclusion |
|---|---:|---:|---|
| Frequency: Poisson deviance | **1.11854** | 1.11884 | no stable XGB gain |
| Frequency: calibration ratio | 0.963 | 0.960 | both close at portfolio level |
| Frequency: top-10% claim capture | 26.62% | **27.04%** | +0.42 pp ranking gain |
| Pure premium: Tweedie deviance | **93.9318** | 93.9513 | no stable XGB gain |
| Pure premium: calibration ratio | **0.953** | 0.934 | GLM closer to observed total |
| Pure premium: top-10% loss capture | 20.44% | **21.13%** | +0.69 pp ranking gain |

The 250-resample OOT bootstrap does **not** support a stable deviance advantage for XGBoost:

- frequency GLM-minus-XGB deviance 95% interval: **[-0.00155, 0.00083]**;
- pure-premium GLM-minus-XGB Tweedie deviance 95% interval: **[-0.988, 0.856]**.

The automatic model-change decision is therefore:

> **Frequency challenger: HOLD**  
> **Pure-premium challenger: HOLD**  
> **Overall: HOLD**

### 3. v0.14 rolling-origin temporal stability

v0.14 adds two one-year-ahead model-family checks. These are deliberately separate from the locked deployment gate above and do not use 2024 outcomes to recalibrate the v0.13 result.

#### 2022 train -> 2023 test

Frequency Poisson deviance:

- GLM: **1.13619**
- XGBoost: 1.13646
- 200-bootstrap GLM-minus-XGB interval: **[-0.00189, 0.00095]**

No stable XGBoost frequency advantage is present in this window.

Pure-premium Tweedie deviance:

- GLM: **92.6970**
- XGBoost: 93.2707
- bootstrap interval: **[-2.149, 0.880]**

Again, no stable XGBoost expected-loss advantage.

#### 2022+2023 train -> 2024 test

Frequency Poisson deviance:

- GLM: 1.11199
- XGBoost: **1.10843**
- top-10% claim capture: 26.98% vs **27.42%**
- 200-bootstrap GLM-minus-XGB interval: **[0.00236, 0.00513]**

After adding 2023 to training, XGBoost shows a small but stable frequency advantage. The relative deviance reduction is only about **0.32%**.

Pure-premium Tweedie results remain less favourable to XGBoost:

- GLM deviance: **92.8213**, calibration 0.948
- XGBoost deviance: 93.1606, calibration 0.842
- bootstrap interval: **[-0.793, 0.160]**

The frequency gain therefore does not justify a pricing-model family change.

## Transport checks

Of the 168,085 usable 2024 policy-year rows:

- 105,307 policy IDs had appeared in 2022 or 2023;
- 62,778 were new in 2024.

Pure-premium calibration differs by transport cohort:

- existing-policy calibration: GLM **0.994**, XGBoost **0.950**;
- new-policy calibration: GLM **0.825**, XGBoost **0.881**.

An illustrative `[0.85, 1.15]` diagnostic is used only to expose transport differences. It is not a FIRST CENTRAL or regulatory threshold.

## Current model-governance conclusion

**KEEP HOLD / NO MODEL-FAMILY PROMOTION.**

The challenger can show a frequency advantage when trained on more recent data, but that advantage is not consistent across temporal windows and does not translate into stable pure-premium superiority. Model-family promotion therefore remains conditional on expected-loss performance, calibration and transport rather than a single frequency ranking metric.

## Reproduce the 2022-2024 track

The normal route is GitHub Actions because the raw file is about 95 MB and is intentionally not committed.

```text
.github/workflows/spanish-oot-2024.yml
```

Local equivalent with network access:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python discover_spanish_motor_2022_2024.py
python download_spanish_motor_2022_2024.py
python audit_spanish_motor_2022_2024.py
python run_spanish_oot_2024.py
python run_rolling_origin_v14.py
```

Key persisted outputs are under:

```text
action_results/spanish_oot_2024/
```

including the source audit, locked OOT model comparisons, bootstrap results, transport calibration and v0.14 rolling-origin summary.

## CI

`tests/test_oot_contract.py` statically protects the temporal and leakage contract. Lightweight GitHub Actions CI checks that current premiums/outcomes/post-period fields are not reintroduced to the feature set and that rolling-origin windows use only prior years.

## Legacy 2015-2018 diagnostic

The older renewal-cohort dataset remains only for audit history. Its 2018 outcome development is materially different from prior years, so it is not used as the main pricing OOT evidence.

## Scope

This is a portfolio model-governance project, not a production pricing engine. It does not set real customer premiums and does not imply transfer to FIRST CENTRAL or the UK motor market. Pure-premium estimates do not include company-specific expenses, reinsurance, commercial adjustments or regulatory approval. Synthetic proposition simulations are labelled separately from observed insurance outcomes.
