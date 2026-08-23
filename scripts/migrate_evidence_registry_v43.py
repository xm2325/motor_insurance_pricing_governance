from pathlib import Path

REGISTRY = Path("EVIDENCE_REGISTRY.md")

ROW_ANCHOR = "| v0.42 governance result | two reproducible negative gates remain negative; model family `HOLD`, serving `HOLD_SHADOW_ONLY`; no promotion or pricing change authorised | `action_results/v42/belgian_external_closeout_summary.json`, `RESULTS_V42.md` |"
ROWS = """| v0.43 model-family evidence synthesis | aggregate-only dossier retains original evidence classes and registered decisions; **0/4 preregistered external target gates pass** across Australia and Belgium; no pooled meta-analysis or evidence-weighting score | `action_results/v43/model_family_evidence_synthesis_summary.json`, `action_results/v43/MODEL_FAMILY_REVIEW_PACK_V43.md`, `RESULTS_V43.md` |
| v0.43 review decision | `HOLD / HOLD_SHADOW_ONLY`; `promotion_review_status=NOT_OPEN`; benchmark evidence cannot override failed validation gates and consumed validation cannot be relabelled independent | `action_results/v43/model_family_evidence_synthesis_summary.json`, `governance/model_family_evidence_synthesis_policy_v43.json` |
| v0.43 reopen requirement | new unseen independent dataset/period, preregistered before row-level access; any positive external support must pass registered performance gates plus the two-independent-Actions numerical reproducibility requirement before a separate governance decision | `action_results/v43/model_family_evidence_synthesis_summary.json`, `RESULTS_V43.md` |"""

INTERPRETATION_ANCHOR = "- Two reproducible negative decisions remain negative; numerical reproducibility is evidence quality, not evidence of challenger superiority."
INTERPRETATION = """- v0.43 is an **aggregate model-risk synthesis**, not a new validation experiment. It does not fit models, access row-level validation data, change historical gates or create a pooled promotion score.
- The strong freMTPL2 benchmark signal is retained as development evidence but cannot override the Spanish/Australian/Belgian validation decisions.
- `0/4` refers only to the four preregistered external target gates across Australia and Belgium; it is not a claim that every XGBoost metric is worse than GLM.
- `promotion_review_status=NOT_OPEN` is a project governance state derived from the existing evidence contracts, not an insurer/FIRST CENTRAL approval policy.
- A future positive result on already-consumed Spanish, Australian or Belgian validation data cannot reopen independent promotion review by rerunning, resplitting or retuning."""

PROTECTION_OLD = "`tests/test_external_validation_firewall_v39.py` and `tests/test_belgian_external_closeout_v42.py`"
PROTECTION_NEW = "`tests/test_external_validation_firewall_v39.py`, `tests/test_belgian_external_closeout_v42.py` and `tests/test_model_family_evidence_synthesis_v43.py`"


def migrate(text: str) -> str:
    if "| v0.43 model-family evidence synthesis |" not in text:
        if ROW_ANCHOR not in text:
            raise RuntimeError("v0.42 evidence-row anchor not found")
        text = text.replace(ROW_ANCHOR, ROW_ANCHOR + "\n" + ROWS, 1)

    if "- v0.43 is an **aggregate model-risk synthesis**" not in text:
        if INTERPRETATION_ANCHOR not in text:
            raise RuntimeError("v0.42 interpretation anchor not found")
        text = text.replace(INTERPRETATION_ANCHOR, INTERPRETATION_ANCHOR + "\n" + INTERPRETATION, 1)

    if PROTECTION_NEW not in text:
        if PROTECTION_OLD not in text:
            raise RuntimeError("automated-protection anchor not found")
        text = text.replace(PROTECTION_OLD, PROTECTION_NEW, 1)

    required = [
        "| v0.43 model-family evidence synthesis |",
        "0/4 preregistered external target gates pass",
        "promotion_review_status=NOT_OPEN",
        "tests/test_model_family_evidence_synthesis_v43.py",
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
    print("V43_EVIDENCE_REGISTRY_MIGRATION_PASS")


if __name__ == "__main__":
    main()
