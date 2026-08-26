# v0.62 — Pricing Game S1 source-contract incident

## Outcome

The first legal row-level opening of `MCR-XGB-MOTOR-002` stage `S1_TEMPORAL_QUALIFICATION` **failed closed before any outcome-value, exposure-value, rating-feature-value, policy-id-value or calendar-year-value inspection, and before model fitting**.

The pinned `pg15training` binary passed the registered source-identity checks before decode:

- CASdatasets commit `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`;
- path `data/pg15training.rda`;
- 1,934,161 bytes;
- Git blob SHA-1 `9e670d214c05a7454d558ab32de5df96a6b0aba6`;
- first-run file SHA-256 `a762362adb188e593de8ce2b811460659cc67de43751b22ac84d749db53f2550`.

The decoded R object then failed the **pre-registered semantic column-name set**. v0.61 registered the exposure field as `Expdays`; the pinned object contains `Exppdays`. All other registered names in the observed schema matched. Column presentation order is not the failure and was explicitly not a v0.61 identity gate.

## Why this is not repaired in place

The v0.61 registration was persisted before S1 access and explicitly states that an opened-stage source-contract incident consumes the stage, source substitution after access is forbidden, and S3 cannot rescue S1/S2 failure. Therefore v0.62 does **not** alias `Exppdays` to `Expdays`, amend the registered feature/exposure contract after access, rerun S1 as though it remained confirmatory, substitute another S1 file, or open S2/S3.

That restriction is intentionally stronger than the engineering observation that the spelling difference is easy to repair. The scientific question is whether the prospectively registered request survives its own pre-access source contract, not whether code can be made to run after inspecting the source.

## Access boundary

At the incident boundary:

- pinned binary downloaded: **yes**;
- R object decoded: **yes**;
- schema names inspected: **yes**;
- `PolNum` values inspected: **no**;
- `CalYear` values inspected: **no**;
- row count computed: **no**;
- cross-year leakage filter executed: **no**;
- exposure values inspected: **no**;
- claim/loss outcome values inspected: **no**;
- rating feature values inspected: **no**;
- model fit/calibration: **no**;
- performance metrics/bootstrap/gates: **no**;
- S2/S3 row access: **no**;
- raw RDA persisted to Git: **no**.

## Request lifecycle

`MCR-XGB-MOTOR-002` therefore becomes `TERMINAL_S1_SOURCE_CONTRACT_INCIDENT` under the rules that were frozen in v0.61. S1 is consumed without creating a temporal-qualification pass. S2 (`swmotorcycle`) and S3 (`brvehins1`) remain sealed and are **not authorised to open for this request**; the reserve cannot rescue S1.

No fresh temporal/external model evidence or committee-gate credit is created. The historical project state remains **5/8**, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, with customer pricing unauthorised.

## Interpretation

This is a source-contract/governance result, not a model-performance result. It demonstrates the intended anti-data-shopping behaviour: authenticated bytes alone are insufficient; a material semantic mismatch discovered after opening a registered stage is preserved rather than silently normalised in whichever way permits the experiment to continue.
