# v0.58 — euMTPL source-contract incident

## Objective and outcome

v0.58 was intended to be the first row-level execution of the v0.57 main-locked `euMTPL` external-temporal protocol. It did **not** reach model fitting. The exact source contract failed immediately after the first R-object decode, and the experiment was stopped rather than repaired after access.

Final incident status:

`V58_FAIL_CLOSED_SOURCE_SCHEMA_PREREGISTRATION_MISMATCH`

This is governance evidence about preregistration integrity, not predictive-performance evidence.

## What was locked before access

v0.57 was persisted on main before any `euMTPL` binary download or decode. Its protocol SHA-256 is:

`a2b49e26aeca619323129ee4b56ff39d110cf68a08bfe0064fbd3f5886f74ff5`

The exact source identity was fixed to CASdatasets commit `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`, path `data/euMTPL.rda`, Git blob `4bb386d89606eb5b529206d0835e11074103042b`, 17,829,164 bytes.

The preregistered exact schema followed the public Format documentation and included `cost_fcd` / `num_fcd`, with `year` immediately after `policy_id`.

## First attempted execution

PR run **32779225893** on Azure `westus` first passed all ten pre-download contracts and then verified the binary **before decode**:

- bytes: **17,829,164** — exact;
- Git blob SHA1: **`4bb386d89606eb5b529206d0835e11074103042b`** — exact;
- file SHA-256: **`cf3594f20c0c108fce8efba167f468697a9233372286b29eb81aa43aa724d195`**.

The binary was therefore the registered upstream object, not a download substitution.

The first R-object decode exposed this actual column order:

`policy_id, group, fuel_type, year, vehicle_category, vehicle_use, province, horsepower, gender, age, exposure, cost_nc, num_nc, cost_cg, num_cg, cost_fcg, num_fcg, cost_cd, num_cd`

This differs from the v0.57 exact contract in two ways:

1. column order differs;
2. the registered `cost_fcd` / `num_fcd` fields are named `cost_fcg` / `num_fcg` in the pinned object.

CASdatasets' public documentation itself is internally inconsistent: its Format section describes `cost_fcd` / `num_fcd`, while the example output from `head(euMTPL)` lists `cost_fcg` / `num_fcg` and the same order observed in the pinned object.

## Why the protocol was not amended

The difference is plausibly an upstream documentation/schema naming defect, and the intended economic target could potentially be reconstructed by aliasing the field. That repair was deliberately **not** used for confirmatory evidence.

v0.57 states that source/schema/target rules may not be changed after row-level access. The R object had already been decoded when the mismatch was discovered. Therefore v0.58 treats the dataset as consumed for fresh-confirmatory purposes rather than changing `fcd` to `fcg` and pretending the preregistration remained untouched.

No source reorder, alias map, target rewrite, model change or gate relaxation was made.

## Access boundary at failure

The fail-closed incident records:

- pinned binary downloaded: **yes**;
- R object decoded: **yes**;
- row-level dataset access occurred: **yes**;
- outcome **values** inspected: **no**;
- actual year values inspected: **no**;
- row-level outcome/year summary computed: **no**;
- model fit executed: **no**;
- calibration executed: **no**;
- locked-test performance metric computed: **no**;
- registered gate evaluated: **no**.

The original modelling runner is no longer called by the active v0.58 workflow. It remains historical implementation context only; the workflow now executes a narrow schema-incident recorder that does not aggregate outcomes or inspect year values.

## Reproduced incident workflow

After the first failure was understood, the same pinned source was re-downloaded and decoded only to machine-record the incident. PR run **32779636742** completed successfully:

- fail-closed contracts: pass;
- pinned binary identity: pass;
- schema mismatch reproduced: pass;
- no outcome/year value inspection: pass;
- no model/performance execution: pass;
- raw-data tracking prohibition: pass;
- aggregate incident artifact: pass.

A green incident workflow does **not** convert the failed experiment into a successful model replication; it proves that the failure state and governance boundary are reproducible.

## Governance consequence

`euMTPL` is no longer classified as a fresh confirmatory external dataset after this row-level schema inspection. It may only be used later if explicitly labelled diagnostic/non-confirmatory, with any schema repair documented as post-access.

v0.58 creates no credit for G2, G3 or G4 and does not alter the committee decision:

- committee: **`EVIDENCE_GAP_HOLD`**;
- machine gates: **5/8**;
- model-family decision: **`HOLD`**;
- serving: **`HOLD_SHADOW_ONLY`**;
- promotion review: **`NOT_OPEN`**;
- customer pricing authorised: **false**.

The next confirmatory attempt requires another genuinely unseen external portfolio with its source/schema contract locked before row-level access.
