# v0.26 — Hybrid XGBoost native model IO

## Decision

**PASS for the model-IO migration. Model-family governance remains HOLD / HOLD_SHADOW_ONLY.**

v0.26 addresses the portability warning exposed by v0.25. The previous bundle serialised the complete sklearn Pipeline, including XGBoost, through joblib/pickle. That produced exact locked predictions in the CPU-only image but emitted XGBoost's cross-version serialization warning because training resolved XGBoost 3.4.1 while the slim runtime uses `xgboost-cpu` 3.4.0.

The fix is to change the persistence boundary rather than suppress the warning.

## Architecture

Reference GLMs remain complete sklearn Pipelines stored with joblib. Their pickle-sensitive model stack is required to match exactly for Python major/minor, NumPy, pandas, SciPy, scikit-learn and joblib.

For each XGBoost challenger:

1. the fitted sklearn preprocessing transformer is stored separately with joblib;
2. the fitted XGBoost estimator is stored with native UBJSON model IO;
3. the loader verifies SHA-256 for both components;
4. the runtime reconstructs an inference wrapper from the preprocessor plus `XGBRegressor.load_model()`;
5. XGBoost native-model compatibility is limited to the same major/minor line.

Training therefore remains on XGBoost **3.4.1**, while the CPU-only runtime remains on **xgboost-cpu 3.4.0**.

## Hard serialization gate

The acceptance test compares the **same fitted models** before persistence with the reloaded hybrid bundle. This deliberately isolates serialization from retraining.

| Gate | Result |
|---|---:|
| Records | 25 |
| Core prediction fields per record | 4 |
| Comparisons | **100** |
| Maximum absolute error | **0.0** |
| Acceptance tolerance | rtol `1e-12`, atol `1e-12` |
| Status | **SAME_FIT_SERIALIZATION_PARITY_PASS** |

All four fields have maximum absolute error 0.0: reference frequency, challenger frequency, reference pure premium and challenger pure premium.

## CPU-only runtime gate

The runtime image loads the same bundle with XGBoost 3.4.0 while the manifest records training XGBoost 3.4.1.

| Runtime evidence | Result |
|---|---:|
| Compatibility status | **HYBRID_MODEL_IO_COMPATIBLE** |
| Pickle-stack mismatches | **none** |
| Native XGBoost compatibility | **pass** |
| HTTP records | 25 |
| Core HTTP fields | 4 |
| HTTP comparisons | **100** |
| Maximum HTTP error vs same-fit reference | **0.0** |
| XGBoost cross-version pickle warning | **not detected** |

The compatibility gate runs before any joblib object is loaded. A mismatch in the pickle-sensitive stack fails closed. A different XGBoost major/minor line also fails closed.

## Why the first v0.26 gate was changed

The first v0.26 implementation required a newly retrained bundle to be bit-for-bit equal to a historical v0.25 bundle. It failed on the GLM frequency reference by only **3.79e-09** on the first checked prediction. That failure was useful: it showed that retraining reproducibility and serialization parity are different controls.

The corrected design does **not** weaken the serialization tolerance. It moves the strict `1e-12` parity test to the correct comparison: one fitted model set before and after persistence.

The historical fixture is retained as a retraining-drift audit. Across 25 records × 4 fields:

- maximum absolute historical-vs-rebuilt difference: **0.4795734**;
- maximum relative difference: **0.0874243%**;
- the maximum occurs in the GLM reference pure-premium prediction, 548.5584 vs 548.0789;
- XGBoost frequency and pure-premium challenger predictions have maximum historical rebuild difference **0.0** on this fixture.

This audit is **not** a promotion or serialization gate. Material model changes remain governed by the existing locked OOT, bootstrap, transport and approval workflows.

## Provenance

Verified GitHub Actions run: **32519475249** on head `671204a800359af55189c395a61d4c28e5198a37`.

Evidence artifact: **9460042916**, digest `sha256:c0c2211e2a45fb690e4d742030ddfed92eec6a3af4f43196ed742ff1d9b4a481`.

The historical reference fixture is traced to v0.25 deployment artifact 9455210467 with digest `sha256:04a7fefcd4a8aaf1f48ef1a9d082a5338bb860b2dcd3c62599e623b464b771e8`.

## Interpretation boundary

This proves a controlled model-persistence and runtime-compatibility improvement for the locked public shadow-scoring project. It does not establish that XGBoost should replace the GLM, does not set customer prices, and does not establish transfer to FIRST CENTRAL or the UK motor market.
