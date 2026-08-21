# v0.14 - Rolling-origin temporal stability and portfolio transport gates

## Purpose

v0.14 is a temporal model-family stability check on the 354,140-policy-year Spanish motor portfolio. It does **not** replace or retune the locked v0.13 deployment gate (`2022 train -> 2023 calibration -> 2024 untouched OOT`).

Two one-year-ahead windows are evaluated without using future-year calibration:

1. `2022 train -> 2023 test`
2. `2022+2023 train -> 2024 test`

The same leakage-controlled rating feature set is used throughout; current premium, current claims/loss, `policy_status`, `insured_id` and `year` are not model inputs.

## Frequency results

### 2022 -> 2023

| Model | Poisson deviance | Calibration | Top-10% claim capture |
|---|---:|---:|---:|
| Poisson GLM | 1.13619 | 0.988 | 24.95% |
| XGBoost Poisson | 1.13646 | 0.973 | 24.89% |

200-bootstrap GLM-minus-XGBoost deviance difference:

- mean: -0.00043
- 95% CI: [-0.00189, 0.00095]

There is no stable XGBoost advantage in the 2023 test year.

### 2022+2023 -> 2024

| Model | Poisson deviance | Calibration | Top-10% claim capture |
|---|---:|---:|---:|
| Poisson GLM | 1.11199 | 0.976 | 26.98% |
| XGBoost Poisson | **1.10843** | 0.971 | **27.42%** |

200-bootstrap GLM-minus-XGBoost deviance difference:

- mean: +0.00355
- 95% CI: [0.00236, 0.00513]
- P(diff > 0): 1.00

After adding 2023 to training, XGBoost has a small but stable frequency advantage. The relative deviance reduction is only about 0.32%, so this is evidence of a modest frequency gain, not a pricing-model promotion result.

## Pure-premium results

### 2022 -> 2023

| Model | Tweedie deviance | Calibration | Top-10% loss capture |
|---|---:|---:|---:|
| Tweedie GLM | **92.6970** | 1.094 | 20.80% |
| XGBoost Tweedie | 93.2707 | 0.828 | **20.99%** |

The bootstrap interval for GLM-minus-XGBoost Tweedie deviance crosses zero: [-2.149, 0.880].

### 2022+2023 -> 2024

| Model | Tweedie deviance | Calibration | Top-10% loss capture |
|---|---:|---:|---:|
| Tweedie GLM | **92.8213** | **0.948** | 22.01% |
| XGBoost Tweedie | 93.1606 | 0.842 | **22.77%** |

The bootstrap interval again crosses zero: [-0.793, 0.160]. XGBoost ranks a little more loss into the top 10%, but has worse deviance and materially lower portfolio calibration.

## New vs existing policy transport

Using the locked v0.13 2024 predictions:

| 2024 cohort | GLM loss calibration | XGBoost loss calibration |
|---|---:|---:|
| Seen in 2022/2023 | **0.994** | 0.950 |
| New in 2024 | 0.825 | **0.881** |

An illustrative [0.85, 1.15] portfolio diagnostic is used only to expose transport differences; it is **not** a FIRST CENTRAL or regulatory threshold. Under that diagnostic, both models are acceptable on existing business, while the GLM misses the lower bound on new business. This does not override the model-family decision because expected-loss evidence is still inconsistent across windows.

## Decision

**KEEP HOLD / NO MODEL-FAMILY PROMOTION.**

The frequency challenger shows a small advantage only after the training window is expanded to include 2023. That gain does not consistently appear in the earlier temporal window and does not translate into a stable pure-premium advantage. The v0.13 locked OOT gate also remains uncleared.

The correct interpretation is therefore:

> frequency ranking can improve after more recent training data is included, but model-family promotion must be based on stable expected-loss performance, calibration and transport - not a single frequency metric.
