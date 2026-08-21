# Motor Insurance Pricing & Model Governance Workbench

A reproducible insurance data-science case study asking one practical question:

> **Does a more flexible ML challenger improve the pricing target reliably enough, across time and customer cohorts, to justify replacing a GLM?**

## 30-second result

| Evidence | Result |
|---|---|
| Cross-sectional frequency benchmark | XGBoost reduced Poisson deviance by **5.43%** and increased top-10% claim capture from **20.59% to 31.17%** |
| Real longitudinal source | **354,140 Spanish motor policy-years**, 47 variables, 2022-2024 |
| Locked temporal design | **2022 train -> 2023 calibration -> 2024 untouched OOT** |
| 2024 frequency result | XGBoost top-10% claim capture **26.62% -> 27.04%**, but locked deviance **1.11884 vs GLM 1.11854** |
| 2024 uncertainty | 250-bootstrap GLM-minus-XGB deviance CI **[-0.00155, 0.00083]** |
| Rolling-origin result | With 2022+2023 training, XGBoost frequency deviance improved by only **~0.32%** |
| Pure-premium result | No stable XGBoost advantage; rolling-origin Tweedie deviance **93.1606 vs GLM 92.8213** |
| Model-family decision | **HOLD / NO PROMOTION** |

The project deliberately does **not** turn a favourable ranking metric into a deployment claim. The challenger can improve frequency ranking, but that improvement is not consistent across time windows and does not translate into stable pure-premium superiority.

**Start here:** [Interview Evidence Pack](INTERVIEW_EVIDENCE_PACK.md) | [Evidence Registry](EVIDENCE_REGISTRY.md) | [Model Card](MODEL_CARD.md) | [v0.13 locked OOT results](RESULTS_V13.md) | [v0.14 rolling-origin results](RESULTS_V14.md)

---

## Why this project exists

Motor pricing is a useful example of a broader model-governance problem: a complex challenger can look strong on one benchmark but still fail to justify a model change once calibration, expected loss, temporal stability and customer-population transport are considered.

The workbench therefore separates three questions:

1. **Can the challenger predict/rank risk better?**
2. **Does the improvement survive a genuinely later period?**
3. **Is the improvement strong enough on the pricing target to justify promotion?**

## Evidence track 1 - freMTPL2 governance benchmark

The public French `freMTPL2` portfolio is used for the detailed modelling and governance workbench:

- Poisson GLM vs XGBoost claim-frequency modelling;
- Gamma severity and Tweedie / two-part expected-loss modelling;
- train / calibration / final-test separation;
- calibration, lift, segment stability and paired bootstrap uncertainty;
- shadow monitoring, PSI, unseen-category and severity-inflation stress tests;
- model-change disagreement and high-disagreement cohort investigation;
- explicitly synthetic Pricing & Proposition simulations kept separate from observed outcomes.

On the full frequency benchmark, XGBoost reduced weighted Poisson deviance by **5.43%** relative to the comparable Poisson GLM and increased claims captured in the highest-risk 10% of exposure by **10.58 percentage points**. The persisted benchmark values are in `results/fremtpl2_full_frequency_benchmark.csv`.

That result justified building a challenger. It did not by itself justify deployment.

## Evidence track 2 - 2022-2024 real calendar OOT

The main temporal validation track uses public Mendeley dataset `sw4jmdb2sm` (version 1), containing **354,140 policy-year rows and 47 variables** from one Spanish motor insurer.

GitHub Actions:

1. discovers the Mendeley files;
2. downloads the 94.7 MB raw CSV over the runner network;
3. records file size and SHA-256;
4. verifies the 47-column schema and calendar-year counts;
5. runs the locked OOT modelling workflow;
6. persists results back under `action_results/spanish_oot_2024/`.

### Leakage-controlled feature policy

The predictive feature set intentionally excludes:

- `insured_id` and `year`;
- `policy_status` because its within-year timing may be post-period;
- all current premium fields;
- all current claim-count fields;
- all current incurred-loss fields;
- exposure as a predictive feature.

Exposure is used only as the modelling weight / denominator.

### Locked design

- **2022:** model training
- **2023:** aggregate calibration only
- **2024:** untouched OOT evaluation

No 2024 outcome is used to fit the model or the calibration scale.

