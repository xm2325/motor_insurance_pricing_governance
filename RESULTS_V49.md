# v0.49 — Model Change Impact Assessment Pack

## Purpose

v0.49 converts persisted model-risk evidence into a decision-ready aggregate pack. It does **not** add another model, dataset, performance threshold or retrospective candidate-selection exercise.

The review order is explicit:

1. **Evidence adequacy** — current status remains `EVIDENCE_GAP_HOLD`.
2. **Model impact review** — v0.47/v0.48 diagnostics are available, but are not promotion authority.
3. **Commercial/customer-pricing governance** — separate and currently out of scope/not authorised.

## Current evidence state

- required committee gates: **5/8 pass**;
- unresolved blockers: `G2_LOCKED_TEMPORAL_SUPPORT`, `G3_PREREGISTERED_EXTERNAL_SUPPORT`, `G4_FRESH_INDEPENDENT_EVIDENCE`;
- preregistered external target gates: **0/4 pass**;
- fresh independent validation currently available: **no**;
- model-family decision: `HOLD`;
- serving: `HOLD_SHADOW_ONLY`;
- promotion review: `NOT_OPEN`;
- customer-pricing change authorised: **false**.

Operational shadow deployment, rollback and attested admission controls remain demonstrated, but they cannot substitute for the three failed evidence gates.

## Impact evidence carried into the pack

### Frequency

- mean absolute frozen GLM/XGBoost log-score disagreement: **0.0993**;
- largest one-factor sensitivities: `vehicle_brand`, `policy_type`, `vehicle_value`;
- portfolio-neutral mean absolute technical-relativity redistribution: **10.18%**;
- exposure with absolute redistribution >10%: **36.81%**;
- exposure with absolute redistribution >20%: **10.98%**.

### Pure premium

- mean absolute frozen GLM/XGBoost log-score disagreement: **0.3171**;
- largest one-factor sensitivities: `business_type`, `power_to_weight_ratio`, `vehicle_value`;
- portfolio-neutral mean absolute technical-relativity redistribution: **32.28%**;
- exposure with absolute redistribution >10%: **78.26%**;
- exposure with absolute redistribution >20%: **58.17%**.

The selected major-segment table is generated from the persisted v0.48 aggregate segment artifact. Tiny-exposure extreme groups are not elevated into the committee headline.

## Numerical limitation

The frozen Tweedie GLM still reaches its existing `max_iter=900` limit. The registered v0.48 repeat-run envelope shows the descriptive headline is stable at the displayed precision, while bitwise or performance reproducibility is **not** claimed.

## Fail-closed design

`build_model_change_impact_assessment_v49.py` refuses to build the committee pack if decision-critical state changes, including:

- committee status is not `EVIDENCE_GAP_HOLD`;
- required gate count is no longer 5/8;
- blocker set is no longer G2/G3/G4;
- external-support state is no longer 0/4;
- fresh independent evidence becomes available;
- model-family decision stops being `HOLD`;
- pricing authority becomes true;
- v0.47 diagnostic top-driver headlines change.

Source SHA-256 values are recorded separately for lineage. They are not misrepresented as approval gates.

## Decision

`DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`

v0.49 does not clear G2/G3/G4, reopen model promotion, authorise a serving change, estimate customer premiums, claim commercial uplift or establish transfer to FIRST CENTRAL / the current UK motor market.
