from pathlib import Path

REGISTRY = Path("EVIDENCE_REGISTRY.md")

ROW_ANCHOR = "| v0.44 fail-closed human boundary | a human-signoff flag cannot override failed machine evidence gates; even an all-pass machine result can only become `READY_FOR_HUMAN_COMMITTEE_REVIEW`, never automatic promotion or customer pricing | `governance/model_change_committee_policy_v44.json`, `tests/test_model_change_committee_v44.py` |"
ROW = "| v0.45 repository front-door sync | README and Interview Evidence Pack are synchronised through v0.44, with v0.36–v0.44 external-validation/reproducibility/change-control evidence visible from the repository entry point; historical model/validation decisions are unchanged | `action_results/v45/repository_front_door_summary_v45.json`, `README.md`, `INTERVIEW_EVIDENCE_PACK.md` |"

INTERPRETATION_ANCHOR = "- The v0.44 gate is a project governance demonstration, not FIRST CENTRAL or insurer policy."
INTERPRETATION = """- v0.45 changes **documentation and evidence navigation only**. It does not rerun models, access row-level data, change historical gates or create new validation evidence.
- The README front door is intentionally concise; `EVIDENCE_REGISTRY.md` and persisted `action_results` remain the source of truth for headline claims.
- Interview wording must preserve the same evidence boundaries as the repository: benchmark uplift is not pricing uplift, consumed validation is not fresh evidence, the external `0/4` scope is explicit, and the committee gate is not a human approval."""

PROTECTION_OLD = "`tests/test_model_family_evidence_synthesis_v43.py` and `tests/test_model_change_committee_v44.py`"
PROTECTION_NEW = "`tests/test_model_family_evidence_synthesis_v43.py`, `tests/test_model_change_committee_v44.py` and `tests/test_repository_front_door_v45.py`"


def migrate(text: str) -> str:
    if "| v0.45 repository front-door sync |" not in text:
        if ROW_ANCHOR not in text:
            raise RuntimeError("v0.44 evidence-row anchor not found")
        text = text.replace(ROW_ANCHOR, ROW_ANCHOR + "\n" + ROW, 1)
    if "- v0.45 changes **documentation and evidence navigation only**" not in text:
        if INTERPRETATION_ANCHOR not in text:
            raise RuntimeError("v0.44 interpretation anchor not found")
        text = text.replace(INTERPRETATION_ANCHOR, INTERPRETATION_ANCHOR + "\n" + INTERPRETATION, 1)
    if PROTECTION_NEW not in text:
        if PROTECTION_OLD not in text:
            raise RuntimeError("automated-protection anchor not found")
        text = text.replace(PROTECTION_OLD, PROTECTION_NEW, 1)
    for marker in [
        "| v0.45 repository front-door sync |",
        "documentation and evidence navigation only",
        "tests/test_repository_front_door_v45.py",
    ]:
        if marker not in text:
            raise RuntimeError(f"registry migration missing marker: {marker}")
    return text


def main() -> None:
    original = REGISTRY.read_text(encoding="utf-8")
    migrated = migrate(original)
    REGISTRY.write_text(migrated, encoding="utf-8")
    assert migrate(migrated) == migrated
    print("V45_EVIDENCE_REGISTRY_MIGRATION_PASS")


if __name__ == "__main__":
    main()
