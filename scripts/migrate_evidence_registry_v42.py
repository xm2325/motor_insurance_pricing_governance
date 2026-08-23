from pathlib import Path

REGISTRY = Path("EVIDENCE_REGISTRY.md")

ROWS_ANCHOR = (
    "| v0.39 next external-evidence rule | unseen external data may enter only through preregistration with **row-level access still forbidden**; future positive support inherits the v0.38 two-run reproducibility gate | `governance/external_validation_use_ledger_v39.json`, `RESULTS_V39.md` |"
)
ROWS = """| v0.40 Belgian external preregistration | `beMTPL97` protocol locked on main **before row-level access**; main run **32637337675**, prereg SHA-256 `19658e3a...96822`; `row_level_external_data_accessed=false`; positive support prospectively requires >=2 independent executions | `action_results/v40/ACTION_V40_STATUS.json`, `action_results/v40/belgian_external_validation_prereg_lock.json`, `RESULTS_V40.md` |
| v0.41 Belgian external source and split | **163,212** unique policies; raw source SHA-256 `955a821a...63a6`; frozen 60/20/20 split with **32,643** locked-test rows; raw data not persisted | `action_results/v41/origin/32637884887/belgian_source_audit.json`, `action_results/v41/origin/32637884887/belgian_external_replication_first_execution.json` |
| v0.41 Belgian frequency replication | GLM deviance **0.604357** vs XGBoost **0.602598**; XGB relative improvement **+0.2910%**; bootstrap 95% **[+0.0987%, +0.4876%]**; below fixed 0.5% point threshold -> `NO_SECOND_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT` | `action_results/v41/origin/32637884887/belgian_external_replication_first_execution.json`, `RESULTS_V41.md` |
| v0.41 Belgian pure-premium replication | GLM deviance **79.843311** vs XGBoost **79.586308**; XGB relative improvement **+0.3219%**; bootstrap 95% **[-0.7918%, +1.3082%]**; top-10 loss capture **20.45% -> 19.12%** -> `NO_SECOND_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT` | `action_results/v41/origin/32637884887/belgian_external_replication_first_execution.json`, `RESULTS_V41.md` |
| v0.42 Belgian numerical reproducibility | completed model executions **32637809066 (eastus2)** and **32637884887 (centralus)** reproduce all registered aggregate metrics within preregistered tolerances; max abs diff **1.421085e-14**, max rel diff **6.898279e-14** | `action_results/v42/belgian_external_closeout_summary.json`, `RESULTS_V42.md` |
| v0.42 Belgian evidence class | `CONSUMED_EXTERNAL_VALIDATION_DATASET`; locked test unavailable for new fitting, tuning, candidate selection or fresh independent confirmation | `action_results/v42/external_validation_use_ledger_v42.json`, `RESULTS_V42.md` |
| v0.42 governance result | two reproducible negative gates remain negative; model family `HOLD`, serving `HOLD_SHADOW_ONLY`; no promotion or pricing change authorised | `action_results/v42/belgian_external_closeout_summary.json`, `RESULTS_V42.md` |"""

INTERPRETATION_ANCHOR = (
    "- Future positive external-support claims require a newly preregistered unseen dataset/period and the prospective v0.38 numerical-reproducibility controls."
)
INTERPRETATION = """- v0.40 is **preregistration evidence**, not a Belgian performance result: source, split, features, models, solver/tolerance, gates and reproducibility rules were fixed on main while Belgian row-level access was still false.
- v0.41 is a **second external model-family replication**, not direct validation of fitted Spanish models and not evidence of UK/FIRST CENTRAL transport. Both registered Belgian support gates fail under the frozen rules.
- The frequency bootstrap interval is positive but the fixed **0.5% materiality threshold** still fails; statistical direction alone is not relabelled as model-family support.
- v0.42 shows observed point-metric reproducibility across the two completed eastus2/centralus executions within preregistered tolerances. It does **not** claim universal bitwise determinism or identify a unique hardware/region cause for the earlier Australian numerical instability.
- v0.42 marks `beMTPL97` as **consumed external validation**. Re-running, resplitting, retuning or changing the solver/features after outcome inspection cannot restore independence.
- Two reproducible negative decisions remain negative; numerical reproducibility is evidence quality, not evidence of challenger superiority."""

PROTECTION_OLD = "`tests/test_external_reproducibility_evidence_v38.py`, `tests/test_external_reproducibility_persisted_v38.py` and `tests/test_external_validation_firewall_v39.py`"
PROTECTION_NEW = "`tests/test_external_reproducibility_evidence_v38.py`, `tests/test_external_reproducibility_persisted_v38.py`, `tests/test_external_validation_firewall_v39.py` and `tests/test_belgian_external_closeout_v42.py`"


def migrate(text: str) -> str:
    if "| v0.40 Belgian external preregistration |" not in text:
        if ROWS_ANCHOR not in text:
            raise RuntimeError("v0.39 evidence-row anchor not found")
        text = text.replace(ROWS_ANCHOR, ROWS_ANCHOR + "\n" + ROWS, 1)

    if "- v0.40 is **preregistration evidence**" not in text:
        if INTERPRETATION_ANCHOR not in text:
            raise RuntimeError("v0.39 interpretation anchor not found")
        text = text.replace(
            INTERPRETATION_ANCHOR,
            INTERPRETATION_ANCHOR + "\n" + INTERPRETATION,
            1,
        )

    if PROTECTION_NEW not in text:
        if PROTECTION_OLD not in text:
            raise RuntimeError("automated-protection anchor not found")
        text = text.replace(PROTECTION_OLD, PROTECTION_NEW, 1)

    required = [
        "| v0.40 Belgian external preregistration |",
        "| v0.41 Belgian frequency replication |",
        "| v0.42 Belgian numerical reproducibility |",
        "CONSUMED_EXTERNAL_VALIDATION_DATASET",
        "tests/test_belgian_external_closeout_v42.py",
    ]
    for marker in required:
        if marker not in text:
            raise RuntimeError(f"registry migration missing marker: {marker}")
    return text


def main() -> None:
    original = REGISTRY.read_text(encoding="utf-8")
    migrated = migrate(original)
    REGISTRY.write_text(migrated, encoding="utf-8")
    # Idempotence is part of the contract.
    assert migrate(migrated) == migrated
    print("V42_EVIDENCE_REGISTRY_MIGRATION_PASS")


if __name__ == "__main__":
    main()
