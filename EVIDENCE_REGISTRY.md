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

## Interpretation rules

- The 5.43% frequency result is a **cross-sectional benchmark result**, not an out-of-time pricing improvement.
- The 0.42 pp 2024 claim-capture gain is a **ranking result** and does not establish lower pricing loss.
- The 0.32% rolling-origin frequency-deviance reduction is a **small model-family stability result**, not a pure-premium improvement.
- v0.21 demonstrates **deployability in shadow mode**, not approval to use XGBoost for customer pricing.
- The v0.21 TestClient latency is a GitHub-runner diagnostic, not a production SLA.
- Synthetic quote-conversion / proposition experiments are not reported as observed commercial impact.
- No result in this repository establishes transport to FIRST CENTRAL or the UK motor market.

## Automated protection

`tests/test_evidence_registry.py` recomputes / verifies the main modelling and deployment headline evidence from persisted result files. CI fails if the stored evidence no longer supports the registered claims.
