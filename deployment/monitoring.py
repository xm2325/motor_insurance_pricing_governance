from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

import numpy as np


DEFAULT_THRESHOLDS: dict[str, float] = {
    "error_rate": 0.02,
    "unseen_category_rate": 0.01,
    "p95_latency_ms": 200.0,
    "frequency_abs_log_ratio_p95": 0.75,
    "pure_premium_abs_log_ratio_p95": 1.00,
}


def _percentile(values: deque[float], q: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(np.asarray(values, dtype=float), q))


@dataclass
class ShadowTelemetry:
    window_size: int = 5000
    thresholds: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THRESHOLDS))
    request_count: int = 0
    error_count: int = 0
    records_scored: int = 0
    unseen_warning_records: int = 0
    latency_ms: deque[float] = field(init=False)
    batch_sizes: deque[float] = field(init=False)
    frequency_abs_log_ratio: deque[float] = field(init=False)
    pure_premium_abs_log_ratio: deque[float] = field(init=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        self.latency_ms = deque(maxlen=self.window_size)
        self.batch_sizes = deque(maxlen=self.window_size)
        self.frequency_abs_log_ratio = deque(maxlen=self.window_size)
        self.pure_premium_abs_log_ratio = deque(maxlen=self.window_size)

    def record_request(self, latency_ms: float, *, error: bool = False) -> None:
        with self._lock:
            self.request_count += 1
            self.error_count += int(error)
            self.latency_ms.append(float(latency_ms))

    def record_scores(self, scores: list[dict[str, Any]]) -> None:
        with self._lock:
            self.records_scored += len(scores)
            self.batch_sizes.append(float(len(scores)))
            for score in scores:
                if score.get("warnings"):
                    self.unseen_warning_records += 1
                self.frequency_abs_log_ratio.append(abs(float(score["frequency_log_ratio"])))
                self.pure_premium_abs_log_ratio.append(abs(float(score["pure_premium_log_ratio"])))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            request_count = self.request_count
            records_scored = self.records_scored
            snapshot = {
                "privacy_boundary": "aggregate_non_pii_only",
                "request_count": request_count,
                "error_count": self.error_count,
                "error_rate": self.error_count / request_count if request_count else 0.0,
                "records_scored": records_scored,
                "unseen_warning_records": self.unseen_warning_records,
                "unseen_category_rate": (
                    self.unseen_warning_records / records_scored if records_scored else 0.0
                ),
                "latency_ms": {
                    "median": _percentile(self.latency_ms, 50),
                    "p95": _percentile(self.latency_ms, 95),
                    "max": max(self.latency_ms) if self.latency_ms else 0.0,
                },
                "batch_size": {
                    "median": _percentile(self.batch_sizes, 50),
                    "p95": _percentile(self.batch_sizes, 95),
                    "max": max(self.batch_sizes) if self.batch_sizes else 0.0,
                },
                "disagreement": {
                    "frequency_abs_log_ratio_p50": _percentile(self.frequency_abs_log_ratio, 50),
                    "frequency_abs_log_ratio_p95": _percentile(self.frequency_abs_log_ratio, 95),
                    "pure_premium_abs_log_ratio_p50": _percentile(self.pure_premium_abs_log_ratio, 50),
                    "pure_premium_abs_log_ratio_p95": _percentile(self.pure_premium_abs_log_ratio, 95),
                },
                "thresholds": dict(self.thresholds),
            }
        snapshot["alerts"] = self.evaluate_alerts(snapshot)
        snapshot["alert_status"] = "RED" if any(snapshot["alerts"].values()) else "GREEN"
        return snapshot

    def evaluate_alerts(self, snapshot: dict[str, Any] | None = None) -> dict[str, bool]:
        if snapshot is None:
            snapshot = self.snapshot()
        return {
            "error_rate": float(snapshot["error_rate"]) > self.thresholds["error_rate"],
            "unseen_category_rate": float(snapshot["unseen_category_rate"])
            > self.thresholds["unseen_category_rate"],
            "p95_latency_ms": float(snapshot["latency_ms"]["p95"])
            > self.thresholds["p95_latency_ms"],
            "frequency_disagreement": float(
                snapshot["disagreement"]["frequency_abs_log_ratio_p95"]
            ) > self.thresholds["frequency_abs_log_ratio_p95"],
            "pure_premium_disagreement": float(
                snapshot["disagreement"]["pure_premium_abs_log_ratio_p95"]
            ) > self.thresholds["pure_premium_abs_log_ratio_p95"],
        }

    def reset(self) -> None:
        with self._lock:
            self.request_count = 0
            self.error_count = 0
            self.records_scored = 0
            self.unseen_warning_records = 0
            self.latency_ms.clear()
            self.batch_sizes.clear()
            self.frequency_abs_log_ratio.clear()
            self.pure_premium_abs_log_ratio.clear()
