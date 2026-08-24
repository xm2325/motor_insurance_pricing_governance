from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.49 model change impact assessment |"
BLOCK = r'''
| v0.49 model change impact assessment | aggregate-only committee-ready synthesis of persisted v0.44/v0.46/v0.47/v0.48 evidence; review order is evidence adequacy → model impact → separate commercial/customer-pricing governance | `MODEL_CHANGE_IMPACT_ASSESSMENT.md`, `action_results/v49/model_change_impact_assessment_v49.json`, `RESULTS_V49.md` |
| v0.49 decision-critical fail-closed state | `EVIDENCE_GAP_HOLD`, **5/8** committee gates, blockers G2/G3/G4, **0/4** preregistered external target gates, no fresh independent validation, and `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN` are pinned before the pack can be generated | `build_model_change_impact_assessment_v49.py`, `tests/test_model_change_impact_assessment_v49.py` |
| v0.49 impact synthesis | frequency: mean absolute log disagreement **0.0993**, portfolio-neutral mean absolute relativity redistribution **10.18%**, **36.81%** exposure >±10%; pure premium: **0.3171**, **32.28%**, **78.26%** exposure >±10% and **58.17%** >±20% | `MODEL_CHANGE_IMPACT_ASSESSMENT.md`, `action_results/v49/model_change_impact_assessment_v49.json` |
| v0.49 governance boundary | impact diagnostics and operational readiness cannot clear validation-evidence blockers; no new performance gate or promotion threshold is created; technical relativity is not customer premium and customer-pricing authority remains false | `MODEL_CHANGE_IMPACT_ASSESSMENT.md`, `action_results/v49/ACTION_V49_STATUS.json` |
'''.strip()

RULES = r'''
- v0.49 enforces **evidence adequacy before impact review before pricing governance**. v0.47/v0.48 post-hoc diagnostics cannot clear G2/G3/G4 or reopen promotion.
- v0.49 records source SHA-256 values for lineage, while CI separately pins the decision-critical fields used in the committee-ready narrative. A hash alone is not treated as a decision gate.
- v0.49 creates no new model-performance gate, promotion threshold, insurer policy or customer-pricing authority. Its impact percentages remain descriptive technical-risk score redistributions.
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
    old = "`tests/test_portfolio_neutral_relativity_v48.py` protects the label-free portfolio-neutral redistribution boundary, float64 aggregate-neutralisation and aggregate-only segment outputs."
    new = old + " `tests/test_model_change_impact_assessment_v49.py` protects evidence-first review sequencing, decision-critical blocker state, diagnostic impact headlines and the no-pricing/no-promotion boundary."
    if new not in text:
        if old not in text:
            raise RuntimeError("Automated-protection v0.48 anchor missing")
        text = text.replace(old, new, 1)
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
