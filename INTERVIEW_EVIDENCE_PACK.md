# Interview Evidence Pack

Use this file as the short-form explanation of the project. Every headline number is mapped in `EVIDENCE_REGISTRY.md`; the current rating-factor review is `RATING_FACTOR_REVIEW_PACK.md`, and the committee-ready model-change synthesis is `MODEL_CHANGE_IMPACT_ASSESSMENT.md`. The latest front door is current through v0.53.

## 20-second version

I built a motor-insurance pricing and model-governance workbench to test whether XGBoost actually deserved to replace a GLM. It looked materially better on a French development benchmark — **5.43% lower Poisson deviance** — but the locked Spanish OOT and two preregistered external portfolios did not support promotion: **0/4 external target gates pass** and the committee gate remains **`EVIDENCE_GAP_HOLD` (5/8)**. I then made the model-risk story insurance-specific. On 2022 development data, `driver_age` has a large GLM/XGB frequency response-shape gap (**0.26866**), yet only **0.00159%** of 2024 exposure is strictly outside the observed 2022 driver-age range. `business_type` shows the opposite pattern: a much smaller frequency shape gap (**0.02571**) but **48.60%** 2022→2024 mix TV with **0% unseen exposure**. Separately, after forcing aggregate technical-risk totals equal, **36.81%** of frequency exposure and **78.26%** of pure-premium exposure still differ by more than ±10%. Those are technical-risk redistributions, not customer-price changes, and promotion remains closed.

## 2-minute walkthrough

### 1. Business question

The question was not “can XGBoost beat a GLM on one split?” It was:

> Does the challenger improve the pricing target reliably enough across time and independent portfolios to justify a model-family change, while keeping deployment readiness separate from approval?

That means ranking improvement alone is insufficient. I also need loss-function improvement, calibration, uncertainty, temporal/external transport, reproducibility and a controlled validation lifecycle.

### 2. Development benchmark: strong enough to investigate

On the public French freMTPL2 benchmark, the comparable XGBoost Poisson model reduced weighted Poisson deviance by **5.43%** versus the Poisson GLM with geography and increased claims captured in the highest-risk 10% of exposure from **20.59% to 31.17%**.

That is a meaningful challenger-development signal. It is **not** an OOT pricing uplift, commercial impact or promotion decision.

### 3. First locked calendar OOT: the strong signal does not transport cleanly

I added a separate public Spanish motor portfolio covering 2022–2024. The original design was fixed as:

- **2022:** model training;
- **2023:** aggregate calibration only;
- **2024:** locked out-of-time evaluation at first use.

On **168,085** usable 2024 policy-years:

- frequency Poisson deviance: GLM **1.11854**, XGBoost 1.11884;
- frequency top-10% claim capture: 26.62% vs **27.04%**;
- GLM-minus-XGB frequency bootstrap interval: **[-0.00155, 0.00083]**;
- pure-premium Tweedie deviance: GLM **93.9318**, XGBoost 93.9513.

So XGBoost ranked slightly differently but did not improve the registered target loss functions. The original model-family decision remained **HOLD**.

### 4. Validation data are not infinitely reusable

Later versions used 2024 for monitoring, realised-outcome review, recalibration evaluation, cohort transport and uncertainty work. I therefore added a machine-readable validation-use ledger. Spanish 2024 keeps its historical status as independent at first locked OOT use, but its **current** role is `CONSUMED_RETROSPECTIVE_VALIDATION`.

That means I cannot tune another candidate on 2024 and then call the same period an independent confirmation sample.

### 5. Australia: preregister first, then accept the result

For Australian `ausprivauto0405` (**67,856 policies**), I merged the source/split/features/models/metrics/gates protocol before row-level access.

Registered outcomes:

- **frequency:** GLM 0.814742 vs XGBoost 0.817878; XGB relative deviance improvement **-0.3849%**; bootstrap interval entirely below zero → `NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT`;
- **pure premium:** the frozen origin-main run had GLM 129.8409 vs XGBoost 114.9561, a favourable XGB point estimate, but the bootstrap lower bound was **-10.69%** and top-10 loss capture deteriorated materially → `NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT`.

I did not relax the gates after seeing this mixed result.

### 6. A reproducibility failure became a governance improvement

