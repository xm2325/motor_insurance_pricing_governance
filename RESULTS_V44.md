# v0.44 — Fail-closed Model Change Committee gate

## Purpose

Turn the v0.43 evidence dossier into an executable change-control gate. The question is narrower than model approval: **does the current challenger request have enough evidence and operational control to advance to a human committee review?**

The machine gate can return only:

- `EVIDENCE_GAP_HOLD`, or
- `READY_FOR_HUMAN_COMMITTEE_REVIEW`.

It can never approve model promotion or customer pricing.

## Current gate result

The current request `MCR-XGB-MOTOR-001` is expected to produce:

`EVIDENCE_GAP_HOLD`

with **5/8 required gates passing** and three evidence blockers:

1. `G2_LOCKED_TEMPORAL_SUPPORT` — Spanish 2024 original locked OOT did not support a global model-family switch.
2. `G3_PREREGISTERED_EXTERNAL_SUPPORT` — Australia + Belgium provide four preregistered external target gates and 0 passes.
3. `G4_FRESH_INDEPENDENT_EVIDENCE` — Spanish 2024, Australian `ausprivauto0405` and Belgian `beMTPL97` are consumed for fresh model-family candidate selection.

## What already passes

- `G1_DEVELOPMENT_SIGNAL`: the freMTPL2 cross-sectional benchmark retains a material XGBoost frequency development signal.
- `G5_REPRODUCIBILITY_CONTROL`: prospective two-run numerical reproducibility is registered and the Belgian observed negative results reproduce within registered tolerance.
- `G6_SHADOW_DEPLOYMENT_BOUNDARY`: the serving contract remains `HOLD_SHADOW_ONLY`.
- `G7_RELEASE_AND_ROLLBACK_CONTROL`: the project demonstrates fail-closed manual rollback without automatic pricing change.
- `G8_ATTESTED_SHADOW_ADMISSION`: attested admission is limited to the shadow registry.

This separation is intentional: operational readiness cannot compensate for insufficient independent validation evidence.

## Human-review boundary

A `human_signoff_recorded=true` flag is audit metadata only and cannot bypass a failed machine evidence gate. Even if every machine gate passed, the only allowed state transition would be `READY_FOR_HUMAN_COMMITTEE_REVIEW`; a separate human governance decision would still be required, and customer pricing would remain unauthorised by this code.

## Interpretation boundary

This is a project model-change governance demonstration, not FIRST CENTRAL policy or evidence of insurer approval. It does not establish transfer to the current UK motor market and does not report commercial uplift.
