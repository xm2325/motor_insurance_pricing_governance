# Evidence Registry

This file maps the project's headline claims to persisted result files. The goal is to keep CV, README and interview numbers traceable and to prevent a later rerun from silently invalidating an old claim.

## Headline evidence

| Claim | Verified value | Source |
|---|---:|---|
| freMTPL2 full-frequency benchmark size | 678,013 policies | project data audit / README |
| XGBoost frequency deviance reduction vs Poisson GLM (+ geography) | 5.43% | `results/fremtpl2_full_frequency_benchmark.csv` |
| Top-10% exposure claim capture, Poisson GLM -> XGBoost | 20.59% -> 31.17% (+10.58 pp) | `results/fremtpl2_full_frequency_benchmark.csv` |
| Spanish longitudinal source size | 354,140 policy-years, 47 variables | `action_results/spanish_oot_2024/schema_data_audit.json` |
| Locked temporal design | 2022 train -> 2023 calibration -> 2024 untouched OOT | `action_results/spanish_oot_2024/oot_2024_summary.json` |
| Usable 2024 OOT cohort | 168,085 policy-years | `action_results/spanish_oot_2024/oot_2024_summary.json` |
| 2024 XGBoost top-10% claim-capture gain | 26.62% -> 27.04% (+0.42 pp) | `action_results/spanish_oot_2024/oot_2024_summary.json` |
| 2024 locked frequency deviance | GLM 1.11854; XGBoost 1.11884 | `action_results/spanish_oot_2024/oot_2024_summary.json` |
| 2024 frequency bootstrap evidence | 95% CI [-0.00155, 0.00083], crosses zero | `action_results/spanish_oot_2024/oot_2024_summary.json` |
| 2024 locked pure-premium deviance | GLM 93.9318; XGBoost 93.9513 | `action_results/spanish_oot_2024/oot_2024_summary.json` |
| Rolling-origin 2022+2023 -> 2024 frequency gain | XGBoost deviance 1.10843 vs GLM 1.11199; ~0.32% reduction | `action_results/spanish_oot_2024/rolling_origin_v14_summary.json` |
| Rolling-origin pure-premium result | GLM 92.8213 vs XGBoost 93.1606; no stable XGBoost gain | `action_results/spanish_oot_2024/rolling_origin_v14_summary.json` |
| Existing-policy pure-premium calibration | GLM 0.994; XGBoost 0.950 | `action_results/spanish_oot_2024/oot_2024_transport_segment_calibration.csv` |
| New-policy pure-premium calibration | GLM 0.825; XGBoost 0.881 | `action_results/spanish_oot_2024/oot_2024_transport_segment_calibration.csv` |
| Final model-family decision | HOLD / no promotion | `action_results/spanish_oot_2024/oot_2024_summary.json`, `RESULTS_V14.md`, `RESULTS_V20.md` |
| v0.21 governance mode | `HOLD_SHADOW_ONLY`; no quote/price endpoint | `action_results/v21/manifest.json`, `tests/test_deployment_contract.py` |
| v0.21 offline-online parity | 25 records; max absolute prediction error **0.0** | `action_results/v21/deployment_smoke_summary.json` |
| v0.21 batch contract | deterministic **1,000-policy** batch tested | `action_results/v21/deployment_smoke_summary.json` |
| v0.21 safety/data-contract checks | forbidden current-outcome field rejected; unseen category warning emitted | `action_results/v21/deployment_smoke_summary.json` |
| v0.21 container/network check | Docker build + HTTP score parity **success** | `action_results/v21/ACTION_V21_STATUS.json`, `action_results/v21/container_smoke_summary.json` |
| v0.21 artifact integrity | all persisted model components have registered SHA-256 digests | `action_results/v21/manifest.json` |
| v0.22 monitoring privacy boundary | aggregate non-PII telemetry only; no policy rows/payloads retained in monitoring snapshot | `action_results/v22/monitoring_replay_summary.json`, `tests/test_monitoring_v22.py` |
| v0.22 2022 monitoring control | 5,000 records; **GREEN**; max feature PSI **0.00973** | `action_results/v22/monitoring_replay_summary.json` |
| v0.22 real 2024 temporal drift | 5,000 records; max feature PSI **1.4116**, driven by `business_type` | `action_results/v22/monitoring_replay_summary.json` |
| Full-year business-type mix | 2022 NB/P **97.91%/2.09%** -> 2024 **57.35%/42.65%** | `action_results/v22/monitoring_replay_summary.json` |
| v0.22 temporal model-disagreement stability | frequency p95 **0.94x** baseline; pure-premium p95 **1.04x** baseline; no relative disagreement alert | `action_results/v22/monitoring_replay_summary.json` |
| v0.22 synthetic monitoring stress | error, unseen-category and feature-drift alerts fire; frequency/pure-premium disagreement p95 **2.54x/2.87x** baseline | `action_results/v22/monitoring_replay_summary.json` |
| v0.22 small-sample drift guard | feature-drift alert requires at least **500** scored records | `action_results/v22/monitoring_replay_summary.json`, `tests/test_monitoring_v22.py` |
| v0.22 container monitoring check | Docker HTTP `/monitoring` verified; 5 valid requests -> **GREEN** | `action_results/v22/container_monitoring_summary.json` |
| v0.23 review hysteresis | **2** consecutive breach windows open review; **2** consecutive green windows close it | `action_results/v23/review_lifecycle_summary.json`, `tests/test_review_v23.py` |
| v0.23 real temporal-review action | persistent 2024 `feature_drift` -> **MEDIUM** `REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION` | `action_results/v23/review_lifecycle_summary.json` |
| v0.23 review recovery | temporal review closes only after **2 green windows** and returns to `HEALTHY` | `action_results/v23/review_lifecycle_summary.json` |
| v0.23 synthetic high-severity review | repeated stress -> **HIGH** `INVESTIGATE_SERVING_DATA_AND_MODEL` | `action_results/v23/review_lifecycle_summary.json` |
| v0.23 lifecycle determinism/privacy | deterministic replay; aggregate-only evidence; SHA-256 evidence lineage; **no automatic model or pricing change** | `action_results/v23/review_lifecycle_summary.json` |
| v0.25 runtime image reduction | **960,271,925 -> 488,778,419 bytes (49.10%; 471,493,506 bytes removed)** | `action_results/v25/image_size_summary.json` |
| v0.25 CPU-only dependency gate | `xgboost-cpu 3.4.0`; no `httpx`, `matplotlib`, `nvidia-nccl-cu13`, `pytest` or `tabulate` in runtime image | `action_results/v25/image_size_summary.json` |
| v0.25 full-vs-runtime HTTP parity | **25 records x 6 numeric fields; max absolute error 0.0** | `action_results/v25/http_parity_summary.json` |
| v0.25 runtime-vs-offline parity | **25 records x 4 core prediction fields; max absolute error 0.0** | `action_results/v25/http_parity_summary.json` |
| v0.26 XGBoost persistence | challengers use sklearn-preprocessor joblib + native XGBoost UBJSON; XGBoost estimator removed from pickle | `action_results/v26/environment_compatibility_result.json`, `RESULTS_V26.md` |
| v0.26 same-fit serialization parity | **25 records x 4 fields = 100 comparisons; max absolute error 0.0** | `action_results/v26/serialization_parity_summary.json` |
| v0.26 CPU runtime native compatibility | training XGBoost **3.4.1** -> CPU runtime **3.4.0**; `HYBRID_MODEL_IO_COMPATIBLE`; no pickle-stack mismatch | `action_results/v26/environment_compatibility_summary.json` |
| v0.26 runtime HTTP parity | **100 same-fit comparisons; max absolute error 0.0** | `action_results/v26/environment_compatibility_summary.json` |
| v0.26 XGBoost serialization warning | cross-version pickle warning **not detected** after XGBoost native-model migration | `action_results/v26/serialization_warning_check.json` |
| v0.26 historical retrain audit | max relative difference **0.0874%**; audit only, not serialization acceptance | `action_results/v26/retrain_drift_audit.json` |
| v0.27 content-addressed bundle | **9 locked artifacts / 1,604,579 bytes** with canonical lock self-digest | `action_results/v27/bundle_integrity_result.json` |
| v0.27 public source provenance | Mendeley `sw4jmdb2sm` v1; portfolio file **94,710,312 bytes**; SHA-256 `6a47d19d...f0faf4` | `action_results/v27/bundle_integrity_result.json` |
| v0.27 fail-closed corruption tests | model-artifact byte tamper, missing GLM artifact and lock self-tamper all rejected | `action_results/v27/tamper_test_summary.json` |
| v0.27 container integrity status | `CONTENT_ADDRESSED_BUNDLE_VERIFIED` + `HYBRID_MODEL_IO_COMPATIBLE` | `action_results/v27/container_integrity_summary.json` |
| v0.27 integrity + HTTP parity | **25 records x 4 fields = 100 comparisons; max absolute error 0.0** | `action_results/v27/container_integrity_summary.json` |
| v0.28 release packaging | A/B have **distinct lock digests** but **identical hashes across 9 locked artifacts** | `action_results/v28/release_control_result.json` |
| v0.28 review/rollback automation boundary | synthetic review leaves B active; unauthorised rollback rejected; authorised target is last-known-good A | `action_results/v28/release_control_result.json` |
| v0.28 release event lineage | **7-event SHA-256 chain verified** | `action_results/v28/release_control_result.json`, `action_results/v28/release_registry.json` |
| v0.28 container bundle switch | candidate B **100 comparisons / max error 0.0** -> rollback A **100 comparisons / max error 0.0**, same runtime image | `action_results/v28/container_rollback_summary.json` |
| v0.28 rollback side-effect boundary | **no model retraining and no pricing change** during release switch | `action_results/v28/release_control_result.json` |
| v0.29 attested release archive | **386,598 bytes**, SHA-256 `14866b17...548bfbf` | `action_results/v29/artifact_attestation_result.json` |
| v0.29 GitHub/Sigstore provenance | GitHub attestation ID **42232000** generated for the sealed release archive | `action_results/v29/artifact_attestation_result.json` |
| v0.29 independent attestation verification | `gh attestation verify` **PASS**, one verification record | `action_results/v29/attestation_verification.json`, `action_results/v29/artifact_attestation_result.json` |
| v0.29 provenance identity | verification material binds repository, v0.29 workflow/ref and build commit `3119dd27...940e4f` | `action_results/v29/attestation_verification.json` |
| v0.29 governance boundary | attestation leaves model serving at `HOLD_SHADOW_ONLY`; it is build provenance, not pricing approval | `action_results/v29/artifact_attestation_result.json`, `RESULTS_V29.md` |
| v0.30 first strict security gate | **50 HIGH / 36 fixable / 3 CRITICAL**; build failed at policy enforcement before remediation | `security/v30_first_pass_failure.json` |
| v0.30 published-fix remediation | fixable HIGH findings **36 -> 0** after Debian runtime package upgrade | `security/v30_first_pass_failure.json`, `action_results/v30/runtime_supply_chain_result.json` |
| v0.30 runtime SBOM | CycloneDX **1.6**, **112 components**, `xgboost-cpu`; no registered dev/GPU packages | `action_results/v30/supply_chain_policy_result.json` |
| v0.30 final HIGH findings | **14 HIGH**, **0 fixable**, all 14 recorded as unfixed at build time | `action_results/v30/runtime_supply_chain_result.json` |
| v0.30 final CRITICAL findings | **3 CRITICAL / 0 fixable / 3 VEX-covered / 0 unreviewed** | `action_results/v30/runtime_supply_chain_result.json`, `action_results/v30/vex_v30.json` |
| v0.30 VEX expiry | exact CVE/package VEX review expires **2026-09-30**; fixed CRITICAL or expiry fails the policy | `action_results/v30/vex_v30.json`, `evaluate_supply_chain_v30.py` |
| v0.30 runtime security + scoring parity | `amd64`; **100 same-fit HTTP comparisons; max absolute error 0.0** | `action_results/v30/runtime_http_parity.json`, `action_results/v30/runtime_supply_chain_result.json` |
| v0.30 SBOM attestation | GitHub/Sigstore attestation ID **42340101**; immediate `gh attestation verify` **PASS** | `action_results/v30/runtime_supply_chain_result.json`, `action_results/v30/sbom_attestation_verification.json` |
| v0.30 immutable scanner/action pins | Trivy v0.36.0 commit `ed142fd0...36c25`; `actions/attest` v4.2.1 commit `508db95d...da05d` | `.github/workflows/v30-sbom-security.yml`, `tests/test_supply_chain_v30.py` |