Repeated Australian runs preserved the negative decisions but exposed sensitivity in one iterative Tweedie GLM point estimate. Instead of hiding it, I separated **decision reproducibility** from **point-metric reproducibility** and changed the prospective external-validation policy: future positive evidence needs a registered solver/tolerance/thread environment plus at least two independent GitHub Actions executions within the registered numerical tolerance.

This is important because a model-governance pipeline should detect when the evidence-generating process itself is unstable.

### 7. Belgium: second preregistered external test with prospective numerical controls

For Belgian `beMTPL97` (**163,212 unique policies**), the protocol was again merged before row-level access. Poisson/Tweedie GLMs used preregistered `newton-cholesky`, `tol=1e-10`, and single-thread numerical settings.

Registered results:

- **frequency:** GLM 0.604357 vs XGBoost 0.602598; XGB **+0.2910%**; bootstrap 95% approximately **[+0.0987%, +0.4876%]**. The direction is favourable, but it misses the fixed **0.5%** materiality threshold → no registered external support;
- **pure premium:** GLM 79.8433 vs XGBoost 79.5863; XGB **+0.3219%**; bootstrap 95% approximately **[-0.7918%, +1.3082%]** → point and CI support gates fail;
- pure-premium top-10 loss capture moves **20.45% → 19.12%**, which I retain as an adverse ranking trade-off.

Two completed Actions executions in different observed Azure regions reproduced all registered aggregate metrics within the preregistered tolerance: maximum absolute difference **1.42×10⁻¹⁴**, maximum relative difference **6.90×10⁻¹⁴**.

Again, reproducible negative decisions remain negative.

### 8. Evidence synthesis: do not average away conflicting evidence

v0.43 builds an aggregate dossier without a pooled meta-analysis or subjective evidence weights. Different portfolios keep their original evidence classes and registered decisions.

Across Australia and Belgium there are **4 preregistered external target gates and 0 passes**. The strong freMTPL2 benchmark remains useful development evidence, but it cannot override the failed external gates.

Current state:

- model-family decision: **HOLD**;
- serving: **HOLD_SHADOW_ONLY**;
- promotion review: **NOT_OPEN**.

### 9. Operational readiness is deliberately not model approval

Separately, the project demonstrates:

- FastAPI/Docker shadow scoring and offline/online parity;
- aggregate monitoring and review hysteresis;
- content-addressed model bundles;
- manual release/rollback control;
- GitHub/Sigstore build provenance;
- attested admission restricted to the **shadow release registry**.

Those controls show that a model can be operationally well governed while still lacking enough validation evidence for pricing promotion.

### 10. Model Change Committee gate

v0.44 converts the evidence dossier into a fail-closed machine readiness check for a hypothetical human model-change review.

Current request `MCR-XGB-MOTOR-001` is:

**`EVIDENCE_GAP_HOLD` — 5 of 8 required gates pass.**

The three blockers are:

1. `G2_LOCKED_TEMPORAL_SUPPORT` — original Spanish OOT does not support a global family switch;
2. `G3_PREREGISTERED_EXTERNAL_SUPPORT` — **0/4** Australian/Belgian external target gates pass;
3. `G4_FRESH_INDEPENDENT_EVIDENCE` — Spanish, Australian and Belgian validation datasets are now consumed.

Even if a `human_signoff_recorded=true` flag is supplied, failed evidence gates cannot be overridden. If all machine gates passed in the future, the highest automatic state would only be `READY_FOR_HUMAN_COMMITTEE_REVIEW`; this code can never authorise model promotion or customer pricing.

### 11. Explain model-family disagreement without reusing outcomes

Once Spanish 2024 had been consumed, I did not use its outcomes to invent another performance claim. v0.47 is a label-free post-hoc diagnostic: it reads rating features and exposure only, uses a fixed 20,000-row sample, and asks how frozen GLM/XGBoost score disagreement changes when one rating factor is replaced by its 2022 training reference.

The exposure-weighted mean absolute `log(XGB/GLM)` disagreement is **0.0993 for frequency** and **0.3171 for pure premium**. The largest descriptive one-factor sensitivities are:

- frequency: `vehicle_brand`, `policy_type`, `vehicle_value`;
- pure premium: `business_type`, `power_to_weight_ratio`, `vehicle_value`.

These effects are explicitly non-additive and non-causal. They are not SHAP values, predictive feature importance or new promotion evidence.

### 12. Translate disagreement into portfolio impact without pretending it is premium

