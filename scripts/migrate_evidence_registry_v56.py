from pathlib import Path

PATH = Path("EVIDENCE_REGISTRY.md")
MARKER = "| v0.56 development rating-context sensitivity |"
BLOCK = r'''
| v0.56 development rating-context sensitivity | preregistered 2022 development-only profile audit: fit the frozen frequency GLM/XGBoost once, keep the exact v0.51 driver-age/vehicle-age grids, and re-score five fixed synthetic reference-profile contexts selected from persisted v0.51 marginal exposure before v0.56 scoring | `governance/rating_context_sensitivity_protocol_v56.json`, `run_rating_context_sensitivity_audit_v56.py`, `RESULTS_V56.md` |
| v0.56 q95 context persistence | `driver_age` q95 log gap remains negative in **5/5** contexts, spanning about **-0.2785 to -0.1872** (range **0.09126**); `vehicle_age` q95 remains positive in **5/5**, about **+0.2639 to +0.3167** (range **0.05278**) | `results_v56/rating_context_sensitivity_summary_v56.json`, `results_v56/rating_context_cross_context_summary_v56.csv`, `RESULTS_V56.md` |
| v0.56 local context counterexample | whole-grid context dependence is non-zero: max context-minus-BASE log-gap difference is **0.08141** for driver age and **0.14179** for vehicle age; vehicle-age q05 changes sign across the registered contexts, so no whole-curve context-invariance claim is allowed | `results_v56/rating_context_curve_points_v56.csv`, `results_v56/rating_context_cross_context_summary_v56.csv`, `RESULTS_V56.md` |
| v0.56 GLM implementation control | after within-context normalisation, the additive/no-interaction Poisson GLM curve is context-invariant to floating-point precision (first-run max log-relativity spread **6.38e-16**); the visible context variation is in the XGBoost response rather than categorical main-effect level | `results_v56/rating_context_sensitivity_summary_v56.json`, `RESULTS_V56.md` |
| v0.56 hosted numerical repeat | exact scoring head ran on centralus and northcentralus; outputs are not byte-identical, maximum GLM relativity drift is **8.02e-8** and log-gap drift **6.92e-8**, while XGBoost relativities are exact and all context ordering/sign conclusions are unchanged | `governance/rating_context_repeat_evidence_v56.json`, `RESULTS_V56.md` |
| v0.56 evidence boundary | the five contexts are synthetic reference-profile perturbations, not observed joint customer cells; marginal exposure shares are not joint-profile prevalence; no predictive validation, CI, causal interaction, observed segment effect, fairness conclusion, candidate selection, promotion evidence, customer-price effect or FIRST CENTRAL/current-UK transport claim is created | `governance/rating_context_sensitivity_protocol_v56.json`, `results_v56/rating_context_sensitivity_summary_v56.json`, `RESULTS_V56.md` |
'''.strip()

RULES = r'''
- v0.56 context profiles are **synthetic reference-profile scenarios**. A v0.51 marginal exposure share describes only the changed categorical level and must not be reported as prevalence of the complete profile.
- Curves are normalised within model/context at the registered target-feature reference value. This removes categorical main-effect level; it does not turn the response into a causal interaction estimate.
- q95 directional persistence across the five registered contexts does not imply whole-curve context invariance. The vehicle-age q05 sign reversal is retained explicitly.
- v0.56 has no post-result context-stability acceptance threshold or composite score. Hosted repeat floating-point differences are retained rather than rounded into a bitwise/exact reproducibility claim.
- v0.56 is development interpretability only and cannot clear `G2/G3/G4`, change `EVIDENCE_GAP_HOLD`, alter `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, or authorise customer pricing.
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
