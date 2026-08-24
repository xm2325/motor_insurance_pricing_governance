# v0.54 — Rating-focused recruiter front door

## Purpose

v0.54 changes documentation and evidence navigation only. It makes the insurance-specific rating-factor story from v0.51–v0.53 visible from the repository front door without changing any model, result, validation role, committee gate or pricing authority.

The refresh updates:

- the README 30-second result, evidence story, Start Here links and evidence boundaries;
- the Interview Evidence Pack 20-second answer, detailed walkthrough, interview questions and STAR answer;
- rolling-writer ownership so the historical v0.50 front-door workflow cannot overwrite the new v0.53-current narrative.

The README body after its single historical separator is preserved byte-for-byte.

## What is now visible immediately

The front door now distinguishes four model-risk questions rather than presenting drift or disagreement as one generic issue.

### 1. Rating response shape

v0.51 is surfaced as **development-only reference-profile interpretability**:

- `driver_age` maximum absolute GLM/XGBoost frequency log-relativity gap: **0.26866**;
- `vehicle_age`: **0.26771**;
- at driver age 68, reference-profile GLM/XGBoost frequency relativities are approximately **1.172 / 0.896**.

These are not population-average PDPs, causal rating effects, validation results or customer premiums.

### 2. Strict support versus mix

v0.52 is surfaced as a **label-free feature support/mix audit**:

- maximum strict numeric out-of-2022-range exposure is only **0.00227%** (`power_to_weight_ratio`);
- `driver_age` strict extrapolation is only **0.00159%**;
- `business_type` exposure-share total-variation distance is **48.60%**;
- unseen 2024 business-type exposure is **0%**.

The front-door explanation therefore says that the large business-type change is reweighting among known rating cells, not broad entry into unknown feature support.

### 3. Portfolio-neutral technical-risk impact

The existing v0.48/v0.49 evidence remains visible:

- frequency: **36.81%** of exposure changes by more than ±10%;
- pure premium: **78.26%** changes by more than ±10% and **58.17%** by more than ±20% after aggregate technical-risk totals are neutralised.

These are technical-risk score redistributions, not realised customer premium changes.

### 4. Evidence adequacy remains controlling

v0.53 is surfaced as the ordered review pack:

`response shape → strict support → portfolio mix → technical-risk redistribution → evidence adequacy → separate pricing governance`.

The front door retains the exact controlling state:

- `EVIDENCE_GAP_HOLD`;
- **5/8** machine gates pass;
- external target support **0/4**;
- model family `HOLD`;
- serving `HOLD_SHADOW_ONLY`;
- promotion review `NOT_OPEN`;
- customer pricing not authorised.

No documentation update can clear G2/G3/G4.

## Interview improvement

The Interview Evidence Pack now contains three additional walkthrough sections:

1. inspect rating-factor response shapes on 2022 development data;
2. separate feature support from portfolio mix;
3. join rating structure, support, impact and evidence without a composite score.

It also adds direct answers to:

- why a driver-age shape gap matters even when support is good;
- why large drift can coexist with near-zero strict extrapolation;
- why shape gap, support drift and impact should not be combined into a single risk score.

The STAR answer now tells the full evaluation story through v0.53 rather than stopping at the v0.49 impact synthesis.

## Stale-writer control

Before v0.54, `.github/workflows/v50-recruiter-front-door.yml` was still an automatic writer whose template was current only through v0.49. v0.54 converts it to a manual, read-only historical audit:

- no `push` listener;
- no `pull_request` listener;
- `contents: read` only;
- no `git push` or evidence-push helper.

The already-frozen v0.45 writer remains read-only. v0.54 becomes the only rolling owner for this front-door generation.

## Evidence boundary

v0.54 accesses no row-level data and fits no model. It creates no performance result, support threshold, composite risk score, validation evidence, serving authority or customer-pricing authority.

The roles remain unchanged:

- v0.51: development interpretability;
- v0.52: post-hoc label-free support/mix on consumed 2024 features;
- v0.53: aggregate review synthesis/navigation;
- v0.48/v0.49: post-hoc technical-risk impact and committee synthesis.

No result establishes transfer to FIRST CENTRAL or the current UK motor market, and no causal, fairness, realised-premium or commercial-uplift conclusion is claimed.
