# v0.43 Model-Family Review Pack

## Executive decision

**HOLD / HOLD_SHADOW_ONLY. Promotion review is NOT OPEN.**

The project has a strong cross-sectional XGBoost frequency benchmark signal, but that signal does not survive as a consistent, preregistered promotion case across the locked Spanish OOT and two independent external portfolios. Both Australian registered external gates fail and both Belgian registered external gates fail. Belgian negative decisions reproduce within the preregistered numerical tolerances.

## Evidence matrix

| Portfolio / evidence source | Target | XGB relative deviance improvement | Registered gate | Registered decision |
|---|---|---:|---|---|
| freMTPL2 | frequency | +5.4274% | n/a | DEVELOPMENT_BENCHMARK_ONLY |
| Spanish insurer 2024 | frequency | -0.0267% | FAIL | HOLD |
| Spanish insurer 2024 | pure_premium | -0.0208% | FAIL | HOLD |
| Australian ausprivauto0405 | frequency | -0.3849% | FAIL | NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT |
| Australian ausprivauto0405 | pure_premium | +11.4639% | FAIL | NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT |
| Belgian beMTPL97 | frequency | +0.2910% | FAIL | NO_SECOND_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT |
| Belgian beMTPL97 | pure_premium | +0.3219% | FAIL | NO_SECOND_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT |

## Why HOLD is the evidence-consistent decision

- freMTPL2 is development/benchmark evidence; it cannot authorise promotion.
- Spanish 2024 was independent at first locked OOT use and did not support a global challenger switch; it is now consumed retrospective validation.
- Australian `ausprivauto0405` was preregistered before row-level access. Frequency favoured GLM; pure premium had a favourable XGB point estimate but failed bootstrap confirmation. The portfolio is now consumed external validation.
- Belgian `beMTPL97` was preregistered before row-level access. Frequency had a small positive XGB direction but missed the fixed 0.5% materiality gate; pure premium failed point/CI support. Both negative decisions reproduced across the two completed observed Actions runs within registered tolerance. The portfolio is now consumed external validation.
- No preregistered independent external target gate has passed.

## What would reopen promotion review

- A genuinely new independent external dataset or new independent period whose row-level outcomes have not been inspected in this project.
- Protocol merged before row-level outcome access with source, split, features, models, metrics, gates, solver/tolerance and reproducibility rules fixed prospectively.
- Any positive external-support result must satisfy its registered model-performance gates.
- Any positive external-support result must satisfy the prospective two-independent-Actions execution and registered numerical reproducibility requirement inherited from v0.38-v0.42.
- A separate authorised governance decision would still be required before any serving-bundle or customer-pricing change.

## Interpretation boundaries

- This is an aggregate evidence-synthesis and model-risk dossier; it does not fit or tune models.
- No pooled meta-analysis or evidence-weighting score is used because the portfolios differ materially in geography, period, features and context.
- HOLD does not mean XGBoost is universally inferior; it means current evidence does not support promotion under the registered project contracts.
- Nothing here establishes transport to FIRST CENTRAL or the current UK motor market.
