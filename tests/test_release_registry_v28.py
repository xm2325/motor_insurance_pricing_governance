from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from deployment.release_registry import ShadowReleaseRegistry


DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def register(registry: ShadowReleaseRegistry, release_id: str, digest: str) -> None:
    registry.register_verified_release(
        release_id=release_id,
        bundle_ref=f"releases/{release_id}",
        bundle_lock_digest_sha256=digest,
        bundle_contract_version="0.27",
        model_version="test-model",
        governance_status="HOLD_SHADOW_ONLY",
        bundle_integrity_status="CONTENT_ADDRESSED_BUNDLE_VERIFIED",
        actor="test",
    )


class TestReleaseRegistryV28(unittest.TestCase):
    def test_rejects_non_shadow_governance(self) -> None:
        registry = ShadowReleaseRegistry()
        with self.assertRaisesRegex(RuntimeError, "governance"):
            registry.register_verified_release(
                release_id="bad",
                bundle_ref="bad",
                bundle_lock_digest_sha256=DIGEST_A,
                bundle_contract_version="0.27",
                model_version="test",
                governance_status="PROMOTE",
                bundle_integrity_status="CONTENT_ADDRESSED_BUNDLE_VERIFIED",
                actor="test",
            )

    def test_rejects_unverified_bundle(self) -> None:
        registry = ShadowReleaseRegistry()
        with self.assertRaisesRegex(RuntimeError, "not integrity-verified"):
            registry.register_verified_release(
                release_id="bad",
                bundle_ref="bad",
                bundle_lock_digest_sha256=DIGEST_A,
                bundle_contract_version="0.27",
                model_version="test",
                governance_status="HOLD_SHADOW_ONLY",
                bundle_integrity_status="UNVERIFIED",
                actor="test",
            )

    def test_activation_requires_operator_authorisation(self) -> None:
        registry = ShadowReleaseRegistry()
        register(registry, "a", DIGEST_A)
        with self.assertRaisesRegex(RuntimeError, "operator authorisation"):
            registry.activate_shadow_release("a", operator_authorised=False, actor="automation")
        self.assertIsNone(registry.active_release_id)

    def test_last_known_good_requires_active_green_release(self) -> None:
        registry = ShadowReleaseRegistry()
        register(registry, "a", DIGEST_A)
        registry.activate_shadow_release("a", operator_authorised=True, actor="operator")
        with self.assertRaisesRegex(RuntimeError, "GREEN"):
            registry.mark_last_known_good(
                "a",
                monitoring_status="RED",
                operator_authorised=True,
                actor="reviewer",
            )
        registry.mark_last_known_good(
            "a",
            monitoring_status="GREEN",
            operator_authorised=True,
            actor="reviewer",
        )
        self.assertEqual(registry.last_known_good_release_id, "a")

    def test_review_does_not_auto_switch_and_rollback_requires_operator(self) -> None:
        registry = ShadowReleaseRegistry()
        register(registry, "a", DIGEST_A)
        register(registry, "b", DIGEST_B)
        registry.activate_shadow_release("a", operator_authorised=True, actor="operator")
        registry.mark_last_known_good(
            "a", monitoring_status="GREEN", operator_authorised=True, actor="reviewer"
        )
        registry.activate_shadow_release("b", operator_authorised=True, actor="operator")
        registry.open_review(
            "b",
            reason="synthetic",
            severity="HIGH",
            evidence_ref="test",
            actor="controller",
        )
        self.assertEqual(registry.active_release_id, "b")
        self.assertEqual(registry.select_rollback_target(), "a")
        with self.assertRaisesRegex(RuntimeError, "operator authorisation"):
            registry.activate_rollback(
                "a", operator_authorised=False, actor="automation", reason="synthetic"
            )
        self.assertEqual(registry.active_release_id, "b")
        registry.activate_rollback(
            "a", operator_authorised=True, actor="operator", reason="synthetic"
        )
        self.assertEqual(registry.active_release_id, "a")

    def test_event_chain_detects_tamper(self) -> None:
        registry = ShadowReleaseRegistry()
        register(registry, "a", DIGEST_A)
        registry.activate_shadow_release("a", operator_authorised=True, actor="operator")
        self.assertEqual(registry.verify_event_chain()["status"], "RELEASE_EVENT_CHAIN_VERIFIED")
        tampered = copy.deepcopy(registry)
        tampered.events[0]["actor"] = "tampered"
        with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            tampered.verify_event_chain()

    def test_registry_round_trip_preserves_verified_chain(self) -> None:
        registry = ShadowReleaseRegistry()
        register(registry, "a", DIGEST_A)
        registry.activate_shadow_release("a", operator_authorised=True, actor="operator")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            registry.save(path)
            loaded = ShadowReleaseRegistry.load(path)
            self.assertEqual(loaded.active_release_id, "a")
            self.assertEqual(loaded.verify_event_chain()["event_count"], 2)


if __name__ == "__main__":
    unittest.main()
