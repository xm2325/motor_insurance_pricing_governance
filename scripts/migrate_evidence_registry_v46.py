from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "EVIDENCE_REGISTRY.md"

ROWS = """| v0.46 model-risk inventory | machine-readable inventory reconciles the four shadow model artifacts with current validation-use, external-evidence, operational-control and committee-readiness states; no row-level access or model fit | `action_results/v46/model_risk_inventory_v46.json`, `MODEL_CARD.md`, `RESULTS_V46.md` |
| v0.46 validation-asset state | Spanish 2024 is `CONSUMED_RETROSPECTIVE_VALIDATION`; Australian `ausprivauto0405` and Belgian `beMTPL97` are `CONSUMED_EXTERNAL_VALIDATION_DATASET`; none is fresh candidate-selection evidence | `action_results/v46/model_risk_inventory_v46.json`, `governance/validation_use_ledger_v35.json`, `governance/external_validation_use_ledger_v39.json`, `governance/external_validation_use_ledger_v42.json` |
| v0.46 reconciled decision | operational controls remain available for shadow use, but external support is **0/4** and committee readiness remains **`EVIDENCE_GAP_HOLD` (5/8)** with G2/G3/G4 blockers; no promotion or pricing authority | `action_results/v46/model_risk_inventory_v46.json`, `action_results/v44/model_change_committee_decision_v44.json` |
"""

BULLETS = """- v0.46 is an **aggregate state-reconciliation artifact**, not a new validation experiment. It reads persisted evidence only and cannot improve, retune or relabel a model result.
- The Model Card now distinguishes each validation asset's **role at first use** from its **current consumed role**. Spanish 2024 must not again be described as a currently untouched holdout.
- Operational readiness remains separate from evidence adequacy: shadow serving, rollback and attested admission may pass while `EVIDENCE_GAP_HOLD` remains the correct model-change state.
"""


def migrate(text: str) -> str:
    if "| v0.46 model-risk inventory |" not in text:
        marker = "\n## Interpretation rules\n"
        if marker not in text:
            raise RuntimeError("EVIDENCE_REGISTRY.md missing Interpretation rules marker")
        text = text.replace(marker, "\n" + ROWS + marker, 1)
    if "- v0.46 is an **aggregate state-reconciliation artifact**" not in text:
        marker = "\n- Synthetic quote-conversion / proposition experiments are not reported as observed commercial impact."
        if marker not in text:
            raise RuntimeError("EVIDENCE_REGISTRY.md missing interpretation insertion marker")
        text = text.replace(marker, "\n" + BULLETS.rstrip() + marker, 1)
    if "tests/test_model_risk_inventory_v46.py" not in text:
        marker = "`tests/test_evidence_push_static_v31.py` also exercises"
        if marker not in text:
            raise RuntimeError("EVIDENCE_REGISTRY.md missing automated-protection marker")
        text = text.replace(
            marker,
            "`tests/test_model_risk_inventory_v46.py` protects current model/data/evidence/committee-state reconciliation. " + marker,
            1,
        )
    return text


def main() -> None:
    original = PATH.read_text(encoding="utf-8")
    updated = migrate(original)
    PATH.write_text(updated, encoding="utf-8")
    if migrate(updated) != updated:
        raise RuntimeError("v0.46 registry migration is not idempotent")
    print("V46_EVIDENCE_REGISTRY_MIGRATION_PASS")


if __name__ == "__main__":
    main()
