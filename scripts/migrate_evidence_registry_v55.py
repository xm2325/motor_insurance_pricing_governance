from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.55 development rating-shape stability |"
BLOCK = r'''
| v0.55 development rating-shape stability | preregistered five-fold, outcome-unstratified 2022 development refits of the frozen v0.21 frequency GLM/XGBoost specifications while keeping the persisted v0.51 reference profile and evaluation grid fixed; no held-out performance metric is computed | `governance/rating_shape_stability_protocol_v55.json`, `run_rating_shape_stability_audit_v55.py`, `RESULTS_V55.md` |
| v0.55 large-gap tail persistence | preselected `driver_age` q95 full-fit log gap **-0.268660** has five-fold range **[-0.356179, -0.122047]** with **5/5** same sign; `vehicle_age` q95 full-fit **+0.267706** has range **[+0.156786, +0.346264]** with **5/5** same sign | `results_v55/rating_shape_stability_summary_v55.json`, `results_v55/rating_shape_stability_point_summary_v55.csv`, `RESULTS_V55.md` |
| v0.55 counterexample / local sensitivity | preregistered smaller-gap `vehicle_value` q95 changes sign across folds (**-0.059073 → +0.028179**, only **2/5** same sign as the full fit); `vehicle_age` also contains registered lower-age points that can reverse sign, so no whole-feature stability claim is made | `results_v55/rating_shape_stability_point_summary_v55.csv`, `RESULTS_V55.md` |
| v0.55 evidence boundary | development fit-sensitivity only: 2023/2024 rows, incurred loss, premium, IDs and policy status are not read; no confidence interval, predictive-validation evidence, candidate selection, promotion threshold, composite score, FIRST CENTRAL/current-UK transport claim or customer-pricing authority is created | `governance/rating_shape_stability_protocol_v55.json`, `results_v55/rating_shape_stability_summary_v55.json`, `RESULTS_V55.md` |
'''.strip()

RULES = r'''
- v0.55 fold min/max and same-sign fractions are **descriptive fixed-design development sensitivity outputs**, not confidence intervals or predictive validation.
- The v0.51 reference profile and registered evaluation points are held fixed across folds; only the 80% development fitting subset changes, so fold variation is not confounded with a moving interpretation grid.
- Directional persistence at selected large-gap tail points does not imply that an entire feature response is stable; local registered points can behave differently and smaller gaps can change sign.
- v0.55 creates no numerical acceptance threshold after observing the folds and does not alter `EVIDENCE_GAP_HOLD`, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, external support `0/4`, or customer-pricing authority.
'''.strip()


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    if MARKER not in text:
        anchor = "\n## Interpretation rules\n"
        if anchor not in text:
            raise RuntimeError("Evidence registry interpretation-rules anchor missing")
        text = text.replace(anchor, "\n\n" + BLOCK + "\n" + anchor, 1)
    if RULES.splitlines()[0] not in text:
        anchor = "## Interpretation rules\n"
        text = text.replace(anchor, anchor + "\n" + RULES + "\n", 1)
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