### Locked 2024 results

| Target | GLM reference | XGBoost challenger | Interpretation |
|---|---:|---:|---|
| Frequency Poisson deviance | **1.11854** | 1.11884 | no deviance gain |
| Frequency calibration ratio | 0.963 | 0.960 | both close in aggregate |
| Top-10% claim capture | 26.62% | **27.04%** | +0.42 pp ranking gain |
| Pure-premium Tweedie deviance | **93.9318** | 93.9513 | no deviance gain |
| Pure-premium calibration ratio | **0.953** | 0.934 | GLM closer in aggregate |
| Top-10% loss capture | 20.44% | **21.13%** | +0.69 pp ranking gain |

The 250-resample bootstrap does not support a stable XGBoost deviance advantage:

- frequency 95% interval: **[-0.00155, 0.00083]**;
- pure-premium 95% interval: **[-0.988, 0.856]**.

Automatic decision: **HOLD** for both challengers.

## Evidence track 3 - v0.14 rolling-origin temporal stability

Rolling-origin evaluation is a stability diagnostic. It does not replace or recalibrate the locked 2024 test.

### 2022 -> 2023

- Frequency deviance: GLM **1.13619**, XGBoost 1.13646
- Frequency bootstrap CI crosses zero
- Pure-premium deviance: GLM **92.6970**, XGBoost 93.2707
- Pure-premium bootstrap CI crosses zero

No stable XGBoost advantage.

### 2022+2023 -> 2024

- Frequency deviance: GLM 1.11199, XGBoost **1.10843**
- Relative XGBoost reduction: **~0.32%**
- Frequency bootstrap CI: **[0.00236, 0.00513]** for GLM-minus-XGB deviance
- Pure-premium deviance: GLM **92.8213**, XGBoost 93.1606
- XGBoost pure-premium calibration: **0.842**
- Pure-premium bootstrap CI crosses zero

The updated training window produces a small stable frequency gain, but still does not support a pricing-model family change.

## New vs returning policy transport

Of the 168,085 usable 2024 policy-years:

- 105,307 policy IDs appeared in 2022 or 2023;
- 62,778 were new in 2024.

Pure-premium calibration differs by cohort:

- returning: GLM **0.994**, XGBoost **0.950**;
- new: GLM **0.825**, XGBoost **0.881**.

The relative model performance therefore changes by customer-population transport. Aggregate calibration alone is not enough for a global model-family decision.

## Current decision

> **KEEP HOLD / NO MODEL-FAMILY PROMOTION.**

The challenger can show a frequency advantage when trained on more recent data, but that advantage is not repeatable across every temporal window and does not translate into stable pure-premium superiority. The project therefore requires expected-loss performance, calibration, uncertainty and cohort transport to support a model change - not a single favourable ranking metric.

## Auditable claims

`EVIDENCE_REGISTRY.md` maps every headline claim to its persisted result file. `tests/test_evidence_registry.py` recomputes the main CV/README figures and fails CI if the evidence no longer supports them.

The lightweight contract tests also protect the leakage and temporal split rules.

## Reproduce the main track

The normal route is GitHub Actions because the raw Mendeley file is intentionally not committed.

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
python run_rolling_origin_v14.py
```

## Repository map

```text
README.md                         recruiter / reviewer entry point
INTERVIEW_EVIDENCE_PACK.md        short explanation and likely interview questions
EVIDENCE_REGISTRY.md              headline claims -> persisted evidence
MODEL_CARD.md                     intended use, limits and decision rules
RESULTS_V10.md                    held-out disagreement investigation
RESULTS_V13.md                    locked 2022/2023/2024 OOT results
RESULTS_V14.md                    rolling-origin stability results
run_spanish_oot_2024.py           locked calendar OOT pipeline
run_rolling_origin_v14.py         temporal stability audit
action_results/spanish_oot_2024/  persisted GitHub Actions evidence
tests/                            leakage, calendar and evidence-registry checks
```

## Scope

This is a portfolio model-governance project, not a production pricing engine. It does not set real customer premiums and does not establish transfer to FIRST CENTRAL or the UK motor market. Pure-premium estimates do not include company-specific expenses, reinsurance, commercial adjustments or regulatory approval. Synthetic proposition simulations are labelled separately from observed insurance outcomes.
