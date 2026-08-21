from __future__ import annotations

import argparse
import json
from pathlib import Path

from deployment.provenance import verify_bundle_lock
from deployment.release_registry import ShadowReleaseRegistry


OUTDIR = Path("results_v28")


def load_release(bundle: Path) -> dict:
    integrity = verify_bundle_lock(bundle)
    lock = json.loads((bundle / "bundle.lock.json").read_text(encoding="utf-8"))
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    return {
        "bundle": bundle,
        "integrity": integrity,
        "lock": lock,
        "manifest": manifest,
    }


def locked_artifact_hashes(release: dict) -> dict[str, str]:
    return {
        item["path"]: item["sha256"]
        for item in release["lock"]["artifacts"]
    }


def register(registry: ShadowReleaseRegistry, release_id: str, release: dict) -> None:
    registry.register_verified_release(
        release_id=release_id,
        bundle_ref=str(release["bundle"]),
        bundle_lock_digest_sha256=release["lock"]["lock_digest_sha256"],
        bundle_contract_version=release["manifest"]["bundle_contract_version"],
        model_version=release["manifest"]["model_version"],
        governance_status=release["manifest"]["governance_status"],
        bundle_integrity_status=release["integrity"].status,
        actor="release-engineer",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-a", default="releases/v28-release-a")
    parser.add_argument("--release-b", default="releases/v28-release-b")
    parser.add_argument("--outdir", default=str(OUTDIR))
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    release_a = load_release(Path(args.release_a))
    release_b = load_release(Path(args.release_b))

    digest_a = release_a["lock"]["lock_digest_sha256"]
    digest_b = release_b["lock"]["lock_digest_sha256"]
    if digest_a == digest_b:
        raise AssertionError("Release A and B must have distinct sealed release identities")

    artifacts_a = locked_artifact_hashes(release_a)
    artifacts_b = locked_artifact_hashes(release_b)
    if artifacts_a != artifacts_b:
        raise AssertionError(
            "v0.28 release-control replay requires identical locked model/content artifacts; "
            "only release packaging provenance should differ"
        )

    registry = ShadowReleaseRegistry()
    register(registry, "shadow-release-a", release_a)
    register(registry, "shadow-release-b", release_b)

    registry.activate_shadow_release(
        "shadow-release-a", operator_authorised=True, actor="release-engineer"
    )
    registry.mark_last_known_good(
        "shadow-release-a",
        monitoring_status="GREEN",
        operator_authorised=True,
        actor="model-governance-reviewer",
    )
    registry.activate_shadow_release(
        "shadow-release-b", operator_authorised=True, actor="release-engineer"
    )

    active_before_review = registry.active_release_id
    registry.open_review(
        "shadow-release-b",
        reason="synthetic_release_control_test",
        severity="HIGH",
        evidence_ref="v0.28 synthetic review-required signal",
        actor="monitoring-review-controller",
    )
    active_after_review = registry.active_release_id
    if active_after_review != active_before_review:
        raise AssertionError("Opening review must not automatically change the active release")

    unauthorised_rejection = None
    try:
        registry.activate_rollback(
            "shadow-release-a",
            operator_authorised=False,
            actor="automated-controller",
            reason="synthetic_release_control_test",
        )
    except RuntimeError as exc:
        unauthorised_rejection = str(exc)
    if unauthorised_rejection is None:
        raise AssertionError("Unauthorised rollback unexpectedly changed release state")
    if registry.active_release_id != "shadow-release-b":
        raise AssertionError("Rejected rollback must leave candidate release active")

    selected_target = registry.select_rollback_target()
    if selected_target != "shadow-release-a":
        raise AssertionError(f"Unexpected rollback target: {selected_target}")

    registry.activate_rollback(
        selected_target,
        operator_authorised=True,
        actor="release-engineer",
        reason="operator-authorised synthetic rollback replay",
    )
    if registry.active_release_id != "shadow-release-a":
        raise AssertionError("Authorised rollback did not restore last-known-good release")

    chain = registry.verify_event_chain()
    registry_path = outdir / "release_registry.json"
    registry.save(registry_path)
    result = {
        "status": "V28_SHADOW_RELEASE_ROLLBACK_PASS",
        "governance_status": "HOLD_SHADOW_ONLY",
        "release_a": {
            "release_id": "shadow-release-a",
            "lock_digest_sha256": digest_a,
            "release_label": release_a["lock"]["build_provenance"].get("release_label"),
        },
        "release_b": {
            "release_id": "shadow-release-b",
            "lock_digest_sha256": digest_b,
            "release_label": release_b["lock"]["build_provenance"].get("release_label"),
        },
        "distinct_release_lock_digests": True,
        "identical_locked_artifact_hashes": True,
        "locked_artifact_count": len(artifacts_a),
        "active_before_review": active_before_review,
        "active_after_review": active_after_review,
        "review_caused_automatic_serving_change": False,
        "unauthorised_rollback_rejected": True,
        "unauthorised_rejection": unauthorised_rejection,
        "selected_rollback_target": selected_target,
        "operator_authorised_rollback": True,
        "final_active_release_id": registry.active_release_id,
        "last_known_good_release_id": registry.last_known_good_release_id,
        "model_retraining_during_rollback": False,
        "pricing_change_during_rollback": False,
        "event_chain": chain,
        "registry_path": str(registry_path),
        "interpretation_boundary": (
            "Synthetic release-control replay over two integrity-verified shadow packages with "
            "identical model artifacts. It demonstrates release selection and manual rollback "
            "controls, not a production incident or customer-pricing change."
        ),
    }
    (outdir / "release_rollback_summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
