# Evidence Registry

This file maps the project's headline claims to persisted result files. The goal is to keep CV, README and interview numbers traceable and to prevent a later rerun from silently invalidating an old claim.

## Headline evidence

| Claim | Verified value | Source |
|---|---:|---|
| freMTPL2 full-frequency benchmark size | 678,013 policies | project data audit / README |
| XGBoost frequency deviance reduction vs Poisson GLM (+ geography) | 5.43% | `results/fremtpl2_full_frequency_benchmark.csv` |
| Top-10% exposure claim capture, Poisson GLM -> XGBoost | 20.59% -> 31.17% (+10.58 pp) | `results/fremtpl2_full_frequency_benchmark.csv` |
| Spanish longitudinal source size | 354,140 policy-years, 47 variables | `action_results/spanish_oot_2024/schema_data_audit.json` |
| Original temporal design | 2022 train -> 2023 calibration -> 2024 untouched at its first OOT evaluation; later v0.32-v0.34 analyses reuse 2024 retrospectively | `action_results/spanish_oot_2024/oot_2024_summary.json`, `RESULTS_V32.md`, `RESULTS_V33.md`, `RESULTS_V34.md` |
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
| v0.30 attested admission policy | `V30_ATTESTED_RELEASE_ADMISSION_PASS`; `ADMIT_TO_SHADOW_REGISTRY_ONLY` | `action_results/v30/release_admission_result.json` |
| v0.30 attestation trust binding | archive digest bound to repository, workflow, SLSA provenance predicate and GitHub Actions build type | `action_results/v30/release_admission_result.json`, `action_results/v30/attested_release_admission_summary.json` |
| v0.30 release data boundary | **0 raw source-data members** in admitted archive; inner bundle integrity verified across **9 artifacts** | `action_results/v30/release_admission_result.json` |
| v0.30 negative admission tests | tampered archive, wrong repository and wrong workflow identity all rejected | `action_results/v30/admission_negative_summary.json` |
| v0.31 early outcome-maturity gate | **60.0001% mature exposure < 95% gate** -> `WAIT_FOR_OUTCOME_MATURITY`; metrics withheld | `action_results/v31/outcome_review_summary.json` |
| v0.31 mature 2024 outcome review | **168,085 rows; 39,276 claims; 38,106,351.28 incurred**; outcome metrics evaluated only at full maturity | `action_results/v31/outcome_review_summary.json` |
| v0.31 mature frequency deviance | GLM **1.118536** vs XGBoost **1.118835**; GLM remains slightly lower | `action_results/v31/outcome_review_summary.json` |
| v0.31 mature pure-premium deviance | GLM **93.931806** vs XGBoost **93.951316**; GLM remains slightly lower | `action_results/v31/outcome_review_summary.json` |
| v0.31 fresh-bundle historical OOT reconciliation | **8/8 metrics exact; max relative difference 0.0** | `action_results/v31/outcome_review_summary.json` |
| v0.31 business-type calibration | NB exposure **48.18%**, P **51.82%**; neither model is uniformly closer to 1.0 across both targets/groups | `action_results/v31/business_type_calibration.csv`, `RESULTS_V31.md` |
| v0.31 governance result | `HOLD` / `HOLD_SHADOW_ONLY`; **no automatic serving or pricing change** | `action_results/v31/outcome_review_summary.json`, `RESULTS_V31.md` |
| v0.32 2023-only frequency recalibration | GLM and XGBoost frequency candidates both supported on reused 2024 evaluation; relative deviance changes **-0.0398% / -0.0640%** | `action_results/v32/business_type_recalibration_summary.json`, `RESULTS_V32.md` |
| v0.32 pure-premium recalibration | both pure-premium candidates retained global calibration: GLM aggregate calibration worsened; XGBoost worst-segment calibration worsened | `action_results/v32/business_type_recalibration_summary.json`, `RESULTS_V32.md` |
| v0.32 drift decomposition | large `business_type` PSI does not by itself explain calibration drift; within-segment/time component dominates all four registered outputs | `action_results/v32/business_type_mix_decomposition.csv`, `RESULTS_V32.md` |
| v0.33 frequency transport review | both fixed v0.32 frequency candidates: **13 major cohorts, 0 gate breaches** | `action_results/v33/frequency_recalibration_transport_summary.json`, `RESULTS_V33.md` |
| v0.33 worst retained trade-offs | largest major-cohort calibration deterioration at `payment_frequency=Q`; largest deviance worsening at `policy_type=TPG`, both inside registered project guardrails | `action_results/v33/frequency_recalibration_transport_cohorts.csv`, `RESULTS_V33.md` |
| v0.34 conditional 2023 factor bootstrap | **500** stratified paired draws; no 2024 labels used to fit factors; factor draws not clipped | `action_results/v34/frequency_recalibration_uncertainty_summary.json`, `RESULTS_V34.md` |
| v0.34 GLM frequency robustness | **398/500 = 79.6%** aggregate-calibration non-worse, narrowly below fixed 80% rule -> `FACTOR_UNCERTAINTY_REVIEW_REQUIRED` | `action_results/v34/frequency_recalibration_uncertainty_summary.json`, `RESULTS_V34.md` |
| v0.34 XGBoost frequency robustness | **499/500 = 99.8%** deviance improvement; **424/500 = 84.8%** aggregate-calibration non-worse; strong gate pass | `action_results/v34/frequency_recalibration_uncertainty_summary.json`, `RESULTS_V34.md` |
| v0.34 factor-direction intervals | all four NB/P 95% factor intervals remain on the point-estimate side of 1; raw extrema are retained rather than clipped | `action_results/v34/frequency_recalibration_factor_bootstrap_summary.csv` |
| v0.34 governance result | only `challenger_frequency` passes conditional factor-uncertainty gate; model family still `HOLD`, serving `HOLD_SHADOW_ONLY` | `action_results/v34/frequency_recalibration_uncertainty_summary.json` |

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
- v0.30 adds an explicit attested release-admission policy. Passing it permits entry to the **shadow release registry only**; it does not promote the model family or approve customer pricing.
- v0.30 attestation/admission evidence may receive a new archive digest on a later rebuild because build provenance changes. Long-term claims should use the verified policy result and trust bindings rather than assuming one archive SHA is permanent.
- v0.31 uses **real historical 2024 claim and incurred values**, but its partial label-arrival timing is synthetic. It tests delayed-label monitoring logic; it is not a live claims-development, IBNR or settlement-timing study.
- The v0.31 60% checkpoint is deliberately below the 95% project maturity gate, so performance metrics are withheld. The 95% threshold is a project rule, not an insurer or regulatory standard.
- v0.31's exact 8-metric reconciliation is a fresh-training regression diagnostic against the same 2024 historical outcomes. It is not the same contract as v0.26 same-fit serialization parity.
- v0.31 `business_type` results support segment review rather than automatic global model replacement: XGBoost is closer to calibration 1.0 for NB, while GLM is closer for P on the registered frequency/pure-premium calibration checks.
- v0.31 does not promote XGBoost, change serving, or change pricing. The model-family decision remains `HOLD` and serving remains `HOLD_SHADOW_ONLY`.
- v0.32 fits incremental `business_type` multipliers from **2023 only** and evaluates them on 2024. The later use of 2024 means those candidate results are retrospective development evidence, not a new untouched holdout.
- v0.32's large `business_type` PSI is not interpreted causally: the mix-only counterfactual does not explain most of the calibration change, and the within-segment/time component dominates.
- v0.33 reuses the already-fixed v0.32 frequency multipliers across orthogonal 2024 cohorts. It is a slice/transport stability check within the same 2024 year, **not a new independent temporal validation sample**.
- v0.34 is a conditional row-bootstrap sensitivity analysis of the incremental 2023 factors. It does not bootstrap model fitting, global calibration, claim development, or a new calendar period.
- The v0.34 GLM result is deliberately retained as a failure at **79.6% vs the pre-registered 80% aggregate-calibration rule**. The threshold is not relaxed or rounded after observing the result.
- The v0.34 XGBoost pass supports **further shadow testing only**. It does not authorise a serving-bundle change, pricing change, or model-family promotion.
- After v0.32-v0.34, 2024 must no longer be described as an untouched model-selection holdout for future candidate tuning; it has been repeatedly interrogated for recalibration, transport and uncertainty evidence.
- Synthetic quote-conversion / proposition experiments are not reported as observed commercial impact.
- No result in this repository establishes transport to FIRST CENTRAL or the UK motor market.

## Automated protection

`tests/test_evidence_registry.py`, `tests/test_runtime_and_model_io_evidence.py`, `tests/test_bundle_integrity_evidence_v27.py`, `tests/test_release_control_evidence_v28.py`, `tests/test_artifact_attestation_evidence_v29.py`, `tests/test_release_admission_evidence_v30.py`, `tests/test_outcome_review_evidence_v31.py`, `tests/test_business_type_recalibration_evidence_v32.py`, `tests/test_frequency_recalibration_transport_evidence_v33.py` and `tests/test_frequency_recalibration_uncertainty_evidence_v34.py` recompute / verify the main modelling, deployment, monitoring, review-lifecycle, runtime, model-IO, content-addressed-integrity, shadow-release-control, attestation/admission, delayed-outcome, recalibration, cohort-transport and factor-uncertainty headline evidence from persisted result files. `tests/test_evidence_push_static_v31.py` also exercises the concurrent evidence-write path with a detached-HEAD Git race simulation. CI fails if the stored evidence no longer supports the registered claims or if the protected evidence-persistence contract regresses.