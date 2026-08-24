from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.48 portfolio-neutral technical relativity design |"
BLOCK = r'''
| v0.48 portfolio-neutral technical relativity design | label-free post-hoc diagnostic on the full **168,085-row** positive-exposure 2024 feature population; frozen GLM/XGBoost scores are aggregate-neutralised before measuring redistribution; no 2024 outcomes or actual premiums are read | `action_results/v48/portfolio_neutral_relativity_summary_v48.json`, `RESULTS_V48.md` |
| v0.48 exact portfolio neutralisation | float64 neutralisation gives `normalised_total_over_reference = 1.0` and absolute aggregate difference **0.0** for both frequency and pure premium | `action_results/v48/portfolio_neutral_relativity_summary_v48.json`, `RESULTS_V48.md` |
| v0.48 frequency redistribution | after aggregate neutralisation, **36.81%** of exposure moves by more than ±10% and **10.98%** by more than ±20%; median technical relativity change is about **-0.61%** | `action_results/v48/portfolio_neutral_relativity_summary_v48.json`, `action_results/v48/relativity_migration_bands_v48.csv`, `RESULTS_V48.md` |
| v0.48 pure-premium redistribution | after aggregate neutralisation, about **78.26%** of exposure moves by more than ±10% and **58.16%** by more than ±20%; median technical relativity change is about **-2.69%** | `action_results/v48/portfolio_neutral_relativity_summary_v48.json`, `action_results/v48/relativity_migration_bands_v48.csv`, `RESULTS_V48.md` |
| v0.48 major-segment redistribution | pure-premium aggregate technical relativity is about **+8.65% NB vs -6.52% P**, **+13.68% COMP_E vs -9.27% CC**, and **+5.20% age 35-49 vs -5.49% age 50-64** after portfolio neutralisation; these are descriptive score shifts, not accuracy or customer-price effects | `action_results/v48/segment_relativity_migration_v48.csv`, `RESULTS_V48.md` |
| v0.48 governance result | diagnostic only: no customer pricing, rate action, new candidate selection or promotion evidence; no row-level changes persisted; frozen Tweedie GLM convergence limitation is retained and repeat-run sensitivity is reported rather than hidden | `action_results/v48/portfolio_neutral_relativity_summary_v48.json`, `RESULTS_V48.md` |
'''.strip()

RULES = r'''
- v0.48 is a **portfolio-neutral technical-risk redistribution diagnostic**, not a premium-change simulation. It does not include expenses, commission, reinsurance, profit, tax, demand/elasticity or underwriting actions.
- The ±5% / ±10% / ±20% migration bands are fixed project diagnostic bins, not insurer, actuarial, regulatory or commercial thresholds.
- v0.48 uses consumed Spanish 2024 features/exposure only. It creates no fresh validation evidence and cannot be used to reopen model-family promotion.
- v0.48 segment shifts describe differences between two frozen technical-risk score families after aggregate neutralisation. They are not segment accuracy, fairness, causality or customer-impact conclusions.
- The frozen Tweedie GLM `max_iter=900` convergence warning remains a registered limitation. Repeat-run numerical sensitivity must accompany any pure-premium v0.48 headline.
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
    old = "`tests/test_disagreement_attribution_v47.py` protects the label-free, post-hoc and non-causal v0.47 diagnostic boundary."
    new = old + " `tests/test_portfolio_neutral_relativity_v48.py` protects the label-free portfolio-neutral redistribution boundary, float64 aggregate-neutralisation and aggregate-only segment outputs."
    if new not in text:
        if old not in text:
            raise RuntimeError("Automated-protection v0.47 anchor missing")
        text = text.replace(old, new, 1)
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
