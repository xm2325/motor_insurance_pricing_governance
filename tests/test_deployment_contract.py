from __future__ import annotations

import unittest

from pydantic import ValidationError

from deployment.app import app
from deployment.contracts import (
    BatchScoreRequest,
    FEATURES,
    FORBIDDEN_FIELDS,
    MAX_BATCH_SIZE,
    PricingFeatures,
    SHADOW_GOVERNANCE_STATUS,
)
from run_spanish_oot_2024 import FEATURES as OOT_FEATURES


def valid_record() -> dict:
    return {
        "driver_age": 42.0,
        "vehicle_age": 5.0,
        "age_driving_licence": 24.0,
        "vehicle_value": 18000.0,
        "seats": 5.0,
        "power_to_weight_ratio": 0.08,
        "policy_type": "P",
        "business_type": "NB",
        "payment_frequency": "A",
        "bonus_score": "3",
        "fuel_type": "G",
        "vehicle_brand": "B1",
        "municipality_type": "U",
        "circulation_area": "A",
    }


class TestDeploymentContract(unittest.TestCase):
    def test_api_feature_contract_matches_locked_oot_features(self) -> None:
        self.assertEqual(FEATURES, OOT_FEATURES)
        self.assertEqual(list(PricingFeatures.model_fields), FEATURES)

    def test_current_outcomes_and_identifiers_are_rejected(self) -> None:
        for field in FORBIDDEN_FIELDS:
            record = valid_record()
            record[field] = 1
            with self.assertRaises(ValidationError, msg=field):
                PricingFeatures.model_validate(record)

    def test_batch_limit_is_explicit(self) -> None:
        policy = valid_record()
        request = BatchScoreRequest.model_validate({"policies": [policy] * MAX_BATCH_SIZE})
        self.assertEqual(len(request.policies), MAX_BATCH_SIZE)
        with self.assertRaises(ValidationError):
            BatchScoreRequest.model_validate({"policies": [policy] * (MAX_BATCH_SIZE + 1)})

    def test_service_is_shadow_only(self) -> None:
        self.assertEqual(SHADOW_GOVERNANCE_STATUS, "HOLD_SHADOW_ONLY")
        paths = {route.path for route in app.routes}
        self.assertTrue({"/health", "/model-info", "/score", "/batch-score"}.issubset(paths))
        self.assertNotIn("/quote", paths)
        self.assertNotIn("/price", paths)


if __name__ == "__main__":
    unittest.main()
