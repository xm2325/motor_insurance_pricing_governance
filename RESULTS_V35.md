# v0.35 — Validation-use firewall

## Why this version exists

The 2024 Spanish motor period was a genuine locked out-of-time test at its **first** model-family evaluation. It has since been interrogated repeatedly for monitoring, mature outcomes, recalibration evaluation, cohort transport and factor-uncertainty analysis.

That history cannot be undone. Continuing to call 2024 an "untouched" holdout for future candidate selection would overstate the independence of later evidence.

v0.35 therefore adds no new model and computes no new 2024 performance metric. It makes validation reuse explicit and machine-enforceable.

## Registered roles

- **2022:** model training.
- **2023:** calibration and development.
- **2024 at first use:** `LOCKED_OOT_FIRST_USE`.
- **2024 now:** `CONSUMED_RETROSPECTIVE_VALIDATION`.

The ledger records seven material 2024 evidence uses, including the original locked OOT run and later v0.22, v0.23 and v0.31–v0.34 analyses. It is deliberately described as a material-use ledger rather than a claim that every diagnostic read has been enumerated.

## Fail-closed firewall

2024 remains available for:

- regression reproduction;
- monitoring replay;
- post-hoc diagnostics;
- governance contract testing.

Those uses must be labelled `REUSED_HISTORICAL_VALIDATION` and cannot be represented as independent confirmation.

The validator rejects any attempt to use 2024 for:

- fitting new model parameters;
- fitting new calibration parameters;
- selecting a new candidate policy;
- claiming independent confirmation;
- authorising model-family promotion;
- authorising customer pricing.

Unknown/unregistered 2024 purposes also fail closed rather than defaulting to allowed.

## Why this matters for v0.32–v0.34

v0.32 correctly fitted its incremental `business_type` factors from 2023 only, and v0.34 correctly bootstrapped those factors from 2023 only. However, 2024 outcomes were used to evaluate candidate behaviour. Those analyses remain valid retrospective evidence, but they consume the independence of 2024 for **future** candidate-selection claims.

The firewall does not retroactively invalidate the first locked OOT result. It distinguishes:

1. **historical first-use independence**, which is preserved; from
2. **current future-use independence**, which is no longer available.

## Promotion requirement

A future model-family promotion claim now requires a genuinely new source of independent evidence, such as:

- a later calendar period that was not inspected during candidate development; or
- an external validation dataset from a different portfolio, with analysis rules fixed before outcomes are inspected.

Until then:

- model-family decision: `HOLD`;
- serving status: `HOLD_SHADOW_ONLY`;
- model promotion authorised: **false**;
- customer-pricing change authorised: **false**.

This is a project validation-governance rule, not a statement of an insurer or regulatory validation standard.
