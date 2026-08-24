from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.50 recruiter front-door refresh |"
BLOCK = r'''
| v0.50 recruiter front-door refresh | documentation-only rolling front door current through v0.49; README and Interview Evidence Pack surface v0.47 disagreement attribution, v0.48 portfolio-neutral impact and v0.49 evidence-first committee sequencing without changing historical evidence | `README.md`, `INTERVIEW_EVIDENCE_PACK.md`, `action_results/v50/repository_front_door_summary_v50.json`, `RESULTS_V50.md` |
| v0.50 stale-writer prevention | historical v0.45 front-door workflow is frozen to manual, read-only audit mode so its v0.44-era template cannot overwrite the current rolling README/Interview front door | `.github/workflows/v45-repository-front-door.yml`, `.github/workflows/v50-recruiter-front-door.yml`, `RESULTS_V50.md` |
| v0.50 historical-body preservation | README content after the single `---` historical separator is preserved byte-for-byte during the refresh and recorded by SHA-256 in the documentation audit | `action_results/v50/repository_front_door_summary_v50.json`, `tests/test_repository_front_door_v50.py` |
| v0.50 decision boundary | documentation still reports `EVIDENCE_GAP_HOLD`, 5/8, 0/4 external gates, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, and `DO_NOT_OPEN_PROMOTION_REVIEW__EVIDENCE_BLOCKERS_REMAIN`; no model fit, row-level access, scientific decision change or pricing authority is created | `README.md`, `INTERVIEW_EVIDENCE_PACK.md`, `action_results/v50/ACTION_V50_STATUS.json` |
'''.strip()

RULES = r'''
- v0.50 changes **navigation and explanation only**. It does not alter a model, validation role, performance result, committee gate or pricing authority.
- v0.47/v0.48 figures are exposed as post-hoc technical-risk diagnostics on consumed validation features. They are not relabelled as fresh performance evidence or customer-premium changes.
- Freezing v0.45 removes stale automatic-write ownership only; the historical v0.45 workflow, results and immutable evidence remain part of the repository record.
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
    old = "`tests/test_model_change_impact_assessment_v49.py` protects evidence-first review sequencing, decision-critical blocker state, diagnostic impact headlines and the no-pricing/no-promotion boundary."
    new = old + " `tests/test_repository_front_door_v50.py` protects the v0.49-current recruiter story, README historical-body preservation, v0.47/v0.48 impact boundaries and retirement of the stale v0.45 rolling writer."
    if new not in text:
        if old not in text:
            raise RuntimeError("Automated-protection v0.49 anchor missing")
        text = text.replace(old, new, 1)
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
