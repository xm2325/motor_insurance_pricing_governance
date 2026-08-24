# v0.60 — Prospective evidence-programme template

## Why this version exists

v0.59 establishes that the existing request `MCR-XGB-MOTOR-001` cannot reach its own 8/8 committee-opening condition without retrospectively changing G2. The next legitimate step is therefore **not** another dataset for MCR-001. It is to define the evidence architecture that a future, separately registered request would have to satisfy before any fresh outcomes are accessed.

v0.60 is a **template only**. It does not create or authorise `MCR-XGB-MOTOR-002`, select a target, select a dataset, inspect row-level data, or reopen the failed request.

## Three-stage evidence architecture

A future request instantiated from this template must register three pairwise-distinct fresh source identities:

1. **S1 — locked temporal qualification**: genuine temporal order with development/calibration/locked-test rules fixed before access.
2. **S2 — independent external replication**: a different portfolio/source identity, prospectively registered and independent of S1.
3. **S3 — sealed reserve confirmation**: a third source identity that remains row-level unaccessed while human-review readiness is evaluated. It cannot be used to rescue S1 or S2.

The same portfolio cannot be counted under multiple labels through random resplitting or alternate upstream files unless independence is established from pre-access metadata.

## Scope must be chosen before outcomes

A future request must select exactly one scope before fresh outcome access:

- `FREQUENCY_ONLY`;
- `PURE_PREMIUM_ONLY`; or
- `GLOBAL_TWO_TARGET`.

For `GLOBAL_TWO_TARGET`, both frequency and pure-premium registered gates must pass in S1 and S2. A future failure cannot be followed by changing the request to whichever target happened to look better.

## Fixed evidence budget

The programme permits exactly one registered fresh source identity for each of S1, S2 and S3. If S1 or S2 fails its registered gate, that future request terminates in HOLD. It may not replace the failed dataset with a new one, promote S3 to rescue the failure, change target scope, or weaken the performance gate.

A later attempt would require a new request ID and another prospective registration before accessing any fresh outcomes relied upon by that new request.

## Inherited quantitative rules

The default project review gate is unchanged from the existing prospective external protocol:

- relative deviance improvement >= 0.5%;
- paired-bootstrap lower bound > 0;
- challenger aggregate absolute-log calibration error no worse than reference + 0.01;
- calibration scale within [0.5, 2.0], no clipping;
- 500 paired bootstrap draws;
- a positive result needs at least two independent GitHub Actions executions with matching decision labels and registered metric reproducibility;
- iterative solvers/tolerances and single-thread numerical controls must be frozen before execution.

These are project review rules, not insurer or regulatory standards.

## Current governance state

No active future request exists yet. No fresh source is selected and no external row-level data or outcome values are accessed in v0.60.

Current state remains `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`; no model promotion or customer-pricing authority is created.
