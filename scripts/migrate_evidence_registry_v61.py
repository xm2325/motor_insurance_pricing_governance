from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.61 prospective three-source request registration |"
BLOCK = r'''
| v0.61 prospective three-source request registration | atomically registers `MCR-XGB-MOTOR-002` before any new source row/outcome access with GLOBAL_TWO_TARGET scope: S1 `pg15training` temporal qualification, S2 `swmotorcycle` external replication, and S3 `brvehins1` sealed confirmation reserve; all three underlying source identities are pairwise distinct even though CASdatasets is the shared distribution channel | `governance/prospective_request_registration_v61.json`, `validate_prospective_request_registration_v61.py`, `action_results/v61/prospective_request_registration_lock.json` |
| v0.61 source-access budget | registration only: no new RDA downloaded/decoded, no new outcomes inspected, no model fit or performance metric; S2 can open only after reproducible S1 success and S3 only after reproducible S1+S2 success; any opened-stage source/schema failure consumes that stage and source substitution is forbidden | `RESULTS_V61.md`, `action_results/v61/ACTION_V61_STATUS.json` |
'''.strip()

RULES = r'''
- A shared public distribution package does not by itself make distinct underlying insurance portfolios one source identity; source identity is attached to the original portfolio/provider/product boundary registered before access.
- Documentation row counts and column order are provenance information, not binary identity gates. Pinned blob identity plus the registered semantic column-name set are the fail-closed controls; a missing or renamed required semantic field after stage opening still consumes that stage.
- Cross-year policy leakage controls must execute before outcome access. For S1, every policy identifier observed in more than one calendar year is removed from all years before claim-count or claim-cost fields may be read; the observed duplicate count is descriptive, not a target to force-match.
- `GLOBAL_TWO_TARGET` means frequency and pure-premium gates must both pass independently and reproducibly at every opened stage. One target cannot compensate for the other, and the sealed reserve cannot rescue an earlier stage failure.
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
