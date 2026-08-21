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
| v0.21 artifact integrity | four serialised models have registered SHA-256 digests | `action_results/v21/manifest.json` |
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
- v0.25 exact parity is evidence for the locked 25-record test set and current bundle; it does **not** prove arbitrary cross-version portability. The successful benchmark still emitted an XGBoost warning when loading the joblib/pickle-serialised model across the training/runtime XGBoost version difference.
- Synthetic quote-conversion / proposition experiments are not reported as observed commercial impact.
- No result in this repository establishes transport to FIRST CENTRAL or the UK motor market.

## Automated protection

`tests/test_evidence_registry.py` recomputes / verifies the main modelling, deployment, monitoring, review-lifecycle and runtime headline evidence from persisted result files. CI fails if the stored evidence no longer supports the registered claims.
