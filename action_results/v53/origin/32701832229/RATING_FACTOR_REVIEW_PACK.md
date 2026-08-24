# Rating Factor Review Pack

This pack joins persisted aggregate evidence from v0.51 (development rating structure), v0.52 (label-free feature support/mix) and v0.49 (portfolio-neutral impact plus committee context). It does not access policy rows, refit a model, create a new performance/support gate, or authorise customer pricing.

## Executive review answer

The 2024 feature population is **not broadly outside the numeric support seen in 2022**. Strict out-of-range exposure is near zero for the main numeric factors. The larger monitoring issue is **portfolio reweighting among known rating cells**, especially business type. Separately, the frozen GLM and XGBoost encode materially different response shapes for supported factors such as driver age and vehicle age, and the portfolio-neutral impact evidence shows that model-family differences can materially redistribute technical risk even after aggregate predicted totals are forced equal.

None of that repairs the validation evidence gap: the committee state remains **`EVIDENCE_GAP_HOLD` (5/8)** with external support **0/4**, so model-family promotion review remains closed.

## 1. Rating structure: what shape did each frequency model learn?

### Driver age

v0.51 max absolute log-relativity gap: **0.26866**. Development median age is 47; the 2024 feature-population median is 49.

| Quantile | Driver age | GLM relativity | XGB relativity | XGB / GLM |
|---:|---:|---:|---:|---:|
| q05 | 30 | 0.880 | 1.013 | 1.152 |
| q50 | 47 | 1.000 | 1.000 | 1.000 |
| q95 | 68 | 1.172 | 0.896 | 0.764 |

Only **0.0016%** of 2024 exposure is outside the actual observed 2022 driver-age range; **8.75%** lies outside the 2022 q05–q95 interval. The structural disagreement is therefore mainly **within supported ages**, not broad extrapolation.

### Vehicle age

v0.51 max absolute log-relativity gap: **0.26771**. Development median is 23; 2024 median is 26.

| Quantile | Vehicle age | GLM relativity | XGB relativity | XGB / GLM |
|---:|---:|---:|---:|---:|
| q05 | 7 | 1.309 | 1.338 | 1.022 |
| q50 | 23 | 1.000 | 1.000 | 1.000 |
| q95 | 44 | 0.702 | 0.918 | 1.307 |

Strict 2024 out-of-range exposure is only **0.0008%**; q05–q95 tail exposure is **9.28%**.

`vehicle_value` is a counterexample: its model-family shape gap is only **0.03394**, despite **9.57%** of 2024 exposure lying outside the development q05–q95 interval. Flexibility does not imply a large response-shape difference for every factor.

## 2. Feature support and portfolio mix: is the current book unfamiliar?

For the main numeric rating factors, strict extrapolation outside observed 2022 min/max is negligible. The dominant change is categorical mix.

### Business type

Both business-type categories were seen in 2022, so unseen 2024 exposure is **0.0000%**. Yet total-variation distance is **48.60%**:

| Business type | 2022 exposure share | 2024 exposure share |
|---|---:|---:|
| NB | 96.78% | 48.18% |
| P | 3.22% | 51.82% |

The v0.51 **frequency** response-shape gap for business type is only **0.02571**. This is the opposite pattern from driver age: **small shape gap, very large portfolio-mix shift**.

### Vehicle brand

`BMW` represented **4.14%** of 2022 development exposure in the v0.51 displayed grid; GLM/XGB frequency relativities were **1.328 / 1.174**. In 2024 there are 6 brand levels absent from 2022, but together they represent only **0.0035%** of exposure; brand mix TV is **2.04%**.

## 3. Portfolio impact: if aggregate technical-risk level is fixed, how much redistribution remains?

The portfolio-neutral diagnostic forces GLM and XGBoost aggregate predicted technical-risk totals equal before comparison. Frequency still shows mean absolute relativity redistribution **10.18%**, with **36.81%** of exposure moving by more than ±10%.

Pure premium is more sensitive: mean absolute redistribution **32.28%**, **78.26%** exposure >±10% and **58.17%** >±20%. Business-type pure-premium total relativity shifts are approximately **NB 8.67% / P -6.53%**.

These are **technical-risk score redistributions, not customer premium changes**. v0.51 contains frequency response-shape analysis only; the pure-premium impact evidence comes from the separate frozen-model diagnostic summarised by v0.49.

## 4. Review matrix: do not collapse different risks into one score

| Question | Driver age | Business type | What it means |
|---|---|---|---|
| Do GLM/XGB frequency shapes differ? | Yes — gap 0.269 | Much less — gap 0.026 | Model-structure question |
| Is 2024 outside development support? | Strict extrapolation 0.0016% | Unseen exposure 0.0000% | Support question |
| Has portfolio weight shifted? | Median age 47 → 49 | TV 48.60%; NB/P almost reverse | Portfolio-mix question |
| Does this prove XGBoost is better? | No | No | Requires outcome-based validation evidence |

No composite score is created because these columns answer different questions and have different governance meanings.

## 5. Evidence adequacy still comes first

Current state: **`EVIDENCE_GAP_HOLD`**, **5/8** machine gates pass, external target support **0/4**, and there is no fresh independent validation asset. Blockers remain `G2_LOCKED_TEMPORAL_SUPPORT, G3_PREREGISTERED_EXTERNAL_SUPPORT, G4_FRESH_INDEPENDENT_EVIDENCE`.

The rating-factor review pack can explain **what differs, where the current book has shifted, and how large technical-risk redistribution could be**. It cannot establish which model is more accurate, clear the failed validation gates, open promotion review, or authorise a serving/customer-pricing change.

## Decision boundary

Current disposition remains **`HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`** and `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`. No FIRST CENTRAL/current UK transport, causal/fairness conclusion, realised premium effect or commercial uplift is claimed.
