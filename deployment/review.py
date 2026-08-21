from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

HIGH_ALERTS = {
    "error_rate",
    "unseen_category_rate",
    "frequency_disagreement",
    "pure_premium_disagreement",
}
MEDIUM_ALERTS = {"feature_drift", "p95_latency_ms"}


def aggregate_evidence(snapshot: dict[str, Any], label: str) -> dict[str, Any]:
    """Reduce a monitoring snapshot to aggregate, non-PII review evidence."""
    alerts = snapshot.get("alerts", {})
    active = sorted(name for name, value in alerts.items() if bool(value))
    feature_drift = snapshot.get("feature_drift", {})
    disagreement = snapshot.get("disagreement", {})
    return {
        "label": label,
        "service_version": snapshot.get("service_version"),
        "model_version": snapshot.get("model_version"),
        "governance_status": snapshot.get("governance_status"),
        "privacy_boundary": snapshot.get("privacy_boundary"),
        "request_count": int(snapshot.get("request_count", 0)),
        "records_scored": int(snapshot.get("records_scored", 0)),
        "error_rate": float(snapshot.get("error_rate", 0.0)),
        "unseen_category_rate": float(snapshot.get("unseen_category_rate", 0.0)),
        "p95_latency_ms": float(snapshot.get("latency_ms", {}).get("p95", 0.0)),
        "frequency_abs_log_ratio_p95": float(
            disagreement.get("frequency_abs_log_ratio_p95", 0.0)
        ),
        "pure_premium_abs_log_ratio_p95": float(
            disagreement.get("pure_premium_abs_log_ratio_p95", 0.0)
        ),
        "max_feature_psi": float(feature_drift.get("max_psi", 0.0)),
        "max_feature_psi_feature": feature_drift.get("max_psi_feature"),
        "feature_drift_alert_eligible": bool(feature_drift.get("alert_eligible", False)),
        "active_alerts": active,
    }


def evidence_digest(evidence: dict[str, Any]) -> str:
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def severity_for(active_alerts: list[str]) -> str:
    active = set(active_alerts)
    if active & HIGH_ALERTS:
        return "HIGH"
    if active & MEDIUM_ALERTS:
        return "MEDIUM"
    return "NONE"


def recommended_action(active_alerts: list[str]) -> str:
    active = set(active_alerts)
    if active & {"error_rate", "unseen_category_rate"} and active & {
        "frequency_disagreement",
        "pure_premium_disagreement",
    }:
        return "INVESTIGATE_SERVING_DATA_AND_MODEL"
    if active & {"error_rate", "unseen_category_rate"}:
        return "INVESTIGATE_SERVING_AND_INPUT_CONTRACT"
    if active & {"frequency_disagreement", "pure_premium_disagreement"}:
        return "REVIEW_MODEL_DISAGREEMENT"
    if "feature_drift" in active:
        return "REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION"
    if "p95_latency_ms" in active:
        return "REVIEW_SERVING_PERFORMANCE"
    return "CONTINUE_SHADOW"


@dataclass
class ReviewLifecycle:
    """Hysteresis around aggregate monitoring alerts.

    The controller recommends review actions only. It never changes model-family approval,
    pricing, or serving configuration automatically.
    """

    open_after_breaches: int = 2
    close_after_green: int = 2
    state: str = "HEALTHY"
    breach_streak: int = 0
    recovery_streak: int = 0
    sequence: int = 0
    review_id: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def observe(self, snapshot: dict[str, Any], label: str) -> dict[str, Any]:
        self.sequence += 1
        evidence = aggregate_evidence(snapshot, label)
        digest = evidence_digest(evidence)
        active = evidence["active_alerts"]
        has_breach = bool(active)
        review_before = self.review_id

        if has_breach:
            self.breach_streak += 1
            self.recovery_streak = 0
            if self.state in {"HEALTHY", "WATCH"}:
                if self.breach_streak >= self.open_after_breaches:
                    self.state = "REVIEW_REQUIRED"
                    if self.review_id is None:
                        self.review_id = f"review-{self.sequence:04d}-{digest[:8]}"
                else:
                    self.state = "WATCH"
            elif self.state == "RECOVERING":
                self.state = "REVIEW_REQUIRED"
        else:
            self.breach_streak = 0
            if self.state == "WATCH":
                self.state = "HEALTHY"
                self.recovery_streak = 0
                self.review_id = None
            elif self.state in {"REVIEW_REQUIRED", "RECOVERING"}:
                self.recovery_streak += 1
                if self.recovery_streak >= self.close_after_green:
                    self.state = "HEALTHY"
                    self.recovery_streak = 0
                    self.review_id = None
                else:
                    self.state = "RECOVERING"
            else:
                self.recovery_streak = 0

        if self.state == "HEALTHY":
            action = "CONTINUE_SHADOW"
        elif self.state == "WATCH":
            action = "OBSERVE_NEXT_WINDOW"
        elif self.state == "RECOVERING":
            action = "VERIFY_RECOVERY"
        else:
            action = recommended_action(active)

        event = {
            "sequence": self.sequence,
            "label": label,
            "state": self.state,
            "severity": severity_for(active),
            "recommended_action": action,
            "active_alerts": active,
            "breach_streak": self.breach_streak,
            "recovery_streak": self.recovery_streak,
            "review_id_before": review_before,
            "review_id_after": self.review_id,
            "evidence_sha256": digest,
            "evidence": evidence,
        }
        self.history.append(event)
        return event

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "review_id": self.review_id,
            "breach_streak": self.breach_streak,
            "recovery_streak": self.recovery_streak,
            "open_after_breaches": self.open_after_breaches,
            "close_after_green": self.close_after_green,
            "events": list(self.history),
            "automation_boundary": (
                "Recommendations only: no automatic pricing, model promotion, rollback, "
                "or serving change is performed by this controller."
            ),
        }
