from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deployment.provenance import canonical_json_bytes, verify_bundle_lock


REGISTRY_VERSION = "0.28"


def _event_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class ReleaseRef:
    release_id: str
    bundle_path: str
    lock_digest_sha256: str
    governance_status: str
    model_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "bundle_path": self.bundle_path,
            "lock_digest_sha256": self.lock_digest_sha256,
            "governance_status": self.governance_status,
            "model_version": self.model_version,
        }


class ShadowReleaseRegistry:
    """Auditable shadow-release registry. It never retrains models or changes pricing."""

    def __init__(self) -> None:
        self.releases: dict[str, ReleaseRef] = {}
        self.active_release_id: str | None = None
        self.last_known_good_release_id: str | None = None
        self.review_required_release_ids: set[str] = set()
        self.events: list[dict[str, Any]] = []

    def _append_event(self, event_type: str, **details: Any) -> dict[str, Any]:
        previous = self.events[-1]["event_sha256"] if self.events else None
        payload = {
            "registry_version": REGISTRY_VERSION,
            "sequence": len(self.events) + 1,
            "event_type": event_type,
            "previous_event_sha256": previous,
            "details": details,
        }
        event_sha = _event_digest(payload)
        event = {**payload, "event_sha256": event_sha}
        self.events.append(event)
        return event

    def register_release(self, release_id: str, bundle_path: str | Path) -> ReleaseRef:
        if release_id in self.releases:
            raise RuntimeError(f"Release already registered: {release_id}")
        bundle_path = Path(bundle_path)
        integrity = verify_bundle_lock(bundle_path)
        manifest = json.loads((bundle_path / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("governance_status") != "HOLD_SHADOW_ONLY":
            raise RuntimeError("Only HOLD_SHADOW_ONLY bundles can enter the shadow release registry")
        release = ReleaseRef(
            release_id=release_id,
            bundle_path=str(bundle_path),
            lock_digest_sha256=integrity.lock_digest_sha256,
            governance_status=manifest["governance_status"],
            model_version=manifest["model_version"],
        )
        self.releases[release_id] = release
        self._append_event("REGISTER_RELEASE", release=release.as_dict())
        return release

    def activate_shadow(self, release_id: str, *, actor: str, reason: str) -> None:
        if release_id not in self.releases:
            raise KeyError(release_id)
        if not actor.strip() or not reason.strip():
            raise RuntimeError("Shadow activation requires actor and reason")
        previous = self.active_release_id
        self.active_release_id = release_id
        self._append_event(
            "ACTIVATE_SHADOW_RELEASE",
            actor=actor,
            reason=reason,
            previous_release_id=previous,
            active_release_id=release_id,
        )

    def mark_last_known_good(self, release_id: str, *, actor: str, evidence: str) -> None:
        if release_id not in self.releases:
            raise KeyError(release_id)
        if self.active_release_id != release_id:
            raise RuntimeError("Last-known-good release must be the currently active shadow release")
        if not actor.strip() or not evidence.strip():
            raise RuntimeError("LKG marking requires actor and evidence")
        self.last_known_good_release_id = release_id
        self._append_event(
            "MARK_LAST_KNOWN_GOOD",
            actor=actor,
            evidence=evidence,
            release_id=release_id,
        )

    def record_review_required(self, release_id: str, *, review_id: str, severity: str, reason: str) -> None:
        if release_id not in self.releases:
            raise KeyError(release_id)
        before = self.active_release_id
        self.review_required_release_ids.add(release_id)
        self._append_event(
            "REVIEW_REQUIRED",
            release_id=release_id,
            review_id=review_id,
            severity=severity,
            reason=reason,
            active_release_id_before=before,
            active_release_id_after=self.active_release_id,
            automatic_serving_change=False,
        )
        if self.active_release_id != before:
            raise AssertionError("Review event must not change the active shadow release")

    def recommend_rollback_to_lkg(self, *, reason: str) -> dict[str, Any]:
        if self.active_release_id is None or self.last_known_good_release_id is None:
            raise RuntimeError("Rollback recommendation requires active and last-known-good releases")
        recommendation = {
            "from_release_id": self.active_release_id,
            "to_release_id": self.last_known_good_release_id,
            "reason": reason,
            "automatic_execution": False,
            "requires_operator_authorisation": True,
        }
        self._append_event("ROLLBACK_RECOMMENDED", **recommendation)
        return recommendation

    def rollback_to_lkg(
        self,
        *,
        authorised: bool,
        actor: str | None,
        approval_reference: str | None,
        reason: str,
    ) -> None:
        if not authorised:
            self._append_event(
                "ROLLBACK_REJECTED_NO_AUTHORISATION",
                from_release_id=self.active_release_id,
                to_release_id=self.last_known_good_release_id,
                reason=reason,
            )
            raise PermissionError("Rollback requires explicit operator authorisation")
        if not actor or not actor.strip() or not approval_reference or not approval_reference.strip():
            raise PermissionError("Authorised rollback requires actor and approval reference")
        if self.last_known_good_release_id is None:
            raise RuntimeError("No last-known-good shadow release is registered")
        target = self.last_known_good_release_id
        if target not in self.releases:
            raise RuntimeError("Last-known-good release is no longer registered")
        # Re-verify the target immediately before changing the active pointer.
        target_ref = self.releases[target]
        integrity = verify_bundle_lock(target_ref.bundle_path)
        if integrity.lock_digest_sha256 != target_ref.lock_digest_sha256:
            raise RuntimeError("Last-known-good bundle digest changed since registration")
        previous = self.active_release_id
        self.active_release_id = target
        self._append_event(
            "ROLLBACK_EXECUTED",
            actor=actor,
            approval_reference=approval_reference,
            reason=reason,
            from_release_id=previous,
            to_release_id=target,
            retraining_performed=False,
            pricing_change_performed=False,
        )

    def verify_event_chain(self) -> dict[str, Any]:
        previous: str | None = None
        for expected_sequence, event in enumerate(self.events, start=1):
            if event.get("sequence") != expected_sequence:
                raise RuntimeError("Release registry sequence mismatch")
            if event.get("previous_event_sha256") != previous:
                raise RuntimeError("Release registry previous-event hash mismatch")
            payload = {key: value for key, value in event.items() if key != "event_sha256"}
            observed = _event_digest(payload)
            if observed != event.get("event_sha256"):
                raise RuntimeError("Release registry event hash mismatch")
            previous = observed
        return {
            "status": "RELEASE_EVENT_HASH_CHAIN_VERIFIED",
            "event_count": len(self.events),
            "head_event_sha256": previous,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "registry_version": REGISTRY_VERSION,
            "active_release_id": self.active_release_id,
            "last_known_good_release_id": self.last_known_good_release_id,
            "review_required_release_ids": sorted(self.review_required_release_ids),
            "releases": {key: value.as_dict() for key, value in sorted(self.releases.items())},
            "events": list(self.events),
            "governance_boundary": (
                "Shadow release control only. Review events never change serving automatically; "
                "rollback requires explicit operator authorisation and does not retrain models or change pricing."
            ),
        }
