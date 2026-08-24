from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.54 rating front-door refresh |"
BLOCK = r'''
| v0.54 rating front-door refresh | documentation-only rolling front door current through v0.53; README and Interview Evidence Pack now surface the rating-factor response-shape, feature-support/mix and review-pack evidence without changing any historical model or validation decision | `README.md`, `INTERVIEW_EVIDENCE_PACK.md`, `action_results/v54/rating_front_door_summary_v54.json`, `RESULTS_V54.md` |
| v0.54 rating-factor surface | recruiter/interview front door now exposes the contrast `driver_age` shape gap **0.26866** with only **0.00159%** strict 2024 extrapolation versus `business_type` frequency shape gap **0.02571** with **48.60%** 2022→2024 mix TV and **0%** unseen exposure | `RATING_FACTOR_REVIEW_PACK.md`, `action_results/v53/rating_factor_review_pack_v53.json`, `README.md`, `INTERVIEW_EVIDENCE_PACK.md` |
| v0.54 stale-writer prevention | historical v0.50 recruiter-front-door workflow is frozen to manual, read-only audit mode so its v0.49-era template cannot overwrite the v0.53-current README/Interview front door; v0.45 remains frozen too | `.github/workflows/v50-recruiter-front-door.yml`, `.github/workflows/v54-rating-front-door.yml`, `RESULTS_V54.md` |
| v0.54 decision boundary | documentation continues to report `EVIDENCE_GAP_HOLD`, **5/8** machine gates, external target support **0/4**, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, and no customer-pricing authority; no model fit, row-level access, scientific decision change or FIRST CENTRAL/current-UK transport claim is created | `README.md`, `INTERVIEW_EVIDENCE_PACK.md`, `action_results/v54/ACTION_V54_STATUS.json` |
'''.strip()

RULES = r'''
- v0.54 changes **navigation and explanation only**. It does not alter a model, validation role, performance result, committee gate or pricing authority.
- v0.51 remains development reference-profile interpretability, v0.52 remains label-free feature support/mix, and v0.53 remains aggregate synthesis; none is relabelled as fresh performance evidence.
- Response shape, strict support, portfolio mix and technical-risk redistribution remain separate review questions and are not collapsed into a composite score.
- Freezing v0.50 removes stale automatic-write ownership only; the historical v0.50 workflow/results/evidence remain part of the repository record.
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
