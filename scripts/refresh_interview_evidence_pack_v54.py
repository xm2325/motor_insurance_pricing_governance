from pathlib import Path

PATH = Path("INTERVIEW_EVIDENCE_PACK.md")

INTRO = "Use this file as the short-form explanation of the project. Every headline number is mapped in `EVIDENCE_REGISTRY.md`; the current rating-factor review is `RATING_FACTOR_REVIEW_PACK.md`, and the committee-ready model-change synthesis is `MODEL_CHANGE_IMPACT_ASSESSMENT.md`. The latest front door is current through v0.53."

TWENTY = "I built a motor-insurance pricing and model-governance workbench to test whether XGBoost actually deserved to replace a GLM. It looked materially better on a French development benchmark — **5.43% lower Poisson deviance** — but the locked Spanish OOT and two preregistered external portfolios did not support promotion: **0/4 external target gates pass** and the committee gate remains **`EVIDENCE_GAP_HOLD` (5/8)**. I then made the model-risk story insurance-specific. On 2022 development data, `driver_age` has a large GLM/XGB frequency response-shape gap (**0.26866**), yet only **0.00159%** of 2024 exposure is strictly outside the observed 2022 driver-age range. `business_type` shows the opposite pattern: a much smaller frequency shape gap (**0.02571**) but **48.60%** 2022→2024 mix TV with **0% unseen exposure**. Separately, after forcing aggregate technical-risk totals equal, **36.81%** of frequency exposure and **78.26%** of pure-premium exposure still differ by more than ±10%. Those are technical-risk redistributions, not customer-price changes, and promotion remains closed."

NEW_SECTIONS = r'''### 14. Inspect rating-factor response shapes on development data

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

'''

NEW_QUESTIONS = r'''### If driver age is well supported, why care about the GLM/XGBoost shape gap?

Because support and model structure are different questions. At age 68, both models are still being evaluated inside the observed 2022 development range, yet the reference-profile frequency relativities are about **1.172 for GLM versus 0.896 for XGBoost**. That is useful model-review evidence: the challenger is encoding a materially different age relationship, not merely extrapolating beyond the training range. It still does not tell me which relationship is more accurate — that requires valid outcome evidence.

### If strict extrapolation is near zero, why did monitoring show such large drift?

Because drift can come from **portfolio reweighting**, not unseen values. `business_type` is the clearest example: both NB and P existed in development, so unseen exposure is zero, but their exposure shares nearly reverse by 2024 and the total-variation distance is **48.60%**. “Known cells, very different weights” is a different risk from extrapolation.

### Why not combine shape gap, support drift and impact into one risk score?

They answer different questions and have different evidence roles. A large shape gap does not imply poor support; a large mix shift does not imply model-family disagreement; a large technical-risk redistribution does not prove better predictive performance. A single hand-built score would introduce arbitrary weights and could hide exactly the trade-offs a model reviewer should see.

'''

STAR_BODY = r'''**Situation:** XGBoost looked materially stronger than a Poisson GLM on a standard motor-frequency development benchmark.

**Task:** Determine whether that apparent improvement was reliable enough across time and independent portfolios to justify opening a model-family promotion review, then make the model-change story interpretable at insurance rating-factor level without confusing technical-risk impact with customer pricing.

**Action:** I built a locked Spanish calendar OOT track, added validation-use ledgers to prevent holdout recycling, preregistered Australian and Belgian external replications before row-level access, retained negative/mixed results without relaxing gates, added numerical-reproducibility controls, and linked the evidence to shadow deployment and a fail-closed Model Change Committee gate. After the validation data were consumed, I used label-free diagnostics to quantify frozen GLM/XGBoost disagreement and portfolio-neutral technical-relativity redistribution. I then added a 2022-only rating-factor response-shape audit and a separate label-free 2022→2024 support/mix audit, before generating a v0.53 review pack that keeps response shape, extrapolation, portfolio mix, impact and evidence adequacy as separate questions.

**Result:** The original **5.43%** development signal did not become a stable promotion case: Spanish OOT stayed HOLD, **0/4** preregistered Australian/Belgian target gates passed, and the committee gate remains **`EVIDENCE_GAP_HOLD` with 5/8 gates passing**. The rating-factor review also shows why model risk cannot be reduced to one number: `driver_age` has a **0.26866** model-family shape gap with only **0.00159%** strict extrapolation, while `business_type` has a **0.02571** frequency shape gap but **48.60%** mix TV and zero unseen exposure. Portfolio-neutral diagnostics still show material technical-risk redistribution, especially pure premium where **78.26%** of exposure differs by more than ±10%. None of these diagnostics overrides the failed evidence gates; model promotion and customer pricing remain unauthorised.'''

EXTRA_CLAIMS = [
    "- “The driver-age curve proves age causes higher/lower claim risk.” v0.51 is a one-factor reference-profile development sensitivity, not a causal estimate or population-average PDP.",
    "- “A 48.60% business-type TV means half the portfolio is out of support.” Both business-type levels were already seen in 2022; the number measures exposure-share reweighting, while unseen exposure is 0%.",
    "- “v0.53 gives a single model-risk score.” It deliberately refuses a composite score because response shape, support, mix, impact and validation answer different questions.",
]


def replace_between(text: str, start: str, end: str, body: str) -> str:
    if start not in text or end not in text:
        raise RuntimeError(f"Interview-pack anchor missing: {start!r} / {end!r}")
    prefix, rest = text.split(start, 1)
    _, suffix = rest.split(end, 1)
    return prefix + start + "\n\n" + body.strip() + "\n\n" + end + suffix


def refresh(text: str) -> str:
    title = "# Interview Evidence Pack\n\n"
    first_heading = "## 20-second version"
    if title not in text or first_heading not in text:
        raise RuntimeError("Interview-pack title/20-second anchors missing")
    _, after_title = text.split(title, 1)
    _, from_heading = after_title.split(first_heading, 1)
    text = title + INTRO + "\n\n" + first_heading + from_heading
    text = replace_between(text, "## 20-second version", "## 2-minute walkthrough", TWENTY)

    if "### 14. Inspect rating-factor response shapes on development data" not in text:
        anchor = "## Likely interview questions"
        if anchor not in text:
            raise RuntimeError("Likely interview questions anchor missing")
        text = text.replace(anchor, NEW_SECTIONS.rstrip() + "\n\n" + anchor, 1)

    if "### If driver age is well supported, why care about the GLM/XGBoost shape gap?" not in text:
        anchor = "## Likely interview questions\n\n"
        if anchor not in text:
            raise RuntimeError("Interview-question insertion anchor missing")
        text = text.replace(anchor, anchor + NEW_QUESTIONS, 1)

    text = replace_between(text, "## STAR version", "## Claims to avoid", STAR_BODY)

    for claim in EXTRA_CLAIMS:
        if claim not in text:
            text = text.rstrip() + "\n" + claim + "\n"

    required = [
        "RATING_FACTOR_REVIEW_PACK.md", "0.26866", "0.00159%", "0.02571", "48.60%",
        "36.81%", "78.26%", "58.17%", "EVIDENCE_GAP_HOLD", "5/8", "0/4",
        "not customer-price changes", "promotion remains closed",
    ]
    for marker in required:
        if marker not in text:
            raise RuntimeError(f"Interview v0.54 refresh missing marker: {marker}")
    return text


def main() -> None:
    original = PATH.read_text(encoding="utf-8")
    updated = refresh(original)
    PATH.write_text(updated, encoding="utf-8")
    assert refresh(updated) == updated
    print("V54_INTERVIEW_EVIDENCE_REFRESH_PASS")


if __name__ == "__main__":
    main()
