from pathlib import Path

README = Path("README.md")

FRONT = r'''# Motor Insurance Pricing & Model Governance Workbench

A reproducible insurance data-science case study asking a deliberately difficult model-risk question:

> **Does a more flexible ML challenger improve the pricing target reliably enough, across time and independent portfolios, to justify replacing a GLM — and can deployment readiness be kept separate from model approval?**

## 30-second result

| Evidence | Result |
|---|---|
| Cross-sectional frequency benchmark | XGBoost reduced Poisson deviance by **5.43%** and increased top-10% exposure claim capture **20.59% → 31.17%**; this is development evidence, not pricing uplift |
| Spanish calendar OOT | **2022 train → 2023 calibration → 2024 locked first-use OOT**; GLM retained slightly lower 2024 frequency and pure-premium deviance, so the registered model-family decision stayed **HOLD** |
| Validation-reuse firewall | After later monitoring/recalibration/uncertainty work, Spanish 2024 is now **`CONSUMED_RETROSPECTIVE_VALIDATION`**, not a fresh candidate-selection holdout |
| Australian external replication | Preregistered before row-level access. Frequency favoured GLM (**XGB -0.3849% relative deviance improvement**); pure premium had a favourable XGB point estimate but failed bootstrap confirmation. Both registered external gates failed |
| Australian reproducibility lesson | Registered decisions reproduced, but one iterative Tweedie GLM point metric did not reproduce exactly across hosted runs; future positive external evidence therefore requires prospective numerical-reproducibility controls |
| Belgian external replication | Preregistered before row-level access. Frequency XGB improvement **+0.2910%** had a positive bootstrap interval but missed the fixed **0.5%** materiality gate; pure premium **+0.3219%** failed point/CI support. Both registered gates failed |
| Belgian numerical reproducibility | Two completed Actions executions (`eastus2`, `centralus`) reproduced all registered aggregate metrics within tolerance; max absolute difference **1.42×10⁻¹⁴**, max relative difference **6.90×10⁻¹⁴** |
| External evidence synthesis | Across Australia + Belgium: **0/4 preregistered external target gates pass**. No pooled meta-analysis or subjective evidence-weighting score is used to override the original decisions |
| Model Change Committee gate | Request `MCR-XGB-MOTOR-001` is **`EVIDENCE_GAP_HOLD`**: **5/8** machine gates pass; blockers are locked temporal support, preregistered external support and fresh independent evidence |
| Operational controls | FastAPI/Docker shadow scoring, monitoring, content-addressed bundles, manual rollback, GitHub/Sigstore provenance and attested **shadow-only** admission are demonstrated — without converting deployability into approval |
| Current decision | **HOLD / HOLD_SHADOW_ONLY**; `promotion_review_status=NOT_OPEN`; no model promotion or customer-pricing change is authorised |

The central result is not that “XGBoost is bad”. It is that a strong development benchmark did **not** become a stable promotion case once the challenger was tested prospectively across calendar time and independent portfolios. The repository therefore treats negative and mixed evidence as first-class results, records when validation datasets have been consumed, and makes operational readiness insufficient by construction when validation evidence is missing.

## Evidence story

1. **Build the challenger:** freMTPL2 shows a material XGBoost frequency signal worth investigating.
2. **Challenge it in time:** the original Spanish 2024 locked OOT does not support a global model-family switch.
3. **Do not recycle the holdout:** later use is recorded and Spanish 2024 becomes consumed retrospective validation.
4. **Replicate externally:** Australian and Belgian protocols are merged before row-level access; their registered gates are not relaxed after seeing outcomes.
5. **Protect numerical evidence:** Australian runner sensitivity leads to explicit solver/thread/tolerance rules; Belgian results then reproduce within the registered tolerance.
6. **Synthesize without score-shopping:** heterogeneous portfolios keep their original evidence classes and decisions; 0/4 external gates pass.
7. **Separate evidence from operations:** shadow deployment, monitoring, rollback and attested release admission can pass while model promotion remains blocked.
8. **Fail closed on change control:** the v0.44 machine gate can only hold the request or open a future human review; it can never auto-promote a model or change customer pricing.

## Start here

- **Short project story:** [Interview Evidence Pack](INTERVIEW_EVIDENCE_PACK.md)
- **Trace every headline claim:** [Evidence Registry](EVIDENCE_REGISTRY.md)
- **Current model-risk synthesis:** [v0.43 results](RESULTS_V43.md) and persisted `action_results/v43/MODEL_FAMILY_REVIEW_PACK_V43.md`
- **Current change-control decision:** [v0.44 results](RESULTS_V44.md) and persisted `action_results/v44/MODEL_CHANGE_COMMITTEE_PACK_V44.md`
- **Model scope/boundaries:** [Model Card](MODEL_CARD.md)
- **External-validation chain:** [v0.36 preregistration](RESULTS_V36.md) → [v0.37 Australia](RESULTS_V37.md) → [v0.38 reproducibility](RESULTS_V38.md) → [v0.39 firewall](RESULTS_V39.md) → [v0.40 Belgian preregistration](RESULTS_V40.md) → [v0.41 Belgium](RESULTS_V41.md) → [v0.42 closeout](RESULTS_V42.md)
- **Deployment/governance chain:** [v0.21 deployment](DEPLOYMENT_V21.md) → [v0.22 monitoring](RESULTS_V22.md) → [v0.28 rollback](RESULTS_V28.md) → [v0.30 admission](RESULTS_V30.md)

## Current evidence boundaries

- The **5.43%** number is a cross-sectional frequency-deviance benchmark result, not an observed pricing/profit uplift.
- Spanish 2024 was independent at its **first** locked OOT use; it is no longer fresh evidence for new candidate selection.
- Australian and Belgian results replicate a **GLM-vs-XGBoost model-family question** in different portfolio contexts; they are not direct validation of the fitted Spanish models.
- `0/4` refers specifically to the four preregistered Australian/Belgian target gates; it does not mean every XGBoost metric is worse.
- Belgian numerical reproducibility strengthens confidence in the recorded negative decisions; it does not turn them into positive challenger support.
- `EVIDENCE_GAP_HOLD`, `HOLD_SHADOW_ONLY` and `promotion_review_status=NOT_OPEN` are project governance states, not FIRST CENTRAL or regulatory approval states.
- No result establishes transport to FIRST CENTRAL, the current UK motor market, production safety, customer-pricing impact, profit or conversion uplift.

'''


def refresh(text: str) -> str:
    marker = "\n---\n"
    if marker not in text:
        raise RuntimeError("README historical-section separator not found")
    _, historical = text.split(marker, 1)
    updated = FRONT.rstrip() + marker + historical
    required = [
        "0/4 preregistered external target gates pass",
        "EVIDENCE_GAP_HOLD",
        "5/8",
        "RESULTS_V43.md",
        "RESULTS_V44.md",
        "CONSUMED_RETROSPECTIVE_VALIDATION",
        "1.42×10⁻¹⁴",
    ]
    for item in required:
        if item not in updated:
            raise RuntimeError(f"README refresh missing marker: {item}")
    return updated


def main() -> None:
    original = README.read_text(encoding="utf-8")
    updated = refresh(original)
    README.write_text(updated, encoding="utf-8")
    # The operation must be idempotent: refreshing the refreshed file must not duplicate content.
    assert refresh(updated) == updated
    print("V45_README_FRONT_DOOR_REFRESH_PASS")


if __name__ == "__main__":
    main()
