from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "EVIDENCE_REGISTRY.md"

ROWS = """| v0.47 disagreement diagnostic design | post-hoc diagnostic on consumed Spanish 2024; **20,000** positive-exposure rows, seed **20260823**, 2024 claim/incurred labels not read; one-factor substitution uses 2022 median/mode references and frozen v0.21 model definitions | `action_results/v47/disagreement_attribution_summary_v47.json`, `action_results/v47/diagnostic_sample_manifest_v47.json`, `RESULTS_V47.md` |
| v0.47 frequency disagreement sensitivity | baseline exposure-weighted mean absolute `log(XGB/GLM)` **0.09926**; largest one-factor reductions are `vehicle_brand` **10.75%**, `policy_type` **10.58%**, `vehicle_value` **6.00%** | `action_results/v47/disagreement_attribution_summary_v47.json`, `action_results/v47/feature_disagreement_attribution_v47.csv`, `RESULTS_V47.md` |
| v0.47 pure-premium disagreement sensitivity | baseline mean absolute `log(XGB/GLM)` **0.31708**; largest one-factor reductions are `business_type` **6.23%**, `power_to_weight_ratio` **3.39%**, `vehicle_value` **3.32%**; effects are explicitly non-additive/non-causal | `action_results/v47/disagreement_attribution_summary_v47.json`, `action_results/v47/feature_disagreement_attribution_v47.csv`, `RESULTS_V47.md` |
| v0.47 governance result | diagnostic only: no 2024 outcome labels in scoring, no new candidate selection, no row-level prediction persistence, no promotion evidence; frozen Tweedie GLM `max_iter=900` convergence warning is retained rather than changing the model after inspection | `action_results/v47/disagreement_attribution_summary_v47.json`, `RESULTS_V47.md` |
"""

BULLETS = """- v0.47 is a **post-hoc score-sensitivity diagnostic** on already-consumed Spanish 2024 validation, not a new model-performance test or independent confirmation.
- v0.47 one-factor reference substitutions are **non-additive and non-causal**. Their reductions cannot be summed and must not be described as SHAP values or predictive feature importance.
- The fact that `business_type` is the largest single pure-premium disagreement sensitivity is consistent with earlier portfolio-mix observations but does **not** establish that mix drift caused predictive deterioration or performance differences.
- v0.47 deliberately retains the frozen Tweedie GLM convergence warning rather than changing `max_iter` after observing the diagnostic. The analysis does not create a new promotion gate.
"""


def migrate(text: str) -> str:
    if "| v0.47 disagreement diagnostic design |" not in text:
        marker = "\n## Interpretation rules\n"
        if marker not in text:
            raise RuntimeError("EVIDENCE_REGISTRY.md missing Interpretation rules marker")
        text = text.replace(marker, "\n" + ROWS + marker, 1)
    if "- v0.47 is a **post-hoc score-sensitivity diagnostic**" not in text:
        marker = "\n- Synthetic quote-conversion / proposition experiments are not reported as observed commercial impact."
        if marker not in text:
            raise RuntimeError("EVIDENCE_REGISTRY.md missing interpretation insertion marker")
        text = text.replace(marker, "\n" + BULLETS.rstrip() + marker, 1)
    if "tests/test_disagreement_attribution_v47.py" not in text:
        marker = "`tests/test_evidence_push_static_v31.py` also exercises"
        if marker not in text:
            raise RuntimeError("EVIDENCE_REGISTRY.md missing automated-protection marker")
        text = text.replace(
            marker,
            "`tests/test_disagreement_attribution_v47.py` protects the label-free, post-hoc and non-causal v0.47 diagnostic boundary. " + marker,
            1,
        )
    return text


def main() -> None:
    original = PATH.read_text(encoding="utf-8")
    updated = migrate(original)
    PATH.write_text(updated, encoding="utf-8")
    if migrate(updated) != updated:
        raise RuntimeError("v0.47 registry migration is not idempotent")
    print("V47_EVIDENCE_REGISTRY_MIGRATION_PASS")


if __name__ == "__main__":
    main()
