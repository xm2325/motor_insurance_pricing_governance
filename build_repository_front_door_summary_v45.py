import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_v45"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    readme_path = ROOT / "README.md"
    interview_path = ROOT / "INTERVIEW_EVIDENCE_PACK.md"
    registry_path = ROOT / "EVIDENCE_REGISTRY.md"

    readme = readme_path.read_text(encoding="utf-8")
    interview = interview_path.read_text(encoding="utf-8")
    registry = registry_path.read_text(encoding="utf-8")
    top = readme.split("\n---\n", 1)[0]

    checks = {
        "readme_mentions_external_gate_summary": "0/4 preregistered external target gates pass" in top,
        "readme_mentions_committee_gate": "EVIDENCE_GAP_HOLD" in top and "5/8" in top,
        "readme_links_v43_v44": "RESULTS_V43.md" in top and "RESULTS_V44.md" in top,
        "readme_marks_spanish_2024_consumed": "CONSUMED_RETROSPECTIVE_VALIDATION" in top,
        "interview_mentions_external_gate_summary": "0 of 4 preregistered Australian/Belgian target gates passed" in interview,
        "interview_mentions_committee_blockers": all(
            marker in interview
            for marker in [
                "G2_LOCKED_TEMPORAL_SUPPORT",
                "G3_PREREGISTERED_EXTERNAL_SUPPORT",
                "G4_FRESH_INDEPENDENT_EVIDENCE",
            ]
        ),
        "interview_preserves_no_uk_transfer_boundary": "not FIRST CENTRAL policy" in interview and "current UK motor market" in interview,
        "registry_contains_v43_v44": "| v0.43 model-family evidence synthesis |" in registry and "| v0.44 model-change committee machine gate |" in registry,
    }

    result = {
        "status": "V45_REPOSITORY_FRONT_DOOR_SYNC_PASS" if all(checks.values()) else "V45_REPOSITORY_FRONT_DOOR_SYNC_FAIL",
        "scope": "documentation_and_evidence_navigation_only",
        "model_fit_executed": False,
        "row_level_data_accessed": False,
        "historical_model_or_validation_decisions_changed": False,
        "source_of_truth": "EVIDENCE_REGISTRY.md plus persisted action_results",
        "current_story_through_version": "v0.44",
        "checks": checks,
        "artifacts": {
            "README.md": {"sha256": sha256(readme_path)},
            "INTERVIEW_EVIDENCE_PACK.md": {"sha256": sha256(interview_path)},
            "EVIDENCE_REGISTRY.md": {"sha256": sha256(registry_path)},
        },
        "headline_boundaries": {
            "benchmark_is_not_pricing_uplift": True,
            "consumed_validation_not_relabelled_fresh": True,
            "external_gate_count_scope_explicit": True,
            "committee_gate_not_human_approval": True,
            "first_central_or_current_uk_transfer_claimed": False,
            "commercial_uplift_claimed": False,
        },
    }

    if result["status"] != "V45_REPOSITORY_FRONT_DOOR_SYNC_PASS":
        failed = [k for k, v in checks.items() if not v]
        raise RuntimeError(f"Front-door audit failed: {failed}")

    OUT.mkdir(exist_ok=True)
    (OUT / "repository_front_door_summary_v45.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
