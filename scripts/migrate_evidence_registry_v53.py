from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.53 rating-factor review pack |"
BLOCK = r'''
| v0.53 rating-factor review pack | aggregate-only synthesis joins v0.51 development response shapes, v0.52 label-free support/mix and v0.49 portfolio-neutral impact/committee context into one ordered model-review narrative; no row-level access or model fit | `RATING_FACTOR_REVIEW_PACK.md`, `action_results/v53/rating_factor_review_pack_v53.json`, `RESULTS_V53.md` |
| v0.53 shape-versus-support contrast | `driver_age` has a large frequency model-family shape gap **0.26866** while only **0.00159%** of 2024 exposure is strictly outside observed 2022 support; `business_type` has a much smaller frequency shape gap **0.02571** but **48.60%** 2022→2024 exposure-share TV with **0%** unseen business-type exposure | `RATING_FACTOR_REVIEW_PACK.md`, `action_results/v51/rating_factor_relativity_summary_v51.json`, `action_results/v52/rating_factor_support_summary_v52.json` |
| v0.53 portfolio-neutral impact context | with aggregate technical-risk totals neutralised, mean absolute relativity redistribution is **10.18% frequency / 32.28% pure premium**; **36.81%** of frequency exposure moves >±10%, while pure premium has **78.26%** >±10% and **58.17%** >±20%; these are technical-risk redistributions, not customer premium changes | `RATING_FACTOR_REVIEW_PACK.md`, `action_results/v49/model_change_impact_assessment_v49.json` |
| v0.53 evidence-first review boundary | committee remains `EVIDENCE_GAP_HOLD`, **5/8** machine gates, external target support **0/4**, fresh independent validation unavailable, promotion review `NOT_OPEN`; the review pack cannot clear G2/G3/G4 or authorise serving/pricing | `action_results/v53/rating_factor_review_pack_v53.json`, `action_results/v49/model_change_impact_assessment_v49.json` |
'''.strip()

RULES = r'''
- v0.53 is a **synthesis/navigation artifact**, not a new validation analysis. It reads only persisted aggregate v0.51/v0.52/v0.49 evidence and creates no new performance or support threshold.
- Response-shape disagreement, feature support, portfolio mix and portfolio-neutral redistribution answer different questions and are deliberately not collapsed into a composite risk score.
- v0.53 technical-risk redistribution is not a realised customer premium, fairness effect, causal effect or commercial uplift.
- v0.53 cannot change `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`; fresh prospectively governed evidence is still required for G2/G3/G4.
'''.strip()


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    if MARKER not in text:
        anchor = "\n## Interpretation rules\n"
        if anchor not in text:
            raise RuntimeError("Evidence registry interpretation-rules anchor missing")
        text = text.replace(anchor, "\n\n" + BLOCK + "\n" + anchor, 1)
    if RULES.splitlines()[0] not in text:
        anchor = "## Interpretation rules\n"
        text = text.replace(anchor, anchor + "\n" + RULES + "\n", 1)
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
