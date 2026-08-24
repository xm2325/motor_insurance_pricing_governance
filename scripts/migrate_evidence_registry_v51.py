from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.51 development rating-factor relativity audit |"
BLOCK = r'''
| v0.51 development rating-factor relativity audit | 2022-only frequency interpretability rebuild on 67,171 rows / 41,912.4959 exposure / 12,664 claims; Poisson GLM and XGBoost use the frozen v0.21 frequency specifications and a common exposure-weighted reference profile | `action_results/v51/rating_factor_relativity_summary_v51.json`, `RESULTS_V51.md` |
| v0.51 numeric rating structure | supported q05–q95 reference-profile sweeps show the largest model-family gaps for `driver_age` (max absolute log-relativity gap **0.26866**) and `vehicle_age` (**0.26771**); `vehicle_value` is much closer (**0.03394**) | `action_results/v51/numeric_rating_factor_relativities_v51.csv`, `RESULTS_V51.md` |
| v0.51 driver-age response example | at driver age 30 the GLM/XGB relativities are about **0.880 / 1.013**; at 68 they are about **1.172 / 0.896** around the same 2022 reference profile | `action_results/v51/numeric_rating_factor_relativities_v51.csv`, `RESULTS_V51.md` |
| v0.51 vehicle-age response example | at vehicle age 7 the GLM/XGB relativities are about **1.309 / 1.338**; at 44 they are about **0.702 / 0.918** around the same 2022 reference profile | `action_results/v51/numeric_rating_factor_relativities_v51.csv`, `RESULTS_V51.md` |
| v0.51 categorical rating structure | `vehicle_brand=BMW` is about **4.14%** of 2022 exposure with GLM/XGB relativities **1.328 / 1.174**; the absolute largest categorical gap is `policy_type=TP`, but that level is only **1.22%** exposure and is retained as a diagnostic rather than a headline | `action_results/v51/categorical_rating_factor_relativities_v51.csv`, `RESULTS_V51.md` |
| v0.51 interpretation boundary | reference-profile development sensitivity only; no 2023/2024 rows, incurred loss, actual premium, customer ID or policy status read; not a population-average PDP, validation result, causal effect, customer premium or promotion gate | `action_results/v51/rating_factor_relativity_summary_v51.json`, `tests/test_rating_factor_relativity_v51.py` |
'''.strip()

RULES = r'''
- v0.51 is **development interpretability evidence**, not fresh temporal/external validation. It cannot clear G2/G3/G4, open promotion review or authorise customer pricing.
- One-factor reference-profile sweeps hold every other feature at the common 2022 reference profile. They are not population-average PDPs, causal effects, actuarial rating recommendations or realised premium impacts.
- Small-exposure extreme categories are retained in the machine evidence but should not be promoted over larger supported groups merely because their model-family gap is numerically largest.
- `glm_direction_changes_over_quantile_grid` / `xgb_direction_changes_over_quantile_grid` are descriptive grid diagnostics only; they are not complexity scores or correctness gates.
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
