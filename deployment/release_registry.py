from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REGISTRY_VERSION = "0.28"
SHADOW_GOVERNANCE_STATUS = "HOLD_SHADOW_ONLY"
VERIFIED_INTEGRITY_STATUS = "CONTENT_ADDRESSED_BUNDLE_VERIFIED"


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


@dataclass
class ShadowReleaseRegistry:
    releases: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_release_id: str | None = None
    last_known_good_release_id: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    version: str = REGISTRY_VERSION

    def _append_event(
        self,
        event_type: str,
        release_id: str | None,
        *,
        actor: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        previous = self.events[-1]["event_sha256"] if self.events else None
        event_payload = {
            "sequence": len(self.events) + 1,
            "event_type": event_type,
            "release_id": release_id,
            "actor": actor,
            "details": details or {},
            "previous_event_sha256": previous,
        }
        event = {**event_payload, "event_sha256": _sha256(event_payload)}
        self.events.append(event)
        return event

    def register_verified_release(
        self,
        *,
        release_id: str,
        bundle_ref: str,
        bundle_lock_digest_sha256: str,
        bundle_contract_version: str,
        model_version: str,
        governance_status: str,
        bundle_integrity_status: str,
        actor: str,
    ) -> None:
        if release_id in self.releases:
            raise RuntimeError(f"Release already registered: {release_id}")
        if governance_status != SHADOW_GOVERNANCE_STATUS:
            raise RuntimeError(
                f"Release governance must remain {SHADOW_GOVERNANCE_STATUS}: {governance_status}"
            )
        if bundle_integrity_status != VERIFIED_INTEGRITY_STATUS:
            raise RuntimeError(
                f"Release bundle is not integrity-verified: {bundle_integrity_status}"
            )
        if str(bundle_contract_version) != "0.27":
            raise RuntimeError(
                f"v0.28 accepts only sealed 0.27 bundles: {bundle_contract_version}"
            )
        if len(bundle_lock_digest_sha256) != 64:
            raise RuntimeError("Release lock digest must be a SHA-256 hex digest")

        self.releases[release_id] = {
            "release_id": release_id,
            "bundle_ref": bundle_ref,
            "bundle_lock_digest_sha256": bundle_lock_digest_sha256,
            "bundle_contract_version": str(bundle_contract_version),
            "model_version": model_version,
            "governance_status": governance_status,
            "bundle_integrity_status": bundle_integrity_status,
            "review_status": "NONE",
            "review_reason": None,
        }
        self._append_event(
            "REGISTER_VERIFIED_SHADOW_RELEASE",
            release_id,
            actor=actor,
            details={
                "bundle_lock_digest_sha256": bundle_lock_digest_sha256,
                "bundle_ref": bundle_ref,
            },
        )

    def activate_shadow_release(
        self, release_id: str, *, operator_authorised: bool, actor: str
    ) -> None:
        if not operator_authorised:
            raise RuntimeError("Shadow release activation requires explicit operator authorisation")
        release = self._require_release(release_id)
        self._require_release_safe_for_shadow(release)
        previous = self.active_release_id
        self.active_release_id = release_id
        self._append_event(
            "ACTIVATE_SHADOW_RELEASE",
            release_id,
            actor=actor,
            details={"previous_active_release_id": previous},
        )

    def mark_last_known_good(
        self,
        release_id: str,
        *,
        monitoring_status: str,
        operator_authorised: bool,
        actor: str,
    ) -> None:
        if not operator_authorised:
            raise RuntimeError("Last-known-good marking requires explicit operator authorisation")
        if self.active_release_id != release_id:
            raise RuntimeError("Only the currently active shadow release can become last-known-good")
        if monitoring_status != "GREEN":
            raise RuntimeError("Last-known-good marking requires GREEN monitoring evidence")
        release = self._require_release(release_id)
        self._require_release_safe_for_shadow(release)
        self.last_known_good_release_id = release_id
        self._append_event(
            "MARK_LAST_KNOWN_GOOD",
            release_id,
            actor=actor,
            details={"monitoring_status": monitoring_status},
        )

    def open_review(
        self,
        release_id: str,
        *,
        reason: str,
        severity: str,
        evidence_ref: str,
        actor: str,
    ) -> None:
        if self.active_release_id != release_id:
            raise RuntimeError("Review can only be opened against the active shadow release")
        release = self._require_release(release_id)
        release["review_status"] = "OPEN"
        release["review_reason"] = reason
        self._append_event(
            "OPEN_SHADOW_RELEASE_REVIEW",
            release_id,
            actor=actor,
            details={
                "reason": reason,
                "severity": severity,
                "evidence_ref": evidence_ref,
                "serving_change": "NONE",
            },
        )

    def select_rollback_target(self) -> str:
        active = self._require_release(self.active_release_id)
        if active["review_status"] != "OPEN":
            raise RuntimeError("Rollback target selection requires an open review on active release")
        target = self.last_known_good_release_id
        if target is None:
            raise RuntimeError("No last-known-good release is registered")
        if target == self.active_release_id:
            raise RuntimeError("Last-known-good is the reviewed active release; no prior target exists")
        target_release = self._require_release(target)
        self._require_release_safe_for_shadow(target_release)
        return target

    def activate_rollback(
        self,
        target_release_id: str,
        *,
        operator_authorised: bool,
        actor: str,
        reason: str,
    ) -> None:
        if not operator_authorised:
            raise RuntimeError("Rollback activation requires explicit operator authorisation")
        expected_target = self.select_rollback_target()
        if target_release_id != expected_target:
            raise RuntimeError(
                f"Rollback target must be last-known-good {expected_target}: {target_release_id}"
            )
        previous = self.active_release_id
        self.active_release_id = target_release_id
        self._append_event(
            "ACTIVATE_SHADOW_ROLLBACK",
            target_release_id,
            actor=actor,
            details={
                "previous_active_release_id": previous,
                "reason": reason,
                "model_retraining": False,
                "pricing_change": False,
            },
        )

    def verify_event_chain(self) -> dict[str, Any]:
        previous = None
        for index, event in enumerate(self.events, start=1):
            if event.get("sequence") != index:
                raise RuntimeError(f"Release event sequence mismatch at {index}")
            if event.get("previous_event_sha256") != previous:
                raise RuntimeError(f"Release event chain pointer mismatch at {index}")
            payload = {key: value for key, value in event.items() if key != "event_sha256"}
            expected = _sha256(payload)
            if event.get("event_sha256") != expected:
                raise RuntimeError(f"Release event hash mismatch at {index}")
            previous = expected
        return {
            "status": "RELEASE_EVENT_CHAIN_VERIFIED",
            "event_count": len(self.events),
            "head_event_sha256": previous,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "governance_boundary": SHADOW_GOVERNANCE_STATUS,
            "active_release_id": self.active_release_id,
            "last_known_good_release_id": self.last_known_good_release_id,
            "releases": self.releases,
            "events": self.events,
            "event_chain": self.verify_event_chain(),
            "automation_boundary": (
                "Review and rollback selection do not change serving automatically. "
                "Activation requires explicit operator_authorised=True; no customer pricing or "
                "model-family promotion is performed."
            ),
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.as_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "ShadowReleaseRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        registry = cls(
            releases=payload.get("releases", {}),
            active_release_id=payload.get("active_release_id"),
            last_known_good_release_id=payload.get("last_known_good_release_id"),
            events=payload.get("events", []),
            version=payload.get("version", REGISTRY_VERSION),
        )
        registry.verify_event_chain()
        return registry

    def _require_release(self, release_id: str | None) -> dict[str, Any]:
        if release_id is None or release_id not in self.releases:
            raise RuntimeError(f"Unknown shadow release: {release_id}")
        return self.releases[release_id]

    @staticmethod
    def _require_release_safe_for_shadow(release: dict[str, Any]) -> None:
        if release.get("governance_status") != SHADOW_GOVERNANCE_STATUS:
            raise RuntimeError("Release is not governed for shadow-only serving")
        if release.get("bundle_integrity_status") != VERIFIED_INTEGRITY_STATUS:
            raise RuntimeError("Release bundle integrity is not verified")