v0.48 uses all **168,085** positive-exposure 2024 feature rows but still reads no 2024 claim/loss outcomes and no actual premium. Before comparing policies, it rescales the challenger so the aggregate XGBoost and GLM predicted technical-risk totals are exactly equal. That removes the overall level difference and isolates redistribution.

After that portfolio-neutral alignment:

- frequency: mean absolute relativity change **10.18%**; **36.81%** of exposure moves by more than ±10%; **10.98%** by more than ±20%;
- pure premium: mean absolute relativity change **32.28%**; **78.26%** of exposure moves by more than ±10%; **58.17%** by more than ±20%.

Major pure-premium segments also move in different directions: NB about **+8.65%** vs P **-6.53%**; COMP_E **+13.68%** vs CC **-9.27%**; driver age 35–49 **+5.20%** vs 50–64 **-5.49%**.

Those are technical-risk score redistributions after aggregate neutralisation. They are **not** realised premium changes, customer impacts, fairness conclusions or commercial recommendations.

The frozen Tweedie GLM still reaches its registered `max_iter=900` limit. Same-head repeat runs keep the displayed redistribution conclusions stable, but I do not claim bitwise reproducibility.

### 13. Put evidence, impact and pricing governance in the right order

v0.49 generates a Model Change Impact Assessment from persisted aggregate evidence only. The sequence is fail closed:

1. **Evidence adequacy:** currently `EVIDENCE_GAP_HOLD`, 5/8 gates, blockers G2/G3/G4, external support 0/4 and no fresh independent validation.
2. **Model impact review:** v0.47/v0.48 explain disagreement and redistribution, but cannot clear the evidence blockers or create promotion authority.
3. **Commercial/customer-pricing governance:** separate and currently out of scope/not authorised.

Current pack disposition is `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`.

This is the main governance lesson: impact analysis matters, but **large impact is not evidence that a challenger is better**, and operational readiness is not statistical approval.

### 14. Inspect rating-factor response shapes on development data

v0.51 goes back to the **2022 development population only** and refits the already frozen frequency specifications. It then varies one rating factor across exposure-weighted q05–q95 values around a common reference profile.

Two examples are especially useful in an insurance interview:

- `driver_age`: maximum absolute GLM/XGBoost log-relativity gap **0.26866**. At q05/q50/q95 ages **30 / 47 / 68**, GLM relativities are about **0.880 / 1.000 / 1.172** while XGBoost is **1.013 / 1.000 / 0.896**.
- `vehicle_age`: maximum gap **0.26771**. At q05/q50/q95 ages **7 / 23 / 44**, GLM is **1.309 / 1.000 / 0.702** while XGBoost is **1.338 / 1.000 / 0.918**.

`vehicle_value` is a useful counterexample: its maximum shape gap is only **0.03394**. So the conclusion is not “XGBoost is non-linear everywhere”.

These are **reference-profile development sensitivities**, not population-average PDPs, causal rating effects, validation results or customer premiums.

### 15. Separate feature support from portfolio mix

v0.52 reads **rating features, year and exposure only** for 2022 and 2024. It does not read claim/loss outcomes and does not fit a model.

I distinguish strict support from central-tail movement:

- strict numeric extrapolation means a 2024 value below the actual observed 2022 minimum or above the observed maximum;
- q01–q99 and q05–q95 exposure are reported separately as tail/mix diagnostics;
- categorical support means whether a 2024 non-missing level was absent from 2022.

The result is that broad numeric extrapolation is negligible. The largest strict out-of-range share is only **0.00227%** of exposure for `power_to_weight_ratio`; `driver_age` is **0.00159%**.

The much larger change is **reweighting among known categories**. For `business_type`, NB/P exposure moves from **96.78% / 3.22%** in 2022 to **48.18% / 51.82%** in 2024. Total-variation distance is **48.60%**, but unseen business-type exposure is **0%**.

That is a stronger monitoring explanation than simply saying “PSI is high”: the current book is not dominated by unknown cells; known rating cells have changed weight dramatically.

### 16. Join rating structure, support, impact and evidence without a composite score

v0.53 generates `RATING_FACTOR_REVIEW_PACK.md` from persisted aggregate evidence only. The review order is:

1. **rating structure** — what response shape did each model learn?
2. **strict support** — is the current book outside development values/categories?
3. **portfolio mix** — have known rating cells reweighted?
4. **portfolio impact** — how differently do frozen model families redistribute technical risk?
5. **evidence adequacy** — do validation gates permit promotion review?
6. **pricing governance** — separate authorisation still required.

