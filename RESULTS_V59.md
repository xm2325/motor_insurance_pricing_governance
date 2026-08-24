# v0.59 — Existing committee-request reachability audit

## Question

Can the already-registered model-change request `MCR-XGB-MOTOR-001` still reach the v0.44 machine condition required to open a human committee review if more fresh external evidence is collected?

## Registered facts used

This is a governance-state audit only. It reads persisted repository evidence and does **not** access any external row-level dataset, inspect new outcomes, fit a model, select a candidate, or create a new performance threshold.

The v0.44 policy requires all eight required gates to pass. Its G2 definition is exact: **the original locked temporal evaluation must support a global model-family change under its registered rule**. The persisted v0.44 decision records G2 as failed. The v0.43 synthesis records both original Spanish 2024 locked targets — frequency and pure premium — as `HOLD` with `gate_passed=false`.

## Reachability result

Under the existing request and its frozen v0.44 semantics:

- current machine-gate state: **5/8**;
- current blockers: G2, G3, G4;
- G3 and G4 are potentially addressable by future prospectively registered evidence;
- G2 is not: it is defined on a completed historical evaluation whose registered outcome is already negative;
- therefore the maximum possible pass count for **this existing request** without redefining its gate is **7/8**;
- `READY_FOR_HUMAN_COMMITTEE_REVIEW` is structurally unreachable for `MCR-XGB-MOTOR-001`.

This is not a new negative performance result and is not a claim that XGBoost can never be useful. It is a reachability result for one specific governance request under its own frozen rules.

## Stop rule

Do **not** consume additional fresh external outcomes solely to try to make `MCR-XGB-MOTOR-001` reach 8/8. Doing so cannot repair its G2 and would unnecessarily consume fresh validation evidence.

A legitimate future path is a distinct, prospectively registered question or a new model-change request with a new request ID and a temporal-evidence criterion frozen **before** any fresh outcomes relied upon by that request are accessed. Such a request must preserve the complete failed MCR-001 history; it cannot relabel Spanish 2024, consumed external portfolios, or the old G2.

v0.59 does not create or authorise that new request. It only establishes the stop condition for the existing one.

## Governance state

Unchanged:

- committee status: `EVIDENCE_GAP_HOLD`;
- model-family decision: `HOLD`;
- serving status: `HOLD_SHADOW_ONLY`;
- promotion review: `NOT_OPEN`;
- automatic or human model promotion: not authorised;
- customer pricing: not authorised;
- no First Central or current-UK transport claim is created.
