# v0.42 — Belgian external reproducibility and validation closeout

## Status

`V42_BELGIAN_EXTERNAL_CLOSEOUT_PASS`

v0.42 is aggregate-only. It does not download `beMTPL97`, read Belgian row-level outcomes, fit a model, recalibrate a model, change a feature, change a solver, resplit data or rerun the locked-test analysis. It audits the already-observed v0.41 executions and closes the Belgian dataset for future candidate selection.

## Execution lineage

Three v0.41 events are deliberately kept distinct:

1. **Run 32637645586** accessed and audited the pinned source, then aborted before any model fit because the implementation compared the registered Python major.minor string `3.12` with the exact patch string `3.12.14`. It generated no locked-test model metrics and is not counted as a completed model execution.
2. **Run 32637809066** completed the frozen protocol on an `eastus2` GitHub-hosted runner. Its uploaded artifact ZIP has SHA-256 `18eacc7a39a460b01021e9295b4241779738e566206668782b147372f56abcb5`.
3. **Run 32637884887** independently completed the same frozen protocol on a `centralus` runner after merge to main. It was persisted as immutable origin evidence under `action_results/v41/origin/32637884887/`. Its artifact ZIP has SHA-256 `34b59e5e492d434bcb3e85856acb7b53a6298aeb8b138f3df18158e821151bf8`.

Both completed executions used the same source file SHA-256 `955a821a7a693bf18076c425e4d5a5a99889f3c89e1fbd99eca6239c11e963a6`, the same v0.40 protocol and the same single-thread numerical environment.

## Registered result remains negative

### Frequency

Main immutable origin evidence records:

- Poisson GLM deviance: `0.604356714368424`;
- XGBoost deviance: `0.6025982649080157`;
- relative XGBoost improvement: **0.290962%**;
- paired 500-draw bootstrap 95% interval: **[0.098721%, 0.487631%]**;
- calibration-scale and aggregate-calibration checks: pass;
- preregistered minimum point improvement: **0.5%**;
- registered decision: `NO_SECOND_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT`.

The bootstrap interval is above zero but the effect is below the preregistered materiality threshold. The project does not round 0.291% up to 0.5% and does not relax the threshold after seeing the result.

### Pure premium

Main immutable origin evidence records:

- Tweedie GLM deviance: `79.84331051378416`;
- XGBoost deviance: `79.58630762159916`;
- relative XGBoost improvement: **0.321884%**;
- paired 500-draw bootstrap 95% interval: **[-0.791760%, 1.308226%]**;
- calibration-scale and aggregate-calibration checks: pass;
- registered decision: `NO_SECOND_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT`.

The point improvement is below 0.5% and the bootstrap lower bound is below zero. The descriptive top-10% exposure loss capture also moves against XGBoost, from **20.45% to 19.12%**; that adverse ranking trade-off remains in the evidence.

## Numerical reproducibility result

The v0.40 protocol registered point-metric reproducibility tolerances of:

- relative tolerance `1e-8`;
- absolute tolerance `1e-10`.

Across the two completed model executions (`eastus2` and `centralus`), all registered aggregate numeric metrics are within those tolerances. The largest observed absolute difference is approximately **1.42e-14**, on the pure-premium GLM deviance. The largest observed relative difference is approximately **6.90e-14**, far below the registered threshold.

This is recorded as:

`V42_BELGIAN_POINT_METRICS_REPRODUCED_WITHIN_REGISTERED_TOLERANCE`

The result is intentionally narrower than “deterministic everywhere”. Two observed GitHub-hosted runner allocations reproduced within the registered tolerance. v0.42 does not claim universal bitwise determinism and does not establish hardware or Azure region as the cause of the earlier Australian v0.38 instability.

The contrast with v0.38 is nevertheless operationally useful: the Belgian protocol used an explicit `newton-cholesky` solver, `tol=1e-10` and a single-thread OpenMP/OpenBLAS/MKL environment, and the two observed completed executions were numerically stable within the preregistered tolerance.

## Why a second run does not turn this into support

v0.40 required at least two independent executions **before a positive external-support result could stand**. Neither Belgian registered gate was positive in the first completed execution. Therefore the negative decision did not need a second run to become valid; the main run supplies an additional numerical-reproducibility observation, not a mechanism for changing the failed gates.

Two reproducible failures remain failures.

## Belgian validation-use firewall

After v0.41, `beMTPL97` is now:

`CONSUMED_EXTERNAL_VALIDATION_DATASET`

The 32,643-row locked test has been inspected and reproduced. It cannot provide fresh candidate-selection or independent-confirmation evidence again.

Allowed future uses are limited to frozen-protocol regression reproduction, numerical-reproducibility audit, clearly labelled post-hoc diagnostics without candidate selection, governance contract testing and aggregate evidence synthesis.

Forbidden future uses include new model/calibration fitting, hyperparameter search, post-outcome feature changes, solver/tolerance changes intended to improve the locked-test result, resplitting/reseeding for candidate selection, new candidate selection, new independent-confirmation claims, model-family promotion authorisation or customer-pricing authorisation.

## Governance decision

v0.42 remains:

- model-family decision: `HOLD`;
- serving status: `HOLD_SHADOW_ONLY`;
- model promotion authorised: no;
- pricing change authorised: no.

The Belgian result is a second external portfolio replication, not direct validation of Spanish/Australian fitted parameters and not evidence of transfer to FIRST CENTRAL or the current UK motor market.
