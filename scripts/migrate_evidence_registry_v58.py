from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.58 euMTPL source-contract incident |"
BLOCK = r'''
| v0.57 euMTPL external-temporal preregistration | third fresh external motor portfolio registered before row-level access; pinned `euMTPL` source identity and a chronological earliest-year train / middle-year calibration / latest-year locked-test design were frozen while preserving the existing v0.40 model/gate/reproducibility rules | `governance/external_temporal_prereg_v57.json`, `action_results/v57/eumtpl_external_temporal_prereg_lock.json`, `action_results/v57/ACTION_V57_STATUS.json` |
| v0.58 euMTPL source-contract incident | first authenticated decode failed the exact v0.57 schema contract before outcome-value inspection, year-value inspection, model fitting, calibration or performance scoring; pinned binary contained `cost_fcg/num_fcg` and a different column order instead of the registered `cost_fcd/num_fcd` exact schema | `RESULTS_V58.md`, `record_eumtpl_schema_contract_incident_v58.py`, `results_v58/eumtpl_schema_contract_incident_v58.json` |
| v0.58 confirmatory eligibility | because row-level R-object decode occurred before the source-schema mismatch was known, no post-access schema amendment is used for confirmatory evidence and `euMTPL` is no longer treated as a fresh independent confirmatory dataset; future use must be explicitly diagnostic/non-confirmatory | `RESULTS_V58.md`, `results_v58/eumtpl_schema_contract_incident_v58.json` |
| v0.58 governance outcome | no external/temporal model evidence or machine-gate credit was created; committee state remains `EVIDENCE_GAP_HOLD`, **5/8**, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, customer pricing unauthorised | `RESULTS_V58.md`, `action_results/v58/ACTION_V58_STATUS.json` |
'''.strip()

RULES = r'''
- A source identity check can pass while a preregistered schema contract fails. Authentic bytes do not justify silently repairing a post-access schema mismatch.
- Decoding a fresh external object consumes fresh-confirmatory eligibility for this project when a material exact-schema/target amendment would be required afterwards, even if no model performance metric was computed.
- A green incident-reproduction workflow is evidence that the failure state is reproducible; it is **not** a successful external replication and cannot clear committee gates.
- Upstream documentation defects must be recorded explicitly rather than resolved in whichever direction would make a later result more favourable.
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
