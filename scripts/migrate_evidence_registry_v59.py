from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.59 committee-gate reachability audit |"
BLOCK = r'''
| v0.59 committee-gate reachability audit | machine audit of existing request `MCR-XGB-MOTOR-001` shows G2 is structurally unreachable because its registered v0.44 definition requires the **original** locked temporal evaluation to support the global family change, while both Spanish 2024 locked targets are already registered HOLD; even assuming future G3/G4 success, the existing request has a 7/8 ceiling and cannot reach `READY_FOR_HUMAN_COMMITTEE_REVIEW` without redefining its historical gate | `governance/model_change_reachability_policy_v59.json`, `audit_model_change_reachability_v59.py`, `action_results/v59/committee_gate_reachability_audit_v59.json` |
| v0.59 stop rule | do not consume additional fresh external outcomes solely to try to make `MCR-XGB-MOTOR-001` reach 8/8; future external evidence may still be valuable only under a distinct prospectively registered scientific question or a new change request whose temporal criterion is frozen before fresh outcome access, while the failed MCR-001 history remains visible | `RESULTS_V59.md`, `action_results/v59/ACTION_V59_STATUS.json` |
'''.strip()

RULES = r'''
- A failed gate tied explicitly to a completed historical event cannot be repaired by unrelated future evidence without changing that existing gate's semantics.
- New evidence can support a **new prospectively registered request**, but must not be used to rewrite, delete or relabel the failed historical request.
- Evidence acquisition has a stop condition: once a request is structurally unable to reach its own all-required-gates rule, consuming fresh validation only to increase that request's score is not justified.
- A terminal HOLD for one change request is not a claim that XGBoost can never be useful; it is a claim about the reachability of that specific registered request under its own frozen evidence rules.
'''.strip()


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    if MARKER not in text:
        anchor = "\n## Interpretation rules\n"
        if anchor not in text:
            raise RuntimeError("Evidence registry interpretation-rules anchor missing")
        text = text.replace(anchor, "\n\n" + BLOCK + "\n" + anchor, 1)
    first_rule = RULES.splitlines()[0]
    if first_rule not in text:
        anchor = "## Interpretation rules\n"
        text = text.replace(anchor, anchor + "\n" + RULES + "\n", 1)
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
