from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

import numpy as np

from deployment.drift import MISSING, UNSEEN, psi


DEFAULT_THRESHOLDS: dict[str, float] = {
    "error_rate": 0.02,
    "unseen_category_rate": 0.01,
    "p95_latency_ms": 200.0,
    "frequency_abs_log_ratio_p95": 0.75,
    "pure_premium_abs_log_ratio_p95": 1.00,
    "max_feature_psi": 0.25,
    "min_feature_drift_records": 500.0,
}


def _percentile(values: deque[float], q: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(np.asarray(values, dtype=float), q))


@dataclass
class ShadowTelemetry:
    window_size: int = 5000
    thresholds: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THRESHOLDS))
    monitoring_baseline: dict[str, Any] | None = None
    request_count: int = 0
    error_count: int = 0
    records_scored: int = 0
    unseen_warning_records: int = 0
    latency_ms: deque[float] = field(init=False)
    batch_sizes: deque[float] = field(init=False)
    frequency_abs_log_ratio: deque[float] = field(init=False)
    pure_premium_abs_log_ratio: deque[float] = field(init=False)
    numeric_bin_counts: dict[str, list[int]] = field(init=False)
    categorical_counts: dict[str, dict[str, int]] = field(init=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        self.latency_ms = deque(maxlen=self.window_size)
        self.batch_sizes = deque(maxlen=self.window_size)
        self.frequency_abs_log_ratio = deque(maxlen=self.window_size)
        self.pure_premium_abs_log_ratio = deque(maxlen=self.window_size)
        baseline = self.monitoring_baseline or {"numeric": {}, "categorical": {}}
        self.numeric_bin_counts = {
            field: [0] * len(spec["expected_proportions"])
            for field, spec in baseline.get("numeric", {}).items()
        }
        self.categorical_counts = {
            field: {key: 0 for key in spec["expected_proportions"]}
            for field, spec in baseline.get("categorical", {}).items()
        }

    def record_request(self, latency_ms: float, *, error: bool = False) -> None:
        with self._lock:
            self.request_count += 1
            self.error_count += int(error)
            self.latency_ms.append(float(latency_ms))

    def _record_features_unlocked(self, records: list[dict[str, Any]]) -> None:
        baseline = self.monitoring_baseline or {"numeric": {}, "categorical": {}}
        for record in records:
            for field, spec in baseline.get("numeric", {}).items():
                value = record.get(field)
                if value is None:
                    index = int(spec["missing_bucket"])
                else:
                    try:
                        numeric_value = float(value)
                    except (TypeError, ValueError):
                        index = int(spec["missing_bucket"])
                    else:
                        index = int(
                            np.searchsorted(spec["cut_points"], numeric_value, side="right")
                        )
                self.numeric_bin_counts[field][index] += 1

            for field, spec in baseline.get("categorical", {}).items():
                value = record.get(field)
                key = MISSING if value is None else str(value)
                if key not in spec["expected_proportions"]:
                    key = UNSEEN
                self.categorical_counts[field][key] = (
                    self.categorical_counts[field].get(key, 0) + 1
                )

    def record_scores(
        self,
        scores: list[dict[str, Any]],
        records: list[dict[str, Any]] | None = None,
    ) -> None:
        with self._lock:
            self.records_scored += len(scores)
            self.batch_sizes.append(float(len(scores)))
            if records is not None:
                if len(records) != len(scores):
                    raise ValueError("records and scores must have the same length")
                self._record_features_unlocked(records)
            for score in scores:
                if score.get("warnings"):
                    self.unseen_warning_records += 1
                self.frequency_abs_log_ratio.append(abs(float(score["frequency_log_ratio"])))
                self.pure_premium_abs_log_ratio.append(abs(float(score["pure_premium_log_ratio"])))

    def _feature_psi_unlocked(self) -> dict[str, float]:
        baseline = self.monitoring_baseline or {"numeric": {}, "categorical": {}}
        values: dict[str, float] = {}
        for field, spec in baseline.get("numeric", {}).items():
            counts = self.numeric_bin_counts[field]
            total = sum(counts)
            if total:
                actual = [count / total for count in counts]
                values[field] = psi(spec["expected_proportions"], actual)
        for field, spec in baseline.get("categorical", {}).items():
            expected_map = spec["expected_proportions"]
            counts = self.categorical_counts[field]
            total = sum(counts.values())
            if total:
                keys = list(expected_map)
                expected = [float(expected_map[key]) for key in keys]
                actual = [counts.get(key, 0) / total for key in keys]
                values[field] = psi(expected, actual)
        return values

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            request_count = self.request_count
            records_scored = self.records_scored
            feature_psi = self._feature_psi_unlocked()
            feature_alert_eligible = records_scored >= int(
                self.thresholds["min_feature_drift_records"]
            )
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
                "feature_drift": {
                    "psi_by_feature": feature_psi,
                    "max_psi": max(feature_psi.values()) if feature_psi else 0.0,
                    "max_psi_feature": (
                        max(feature_psi, key=feature_psi.get) if feature_psi else None
                    ),
                    "alert_eligible": feature_alert_eligible,
                    "minimum_records": int(self.thresholds["min_feature_drift_records"]),
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
            "feature_drift": bool(snapshot["feature_drift"]["alert_eligible"])
            and float(snapshot["feature_drift"]["max_psi"])
            > self.thresholds["max_feature_psi"],
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
            for counts in self.numeric_bin_counts.values():
                for idx in range(len(counts)):
                    counts[idx] = 0
            for counts in self.categorical_counts.values():
                for key in list(counts):
                    counts[key] = 0
