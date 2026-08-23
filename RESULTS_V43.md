# v0.43 — Model-family evidence synthesis and challenger review pack

## Purpose

Turn the already-persisted modelling and validation evidence into one machine-verifiable review dossier that answers a model-risk question: **does the current evidence support opening XGBoost model-family promotion review?**

v0.43 is aggregate-only. It does not download source portfolios, read row-level outcomes, fit or recalibrate a model, alter hyperparameters, resplit data, change any historical threshold, or re-open a consumed validation set.

## Synthesis design

The dossier keeps each evidence source in its original class rather than forcing heterogeneous portfolios into one pooled score:

- freMTPL2 cross-sectional frequency benchmark — development evidence only;
- Spanish 2024 — locked OOT at first use, now consumed retrospective validation;
- Australian `ausprivauto0405` — preregistered external model-family replication, now consumed external validation;
- Belgian `beMTPL97` — preregistered external model-family replication with observed two-run numerical reproducibility, now consumed external validation.

No pooled meta-analysis and no subjective evidence weights are used. A historical registered gate failure remains a failure; numerical reproducibility can strengthen confidence in the measurement but cannot convert a negative model-support gate into a positive one.

## Evidence pattern

The evidence is deliberately mixed:

- the cross-sectional freMTPL2 benchmark has a strong XGBoost frequency signal;
- the original Spanish 2024 locked frequency and pure-premium deviances are slightly lower for GLM, and the registered model-change decision is HOLD;
- Australian frequency favours GLM; Australian pure premium has a favourable XGBoost point estimate but fails bootstrap confirmation;
- Belgian frequency has a small favourable XGBoost direction but misses the fixed 0.5% materiality gate; Belgian pure premium fails point/CI support;
- both Belgian negative registered decisions reproduce across the two completed observed GitHub Actions executions within the preregistered numerical tolerance.

Thus **0 of 4 preregistered external target gates pass** across the Australian and Belgian portfolios.

## Review decision

`HOLD / HOLD_SHADOW_ONLY`; `promotion_review_status = NOT_OPEN`.

This does not claim that XGBoost is universally inferior to GLM. It means the current evidence does not support promotion under the project's registered contracts. Cross-sectional development performance cannot override failed independent validation gates.

## What would reopen review

A future review requires genuinely new independent evidence whose outcomes have not already been inspected, with the protocol merged before row-level access. Any positive external-support result must pass its own prospective model-performance gates and the two-independent-Actions numerical-reproducibility requirement inherited from v0.38-v0.42. Even then, model promotion or a customer-pricing change would require a separate authorised governance decision.

## Boundaries

This is a project model-risk/challenger review pack, not an insurer approval policy. It makes no claim of transport to FIRST CENTRAL or the current UK motor market and no claim of observed commercial uplift.
