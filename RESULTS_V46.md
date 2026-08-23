# v0.46 — Model Risk Inventory and Model Card Reconciliation

## Why this version exists

The repository front door was current through v0.44, but `MODEL_CARD.md` still described Spanish 2024 as an untouched final OOT holdout and listed only the earlier French/Spanish evidence sources. That contradicted the validation-use firewalls and the later Australian/Belgian external evidence.

v0.46 fixes the state inconsistency without adding a model, changing a historical threshold, reopening a consumed validation set or accessing row-level data.

## Machine-readable inventory

`build_model_risk_inventory_v46.py` reconciles persisted evidence into one current inventory covering:

- the four GLM/XGBoost shadow model artifacts;
- Spanish/Australian/Belgian validation-asset roles at first use and now;
- the current external-evidence count;
- shadow deployment, rollback and attested-admission controls;
- Model Change Committee readiness and blockers;
- the current HOLD / HOLD_SHADOW_ONLY / NOT_OPEN decision.

The inventory is aggregate-only and reads existing persisted evidence. It performs **no model fit, calibration, row-level validation access, retuning or resplitting**.

## Current reconciled state

### Models

Four artifacts remain in shadow-comparison scope:

- Poisson GLM frequency reference;
- XGBoost Poisson frequency challenger;
- Tweedie GLM pure-premium reference;
- XGBoost Tweedie pure-premium challenger.

No artifact is authorised for customer-pricing use.

### Validation assets

| Dataset | First-use role | Current role | Fresh candidate-selection evidence? |
|---|---|---|---|
| Spanish 2024 | `LOCKED_OOT_FIRST_USE` | `CONSUMED_RETROSPECTIVE_VALIDATION` | No |
| Australian `ausprivauto0405` | independent external first use | `CONSUMED_EXTERNAL_VALIDATION_DATASET` | No |
| Belgian `beMTPL97` | independent external first use | `CONSUMED_EXTERNAL_VALIDATION_DATASET` | No |

### Evidence

- external portfolios evaluated: **2**;
- preregistered external target gates evaluated: **4**;
- preregistered external target gates passed: **0**;
- fresh independent validation assets currently available: **0**;
- pooled meta-analysis used: **no**;
- subjective evidence weighting used: **no**.

### Operational controls

The reconciled inventory records that shadow-serving boundaries, manual rollback controls and attested shadow admission are demonstrated. Review signals do not automatically switch serving, and the admitted release archive contains zero raw-source-data members.

Those controls do not override validation evidence.

### Committee readiness

`MCR-XGB-MOTOR-001` remains:

**`EVIDENCE_GAP_HOLD` — 5 / 8 required gates pass.**

Blockers remain:

1. `G2_LOCKED_TEMPORAL_SUPPORT`;
2. `G3_PREREGISTERED_EXTERNAL_SUPPORT`;
3. `G4_FRESH_INDEPENDENT_EVIDENCE`.

Human sign-off cannot override failed evidence gates.

## Model Card correction

`MODEL_CARD.md` is now aligned to the current evidence lineage. In particular it:

- describes 2024 as locked OOT **at first use**, not as a currently untouched holdout;
- distinguishes development benchmark evidence from validation/promotion evidence;
- includes Australian and Belgian preregistered replications;
- records validation consumption explicitly;
- retains the Australian numerical-reproducibility limitation and Belgian successful tolerance-based reproduction;
- records `0/4` external gates and the v0.44 `5/8` committee state;
- keeps operational readiness separate from model approval;
- preserves the no-FIRST-CENTRAL/no-current-UK/no-commercial-uplift boundary.

## Decision

No historical model result changes.

**HOLD / HOLD_SHADOW_ONLY / promotion review NOT_OPEN.**

v0.46 improves evidence-state consistency and model-risk traceability; it does not provide new model-performance evidence.
