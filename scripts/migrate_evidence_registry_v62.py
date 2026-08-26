from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.62 Pricing Game S1 source-contract incident |"
BLOCK = r'''
| v0.62 Pricing Game S1 source-contract incident | first legal opening of `MCR-XGB-MOTOR-002` S1 authenticated the pinned `pg15training` binary, then failed the v0.61 semantic column-name contract because the registered exposure field was `Expdays` while the decoded object contains `Exppdays`; execution stopped before policy/year values, exposure, outcomes, features, model fit, calibration or performance metrics | `RESULTS_V62.md`, `record_pricing_game_s1_schema_incident_v62.py`, `action_results/v62/pricing_game_s1_schema_incident_v62.json` |
| v0.62 MCR-XGB-MOTOR-002 lifecycle | under the v0.61 rules an opened-stage source-contract incident consumes S1; no S1 pass or reproduction is authorised, S2 `swmotorcycle` and S3 `brvehins1` remain sealed, source substitution and reserve rescue are forbidden, and the request is terminal as `TERMINAL_S1_SOURCE_CONTRACT_INCIDENT` | `governance/prospective_request_registration_v61.json`, `RESULTS_V62.md`, `action_results/v62/ACTION_V62_STATUS.json` |
| v0.62 evidence/governance outcome | no fresh temporal/external model evidence and no committee-gate credit were created; historical state remains **5/8**, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, customer pricing unauthorised | `RESULTS_V62.md`, `action_results/v62/ACTION_V62_STATUS.json` |
'''.strip()

RULES = r'''
- A semantic source-contract incident in an opened prospective stage is not repaired retrospectively for confirmatory credit when the pre-access programme explicitly says that such an incident consumes the stage.
- A trivial engineering compatibility fix can still be a material governance amendment: `Expdays` versus `Exppdays` is easy to alias in code, but doing so after first stage access would change the registered semantic contract and is therefore not used to rescue `MCR-XGB-MOTOR-002`.
- A sealed later source is not a replacement pool. Under the v0.61 programme, S2/S3 cannot be opened to rescue a consumed/failed S1.
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
