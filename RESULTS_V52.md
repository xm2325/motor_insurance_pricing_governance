# v0.52 — Label-free rating-factor support and portfolio-mix audit

## Purpose

v0.51 showed that the frozen GLM and XGBoost frequency specifications can imply materially different **rating-factor response shapes** around the same 2022 development reference profile. v0.52 asks the next question without reopening validation outcomes:

> Is the 2024 feature population actually moving outside the 2022 development support, or is the larger issue a redistribution of exposure across rating cells that were already observed?

This distinction matters. A model can face little strict extrapolation while still seeing a very different portfolio mix. Conversely, a factor can show a large GLM/XGBoost shape difference even when the current portfolio remains well supported by development data.

v0.52 therefore keeps **shape gap**, **strict support**, **tail shift** and **categorical mix shift** separate. It does not combine them into a subjective score or create a new acceptance/alert threshold.

## Scope and data boundary

Actions run 32700628385 verified the initial implementation end to end using only lightweight support-audit dependencies; no sklearn or XGBoost import/model fit is required.

The audit reads only:

- the 14 registered rating features;
- `year`;
- `total_exposure`.

It reads **no claim-count outcomes, incurred losses, actual premiums, customer IDs or policy status**.

The two positive-exposure populations under this exact v0.52 filter are:

| Population | Rows | Exposure |
|---|---:|---:|
| 2022 development | **67,171** | **41,912.4959** |
| 2024 current feature population | **168,085** | **126,014.3644** |

Spanish 2024 remains `CONSUMED_RETROSPECTIVE_VALIDATION`. Reading its rating features for a label-free support diagnostic does not restore fresh validation status or create candidate-selection authority.

## Definitions: do not call every tail observation extrapolation

For numeric factors:

- **strict extrapolation** = a non-missing 2024 value below the observed 2022 minimum or above the observed 2022 maximum;
- **q01–q99 / q05–q95 tail shift** = 2024 exposure outside an exposure-weighted development central interval.

A q05–q95 tail observation is still within development support unless it also lies outside the actual 2022 observed range.

For categorical factors:

- **strict unseen** = a non-missing 2024 category absent from 2022 development;
- **mix shift** = change in exposure shares across the union of known levels, summarised descriptively with total-variation distance `0.5 * sum(abs(p_2024 - p_2022))`.

These are descriptive diagnostics, not insurer/regulatory thresholds.

## 1. Strict numeric extrapolation is negligible

Across the six numeric rating factors, 2024 exposure outside the actual 2022 observed range is tiny:

| Factor | v0.51 max abs log-relativity gap | 2024 outside 2022 observed range | 2024 outside 2022 q05–q95 | Median: 2022 → 2024 |
|---|---:|---:|---:|---:|
| `driver_age` | **0.26866** | **0.00159%** | 8.75% | 47 → 49 |
| `vehicle_age` | **0.26771** | **0.00079%** | 9.28% | 23 → 26 |
| `age_driving_licence` | 0.17069 | **0.00133%** | 4.48% | 21 → 20 |
| `vehicle_value` | 0.03394 | **0.00140%** | **9.57%** | 24,693.375 → 24,934.875 |
| `seats` | 0.07232 | **0.00000%** | 2.62% | 5 → 5 |
| `power_to_weight_ratio` | 0.06065 | **0.00227%** | 9.41% | 12 → 12 |

The largest strict out-of-range share is only about **0.0023%** of exposure (`power_to_weight_ratio`). This does not support a story that 2024 is broadly forcing the frequency models into unseen numeric space.

The q05–q95 figures tell a different but still moderate story: current exposure is redistributed within the known range, with `vehicle_value`, `power_to_weight_ratio` and `vehicle_age` each around 9–10% outside the 2022 central 90% interval. That is a tail/mix diagnostic, not strict extrapolation.

## 2. Large response-shape differences do not imply weak numeric support

The strongest v0.51 structural disagreements remain `driver_age` and `vehicle_age`, with max absolute log-relativity gaps **0.26866** and **0.26771**. Yet v0.52 finds only **0.00159%** and **0.00079%** of 2024 exposure outside their 2022 observed ranges.

This is an important model-risk distinction:

