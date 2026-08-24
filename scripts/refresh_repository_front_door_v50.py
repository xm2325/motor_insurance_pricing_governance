from pathlib import Path

README = Path("README.md")

FRONT = r'''# Motor Insurance Pricing & Model Governance Workbench

A reproducible insurance data-science case study asking a deliberately difficult model-risk question:

> **Does a more flexible ML challenger improve the pricing target reliably enough, across time and independent portfolios, to justify replacing a GLM — and can deployment readiness and model-impact analysis be kept separate from approval?**

## 30-second result

| Evidence | Result |
|---|---|
| Cross-sectional development signal | XGBoost reduced Poisson deviance by **5.43%** and increased top-10% exposure claim capture **20.59% → 31.17%** on freMTPL2; this is development evidence, not pricing uplift |
| Spanish calendar OOT | **2022 train → 2023 calibration → 2024 locked first-use OOT**; GLM retained slightly lower 2024 frequency and pure-premium deviance, so the registered model-family decision stayed **HOLD** |
| Validation lifecycle | Spanish 2024 is now **`CONSUMED_RETROSPECTIVE_VALIDATION`**, not a fresh candidate-selection holdout; Australia and Belgium are also consumed external validation assets |
| Preregistered external replication | Australia + Belgium contribute **4 preregistered target gates and 0 passes**; mixed/favourable point metrics are retained, but no gate is relaxed after outcomes are seen |
| Model Change Committee gate | Request `MCR-XGB-MOTOR-001` is **`EVIDENCE_GAP_HOLD`**: **5/8** required gates pass; blockers are locked temporal support, preregistered external support and fresh independent evidence |
| Why the frozen models disagree | Label-free v0.47 diagnostic: mean absolute log(XGB/GLM) disagreement **0.0993 frequency / 0.3171 pure premium**; leading sensitivities are `vehicle_brand`, `policy_type`, `vehicle_value` for frequency and `business_type`, `power_to_weight_ratio`, `vehicle_value` for pure premium |
| Portfolio-neutral impact | On all **168,085** positive-exposure 2024 feature rows, aggregate GLM/XGB technical-risk totals are forced equal first. **36.81%** of exposure moves by >±10% for frequency; **78.26%** by >±10% and **58.17%** by >±20% for pure premium |
| Major pure-premium segment redistribution | After aggregate neutralisation: business type **NB +8.65% vs P −6.53%**, policy type **COMP_E +13.68% vs CC −9.27%**, driver age **35–49 +5.20% vs 50–64 −5.49%**; these are technical-risk score shifts, not price changes |
| Numerical limitation retained | Frozen Tweedie GLM reaches its registered `max_iter=900`; same-head v0.48 repeats keep the displayed redistribution headlines stable, but bitwise/performance reproducibility is not claimed |
| Operational controls | FastAPI/Docker shadow scoring, monitoring, content-addressed bundles, manual rollback, GitHub/Sigstore provenance and attested **shadow-only** admission are demonstrated — without converting deployability into approval |
| Committee-ready impact assessment | v0.49 enforces **evidence adequacy → model impact review → separate commercial/customer-pricing governance**. Current disposition: `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN` |
| Current decision | **HOLD / HOLD_SHADOW_ONLY**; `promotion_review_status=NOT_OPEN`; no model promotion or customer-pricing change is authorised |

The central result is not that “XGBoost is bad”. It is that a strong development signal did **not** become a stable promotion case once challenged across calendar time and independent portfolios. The later diagnostics add a second lesson: even with aggregate technical-risk totals held equal, two plausible model families can redistribute risk materially across policies and major segments. That impact matters for review, but it does not repair missing validation evidence or become a customer premium by itself.

## Evidence story

1. **Build the challenger:** freMTPL2 shows a material XGBoost frequency signal worth investigating.
2. **Challenge it in time:** the original Spanish 2024 locked OOT does not support a global model-family switch.
3. **Do not recycle the holdout:** later use is recorded and Spanish 2024 becomes consumed retrospective validation.
4. **Replicate externally:** Australian and Belgian protocols are merged before row-level access; registered gates are not relaxed after outcomes.
5. **Protect numerical evidence:** external replication separates stable decisions from point-metric reproducibility and adds prospective numerical controls.
6. **Synthesize without score-shopping:** heterogeneous portfolios keep their original evidence classes and decisions; **0/4** external target gates pass.
7. **Separate evidence from operations:** shadow deployment, monitoring, rollback and attested admission can pass while model promotion remains blocked.
8. **Explain the frozen-model difference without reusing outcomes:** v0.47 reads 2024 rating features/exposure only and identifies descriptive disagreement sensitivities.
9. **Translate disagreement into impact:** v0.48 forces aggregate technical-risk totals equal, then measures full-population and major-segment relativity redistribution without reading 2024 outcomes or actual premiums.
10. **Put review steps in the right order:** v0.49 requires evidence adequacy first, impact review second, and separate commercial/customer-pricing governance last.

## Start here

- **Short interview story:** [Interview Evidence Pack](INTERVIEW_EVIDENCE_PACK.md)
- **Decision-ready impact assessment:** [Model Change Impact Assessment](MODEL_CHANGE_IMPACT_ASSESSMENT.md)
- **Trace every headline claim:** [Evidence Registry](EVIDENCE_REGISTRY.md)
- **Current model scope and consumed-validation roles:** [Model Card](MODEL_CARD.md)
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
- v0.47 and v0.48 are **post-hoc diagnostics on consumed validation features**, not new performance evidence and not a way to clear G2/G3/G4.
- v0.48 technical-relativity percentages are **score redistribution after aggregate neutralisation**, not customer premium, quote or realised commercial impact.
- The frozen Tweedie GLM `max_iter=900` warning remains registered; descriptive v0.48 headlines are reported only at precision supported by the repeat-run envelope.
- `EVIDENCE_GAP_HOLD`, `HOLD_SHADOW_ONLY`, `NOT_OPEN` and the v0.49 impact-pack disposition are project governance states, not FIRST CENTRAL or regulatory approval states.
- No result establishes transport to FIRST CENTRAL, the current UK motor market, production safety, customer-pricing impact, profit or conversion uplift.

'''


def refresh(text: str) -> str:
    marker = "\n---\n"
    if marker not in text:
        raise RuntimeError("README historical-section separator not found")
    _, historical = text.split(marker, 1)
    updated = FRONT.rstrip() + marker + historical
    required = [
        "0/4",
        "EVIDENCE_GAP_HOLD",
        "5/8",
        "0.0993 frequency / 0.3171 pure premium",
        "36.81%",
        "78.26%",
        "58.17%",
        "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
        "MODEL_CHANGE_IMPACT_ASSESSMENT.md",
        "CONSUMED_RETROSPECTIVE_VALIDATION",
        "not customer premium",
    ]
    for item in required:
        if item not in updated:
            raise RuntimeError(f"README v0.50 refresh missing marker: {item}")
    return updated


def main() -> None:
    original = README.read_text(encoding="utf-8")
    updated = refresh(original)
    README.write_text(updated, encoding="utf-8")
    assert refresh(updated) == updated
    print("V50_README_FRONT_DOOR_REFRESH_PASS")


if __name__ == "__main__":
    main()
