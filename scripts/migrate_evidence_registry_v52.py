from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.52 label-free rating-factor support audit |"
BLOCK = r'''
| v0.52 label-free rating-factor support audit | compares 2022 development and 2024 positive-exposure rating-feature populations using features/year/exposure only; **67,171 / 168,085 rows**, with no 2024 outcomes, premium, ID, policy-status or model fit | `action_results/v52/rating_factor_support_summary_v52.json`, `RESULTS_V52.md` |
| v0.52 strict numeric support | 2024 exposure outside the actual 2022 observed numeric range is negligible: maximum **0.00227%** for `power_to_weight_ratio`; `driver_age` **0.00159%**, `vehicle_age` **0.00079%** | `action_results/v52/numeric_feature_support_v52.csv`, `RESULTS_V52.md` |
| v0.52 central numeric tails | outside the development q05–q95 interval is **9.57% vehicle_value / 9.41% power_to_weight_ratio / 9.28% vehicle_age / 8.75% driver_age**; this is tail/mix shift, not strict extrapolation | `action_results/v52/numeric_feature_support_v52.csv`, `RESULTS_V52.md` |
| v0.52 business-type mix shift | under the exact v0.52 positive-exposure filter, `NB` **96.78% -> 48.18%** and `P` **3.22% -> 51.82%**; total-variation distance **48.60%**, while both categories remain seen | `action_results/v52/categorical_feature_support_v52.csv`, `action_results/v52/categorical_level_shift_v52.csv`, `RESULTS_V52.md` |
| v0.52 categorical unseen support | only `vehicle_brand` has non-missing 2024 levels absent from 2022: **6 brands / 0.00345% exposure**; all other registered categorical factors have zero unseen non-missing exposure under this audit | `action_results/v52/categorical_feature_support_v52.csv`, `action_results/v52/categorical_level_shift_v52.csv` |
| v0.52 shape-vs-support separation | `driver_age` has large v0.51 model-family shape gap **0.26866** but only **0.00159%** strict extrapolation; `business_type` has small frequency shape gap **0.02571** but **48.60%** mix TV; no composite score is created | `action_results/v51/rating_factor_relativity_summary_v51.json`, `action_results/v52/rating_factor_support_summary_v52.json`, `RESULTS_V52.md` |
| v0.52 governance boundary | post-hoc consumed-validation feature audit only; no performance evidence, candidate selection, model fit, promotion/pricing authority, causal/fairness conclusion or FIRST CENTRAL/current UK transport claim | `action_results/v52/ACTION_V52_STATUS.json`, `tests/test_rating_factor_support_v52.py` |
'''.strip()

RULES = r'''
- v0.52 defines **strict numeric extrapolation** only as values outside the observed 2022 min/max. Exposure outside q01-q99 or q05-q95 is a central-support/tail diagnostic and must not be relabelled as unseen numeric space.
- Categorical **unseen exposure** and **mix shift among seen levels** are separate diagnostics. A large total-variation distance does not imply new categories are present.
- v0.51 response-shape gap and v0.52 support/mix evidence are shown side by side and must not be combined into a subjective model-risk, promotion or pricing score.
- The v0.52 business-type shares use the exact v0.52 positive-exposure filter and should not be substituted mechanically for older monitoring percentages produced by different replay/baseline constructions.
- v0.52 uses no outcome labels and cannot clear G2/G3/G4, create fresh validation evidence or reopen model-family promotion review.
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
