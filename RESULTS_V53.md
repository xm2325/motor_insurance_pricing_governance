# v0.53 — Rating-factor review pack

## Purpose

v0.53 does not fit a new model or run another validation exercise. It creates one evidence-first review pack from already persisted aggregate evidence so a reviewer can answer, in order:

1. what rating-factor response shape did each frozen frequency model learn?
2. does the 2024 feature population sit outside the 2022 development support?
3. have already-known rating cells materially reweighted?
4. how much technical-risk redistribution remains between frozen model families after aggregate neutralisation?
5. is the validation evidence strong enough to open promotion review?
6. if not, what remains outside technical model review and requires separate pricing governance?

The generated artifact is `RATING_FACTOR_REVIEW_PACK.md`; the machine-readable source is `results_v53/rating_factor_review_pack_v53.json` and, after a successful main run, `action_results/v53/rating_factor_review_pack_v53.json`.

## Evidence boundary

The generator reads only persisted aggregate artifacts from v0.51, v0.52 and v0.49. It does not read the Spanish row-level source, claim or loss outcomes, premiums, customer IDs or policy status. It imports no modelling library, performs no model fit and creates no new performance/support threshold or composite risk score.

Source roles remain unchanged:

- v0.51: development-only reference-profile frequency interpretability;
- v0.52: post-hoc label-free feature support and mix audit on consumed 2024 features;
- v0.49: aggregate synthesis of existing model-impact and committee evidence.

## Review finding 1 — shape disagreement can be large inside supported data

For `driver_age`, the frozen Poisson GLM and XGBoost frequency specifications have a maximum absolute log-relativity gap of **0.26866** across the exposure-weighted 2022 q05–q95 grid. The q05/q50/q95 ages are **30 / 47 / 68**.

Yet only **0.00159%** of 2024 exposure lies strictly outside the actual observed 2022 driver-age range. The 2024 share outside the 2022 q05–q95 interval is **8.75%**.

For `vehicle_age`, the corresponding shape gap is **0.26771**, while strict 2024 out-of-range exposure is only **0.00079%**.

This matters because model-structure disagreement is not the same as extrapolation risk: both models can disagree materially while operating on feature values that remain well supported by development data.

## Review finding 2 — large portfolio change can occur without unseen categories

`business_type` shows the opposite pattern. Its v0.51 frequency response-shape gap is only **0.02571**, but the 2022→2024 exposure-share total-variation distance is **48.60%**.

Under the identical positive-exposure feature filter used by v0.52:

- `NB`: **96.78% → 48.18%** exposure;
- `P`: **3.22% → 51.82%** exposure;
- unseen 2024 business-type exposure: **0%**.

So the important monitoring issue is not unfamiliar categories. It is large reweighting among categories already present in development.

`vehicle_brand` provides a useful secondary check. Six 2024 brands are absent from 2022, but together they account for only about **0.00345%** of exposure. Meanwhile `BMW` was about **4.14%** of 2022 development exposure in the v0.51 displayed grid, with GLM/XGBoost frequency relativities **1.328 / 1.174** around the common reference profile.

## Review finding 3 — equal aggregate technical-risk totals can hide material redistribution

The v0.49 impact synthesis carries forward the frozen-model portfolio-neutral diagnostic: aggregate predicted technical-risk totals are forced equal before measuring redistribution.

Even after that neutralisation:

- frequency mean absolute relativity redistribution is **10.18%**;
- **36.81%** of exposure changes by more than ±10% on frequency relativity;
- pure-premium mean absolute relativity redistribution is **32.28%**;
- **78.26%** of exposure changes by more than ±10% on pure-premium relativity;
- **58.17%** changes by more than ±20%.

For the two dominant 2024 business-type groups, pure-premium total relativity shifts are approximately **+8.67% for NB** and **−6.53% for P**.

These are technical-risk score redistributions only. They are not realised customer premium changes, commercial outcomes or pricing recommendations.

## Why v0.53 refuses a composite score

The project now deliberately separates four questions:

- **response shape** — do model families encode different technical-risk relationships?
- **strict support** — is the current book outside values/categories seen in development?
- **portfolio mix** — have known rating cells reweighted?
- **portfolio impact** — how differently do frozen model families distribute technical risk?

`driver_age` and `business_type` demonstrate why these cannot be collapsed safely: the former has a large shape gap with negligible strict extrapolation; the latter has a small frequency shape gap but an enormous mix shift.

No project-defined acceptance threshold or composite risk score is introduced in v0.53.

## Evidence adequacy remains controlling

The rating-factor review is explanatory, not promotional. The existing committee state remains:

- `EVIDENCE_GAP_HOLD`;
- **5/8** machine gates pass;
- external target support **0/4**;
- fresh independent validation unavailable;
- blockers `G2_LOCKED_TEMPORAL_SUPPORT`, `G3_PREREGISTERED_EXTERNAL_SUPPORT`, `G4_FRESH_INDEPENDENT_EVIDENCE` remain unresolved;
- promotion review `NOT_OPEN`;
- model family `HOLD`;
- serving `HOLD_SHADOW_ONLY`;
- customer pricing not authorised.

The review pack therefore improves model-review clarity without converting development interpretability, label-free monitoring or post-hoc impact diagnostics into fresh validation evidence.

## Claim boundary

No v0.53 result establishes transfer to FIRST CENTRAL or the current UK motor market. No causal, fairness, customer-premium or commercial-uplift conclusion is claimed.