## Interpretation rules

- The 5.43% frequency result is a **cross-sectional benchmark result**, not an out-of-time pricing improvement.
- The 0.42 pp 2024 claim-capture gain is a **ranking result** and does not establish lower pricing loss.
- The 0.32% rolling-origin frequency-deviance reduction is a **small model-family stability result**, not a pure-premium improvement.
- v0.21 demonstrates **deployability in shadow mode**, not approval to use XGBoost for customer pricing.
- v0.22 monitoring thresholds (including PSI 0.25 and minimum 500 records) are **project demonstration rules**, not insurer, regulatory or FIRST CENTRAL thresholds.
- The v0.22 2024 feature-PSI result is from a seeded **5,000-policy sample** against the 2022 aggregate training baseline; the quoted NB/P percentages are full-year aggregate distributions.
- A v0.22 feature-drift alert does **not** prove predictive deterioration. In the 2024 replay, portfolio mix drifted materially while reference/challenger disagreement remained comparatively stable.
- The v0.21/v0.22 latency measurements are GitHub-runner/TestClient diagnostics, not production SLAs.
- The v0.22 stress replay is synthetic and verifies alert behaviour; it is not an observed production incident.
- v0.23 uses **review hysteresis** to avoid opening/closing reviews on single windows. The 2-window rules are project demonstration rules, not insurer governance policy.
- v0.23 review actions are recommendations only. The controller never changes customer pricing, model approval, rollback state or serving configuration automatically.
- The v0.23 synthetic high-severity review validates controller behaviour and is not an observed production incident.
- v0.25 is a **runtime/dependency optimisation**, not model approval. The model-family status remains `HOLD` and serving remains `HOLD_SHADOW_ONLY`.
- v0.25 exact parity is evidence for the locked 25-record test set and current bundle; it did **not** establish arbitrary cross-version pickle portability and exposed the XGBoost serialization warning addressed in v0.26.
- v0.26's strict **0.0 same-fit parity** is a serialization-migration result, not a retraining-reproducibility result.
- v0.26 allows the XGBoost 3.4.1 -> 3.4.0 patch difference only because the estimator is loaded through native model IO; the remaining joblib/pickle stack is still exact-version gated before deserialization.
- The v0.26 historical retrain comparison is diagnostic only. Its 0.0874% maximum relative difference must not be described as serialization error or model improvement.
- v0.26 changes model persistence and deployment reproducibility only. It does not alter the model-family `HOLD` decision or permit customer pricing.
- v0.27 is a **content-addressed integrity and provenance contract**, not a cryptographic signature. Its lock digest identifies one sealed build and may change legitimately when code/build provenance or any locked artifact changes.
- v0.27 detects missing/modified locked files when the lock digest is trusted; it does not claim resistance to an attacker able to replace both bundle artifacts and lockfile.
- v0.27 integrity verification occurs before model deserialisation for contract `0.27`; the 0.0 parity result remains a same-fit serving check, not model approval.
- v0.28 is a **synthetic shadow release-control replay**, not a production incident. It verifies release selection and rollback mechanics over already integrity-verified bundles.
- v0.28 opening a review does not switch serving automatically. An unauthorised rollback is rejected; only the explicit project flag `operator_authorised=True` permits the switch to last-known-good.
- `operator_authorised=True` is a demonstration governance contract, **not an authentication/IAM system** or evidence of production separation of duties.
- v0.28 rollback does not retrain models, approve the challenger or change customer pricing; it only selects a previously sealed shadow bundle.
- v0.29 uses GitHub Artifact Attestations to provide **cryptographically verifiable build provenance for one release archive**. This is stronger than the v0.27 self-contained content lock because verification is rooted in GitHub Actions OIDC/Sigstore rather than a repository-local digest alone.
- v0.29 attestation does **not** prove the model is safe, accurate, regulator-approved or suitable for customer pricing; it links the exact archive digest to the repository/workflow/commit that built it.
- v0.29 does not expose the raw Mendeley portfolio in the attested archive and does not change `HOLD_SHADOW_ONLY` governance.
- v0.30 is a **build-time runtime-supply-chain gate**, not evidence that the image is permanently vulnerability-free or production-approved.
- v0.30 did not weaken the rule after the first failure: published Debian fixes removed all **36 fixable HIGH** findings, while the remaining unfixed findings remain visible in evidence.
- The three v0.30 CRITICAL VEX statements are CVE/package-specific `not_affected` assessments with Debian tracker references and expiry **2026-09-30**. They are not a blanket ignore list; any published CRITICAL fix, new/unreviewed CRITICAL, package mismatch or VEX expiry must fail the gate.
- v0.30 SBOM attestation proves provenance for the exact runtime archive/SBOM subject used by the workflow; it does not prove model validity, security against all threats, pricing safety or transport to FIRST CENTRAL / the UK market.
- Synthetic quote-conversion / proposition experiments are not reported as observed commercial impact.
- No result in this repository establishes transport to FIRST CENTRAL or the UK motor market.

## Automated protection

`tests/test_evidence_registry.py`, `tests/test_runtime_and_model_io_evidence.py`, `tests/test_bundle_integrity_evidence_v27.py`, `tests/test_release_control_evidence_v28.py`, `tests/test_artifact_attestation_evidence_v29.py` and `tests/test_supply_chain_evidence_v30.py` recompute / verify the main modelling, deployment, monitoring, review-lifecycle, runtime, model-IO, content-addressed-integrity, shadow-release-control, GitHub-attestation and runtime-supply-chain headline evidence from persisted result files. CI fails if the stored evidence no longer supports the registered claims.
