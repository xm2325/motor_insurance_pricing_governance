# v0.51 — 2022 development rating-factor relativity audit

## Purpose

v0.51 adds an insurance-pricing interpretability diagnostic that asks a narrower question than validation:

> For the same supported 2022 reference policy profile, how do the frozen Poisson GLM and XGBoost frequency specifications change their technical-risk relativity when one rating factor is varied at a time?

This is deliberately **development-only**. The workflow reads 2022 rating features, exposure and claim counts to refit the already registered frequency specifications. It reads no 2023/2024 rows, incurred losses, actual premiums, customer IDs or policy status. It does not create validation evidence, candidate-selection authority, model-promotion evidence or customer-pricing authority.

The output is a **reference-profile sensitivity audit**, not a population-average partial-dependence plot, causal effect, realised premium effect or statement that one response shape is objectively correct.

## Data and model contract

Actions run 32699530679 verified:

- source: Mendeley `sw4jmdb2sm` v1, source SHA-256 `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4`;
- year read: **2022 only**;
- usable development rows: **67,171**;
- exposure: **41,912.4959**;
- observed claims used for the development frequency fit: **12,664**;
- model definitions: `build_deployment_bundle_v21.py::model_definitions`;
- models: Poisson GLM reference and XGBoost Poisson challenger only;
- calibration is not applied because each factor sweep is normalised to the model's own reference-profile score, so a global multiplicative calibration factor cancels from the relativity;
- numeric grids use exposure-weighted 2022 q05, q10, q20, ..., q90, q95 support;
- categorical grids use the ten highest-exposure 2022 levels plus the reference level if required.

The common exposure-weighted reference profile is:

`driver_age=47`, `vehicle_age=23`, `age_driving_licence=21`, `vehicle_value=24693.375`, `seats=5`, `power_to_weight_ratio=12`, `policy_type=CC`, `business_type=NB`, `payment_frequency=A`, `bonus_score=G`, `fuel_type=D`, `vehicle_brand=RENAULT`, `municipality_type=I`, `circulation_area=U`.

## Numeric rating-factor response shapes

The most informative result is not simply that XGBoost is more flexible. The two model families imply materially different *shapes* for some factors while staying close for others.

### Driver age

Across the exposure-supported q05–q95 values (**30 → 68 years**):

| Driver age | GLM relativity | XGB relativity | XGB / GLM |
|---:|---:|---:|---:|
| 30 | 0.880 | 1.013 | 1.152 |
| 47 reference | 1.000 | 1.000 | 1.000 |
| 59 | 1.095 | 0.899 | 0.822 |
| 68 | 1.172 | 0.896 | 0.764 |

The GLM response is smooth and monotonic over this grid: technical frequency relativity rises with driver age. The XGBoost reference-profile response is close to flat through roughly the middle of the support, then moves down at older ages. The largest absolute `log(XGB relativity / GLM relativity)` gap is **0.26866** at age 68.

This does **not** establish that the GLM age trend is correct or that older drivers should receive a higher customer premium. It exposes a model-family structural difference that would need actuarial/data review before a real rating change.

### Vehicle age

Across q05–q95 (**7 → 44 years**):

| Vehicle age | GLM relativity | XGB relativity | XGB / GLM |
|---:|---:|---:|---:|
| 7 | 1.309 | 1.338 | 1.022 |
| 10 | 1.245 | 1.053 | 0.846 |
| 23 reference | 1.000 | 1.000 | 1.000 |
| 32 | 0.859 | 1.001 | 1.165 |
| 44 | 0.702 | 0.918 | 1.307 |

The GLM again produces a smooth monotonic response, here declining with vehicle age. XGBoost falls sharply from the youngest supported point, stays much flatter through the middle of the grid, and declines again at older vehicles. The maximum absolute log-relativity gap is **0.26771**, at vehicle age 44.

### Other numeric factors

| Factor | Max absolute log-relativity gap | Interpretation |
|---|---:|---|
| `age_driving_licence` | **0.17069** | Material divergence at the high end of the supported grid; at 37 years GLM relativity is ~0.907 vs XGB ~1.076 |
| `seats` | 0.07232 | Sparse/discrete support; most weighted quantiles are five seats, so do not over-interpret as a smooth numeric response |
| `power_to_weight_ratio` | 0.06065 | Model families broadly close through most support, with larger divergence at q95 |
| `vehicle_value` | **0.03394** | Relatively similar model-family response across the supported grid |

The `vehicle_value` result is useful precisely because it is *not* dramatic: a flexible model does not imply large non-linear differences for every rating factor.

## Categorical rating factors

The largest categorical gap occurs for `policy_type=TP`, but that level represents only **1.22%** of 2022 exposure, so it is retained in the machine artifact rather than promoted as a headline.

More interpretable examples are:

| Factor / level | 2022 exposure share | GLM relativity | XGB relativity | Comment |
|---|---:|---:|---:|---|
| `vehicle_brand=BMW` | **4.14%** | 1.328 | 1.174 | XGB reference-profile brand relativity is ~11.6% lower than the GLM relativity |
| `municipality_type=IS` | **7.27%** | 0.888 | 0.947 | Moderate model-family difference on a larger supported group |
| `fuel_type=G` | **36.07%** | 0.876 | 0.890 | Very similar despite substantial exposure |
| `circulation_area=R` | **45.98%** | 0.904 | 0.925 | Very similar despite substantial exposure |
| `business_type=P` | **3.22%** | 1.029 | 1.003 | Small frequency response difference in 2022 development data |

For `vehicle_brand`, only the ten highest-exposure brands are displayed, covering **72.66%** of 2022 exposure; this is not an exhaustive category-effect analysis.

## Reproducibility observation

Two hosted executions of the unchanged factor-audit implementation were compared during PR development. XGBoost numeric and categorical relativities were identical at all persisted points. The maximum run-to-run absolute difference in GLM relativity was approximately **8.0×10⁻⁸** for numeric points and **3.9×10⁻⁸** for categorical points. This does not create validation evidence; it only supports reporting the development response shapes at the precision shown above.

The final immutable main snapshot will be registered after merge.

## What v0.51 adds to the project

The project already showed that a flexible challenger can have stronger development metrics but fail to build a stable promotion case across time/external portfolios. v0.51 adds a different insurance-pricing skill: **rating-structure interpretation**.

A defensible model-change discussion can now distinguish:

1. **performance evidence** — whether XGBoost improves registered validation targets;
2. **rating structure** — how GLM and XGBoost translate supported factor changes into technical-risk relativities;
3. **portfolio impact** — how frozen model families redistribute technical risk after aggregate neutralisation (v0.48);
4. **pricing governance** — a separate decision that remains unauthorised.

That separation is important. A response curve can be interpretable without being validated, and a materially different response curve is a reason for review rather than evidence for promotion.

## Governance boundary

v0.51 leaves the project decision unchanged:

- model-family decision: **`HOLD`**;
- serving: **`HOLD_SHADOW_ONLY`**;
- committee readiness: **`EVIDENCE_GAP_HOLD`**;
- promotion review: **not opened by this diagnostic**;
- customer pricing: **not authorised**.

No result establishes transfer to FIRST CENTRAL, the current UK motor market, a causal rating-factor effect, a fairness conclusion, an observed premium change, or commercial uplift.
