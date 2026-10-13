"""Independent numeric checks and security regressions for real PD calculations."""
import math

import pytest
from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail
from peritoneal_dialysis_adequacy_agent.clinical import pet_creatinine, weekly_ktv


@pytest.mark.parametrize("dialysate,category", [
    (4.9, "Low"),
    (5.0, "Low-average"),
    (6.49, "Low-average"),
    (6.5, "High-average"),
    (8.09, "High-average"),
    (8.1, "High"),
])
def test_historical_pet_bands(dialysate, category):
    result = pet_creatinine(dialysate, 10)
    assert result["historical_transport_category"] == category


def test_pet_ratio():
    assert pet_creatinine(6.8, 10)["dp_creatinine_4h"] == 0.68


@pytest.mark.parametrize("dialysate,plasma", [
    (-1, 10), (4, 0), (float("nan"), 10), (4, float("inf")), (11, 10)
])
def test_pet_invalid_inputs(dialysate, plasma):
    with pytest.raises(ValueError):
        pet_creatinine(dialysate, plasma)


def test_ktv_with_and_without_renal_component():
    inputs = dict(serum_urea=50, dialysate_urea=40, daily_drain_volume_l=10, urea_distribution_volume_l=40)
    result = weekly_ktv(**inputs)
    assert result["peritoneal_weekly_ktv"] == 1.4
    assert result["renal_weekly_ktv"] == 0
    assert result["total_weekly_ktv"] == 1.4
    result = weekly_ktv(**inputs, urine_urea=150, daily_urine_volume_l=0.5)
    assert result["renal_weekly_ktv"] == 0.2625
    assert result["total_weekly_ktv"] == 1.6625


@pytest.mark.parametrize("overrides", [
    {"serum_urea": 0},
    {"dialysate_urea": -1},
    {"daily_drain_volume_l": float("nan")},
    {"urea_distribution_volume_l": float("inf")},
    {"urine_urea": 10},
    {"daily_urine_volume_l": 0.5},
    {"urine_urea": -2, "daily_urine_volume_l": 0.5},
])
def test_ktv_invalid_inputs(overrides):
    data = dict(serum_urea=50, dialysate_urea=40, daily_drain_volume_l=10, urea_distribution_volume_l=40)
    data.update(overrides)
    with pytest.raises(ValueError):
        weekly_ktv(**data)


def test_ktv_rejects_overflow():
    with pytest.raises(ValueError):
        weekly_ktv(1, 1e308, 1e308, 1)


def test_audit_hmac_verification_detects_single_entry_tampering():
    trail = AuditTrail(secret_key="fixed-test-secret")
    trail.log("test", "reviewer", "CALCULATE", {"status": "OK"})
    assert trail.verify_integrity()
    entry = trail.get_trail()
    entry[0]["actor"] = "tampered copy"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "tampered live"
    assert not trail.verify_integrity()


def test_api_pet_and_ktv_and_validation():
    client = TestClient(app)
    response = client.post("/api/pet", json={"dialysate_creatinine_4h": 6.8, "plasma_creatinine": 10})
    assert response.status_code == 200
    assert response.json()["dp_creatinine_4h"] == 0.68
    response = client.post("/api/ktv", json={
        "serum_urea": 50, "dialysate_urea": 40, "daily_drain_volume_l": 10,
        "urea_distribution_volume_l": 40,
    })
    assert response.status_code == 200
    assert response.json()["total_weekly_ktv"] == 1.4
    assert client.post("/api/pet", json={"dialysate_creatinine_4h": 9, "plasma_creatinine": 0}).status_code == 422
    assert client.post("/api/ktv", json={
        "serum_urea": 50, "dialysate_urea": 40, "daily_drain_volume_l": 10,
        "urea_distribution_volume_l": 40, "urine_urea": 150
    }).status_code == 422
