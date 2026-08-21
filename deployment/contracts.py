from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

NUMERIC_FEATURES = [
    "driver_age",
    "vehicle_age",
    "age_driving_licence",
    "vehicle_value",
    "seats",
    "power_to_weight_ratio",
]

CATEGORICAL_FEATURES = [
    "policy_type",
    "business_type",
    "payment_frequency",
    "bonus_score",
    "fuel_type",
    "vehicle_brand",
    "municipality_type",
    "circulation_area",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
SHADOW_GOVERNANCE_STATUS = "HOLD_SHADOW_ONLY"
MAX_BATCH_SIZE = 1000

FORBIDDEN_FIELDS = {
    "insured_id",
    "year",
    "policy_status",
    "total_premium",
    "total_claims",
    "total_incurred",
    "total_exposure",
}


def feature_contract_hash() -> str:
    payload = json.dumps(
        {
            "numeric": NUMERIC_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
            "forbidden": sorted(FORBIDDEN_FIELDS),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class PricingFeatures(BaseModel):
    """Leakage-controlled rating features accepted by the shadow service."""

    model_config = ConfigDict(extra="forbid")

    driver_age: float | None
    vehicle_age: float | None
    age_driving_licence: float | None
    vehicle_value: float | None
    seats: float | None
    power_to_weight_ratio: float | None
    policy_type: str | None
    business_type: str | None
    payment_frequency: str | None
    bonus_score: str | None
    fuel_type: str | None
    vehicle_brand: str | None
    municipality_type: str | None
    circulation_area: str | None

    def as_model_record(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in FEATURES}


class BatchScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policies: list[PricingFeatures] = Field(min_length=1, max_length=MAX_BATCH_SIZE)
