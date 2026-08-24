# v0.50 — Recruiter front-door refresh

## Purpose

v0.50 fixes a documentation-governance problem rather than adding another model experiment. The repository's technical evidence had advanced through v0.49, while the README and Interview Evidence Pack still presented the v0.44-era story. In addition, the historical v0.45 workflow still had automatic write permissions and could regenerate that stale front door after newer documentation changes.

The v0.50 objective is therefore:

1. make the first 30–60 seconds of the repository reflect the current evidence chain through v0.49;
2. preserve all historical technical detail rather than rewriting the project record;
3. stop the historical v0.45 template from automatically overwriting the rolling front door;
4. keep every scientific and pricing boundary unchanged.

## Rolling-writer ownership fix

`.github/workflows/v45-repository-front-door.yml` is retained, but converted to a **manual, read-only historical audit**:

- `workflow_dispatch` only;
- `contents: read`;
- no `push` or `pull_request` listener;
- no Git commit/push or evidence persistence.

This does not delete v0.45 evidence. It prevents an old v0.44-era documentation template from acting as the current writer.

v0.50 becomes the rolling front-door owner.

## README front door

The refreshed 30-second table now exposes the complete decision story:

- freMTPL2 development signal: **5.43%** frequency-deviance improvement;
- Spanish locked calendar OOT: registered **HOLD**;
- Spanish 2024 current role: `CONSUMED_RETROSPECTIVE_VALIDATION`;
- Australia + Belgium: **0/4** preregistered external target gates pass;
- committee readiness: `EVIDENCE_GAP_HOLD`, **5/8** gates pass, blockers G2/G3/G4;
- v0.47 disagreement: mean absolute log(XGB/GLM) **0.0993 frequency / 0.3171 pure premium**, with leading descriptive sensitivities surfaced;
- v0.48 portfolio-neutral impact on all **168,085** positive-exposure 2024 feature rows: frequency **36.81%** exposure >±10%; pure premium **78.26%** >±10% and **58.17%** >±20%;
- major pure-premium segment redistribution: NB/P, COMP_E/CC, and 35–49/50–64 age groups;
- frozen Tweedie GLM `max_iter=900` numerical limitation remains visible;
- v0.49 review order: **evidence adequacy → model impact → separate commercial/customer-pricing governance**;
- current disposition: `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`;
- current model state: `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, with no pricing authority.

The historical README body after the single `---` separator is preserved byte-for-byte. The workflow records its SHA-256 so a future front-door refresh cannot silently rewrite the historical technical sections.

## Interview Evidence Pack

The short-form interview narrative is updated without deleting the existing detailed material.

New sections are:

- **11. Explain model-family disagreement without reusing outcomes** — v0.47 label-free diagnostic and its non-additive/non-causal boundary;
- **12. Translate disagreement into portfolio impact without pretending it is premium** — v0.48 exact aggregate-neutralisation and redistribution results;
- **13. Put evidence, impact and pricing governance in the right order** — v0.49 committee-ready sequence.

Two explicit interview questions are added:

- what does the **78.26% >±10%** figure actually mean?;
- why perform impact analysis when the promotion gate is already HOLD?

The STAR answer is also brought through v0.49 so the portfolio story ends with a defensible business/governance conclusion rather than with infrastructure alone.

## Boundaries retained

v0.50 is **documentation and evidence navigation only**:

- no row-level data access;
- no model fit or calibration;
- no threshold or performance-gate change;
- no validation-role change;
- no historical scientific decision change;
- no customer-pricing authority.

The v0.47/v0.48 figures remain post-hoc technical-risk diagnostics on consumed validation features. They are not new performance evidence, observed premium changes, fairness conclusions or commercial uplift.

The 5.43% benchmark remains development deviance evidence, not pricing/profit uplift. `EVIDENCE_GAP_HOLD`, `HOLD_SHADOW_ONLY`, `NOT_OPEN` and the v0.49 impact-pack disposition remain project governance states, not FIRST CENTRAL or regulatory approval states.

## Decision

The documentation is allowed to become easier to understand; the model decision is not allowed to change because of that documentation.

Current state remains:

**`HOLD / HOLD_SHADOW_ONLY / EVIDENCE_GAP_HOLD / promotion review NOT_OPEN`.**
