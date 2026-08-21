# Interview Evidence Pack

Use this file as the short-form explanation of the project. Every headline number below is mapped in `EVIDENCE_REGISTRY.md`.

## 20-second version

I built a motor-insurance pricing and model-governance workbench to test whether a more flexible ML challenger actually deserved to replace a GLM. XGBoost looked substantially better on a cross-sectional frequency benchmark, but I then challenged that result using a separate 354,140-policy-year longitudinal portfolio with a locked 2022 train, 2023 calibration and 2024 out-of-time test. In 2024, XGBoost captured only 0.42 percentage points more claims in the highest-risk 10% of exposure and did not improve Poisson deviance; the bootstrap interval crossed zero. Rolling-origin retraining later produced a small 0.32% frequency-deviance gain, but no stable pure-premium advantage, so I kept the model-family decision at HOLD.

## 2-minute walkthrough

### 1. Business question

The question was not "can XGBoost beat a GLM on one split?" It was:

> Does the challenger improve the pricing target reliably enough, across time and customer cohorts, to justify a model-family change?

That changes the evaluation design. A higher ranking metric alone is not enough if calibration, expected loss or temporal transport deteriorate.

### 2. Cross-sectional benchmark

On the French freMTPL2 benchmark, the full-data XGBoost Poisson model reduced weighted Poisson deviance by 5.43% relative to the Poisson GLM with the same geography variables, and increased claims captured in the highest-risk 10% of exposure from 20.59% to 31.17%.

That was strong enough to justify a challenger, but not enough to justify deployment.

### 3. Real calendar OOT

I then added a separate public Spanish motor portfolio with 354,140 policy-year records and 47 variables. GitHub Actions downloads and audits the raw source before modelling.

The locked design is:

- 2022: train;
- 2023: estimate an aggregate calibration scale only;
- 2024: untouched out-of-time evaluation.

The feature contract excludes current premiums, current claim counts, current incurred losses, policy status, year and customer ID from the predictive feature set.

### 4. 2024 result

On 168,085 usable 2024 policy-years:

- Poisson GLM deviance: 1.11854;
- XGBoost Poisson deviance: 1.11884;
- top-10% claim capture: 26.62% vs 27.04%;
- 250-bootstrap GLM-minus-XGB deviance interval: [-0.00155, 0.00083].

So XGBoost ranked a little better, but the overall loss function did not improve and the uncertainty interval crossed zero.

Pure premium gave the same governance answer:

- Tweedie GLM deviance: 93.9318;
- XGBoost Tweedie deviance: 93.9513;
- calibration: 0.953 vs 0.934;
- bootstrap interval crossed zero.

### 5. Rolling-origin check

I did not retune the locked 2024 result. Instead, I used rolling-origin evaluation as a separate stability diagnostic.

- 2022 -> 2023: no stable XGBoost frequency advantage;
- 2022+2023 -> 2024: XGBoost achieved a small 0.32% frequency-deviance reduction, with a positive bootstrap interval;
- pure premium still did not show a stable XGBoost advantage.

That tells me the frequency result is sensitive to how recent the training data are. It does not justify changing the pricing-model family on its own.

### 6. Transport by customer cohort

The 2024 population contains both returning and new policy IDs.

Pure-premium calibration:

- returning policies: GLM 0.994, XGBoost 0.950;
- new policies: GLM 0.825, XGBoost 0.881.

The relative model performance changes across cohorts. That is another reason to avoid a global promotion decision based only on aggregate metrics.

### 7. Decision

**HOLD / no model-family promotion.**

I would require the challenger to improve the actual pricing target, remain acceptably calibrated, and transport across relevant customer cohorts and time windows. A small frequency-only gain is not sufficient.

## Likely interview questions

### Why keep a GLM reference?

GLMs give a strong statistical baseline for insurance frequency and pure-premium modelling. They are comparatively easy to audit, their multiplicative effects are familiar in pricing work, and they make it easier to determine whether the complexity of a challenger buys enough incremental value.

### Why use XGBoost at all?

It can capture nonlinearities and interactions that a simple GLM specification may miss. The cross-sectional benchmark demonstrated that this can materially improve frequency ranking. The point of the project was to test whether that improvement survives stronger validation.

### Why not promote XGBoost if top-10 capture is higher?

Because top-risk capture is only one ranking metric. A pricing-model change should improve the target loss function and calibration as well. In the locked 2024 test the frequency deviance did not improve, the bootstrap interval crossed zero, and the pure-premium model did not show a stable gain.

### Why use a separate calibration year?

To avoid using the final test period to set the aggregate price level. The 2023 calibration factor is locked before any 2024 evaluation. This separates calibration from performance measurement and prevents a test-period scaling adjustment from making a model look better than it would have been prospectively.

### Why rolling-origin validation after a locked OOT test?

To understand temporal stability, not to replace the locked test. The rolling-origin windows show whether the model-family conclusion is repeatable as the information set expands. They showed that XGBoost frequency becomes slightly better with fresher data, while pure premium still does not support promotion.

### Why separate new and returning business?

A model can be well calibrated in aggregate while transporting differently to customers with no prior portfolio history. The 2024 result shows this directly: the GLM is closer on returning policies, while XGBoost is closer on new policies. That matters for pricing strategy and monitoring.

### What would you do next in a real insurer?

I would move from public demonstration data to the insurer's governed rating data, verify as-of feature lineage, include expense/reinsurance/commercial components, agree acceptance thresholds with pricing and actuarial stakeholders, check relevant proxy/fairness risks, and run prospective shadow monitoring before any controlled deployment.

## STAR version

**Situation:** A flexible XGBoost challenger looked much stronger than a Poisson GLM on a standard motor-frequency benchmark.

**Task:** Determine whether that apparent improvement was strong and stable enough to justify a pricing-model family change.

**Action:** I built a second longitudinal validation track using 354,140 Spanish policy-years, locked 2022 for training, 2023 for calibration and 2024 for untouched OOT testing, added bootstrap uncertainty, rolling-origin checks, transport analysis for new vs returning policies, and CI tests to prevent leakage or stale headline claims.

**Result:** The original 5.43% frequency improvement did not transport as a stable pricing-model advantage. Locked 2024 XGBoost claim capture increased by only 0.42 pp with no deviance gain; rolling-origin retraining produced a small 0.32% frequency gain but still no pure-premium advantage. I therefore kept the challenger at HOLD rather than promoting it on a single favourable metric.

## Claims to avoid

Do not say:

- "XGBoost improved motor pricing by 5.4%." The 5.43% result is frequency deviance on the cross-sectional benchmark.
- "The model increased profit/conversion." Proposition simulations are synthetic.
- "The project proves the model works for UK motor insurance or FIRST CENTRAL." It does not.
- "XGBoost is worse than GLM." The correct conclusion is that evidence for a global model-family promotion is not stable across targets and time windows.