> The model families disagree about the *technical-risk response shape* for supported driver/vehicle ages; the issue is not that the 2024 portfolio is mostly extrapolating beyond development ages.

That makes the v0.51 curves relevant for interpretability review, but it still does not say which curve is more accurate or suitable for customer pricing.

## 3. The major shift is categorical portfolio mix, especially business type

`business_type` is the dominant categorical mix change under the exact v0.52 positive-exposure filter:

| Business type | 2022 exposure share | 2024 exposure share | Change |
|---|---:|---:|---:|
| `NB` | **96.78%** | **48.18%** | **−48.60 pp** |
| `P` | **3.22%** | **51.82%** | **+48.60 pp** |

The resulting total-variation distance is **48.60%**. Both levels were already present in 2022, so strict unseen exposure is **0%**.

This result is recomputed from the v0.52 filter and should not be substituted mechanically for older monitoring percentages that used different replay/baseline constructions. The stable qualitative conclusion is that business-type drift is primarily a **large reweighting of known categories**, not appearance of a new category.

Other categorical mix distances are much smaller:

| Factor | Total-variation distance | Largest level shift | Unseen 2024 exposure |
|---|---:|---|---:|
| `business_type` | **48.60%** | `NB`: 96.78% → 48.18% | 0.0000% |
| `payment_frequency` | 5.29% | `A`: 77.90% → 83.19% | 0.0000% |
| `policy_type` | 3.88% | `COMP_E`: 23.75% → 27.16% | 0.0000% |
| `vehicle_brand` | 2.04% | `RENAULT`: 9.94% → 9.53% | **0.00345%** |
| `municipality_type` | 2.03% | `I`: 62.89% → 64.92% | 0.0000% |
| `bonus_score` | 1.89% | `G`: +1.89 pp | 0.0000% |
| `fuel_type` | 0.41% | `G`: −0.41 pp | 0.0000% |
| `circulation_area` | 0.17% | `R`: −0.17 pp | 0.0000% |

## 4. Unseen categorical exposure is also negligible

Only `vehicle_brand` introduces non-missing 2024 levels absent from 2022: **6 brands**, together only **0.00345%** of 2024 exposure.

The largest unseen brands by exposure are `MG`, `ASIA MOTORS` and `LIGIER`, each individually below **0.001%** exposure. The machine artifact retains every aggregated level, but these rare additions are not promoted over the much larger known-category reweighting.

Thus the strongest categorical monitoring story is again **mix shift among seen cells**, not broad unseen-category exposure.

## 5. v0.51 shape gap and v0.52 support/mix must stay side by side

Two examples show why no composite score is created:

- `driver_age`: **large model-family shape gap (0.26866)**, but only **0.00159% strict numeric extrapolation**;
- `business_type`: **small v0.51 frequency shape gap (0.02571)**, but **48.60% categorical total-variation shift**.

A single scalar “risk” score would hide the fact that these are different questions:

1. **model-structure question:** do GLM and XGBoost encode the factor differently?
2. **data-support question:** is the current book outside development support?
3. **portfolio-mix question:** have known rating cells changed weight materially?
4. **performance question:** does either model predict outcomes better? — not answered by v0.52.

This separation is more useful for a real pricing/model-risk review than an arbitrary weighted blend.

## What v0.52 adds to the insurance story

The project can now describe a coherent chain:

- v0.51: **what rating structure did each model learn?**
- v0.52: **does the current portfolio still sit inside development support, and where has the rating mix moved?**
- v0.48: **if aggregate technical-risk totals are neutralised, how differently would the frozen model families redistribute technical risk?**
- v0.44/v0.49: **is there enough validation evidence even to open model-family promotion review?**

The answer remains that impact/interpretability/monitoring evidence can be important while validation evidence is still insufficient for promotion.

## Governance boundary

v0.52 changes no historical decision:

- model-family decision: **`HOLD`**;
- serving: **`HOLD_SHADOW_ONLY`**;
- committee readiness: **`EVIDENCE_GAP_HOLD`**;
- candidate selection: **not allowed from this diagnostic**;
- model promotion: **not authorised**;
- customer pricing: **not authorised**.

No claim is made that v0.52 establishes predictive performance, causal/fair rating effects, current UK/FIRST CENTRAL transport, customer premium impact, profit or conversion uplift.