`driver_age` and `business_type` explain why I refuse a composite score. Driver age has a **large shape gap (0.26866)** but negligible strict extrapolation (**0.00159%**). Business type has a **small frequency shape gap (0.02571)** but an enormous **48.60%** mix shift.

Those are different model-risk questions. Neither says XGBoost is more accurate. The controlling state therefore remains **`EVIDENCE_GAP_HOLD`, 5/8 gates, 0/4 external support, promotion review NOT_OPEN**.

## Likely interview questions

### If driver age is well supported, why care about the GLM/XGBoost shape gap?

Because support and model structure are different questions. At age 68, both models are still being evaluated inside the observed 2022 development range, yet the reference-profile frequency relativities are about **1.172 for GLM versus 0.896 for XGBoost**. That is useful model-review evidence: the challenger is encoding a materially different age relationship, not merely extrapolating beyond the training range. It still does not tell me which relationship is more accurate — that requires valid outcome evidence.

### If strict extrapolation is near zero, why did monitoring show such large drift?

Because drift can come from **portfolio reweighting**, not unseen values. `business_type` is the clearest example: both NB and P existed in development, so unseen exposure is zero, but their exposure shares nearly reverse by 2024 and the total-variation distance is **48.60%**. “Known cells, very different weights” is a different risk from extrapolation.

### Why not combine shape gap, support drift and impact into one risk score?

They answer different questions and have different evidence roles. A large shape gap does not imply poor support; a large mix shift does not imply model-family disagreement; a large technical-risk redistribution does not prove better predictive performance. A single hand-built score would introduce arbitrary weights and could hide exactly the trade-offs a model reviewer should see.

### What does “78.26% of exposure moves by more than ±10%” actually mean?

It is **not** a statement that 78.26% of customers would receive a >10% premium change. I first force the frozen GLM and XGBoost pure-premium technical-risk totals to be equal across the portfolio, then compare the resulting technical-risk relativities. The 78.26% figure is the exposure share where those two technical-risk indications differ by more than 10%. Actual premiums would also involve expenses, commission, reinsurance, profit, tax, commercial strategy, underwriting and other controls that this project does not model.

### Why do impact analysis when the promotion gate is already HOLD?

Because a real model-change review needs two separate questions answered: **is the evidence strong enough to consider changing the model, and what would the model change do if considered?** The current evidence fails the first question, so impact diagnostics cannot trigger promotion. But quantifying disagreement and redistribution makes the project ready for a future review without confusing impact with performance evidence.

### Why keep a GLM reference?

GLMs are strong insurance baselines and make the incremental value of complexity explicit. The point is not that GLMs are automatically preferable; it is that a challenger should demonstrate enough incremental value to justify additional complexity and governance burden.

### Why use XGBoost at all if the final decision is HOLD?

Because the benchmark showed a real development signal: **5.43% lower Poisson deviance** and substantially higher top-decile claim capture. A good challenger process should investigate that signal rather than assume the simpler model wins. The stronger validation stages then determine whether the gain survives.

### Why not promote XGBoost when Belgian frequency has a positive bootstrap interval?

Because the preregistered Belgian rule required both positive uncertainty evidence **and at least 0.5% relative deviance improvement**. The observed improvement is **0.291%**. Changing or rounding the materiality threshold after seeing the result would invalidate the prospective test.

The 0.5% threshold is a **project demonstration rule**, not an insurer or regulatory standard.

### Why not tune on Australia or Belgium now that you know where XGBoost struggled?

I can use those datasets for diagnostics or frozen-protocol regression, but not for a new claim of independent confirmation. Their outcomes have been inspected, so the validation-use ledger marks them consumed. A genuinely new candidate-selection claim needs new unseen data or a new independent period.

### Why no pooled score across Spain, Australia and Belgium?

The portfolios differ in geography, period, feature definitions and context. A hand-built weighted score could hide those differences and let me choose weights that favour the challenger. I retain each registered decision instead. The synthesis answers a governance question — whether the existing evidence is sufficient to open promotion review — rather than claiming a pooled causal effect.

### What did you learn from the Australian numerical reproducibility issue?

A stable decision is not the same as a stable point estimate. One iterative GLM point metric shifted across hosted executions even though both registered decisions stayed negative. I made that visible and prospectively tightened solver, tolerance, thread and multi-run requirements. The Belgian implementation then reproduced within those pre-set tolerances across two observed runner regions.

