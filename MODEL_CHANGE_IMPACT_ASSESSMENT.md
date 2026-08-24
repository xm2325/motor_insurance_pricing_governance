# Model Change Impact Assessment

**Current disposition: `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`.**

This pack is generated from persisted aggregate evidence. It does not access policy rows, refit a model, create a new performance gate, or authorise customer pricing.

## 1. Evidence adequacy comes first

The machine committee gate remains **`EVIDENCE_GAP_HOLD`** with **5/8** required gates passing. The unresolved blockers are `G2_LOCKED_TEMPORAL_SUPPORT, G3_PREREGISTERED_EXTERNAL_SUPPORT, G4_FRESH_INDEPENDENT_EVIDENCE`. Preregistered external support is **0/4**, and no fresh independent validation asset is currently available.

Operational shadow controls are demonstrated, but they cannot compensate for failed validation-evidence gates. Human sign-off is not recorded and cannot override failed evidence gates in this project contract.

## 2. Impact evidence is diagnostic, not promotion authority

For frequency, frozen GLM/XGBoost disagreement has exposure-weighted mean absolute log-ratio **0.0993**. After portfolio-neutral alignment, mean absolute technical-relativity redistribution is **10.18%**; **36.81%** of exposure moves by more than ±10% and **10.98%** by more than ±20%.

For pure premium, mean absolute log-ratio disagreement is **0.3171**. After portfolio-neutral alignment, mean absolute redistribution is **32.28%**; **78.26%** of exposure moves by more than ±10% and **58.17%** by more than ±20%.

Largest one-factor disagreement sensitivities are descriptive only: frequency is led by `vehicle_brand`, `policy_type`, `vehicle_value`; pure premium by `business_type`, `power_to_weight_ratio`, `vehicle_value`. These are non-additive, non-causal sensitivities, not SHAP values or predictive feature importance.

### Major segment redistribution

| Dimension | Group | Exposure share | Frequency relativity shift | Pure-premium relativity shift |
|---|---:|---:|---:|---:|
| business_type | NB | 48.18% | 1.04% | 8.67% |
| business_type | P | 51.82% | -0.91% | -6.53% |
| policy_type | COMP_E | 27.16% | 1.19% | 13.68% |
| policy_type | CC | 56.93% | -0.29% | -9.27% |
| driver_age_band | 35-49 | 42.01% | -2.72% | 5.20% |
| driver_age_band | 50-64 | 34.48% | 0.99% | -5.49% |

These are technical-risk score redistributions, not segment accuracy, fairness, causality or realised customer-price effects.

## 3. Numerical limitation is retained

The frozen Tweedie GLM still reaches its registered `max_iter=900` limit. Same-head repeat runs show the descriptive pure-premium redistribution headline is stable at the reporting precision used here, but bitwise reproducibility is not claimed.

## 4. Required review order

1. Resolve G2/G3/G4 using genuinely new prospectively governed evidence; v0.47/v0.48 cannot clear these blockers.
2. If evidence adequacy is later achieved, explicitly review model-family disagreement drivers and portfolio-neutral redistribution before any serving change.
3. Evaluate pricing/commercial components separately; technical-risk relativity is not a customer premium.
4. Require separate authorised governance for any serving-bundle or customer-pricing action.

## Decision boundary

The current decision remains **`HOLD / HOLD_SHADOW_ONLY / EVIDENCE_GAP_HOLD`**. This pack does not reopen model-family promotion, authorise a serving change, estimate a customer premium, claim commercial uplift, or establish transfer to FIRST CENTRAL / the current UK motor market.

Source hashes are recorded in `results_v49/model_change_impact_assessment_v49.json` so this document fails closed if the persisted evidence it summarises changes.
