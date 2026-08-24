from pathlib import Path

README = Path("README.md")

FRONT = r'''# Motor Insurance Pricing & Model Governance Workbench

A reproducible insurance data-science case study asking a deliberately difficult model-risk question:

> **Does a more flexible ML challenger improve the pricing target reliably enough, across time and independent portfolios, to justify replacing a GLM — and can rating structure, portfolio drift, deployment readiness and model impact be reviewed without confusing any of them with approval?**

## 30-second result

| Evidence | Result |
|---|---|
| Cross-sectional development signal | XGBoost reduced Poisson deviance by **5.43%** and increased top-10% exposure claim capture **20.59% → 31.17%** on freMTPL2; this is development evidence, not pricing uplift |
| Spanish calendar OOT | **2022 train → 2023 calibration → 2024 locked first-use OOT**; GLM retained slightly lower 2024 frequency and pure-premium deviance, so the registered model-family decision stayed **HOLD** |
| Validation lifecycle | Spanish 2024 is now **`CONSUMED_RETROSPECTIVE_VALIDATION`**; Australia and Belgium are also consumed external validation assets rather than reusable independent confirmation samples |
| Preregistered external replication | Australia + Belgium contribute **4 preregistered target gates and 0 passes**; mixed/favourable point metrics are retained, but no gate is relaxed after outcomes are seen |
| Model Change Committee gate | Request `MCR-XGB-MOTOR-001` is **`EVIDENCE_GAP_HOLD`**: **5/8** required gates pass; blockers remain locked temporal support, preregistered external support and fresh independent evidence |
| Rating-factor response shape | v0.51 development-only reference-profile audit: `driver_age` and `vehicle_age` show large GLM/XGB frequency shape gaps (**0.26866 / 0.26771**). At driver age 68, GLM/XGB relativities are **1.172 / 0.896** around the same 2022 reference profile |
| Support vs mix | v0.52 reads 2022/2024 rating features + exposure only. Maximum strict numeric extrapolation is only **0.00227% exposure**, while `business_type` mix TV is **48.60%** with **0% unseen business-type exposure** — known cells reweighted rather than becoming unfamiliar |
| Portfolio-neutral impact | On all **168,085** positive-exposure 2024 feature rows, aggregate GLM/XGB technical-risk totals are forced equal first. **36.81%** of exposure moves by >±10% for frequency; pure premium has **78.26% >±10%** and **58.17% >±20%** |
| Rating-factor review pack | v0.53 joins **response shape → strict support → portfolio mix → technical-risk redistribution → evidence adequacy → separate pricing governance**, without a composite risk score or new promotion threshold |
| Operational controls | FastAPI/Docker shadow scoring, monitoring, content-addressed bundles, manual rollback, GitHub/Sigstore provenance and attested **shadow-only** admission are demonstrated — without converting deployability into approval |
| Current decision | **HOLD / HOLD_SHADOW_ONLY**; `promotion_review_status=NOT_OPEN`; no model promotion or customer-pricing change is authorised |

The central result is not that “XGBoost is bad”. A strong development signal did **not** become a stable promotion case across calendar time and independent portfolios. The later rating-factor work adds a more insurance-specific lesson: **model response-shape disagreement, feature support, portfolio mix and technical-risk redistribution are different risks**. `driver_age` has a large model-family shape gap while remaining well inside development support; `business_type` has a much smaller frequency shape gap but a **48.60%** portfolio-mix shift. Those diagnostics improve review quality, but they do not repair missing validation evidence or become customer premiums.

## Evidence story

1. **Build the challenger:** freMTPL2 shows a material XGBoost frequency signal worth investigating.
2. **Challenge it in time:** the original Spanish 2024 locked OOT does not support a global model-family switch.
3. **Do not recycle the holdout:** later use is recorded and Spanish 2024 becomes consumed retrospective validation.
4. **Replicate externally:** Australian and Belgian protocols are merged before row-level access; registered gates are not relaxed after outcomes.
5. **Protect numerical evidence:** external replication separates stable decisions from point-metric reproducibility and adds prospective numerical controls.
6. **Synthesize without score-shopping:** heterogeneous portfolios keep their original evidence classes and decisions; **0/4** external target gates pass.
7. **Separate evidence from operations:** shadow deployment, monitoring, rollback and attested admission can pass while model promotion remains blocked.
8. **Explain frozen-model disagreement without reusing outcomes:** v0.47 reads consumed 2024 rating features/exposure only and identifies descriptive disagreement sensitivities.
9. **Translate disagreement into impact:** v0.48 forces aggregate technical-risk totals equal, then measures portfolio and major-segment relativity redistribution without reading 2024 outcomes or actual premiums.
10. **Put review steps in the right order:** v0.49 requires evidence adequacy first, impact review second and separate commercial/customer-pricing governance last.
11. **Inspect rating structure on development data:** v0.51 compares frozen Poisson-GLM/XGBoost frequency relativities across supported 2022 rating-factor grids; it is interpretability, not validation.
12. **Separate extrapolation from mix drift:** v0.52 shows strict numeric/unseen-category support remains strong while `business_type` exposure shares almost reverse.
13. **Package the insurance review logic:** v0.53 joins rating structure, support, mix and technical-risk impact but refuses a composite score and leaves the 5/8, 0/4 HOLD state controlling.

## Start here

- **Short interview story:** [Interview Evidence Pack](INTERVIEW_EVIDENCE_PACK.md)
- **Rating-factor model review:** [Rating Factor Review Pack](RATING_FACTOR_REVIEW_PACK.md)
- **Decision-ready impact assessment:** [Model Change Impact Assessment](MODEL_CHANGE_IMPACT_ASSESSMENT.md)
- **Trace every headline claim:** [Evidence Registry](EVIDENCE_REGISTRY.md)
- **Current model scope and consumed-validation roles:** [Model Card](MODEL_CARD.md)
- **Rating-factor chain:** [v0.51 response shapes](RESULTS_V51.md) → [v0.52 support/mix](RESULTS_V52.md) → [v0.53 review pack](RESULTS_V53.md)
- **Why the frozen models disagree:** [v0.47 results](RESULTS_V47.md)
- **Portfolio-neutral technical relativity migration:** [v0.48 results](RESULTS_V48.md)
- **Committee-ready synthesis:** [v0.49 results](RESULTS_V49.md)
- **Model-family evidence / committee gate:** [v0.43 results](RESULTS_V43.md) → [v0.44 results](RESULTS_V44.md)
- **External-validation chain:** [v0.36 preregistration](RESULTS_V36.md) → [v0.37 Australia](RESULTS_V37.md) → [v0.38 reproducibility](RESULTS_V38.md) → [v0.39 firewall](RESULTS_V39.md) → [v0.40 Belgian preregistration](RESULTS_V40.md) → [v0.41 Belgium](RESULTS_V41.md) → [v0.42 closeout](RESULTS_V42.md)
- **Deployment/governance chain:** [v0.21 deployment](DEPLOYMENT_V21.md) → [v0.22 monitoring](RESULTS_V22.md) → [v0.28 rollback](RESULTS_V28.md) → [v0.30 admission](RESULTS_V30.md)

## Current evidence boundaries

- The **5.43%** number is a cross-sectional frequency-deviance benchmark result, not observed pricing/profit uplift.
- Spanish 2024 was independent at its **first** locked OOT use; it is no longer fresh evidence for candidate selection. Australia and Belgium are likewise consumed for new independent-confirmation claims.
- Australian and Belgian results replicate a **GLM-vs-XGBoost model-family question** in different portfolio contexts; they are not direct validation of the fitted Spanish models.
- `0/4` refers specifically to the four preregistered Australian/Belgian target gates; it does not mean every XGBoost metric is worse.
- v0.47/v0.48 are **post-hoc diagnostics on consumed validation features**; v0.51 is **development interpretability**; v0.52 is a **label-free feature support/mix audit**; v0.53 is an **aggregate synthesis/navigation pack**. None is fresh performance evidence or a way to clear G2/G3/G4.
- v0.51 response profiles hold other factors at a common 2022 reference profile. They are not population-average PDPs, causal rating effects or pricing recommendations.
- v0.52 distinguishes strict observed-range/unseen-category support from q05–q95 tail exposure and portfolio mix; tail exposure is not automatically extrapolation.
- v0.48/v0.53 technical-relativity percentages are **score redistribution after aggregate neutralisation**, not customer premium, quote or realised commercial impact.
- The frozen Tweedie GLM `max_iter=900` warning remains registered; descriptive v0.48 headlines are reported only at precision supported by the repeat-run envelope.
- `EVIDENCE_GAP_HOLD`, `HOLD_SHADOW_ONLY`, `NOT_OPEN` and `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN` are project governance states, not FIRST CENTRAL or regulatory approval states.
- No result establishes transport to FIRST CENTRAL, the current UK motor market, production safety, customer-pricing impact, profit or conversion uplift.

'''


def refresh(text: str) -> str:
    marker = "\n---\n"
    if text.count(marker) != 1:
        raise RuntimeError("README must contain exactly one historical-section separator")
    _, historical = text.split(marker, 1)
    updated = FRONT.rstrip() + marker + historical
    required = [
        "0/4", "EVIDENCE_GAP_HOLD", "5/8", "0.26866 / 0.26771", "0.00227% exposure",
        "48.60%", "36.81%", "78.26%", "58.17%", "RATING_FACTOR_REVIEW_PACK.md",
        "RESULTS_V51.md", "RESULTS_V52.md", "RESULTS_V53.md", "not customer premium",
        "CONSUMED_RETROSPECTIVE_VALIDATION", "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
    ]
    for item in required:
        if item not in updated:
            raise RuntimeError(f"README v0.54 refresh missing marker: {item}")
    return updated


def main() -> None:
    original = README.read_text(encoding="utf-8")
    updated = refresh(original)
    README.write_text(updated, encoding="utf-8")
    assert refresh(updated) == updated
    print("V54_README_FRONT_DOOR_REFRESH_PASS")


if __name__ == "__main__":
    main()
