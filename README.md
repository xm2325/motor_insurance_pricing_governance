# Motor Insurance Pricing & Model Governance Workbench

A reproducible motor-insurance pricing project covering GLM and gradient-boosting benchmarks, expected-loss modelling, locked validation, monitoring, model-change governance and real calendar out-of-time (OOT) validation.

## Current validation status

The project now has two distinct evidence tracks.

### 1. freMTPL2 governance benchmark

The public French `freMTPL2` portfolio is used for the detailed model-governance workbench:

- Poisson GLM vs XGBoost claim-frequency modelling;
- Gamma severity and Tweedie / two-part expected-loss modelling;
- train / calibration / final-test separation;
- calibration, lift, segment stability and paired bootstrap uncertainty;
- shadow monitoring, PSI, unseen-category and severity-inflation stress tests;
- model-change disagreement, exact log-risk attribution and high-disagreement cohort investigation;
- explicitly synthetic Pricing & Proposition simulations kept separate from observed insurance outcomes.

The governance conclusion through v0.10 was **HOLD pending new OOT evidence**: XGBoost improved claim-frequency ranking on the cross-sectional benchmark, but the held-out expected-loss evidence did not identify a stable production challenger.

### 2. 2022–2024 Spanish motor calendar OOT

The main temporal validation track uses the public Mendeley dataset `sw4jmdb2sm` (version 1), a longitudinal Spanish motor portfolio with **354,140 policy-year rows and 47 variables** covering 2022–2024.

GitHub Actions downloads the source directly from Mendeley, records file hashes and sizes, verifies the 47-column schema, and runs the locked calendar split:

- **2022:** model training;
- **2023:** aggregate calibration only;
- **2024:** untouched OOT evaluation.

Current rating features include driver, vehicle and policy characteristics available without using the current outcome. The model feature set intentionally excludes `insured_id`, `year`, `policy_status`, all current premiums, all current claim counts, all current incurred losses and exposure as a predictive feature. Exposure is used only as the modelling weight / denominator.

#### Verified source audit

- Source rows: **354,140**
- Columns: **47**
- 2022 rows: **67,172**
- 2023 rows: **118,835**
- 2024 rows: **168,133**
- Main CSV: **94,710,312 bytes**
- Main CSV SHA-256: `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4`

The model run uses 354,091 rows after requiring positive exposure and valid outcomes.

#### 2024 OOT results

| Target | Reference | XGBoost challenger | OOT conclusion |
|---|---:|---:|---|
| Frequency: locked Poisson deviance | **1.11854** | 1.11884 | no stable XGB gain |
| Frequency: locked calibration ratio | 0.963 | 0.960 | both close to portfolio level |
| Frequency: top-10% exposure claim capture | 26.62% | **27.04%** | +0.42 pp ranking gain |
| Pure premium: locked Tweedie deviance | **93.9318** | 93.9513 | no stable XGB gain |
| Pure premium: locked calibration ratio | 0.953 | 0.934 | GLM closer to observed total |
| Pure premium: top-10% exposure loss capture | 20.44% | **21.13%** | +0.69 pp ranking gain |

The 250-resample OOT bootstrap did **not** support a stable deviance advantage for XGBoost:

- frequency GLM-minus-XGB deviance difference 95% interval: **[-0.00155, 0.00083]**;
- pure-premium GLM-minus-XGB Tweedie deviance difference 95% interval: **[-0.988, 0.856]**.

The automatic model-change rule therefore returns:

> **Frequency challenger: HOLD**  
> **Pure-premium challenger: HOLD**  
> **Overall: HOLD**

This is a useful result rather than a failed experiment: the challenger captures slightly more claims/loss in the highest-risk 10% of exposure, but that ranking gain does not translate into a statistically stable OOT deviance improvement.

#### Transport checks

Of the 168,085 usable 2024 policy-year rows, 105,307 policy IDs had appeared in 2022 or 2023 and 62,778 were new in 2024. Segment calibration is not uniform:

- existing-policy pure-premium calibration: GLM **0.994**, XGBoost **0.950**;
- new-policy pure-premium calibration: GLM **0.825**, XGBoost **0.881**.

This is another reason not to promote one model family from aggregate metrics alone.

## Reproduce the 2022–2024 OOT track

The normal route is GitHub Actions because the raw file is about 95 MB and is intentionally not committed to this repository.

Workflow:

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
```

Key persisted outputs:

```text
action_results/spanish_oot_2024/
  ACTION_RUN_STATUS_2024.json
  download_format_audit.json
  schema_data_audit.json
  oot_2024_summary.json
  oot_2024_model_decision.json
  oot_2024_frequency_model_comparison.csv
  oot_2024_pure_premium_model_comparison.csv
  oot_2024_bootstrap_deviance_differences.csv
  oot_2024_transport_segment_calibration.csv
```

## Legacy 2015–2018 temporal diagnostic

The earlier `spanish-oot.yml` workflow remains for audit history, but it is **not** the main OOT evidence. That older portfolio shows very large year-to-year changes in claim frequency and pure premium, especially in 2018, so it is retained as an example of why a mechanically time-ordered split is not automatically a reliable pricing validation set.

## Scope

This is a portfolio model-governance project, not a production pricing engine. It does not set real customer premiums and does not imply transfer to FIRST CENTRAL or the UK motor market. Pure-premium estimates do not include company-specific expenses, reinsurance, commercial adjustments or regulatory approval. Any synthetic proposition simulation is labelled separately from observed insurance outcomes.
