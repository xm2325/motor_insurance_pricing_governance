from pathlib import Path

REGISTRY = Path("EVIDENCE_REGISTRY.md")

ROW_ANCHOR = "| v0.43 reopen requirement | new unseen independent dataset/period, preregistered before row-level access; any positive external support must pass registered performance gates plus the two-independent-Actions numerical reproducibility requirement before a separate governance decision | `action_results/v43/model_family_evidence_synthesis_summary.json`, `RESULTS_V43.md` |"
ROWS = """| v0.44 model-change committee machine gate | request `MCR-XGB-MOTOR-001` -> `EVIDENCE_GAP_HOLD`; **5/8** required gates pass; blockers are `G2_LOCKED_TEMPORAL_SUPPORT`, `G3_PREREGISTERED_EXTERNAL_SUPPORT`, `G4_FRESH_INDEPENDENT_EVIDENCE` | `action_results/v44/model_change_committee_decision_v44.json`, `action_results/v44/MODEL_CHANGE_COMMITTEE_PACK_V44.md`, `RESULTS_V44.md` |
| v0.44 operational-vs-evidence separation | shadow deployment, release/rollback and attested shadow admission gates pass, but operational readiness cannot compensate for failed validation evidence | `action_results/v44/model_change_committee_decision_v44.json` |
| v0.44 fail-closed human boundary | a human-signoff flag cannot override failed machine evidence gates; even an all-pass machine result can only become `READY_FOR_HUMAN_COMMITTEE_REVIEW`, never automatic promotion or customer pricing | `governance/model_change_committee_policy_v44.json`, `tests/test_model_change_committee_v44.py` |"""

INTERPRETATION_ANCHOR = "- A future positive result on already-consumed Spanish, Australian or Belgian validation data cannot reopen independent promotion review by rerunning, resplitting or retuning."
INTERPRETATION = """- v0.44 is a **machine readiness gate for human review**, not a human committee decision and not an automated model approval engine.
- The current 5/8 gate pattern deliberately separates operational controls from validation adequacy: deployability, rollback and attested shadow admission all pass while the evidence blockers keep the request on `EVIDENCE_GAP_HOLD`.
- Human sign-off is audit metadata only in this project contract and cannot override failed evidence gates.
- Even a future all-pass machine evaluation would only open a human review; it would not authorise production serving or customer pricing.
- The v0.44 gate is a project governance demonstration, not FIRST CENTRAL or insurer policy."""

PROTECTION_OLD = "`tests/test_belgian_external_closeout_v42.py` and `tests/test_model_family_evidence_synthesis_v43.py`"
PROTECTION_NEW = "`tests/test_belgian_external_closeout_v42.py`, `tests/test_model_family_evidence_synthesis_v43.py` and `tests/test_model_change_committee_v44.py`"


def migrate(text: str) -> str:
    if "| v0.44 model-change committee machine gate |" not in text:
        if ROW_ANCHOR not in text:
            raise RuntimeError("v0.43 evidence-row anchor not found")
        text = text.replace(ROW_ANCHOR, ROW_ANCHOR + "\n" + ROWS, 1)

    if "- v0.44 is a **machine readiness gate for human review**" not in text:
        if INTERPRETATION_ANCHOR not in text:
            raise RuntimeError("v0.43 interpretation anchor not found")
        text = text.replace(INTERPRETATION_ANCHOR, INTERPRETATION_ANCHOR + "\n" + INTERPRETATION, 1)

    if PROTECTION_NEW not in text:
        if PROTECTION_OLD not in text:
            raise RuntimeError("automated-protection anchor not found")
        text = text.replace(PROTECTION_OLD, PROTECTION_NEW, 1)

    required = [
        "| v0.44 model-change committee machine gate |",
        "**5/8** required gates pass",
        "EVIDENCE_GAP_HOLD",
        "READY_FOR_HUMAN_COMMITTEE_REVIEW",
        "tests/test_model_change_committee_v44.py",
    ]
    for marker in required:
        if marker not in text:
            raise RuntimeError(f"registry migration missing marker: {marker}")
    return text


def main() -> None:
    original = REGISTRY.read_text(encoding="utf-8")
    migrated = migrate(original)
    REGISTRY.write_text(migrated, encoding="utf-8")
    assert migrate(migrated) == migrated
    print("V44_EVIDENCE_REGISTRY_MIGRATION_PASS")


if __name__ == "__main__":
    main()
