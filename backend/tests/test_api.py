"""
Automated Test Suite for NeoGuardian API
Tests all three condition-specific diagnostic pipelines, ML inference with TreeSHAP,
fused NDI scoring, and HTTP 404 edge cases using FastAPI TestClient.
"""

import pytest
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "NeoGuardian" in data["system"]


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["models_loaded"] is True
    assert data["sepsis_cohort_loaded"] is True
    assert data["waveform_records_count"] >= 10


def test_patients_list():
    response = client.get("/api/patients")
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) > 0

    first = patients[0]
    # Check all 4 independent condition badges are present
    assert "apnea_badge" in first
    assert "bradycardia_badge" in first
    assert "sepsis_badge" in first
    assert "ndi_badge" in first
    assert first["apnea_badge"]["status"] in ("GREEN", "YELLOW", "RED")
    assert first["bradycardia_badge"]["status"] in ("GREEN", "YELLOW", "RED")
    assert first["sepsis_badge"]["status"] in ("GREEN", "YELLOW", "RED")
    assert first["ndi_badge"]["status"] in ("GREEN", "YELLOW", "RED")


def test_patient_detail_valid():
    response = client.get("/api/patients/infant1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "infant1"
    assert data["has_waveform"] is True
    assert "ndi_score" in data
    assert 0.0 <= data["ndi_score"] <= 100.0


def test_patient_detail_404():
    response = client.get("/api/patients/nonexistent_patient_999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_apnea_valid():
    response = client.get("/api/apnea/infant1?window_start_sec=13080&window_duration_sec=120")
    assert response.status_code == 200
    data = response.json()
    assert data["infant_id"] == "infant1"
    assert "respiration_waveform" in data
    assert len(data["respiration_waveform"]) > 0
    assert "events" in data
    assert data["status"] in ("GREEN", "YELLOW", "RED")
    assert data["events_per_hour"] >= 0.0


def test_apnea_404():
    response = client.get("/api/apnea/infant99")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_bradycardia_valid():
    response = client.get("/api/bradycardia/infant1?window_start_sec=13080&window_duration_sec=120")
    assert response.status_code == 200
    data = response.json()
    assert data["infant_id"] == "infant1"
    assert "heart_rate_trend" in data
    assert len(data["heart_rate_trend"]) > 0
    assert data["threshold_bpm"] == 100.0
    assert data["status"] in ("GREEN", "YELLOW", "RED")


def test_bradycardia_404():
    response = client.get("/api/bradycardia/infant99")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_predict_sepsis_risk():
    payload = {
        "gestational_age_at_birth_weeks": 26.0,
        "birth_weight_kg": 0.85,
        "sex": 1,
        "onset_age_in_days": 12.0,
        "onset_hour_of_day": 8,
        "temp_celsius": 36.2,  # Hypothermia
        "intubated_at_time_of_sepsis_evaluation": 1,
        "inotrope_at_time_of_sepsis_eval": 1,
        "central_venous_line": 1,
        "umbilical_arterial_line": 0,
        "ecmo": 0,
        "comorbidity_necrotizing_enterocolitis": 1,
        "comorbidity_chronic_lung_disease": 0,
        "comorbidity_cardiac": 0,
        "comorbidity_surgical": 0,
        "comorbidity_ivh_or_shunt": 0
    }
    response = client.post("/api/predict/sepsis-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["sepsis_probability"] <= 1.0
    assert data["status"] in ("GREEN", "YELLOW", "RED")
    assert "top_contributing_features" in data
    # Verify TreeSHAP attributions
    assert len(data["top_contributing_features"]) > 0
    first_contrib = data["top_contributing_features"][0]
    assert "feature" in first_contrib
    assert "impact" in first_contrib
    assert first_contrib["direction"] in ("INCREASES_RISK", "DECREASES_RISK")


def test_predict_mortality_risk():
    payload = {
        "gestational_age_at_birth_weeks": 24.0,
        "birth_weight_kg": 0.65,
        "sex": 0,
        "onset_age_in_days": 5.0,
        "temp_celsius": 35.8,
        "intubated_at_time_of_sepsis_evaluation": 1,
        "inotrope_at_time_of_sepsis_eval": 1,
        "central_venous_line": 1
    }
    response = client.post("/api/predict/mortality-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["mortality_probability"] <= 1.0
    assert data["status"] in ("GREEN", "YELLOW", "RED")


def test_ndi_endpoint_and_bounds():
    response = client.get("/api/ndi/infant1")
    assert response.status_code == 200
    data = response.json()
    # Check strict 0-100 clamping
    assert 0.0 <= data["ndi_score"] <= 100.0
    assert data["ndi_band"] in ("GREEN", "YELLOW", "RED")
    # Check separate sub-scores
    sub = data["sub_scores"]
    assert 0.0 <= sub["apnea_score"] <= 100.0
    assert 0.0 <= sub["bradycardia_score"] <= 100.0
    assert 0.0 <= sub["sepsis_score"] <= 100.0
    assert 0.0 <= sub["prematurity_vulnerability_score"] <= 100.0
    assert "primary_driver" in data


def test_alerts_endpoint():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "total_alerts" in data
    assert "alerts" in data
    if data["total_alerts"] > 0:
        first_alert = data["alerts"][0]
        assert first_alert["severity"] in ("RED", "YELLOW")
        assert first_alert["source_condition"] in ("APNEA", "BRADYCARDIA", "SEPSIS", "COMBINED")
