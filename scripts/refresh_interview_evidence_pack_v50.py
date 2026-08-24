from pathlib import Path

PATH = Path("INTERVIEW_EVIDENCE_PACK.md")

INTRO = "Use this file as the short-form explanation of the project. Every headline number is mapped in `EVIDENCE_REGISTRY.md`; the current committee-ready synthesis is `MODEL_CHANGE_IMPACT_ASSESSMENT.md`, backed by machine-readable v0.44/v0.46/v0.47/v0.48/v0.49 evidence."

TWENTY = "I built a motor-insurance pricing and model-governance workbench to test whether XGBoost actually deserved to replace a GLM. XGBoost looked materially better on a French cross-sectional frequency benchmark, with a **5.43% Poisson-deviance reduction**, but the locked Spanish calendar OOT and two preregistered external portfolios did not produce a stable promotion case: **0 of 4 Australian/Belgian target gates passed**, and the machine committee gate remains **`EVIDENCE_GAP_HOLD` (5/8 gates pass)**. I then separated model impact from model approval. Without reading 2024 outcomes or actual premiums, I measured frozen GLM/XGBoost disagreement and portfolio-neutral technical-relativity redistribution: **36.81%** of exposure moves by more than ±10% for frequency, while pure premium is much more sensitive at **78.26% >±10%** and **58.17% >±20%**. v0.49 packages the review order as **evidence adequacy → model impact → separate commercial/customer-pricing governance**. Those impact numbers are technical-risk score redistributions, not customer-price changes, and promotion remains closed."

NEW_SECTIONS = r'''### 11. Explain model-family disagreement without reusing outcomes

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

'''

NEW_QUESTIONS = r'''### What does “78.26% of exposure moves by more than ±10%” actually mean?

It is **not** a statement that 78.26% of customers would receive a >10% premium change. I first force the frozen GLM and XGBoost pure-premium technical-risk totals to be equal across the portfolio, then compare the resulting technical-risk relativities. The 78.26% figure is the exposure share where those two technical-risk indications differ by more than 10%. Actual premiums would also involve expenses, commission, reinsurance, profit, tax, commercial strategy, underwriting and other controls that this project does not model.

### Why do impact analysis when the promotion gate is already HOLD?

Because a real model-change review needs two separate questions answered: **is the evidence strong enough to consider changing the model, and what would the model change do if considered?** The current evidence fails the first question, so impact diagnostics cannot trigger promotion. But quantifying disagreement and redistribution makes the project ready for a future review without confusing impact with performance evidence.

'''

STAR = r'''## STAR version

**Situation:** XGBoost looked materially stronger than a Poisson GLM on a standard motor-frequency development benchmark.

**Task:** Determine whether that apparent improvement was reliable enough across time and independent portfolios to justify opening a model-family promotion review, then quantify model-change impact without confusing technical-risk redistribution with customer pricing.

**Action:** I built a locked Spanish calendar OOT track, added validation-use ledgers to prevent holdout recycling, preregistered Australian and Belgian external replications before row-level access, retained negative/mixed results without relaxing gates, added numerical-reproducibility controls, and linked the evidence to shadow deployment and a fail-closed Model Change Committee gate. After the validation data were consumed, I used label-free diagnostics to explain frozen GLM/XGBoost disagreement and measured portfolio-neutral technical-relativity redistribution across all 168,085 positive-exposure 2024 feature rows. I then generated a committee-ready v0.49 pack enforcing evidence adequacy before impact review and separate pricing governance.

**Result:** The original **5.43%** development signal did not become a stable promotion case: Spanish OOT stayed HOLD, **0/4** preregistered Australian/Belgian target gates passed, and the committee gate remains **`EVIDENCE_GAP_HOLD` with 5/8 gates passing**. At the same time, portfolio-neutral diagnostics show that the frozen model families can redistribute technical risk materially — especially pure premium, where **78.26%** of exposure differs by more than ±10% and **58.17%** by more than ±20%. Those impact results do not override the failed evidence gates; model promotion and customer pricing remain unauthorised.

'''

EXTRA_CLAIM = "- “The v0.48 ±10% / ±20% migration figures are customer premium changes.” They are portfolio-neutral technical-risk score redistributions with no actual premium, commercial or pricing-action model."


def replace_between(text: str, start: str, end: str, body: str) -> str:
    if start not in text or end not in text:
        raise RuntimeError(f"Interview-pack anchor missing: {start!r} / {end!r}")
    prefix, rest = text.split(start, 1)
    _, suffix = rest.split(end, 1)
    return prefix + start + "\n\n" + body.strip() + "\n\n" + end + suffix


def refresh(text: str) -> str:
    # Intro paragraph.
    title = "# Interview Evidence Pack\n\n"
    first_heading = "## 20-second version"
    if title not in text or first_heading not in text:
        raise RuntimeError("Interview-pack title/20-second anchors missing")
    _, after_title = text.split(title, 1)
    _, from_heading = after_title.split(first_heading, 1)
    text = title + INTRO + "\n\n" + first_heading + from_heading

    text = replace_between(text, "## 20-second version", "## 2-minute walkthrough", TWENTY)

    if "### 11. Explain model-family disagreement without reusing outcomes" not in text:
        anchor = "## Likely interview questions"
        if anchor not in text:
            raise RuntimeError("Likely interview questions anchor missing")
        text = text.replace(anchor, NEW_SECTIONS.rstrip() + "\n\n" + anchor, 1)

    if "### What does “78.26% of exposure moves by more than ±10%” actually mean?" not in text:
        anchor = "## Likely interview questions\n\n"
        if anchor not in text:
            raise RuntimeError("Interview-question insertion anchor missing")
        text = text.replace(anchor, anchor + NEW_QUESTIONS, 1)

    text = replace_between(text, "## STAR version", "## Claims to avoid", STAR.split("## STAR version\n\n", 1)[1].rstrip())

    if EXTRA_CLAIM not in text:
        text = text.rstrip() + "\n" + EXTRA_CLAIM + "\n"

    required = [
        "MODEL_CHANGE_IMPACT_ASSESSMENT.md",
        "36.81%",
        "78.26%",
        "58.17%",
        "DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN",
        "technical-risk score redistributions",
        "EVIDENCE_GAP_HOLD",
    ]
    for marker in required:
        if marker not in text:
            raise RuntimeError(f"Interview v0.50 refresh missing marker: {marker}")
    return text


def main() -> None:
    original = PATH.read_text(encoding="utf-8")
    updated = refresh(original)
    PATH.write_text(updated, encoding="utf-8")
    assert refresh(updated) == updated
    print("V50_INTERVIEW_EVIDENCE_REFRESH_PASS")


if __name__ == "__main__":
    main()