### Why does deployment readiness not open promotion review?

Because software controls answer a different question. Shadow serving, monitoring, rollback and provenance show that the system can be operated safely as a project demo. They do not prove the challenger improves the pricing target. v0.44 therefore has operational gates passing while evidence gates keep the request on HOLD.

### What would reopen the model-family review?

A genuinely new external dataset or independent calendar period whose outcomes have not been inspected, with source/split/features/models/metrics/gates and numerical controls registered before row-level access. Any positive external result would also need the two-independent-Actions reproducibility requirement. Even then, the machine gate would only open a human review; a separate authorised governance decision would still be required.

### What would you do differently inside a real insurer?

I would use governed rating and claims data with as-of feature lineage; align acceptance thresholds with pricing/actuarial/model-risk stakeholders; incorporate expense, reinsurance and commercial constraints; examine proxy/fairness and regulatory obligations; and run controlled prospective shadow monitoring. The public project demonstrates the evaluation and governance mechanics, not insurer-specific approval.

## STAR version

**Situation:** XGBoost looked materially stronger than a Poisson GLM on a standard motor-frequency development benchmark.

**Task:** Determine whether that apparent improvement was reliable enough across time and independent portfolios to justify opening a model-family promotion review, then make the model-change story interpretable at insurance rating-factor level without confusing technical-risk impact with customer pricing.

**Action:** I built a locked Spanish calendar OOT track, added validation-use ledgers to prevent holdout recycling, preregistered Australian and Belgian external replications before row-level access, retained negative/mixed results without relaxing gates, added numerical-reproducibility controls, and linked the evidence to shadow deployment and a fail-closed Model Change Committee gate. After the validation data were consumed, I used label-free diagnostics to quantify frozen GLM/XGBoost disagreement and portfolio-neutral technical-relativity redistribution. I then added a 2022-only rating-factor response-shape audit and a separate label-free 2022→2024 support/mix audit, before generating a v0.53 review pack that keeps response shape, extrapolation, portfolio mix, impact and evidence adequacy as separate questions.

**Result:** The original **5.43%** development signal did not become a stable promotion case: Spanish OOT stayed HOLD, **0/4** preregistered Australian/Belgian target gates passed, and the committee gate remains **`EVIDENCE_GAP_HOLD` with 5/8 gates passing**. The rating-factor review also shows why model risk cannot be reduced to one number: `driver_age` has a **0.26866** model-family shape gap with only **0.00159%** strict extrapolation, while `business_type` has a **0.02571** frequency shape gap but **48.60%** mix TV and zero unseen exposure. Portfolio-neutral diagnostics still show material technical-risk redistribution, especially pure premium where **78.26%** of exposure differs by more than ±10%. None of these diagnostics overrides the failed evidence gates; model promotion and customer pricing remain unauthorised.

## Claims to avoid

Do not say:

- “XGBoost improved motor pricing by 5.4%.” The 5.43% result is frequency deviance on a cross-sectional development benchmark.
- “The external studies prove GLM is universally better.” Australia and Belgium answer registered model-family questions in their own portfolio contexts; some XGBoost point/ranking metrics are favourable.
- “Belgian frequency passed because its bootstrap CI is positive.” It failed the preregistered 0.5% materiality gate.
- “The 0.5% threshold is an industry standard.” It is a project review rule.
- “The project proves the model works for UK motor insurance or FIRST CENTRAL.” It does not.
- “The model was approved by a committee.” v0.44 is a machine readiness gate for a hypothetical human review; no human approval is recorded.
- “Deployment, attestation or rollback proves the model is safe for customer pricing.” Those are operational/provenance controls, not pricing approval.
- “The project increased profit or conversion.” No observed commercial uplift is claimed.
- “The v0.48 ±10% / ±20% migration figures are customer premium changes.” They are portfolio-neutral technical-risk score redistributions with no actual premium, commercial or pricing-action model.
- “The driver-age curve proves age causes higher/lower claim risk.” v0.51 is a one-factor reference-profile development sensitivity, not a causal estimate or population-average PDP.
- “A 48.60% business-type TV means half the portfolio is out of support.” Both business-type levels were already seen in 2022; the number measures exposure-share reweighting, while unseen exposure is 0%.
- “v0.53 gives a single model-risk score.” It deliberately refuses a composite score because response shape, support, mix, impact and validation answer different questions.
