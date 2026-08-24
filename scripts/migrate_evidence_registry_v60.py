from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.60 prospective evidence-programme template |"
BLOCK = r'''
| v0.60 prospective evidence-programme template | non-active template for a future change request after terminal MCR-001; requires three pairwise-distinct fresh source identities — S1 locked temporal qualification, S2 independent external replication, and S3 sealed reserve — with target scope fixed before fresh outcome access and no source replacement after a registered S1/S2 failure | `governance/prospective_evidence_program_template_v60.json`, `validate_prospective_evidence_program_v60.py`, `action_results/v60/prospective_evidence_program_validation_v60.json` |
| v0.60 evidence budget | one source identity per S1/S2/S3; failed S1/S2 cannot be replaced, S3 cannot rescue them, target scope and performance gates cannot be changed after failure, and a later attempt requires a new prospectively registered request ID | `RESULTS_V60.md`, `action_results/v60/ACTION_V60_STATUS.json` |
'''.strip()

RULES = r'''
- Qualification evidence, independent replication evidence and a still-sealed reserve are different evidence roles; one portfolio must not be relabelled to satisfy all three roles.
- A prospective evidence budget is part of the anti-data-shopping contract: a failed registered source is evidence, not permission to keep replacing sources until one passes.
- Target-specific and global-family questions must be separated prospectively. A global two-target request cannot be rescued by whichever target looks better after outcomes are observed.
- A template is not an active model-change request. Source selection, row-level access or candidate evaluation requires a separately registered request whose scope is already fixed.
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
