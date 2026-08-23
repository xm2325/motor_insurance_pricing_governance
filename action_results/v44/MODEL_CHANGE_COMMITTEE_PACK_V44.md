# v0.44 Model Change Committee Gate

## Current machine decision

**EVIDENCE_GAP_HOLD — do not advance the XGBoost model-family request to human approval review.**

This result is intentionally stricter than deployment readiness. The project can package, attest, shadow-score and roll back models, but those operational controls do not replace validation evidence.

## Gate matrix

| Gate | Status | Evidence |
|---|---|---|
| G1_DEVELOPMENT_SIGNAL | PASS | freMTPL2 XGBoost frequency relative deviance improvement is 5.4274%; development benchmark only. |
| G2_LOCKED_TEMPORAL_SUPPORT | FAIL | Spanish 2024 registered decisions remain HOLD for frequency and pure premium; both original locked target gates are not supportive of a global family switch. |
| G3_PREREGISTERED_EXTERNAL_SUPPORT | FAIL | Preregistered external target gates passed: 0/4. |
| G4_FRESH_INDEPENDENT_EVIDENCE | FAIL | Spanish 2024, Australian ausprivauto0405 and Belgian beMTPL97 are all consumed for fresh candidate selection; no current fresh independent validation dataset is available. |
| G5_REPRODUCIBILITY_CONTROL | PASS | Prospective two-independent-Actions reproducibility rule is registered; Belgian observed point metrics reproduced within registered tolerance. |
| G6_SHADOW_DEPLOYMENT_BOUNDARY | PASS | v0.21 manifest is HOLD_SHADOW_ONLY and explicitly limits scores to shadow comparison rather than customer pricing. |
| G7_RELEASE_AND_ROLLBACK_CONTROL | PASS | v0.28 release-control replay rejects unauthorised rollback, performs no automatic serving switch from review, and performs no pricing change. |
| G8_ATTESTED_SHADOW_ADMISSION | PASS | v0.30 attested release admission permits shadow-registry entry only, with zero raw-source-data archive members and no model-family promotion authority. |

## Blocking evidence gaps

- `G2_LOCKED_TEMPORAL_SUPPORT`: the original Spanish locked OOT did not support a global model-family switch.
- `G3_PREREGISTERED_EXTERNAL_SUPPORT`: Australia + Belgium provide four preregistered external target gates and **0 passes**.
- `G4_FRESH_INDEPENDENT_EVIDENCE`: all three validation datasets currently used for model-family decisions are consumed; none can be relabelled fresh by rerunning or retuning.

## Controls already demonstrated

- Development signal exists in the cross-sectional freMTPL2 frequency benchmark.
- Prospective numerical-reproducibility policy exists; Belgian negative decisions reproduced within registered tolerance.
- Shadow deployment, manual rollback control and attested shadow admission are demonstrated.

## Fail-closed approval boundary

Even a recorded human sign-off flag cannot override a failed evidence gate in this project contract. If every required machine gate passed, the only possible result would be `READY_FOR_HUMAN_COMMITTEE_REVIEW` — never automatic model promotion or customer pricing.

This is a project governance demonstration, not FIRST CENTRAL policy and not evidence of current UK-market transport.
