from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.63 pre-seal source-contract qualification |"
BLOCK = r'''
| v0.63 pre-seal source-contract qualification | prospective `Q0_SOURCE_CONTRACT_QUALIFICATION` requires binary/documentation identity plus metadata-only object/column-name qualification before a future fresh source/request can be sealed; `pyreadr.read_r`, row/outcome/exposure/feature values, summaries, model fitting and performance metrics remain forbidden | `governance/source_contract_qualification_policy_v63.json`, `run_source_contract_qualification_v63.py`, `execute_source_contract_qualification_v63.py`, `RESULTS_V63.md` |
| v0.63 historical Q0 replay | metadata-only replay on already-consumed `pg15training` and `euMTPL` would have blocked both before seal: `Expdays` vs `Exppdays`, and `cost_fcd/num_fcd` vs `cost_fcg/num_fcg`; no automatic aliases are used | `action_results/v63/source_contract_qualification_replay_v63.json`, `RESULTS_V63.md` |
| v0.63 metadata-reader compatibility evidence | pyreadr 0.5.3 and 0.5.6 `list_objects` required a narrow no-op `ListObjectsParser.handle_row_name` compatibility patch for these RDA files; row names are discarded and no value callback or `read_r` path is introduced | `action_results/v63/metadata_reader_patch_v63.json`, `RESULTS_V63.md` |
| v0.63 governance outcome | process control only: no new change request/source, no fresh performance evidence, MCR-001 and MCR-002 remain terminal, historical committee state stays **5/8**, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, pricing unauthorised | `action_results/v63/ACTION_V63_STATUS.json`, `RESULTS_V63.md` |
'''.strip()

RULES = r'''
- Future prospective fresh-source work must complete `Q0_SOURCE_CONTRACT_QUALIFICATION` before sealing the source/request. Metadata-only schema qualification can block or correct a source specification before any row/outcome value is inspected; it is not model validation.
- Binary authenticity and documentation prose are not enough by themselves. Proposed semantic identifiers must also agree with pinned binary schema metadata; near matches trigger explicit review and never auto-alias.
- A metadata-reader limitation must not be bypassed with value decoding. Qualification must either obtain schema metadata under the Q0 boundary or block sealing until a compliant metadata path exists.
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
