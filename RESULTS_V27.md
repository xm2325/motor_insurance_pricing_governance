# v0.27 — Content-Addressed Deployment Bundle

## Decision

**PASS — bundle integrity and provenance controls added; model-family governance remains `HOLD / HOLD_SHADOW_ONLY`.**

v0.27 does not change pricing logic or model approval. It adds a fail-closed integrity layer around the already validated v0.26 hybrid bundle.

## Verified PR-run evidence

GitHub Actions run `32521382766` rebuilt the public-data bundle, sealed it, exercised deliberate tamper cases, built the CPU-only service image and verified the running HTTP service.

| Check | Result |
|---|---:|
| Locked deployment artifacts | **9** |
| Total locked bundle bytes | **1,604,579** |
| Public portfolio source bytes | **94,710,312** |
| Public portfolio SHA-256 | `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4` |
| Same-fit container parity | **25 records × 4 fields = 100 comparisons** |
| Max HTTP absolute error | **0.0** |
| Runtime environment | **HYBRID_MODEL_IO_COMPATIBLE** |
| Governance | **HOLD_SHADOW_ONLY** |

The run's content-addressed lock digest was:

`ae33f4001b7c72c2d5ca60c5bc3b47db17a9fe22b7a29ad37356783e9d4be58f`

The digest is expected to change when code/build provenance or any locked artifact legitimately changes; it is an identity for one bundle build, not a permanent model-family identifier.

## What is locked

`bundle.lock.json` includes SHA-256 and byte size for:

- `manifest.json`;
- the same-fit parity reference and serialization evidence;
- both GLM joblib pipelines;
- both XGBoost sklearn preprocessing artifacts;
- both XGBoost native UBJSON model files.

The lock also records the Mendeley dataset/version/file digest and the repository/build-run provenance.

## Fail-closed tests

The verified run deliberately exercised three runtime-independent corruption cases:

1. Appending one byte to `xgb_poisson_frequency.ubj` was rejected by the locked size/hash contract.
2. Deleting `poisson_glm_frequency.joblib` was rejected as a missing locked artifact.
3. Changing the governance value inside `bundle.lock.json` without recomputing its canonical digest was rejected as a lock self-digest mismatch.

Unit contracts additionally reject unsafe relative paths such as `../outside`, and the final verifier rejects duplicate artifact paths.

For contract `0.27`, the service performs content-addressed verification **before** any joblib deserialisation or native XGBoost model load. Older contracts remain readable only so historical v0.21–v0.26 regression workflows can continue to validate their own boundaries.

## Serving evidence

The container `/health` endpoint must report:

- `bundle_integrity = CONTENT_ADDRESSED_BUNDLE_VERIFIED`;
- a lock digest matching the mounted bundle;
- `environment_compatibility = HYBRID_MODEL_IO_COMPATIBLE`;
- `governance_status = HOLD_SHADOW_ONLY`.

The same container then reproduces all 100 same-fit reference predictions with max absolute error `0.0`.

## Interpretation boundary

This is a **content-addressed integrity contract**, not a cryptographic signature. It detects missing or modified files when the lockfile digest is trusted. It does **not** claim protection against an attacker who can replace both the bundle and its lockfile, and it does not establish insurer/regulatory approval, production pricing use, or transfer to FIRST CENTRAL / the UK motor market.
