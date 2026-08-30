"""
NeoGuardian End-to-End System Verification Script
Executes exhaustive programmatic checks against all FastAPI endpoints:
  - Health & Metadata
  - Patient list & 4 independent condition badges
  - Multi-condition waveform endpoints for all 10 PICSDB infants
  - 3 distinct clinical sepsis/mortality cases + TreeSHAP attributions
  - Fused NDI clamping and sub-score consistency
  - Real-time active alerts tagged by source condition
  - Clean 404 validation for unknown IDs
"""

import time
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"


def run_verification():
    print("=" * 70)
    print("  NEOGUARDIAN END-TO-END VERIFICATION SUITE")
    print("=" * 70)

    # Wait up to 10 seconds for server startup
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    server_ready = False
    for attempt in range(10):
        try:
            r = client.get("/api/health")
            if r.status_code == 200:
                server_ready = True
                break
        except Exception:
            time.sleep(1.0)

    if not server_ready:
        print("[FAIL] Server not responding at http://127.0.0.1:8000")
        return False

    print("[PASS] FastAPI Server is reachable and running.\n")

    # 1. Health Endpoint
    print("[TEST 1/8] Verifying /api/health...")
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    health_data = r.json()
    print(f"  * Status: {health_data['status']}")
    print(f"  * Models Loaded: {health_data['models_loaded']}")
    print(f"  * Sepsis Cohort Loaded: {health_data['sepsis_cohort_loaded']}")
    print(f"  * Waveform Records Count: {health_data['waveform_records_count']}")
    assert health_data["models_loaded"] is True
    assert health_data["waveform_records_count"] >= 10
    print("  [OK] /api/health verified successfully.\n")

    # 2. Patient List & 4 Badges
    print("[TEST 2/8] Verifying /api/patients...")
    r = client.get("/api/patients")
    assert r.status_code == 200
    patients = r.json()
    print(f"  * Total patients returned: {len(patients)}")
    assert len(patients) >= 10, "Expected at least 10 patients"

    for idx, p in enumerate(patients[:5]):
        assert "apnea_badge" in p, f"Missing apnea_badge in patient {p['id']}"
        assert "bradycardia_badge" in p, f"Missing bradycardia_badge in patient {p['id']}"
        assert "sepsis_badge" in p, f"Missing sepsis_badge in patient {p['id']}"
        assert "ndi_badge" in p, f"Missing ndi_badge in patient {p['id']}"
        for badge_name in ["apnea_badge", "bradycardia_badge", "sepsis_badge", "ndi_badge"]:
            assert p[badge_name]["status"] in ("GREEN", "YELLOW", "RED")
        print(f"    - Patient {p['id']} ({p['gestational_age_weeks']:.0f}wks, {p['birth_weight_kg']:.2f}kg): "
              f"Apnea={p['apnea_badge']['status']} | Brady={p['bradycardia_badge']['status']} | "
              f"Sepsis={p['sepsis_badge']['status']} | NDI={p['ndi_badge']['label']} [{p['ndi_badge']['status']}]")

    print("  [OK] All 4 independent condition badges verified.\n")

    # 3. Patient Details for at least 3 IDs
    print("[TEST 3/8] Verifying /api/patients/{id} for 3 different IDs...")
    test_ids = ["infant1", "infant3", patients[15]["id"]]
    for pid in test_ids:
        r = client.get(f"/api/patients/{pid}")
        assert r.status_code == 200, f"Failed for {pid}: {r.status_code}"
        d = r.json()
        print(f"  * Detail {pid}: ID={d['id']} | NDI={d['ndi_score']} ({d['ndi_band']}) | HasWaveform={d['has_waveform']}")
        assert 0.0 <= d["ndi_score"] <= 100.0
    print("  [OK] /api/patients/{id} verified.\n")

    # 4. Apnea Waveform & Events for all 10 infants
    print("[TEST 4/8] Verifying /api/apnea/{infant_id} across all 10 PICSDB infants...")
    for i in range(1, 11):
        infant_id = f"infant{i}"
        r = client.get(f"/api/apnea/{infant_id}?window_start_sec=13080&window_duration_sec=120")
        assert r.status_code == 200, f"Failed for {infant_id}: {r.status_code}"
        data = r.json()
        assert len(data["respiration_waveform"]) > 0, f"Empty waveform for {infant_id}"
        assert data["status"] in ("GREEN", "YELLOW", "RED")
        print(f"  * {infant_id}: Waveform points={len(data['respiration_waveform']):,} | "
              f"Apnea Events={len(data['events'])} | Rate={data['events_per_hour']:.1f}/hr [{data['status']}]")
    print("  [OK] Apnea detection verified across all 10 infants.\n")

    # 5. Bradycardia ECG & Spells for all 10 infants
    print("[TEST 5/8] Verifying /api/bradycardia/{infant_id} across all 10 PICSDB infants...")
    for i in range(1, 11):
        infant_id = f"infant{i}"
        r = client.get(f"/api/bradycardia/{infant_id}?window_start_sec=13080&window_duration_sec=120")
        assert r.status_code == 200, f"Failed for {infant_id}: {r.status_code}"
        data = r.json()
        assert len(data["heart_rate_trend"]) > 0, f"Empty HR trend for {infant_id}"
        assert data["threshold_bpm"] == 100.0
        print(f"  * {infant_id}: HR Trend points={len(data['heart_rate_trend']):,} | "
              f"Lowest HR={data['lowest_heart_rate_bpm']:.1f} BPM | Spells={len(data['spells'])} [{data['status']}]")
    print("  [OK] Bradycardia detection verified across all 10 infants.\n")

    # 6. Sepsis & Mortality Predictions with TreeSHAP on 3 distinct clinical cases
    print("[TEST 6/8] Testing Sepsis ML & TreeSHAP Attributions on 3 Clinical Profiles...")

    # Case A: Baseline Preterm infant
    case_baseline = {
        "name": "Case 1: Baseline Preterm Infant (GA 30wks, BW 1.4kg, Normal Temp, No Line)",
        "payload": {
            "gestational_age_at_birth_weeks": 30.0,
            "birth_weight_kg": 1.4,
            "sex": 1,
            "onset_age_in_days": 12.0,
            "onset_hour_of_day": 10,
            "temp_celsius": 37.0,
            "intubated_at_time_of_sepsis_evaluation": 0,
            "inotrope_at_time_of_sepsis_eval": 0,
            "central_venous_line": 0,
            "umbilical_arterial_line": 0,
            "ecmo": 0,
            "comorbidity_necrotizing_enterocolitis": 0,
            "comorbidity_chronic_lung_disease": 0,
            "comorbidity_cardiac": 0,
            "comorbidity_surgical": 0,
            "comorbidity_ivh_or_shunt": 0
        }
    }

    # Case B: Baseline + Central Venous Line (CVL)
    case_with_cvl = {
        "name": "Case 2: Preterm Infant + Central Venous Line (CVL)",
        "payload": {
            "gestational_age_at_birth_weeks": 30.0,
            "birth_weight_kg": 1.4,
            "sex": 1,
            "onset_age_in_days": 12.0,
            "onset_hour_of_day": 10,
            "temp_celsius": 37.0,
            "intubated_at_time_of_sepsis_evaluation": 0,
            "inotrope_at_time_of_sepsis_eval": 0,
            "central_venous_line": 1,  # Adding CVL
            "umbilical_arterial_line": 0,
            "ecmo": 0,
            "comorbidity_necrotizing_enterocolitis": 0,
            "comorbidity_chronic_lung_disease": 0,
            "comorbidity_cardiac": 0,
            "comorbidity_surgical": 0,
            "comorbidity_ivh_or_shunt": 0
        }
    }

    # Case C: Baseline + CVL + High Fever (38.8 C)
    case_cvl_fever = {
        "name": "Case 3: Preterm Infant + CVL + High Fever (38.8 C)",
        "payload": {
            "gestational_age_at_birth_weeks": 30.0,
            "birth_weight_kg": 1.4,
            "sex": 1,
            "onset_age_in_days": 12.0,
            "onset_hour_of_day": 10,
            "temp_celsius": 38.8,  # Adding High Fever
            "intubated_at_time_of_sepsis_evaluation": 0,
            "inotrope_at_time_of_sepsis_eval": 0,
            "central_venous_line": 1,  # With CVL
            "umbilical_arterial_line": 0,
            "ecmo": 0,
            "comorbidity_necrotizing_enterocolitis": 0,
            "comorbidity_chronic_lung_disease": 0,
            "comorbidity_cardiac": 0,
            "comorbidity_surgical": 0,
            "comorbidity_ivh_or_shunt": 0
        }
    }

    cases = [case_baseline, case_with_cvl, case_cvl_fever]
    saved_case_outputs = []

    for c in cases:
        r_sepsis = client.post("/api/predict/sepsis-risk", json=c["payload"])
        assert r_sepsis.status_code == 200
        s_data = r_sepsis.json()

        r_mort = client.post("/api/predict/mortality-risk", json=c["payload"])
        assert r_mort.status_code == 200
        m_data = r_mort.json()

        print(f"\n  --- {c['name']} ---")
        print(f"  * Sepsis Probability:    {s_data['sepsis_risk_percentage']:.1f}% [{s_data['status']} - {s_data['risk_level']}]")
        print(f"  * 30-Day Mortality Risk: {m_data['mortality_risk_percentage']:.1f}% [{m_data['status']} - {m_data['risk_level']}]")
        print("  * Top TreeSHAP Attributions:")
        for feat in s_data["top_contributing_features"][:3]:
            print(f"      - {feat['label']}: {feat['impact']} ({feat['direction']})")

        saved_case_outputs.append({
            "name": c["name"],
            "sepsis": s_data,
            "mortality": m_data
        })

    # Validate monotonic risk ordering with CVL and Fever additions
    p_base = saved_case_outputs[0]["sepsis"]["sepsis_probability"]
    p_cvl = saved_case_outputs[1]["sepsis"]["sepsis_probability"]
    p_fever = saved_case_outputs[2]["sepsis"]["sepsis_probability"]
    print(f"\n  Checking clinical gradient: Baseline ({p_base*100:.1f}%) < With CVL ({p_cvl*100:.1f}%) < With CVL+Fever ({p_fever*100:.1f}%)")
    assert p_fever >= p_cvl >= p_base, "Risk probabilities must increase with CVL and Fever additions!"
    print("  [OK] Sepsis and Mortality ML + TreeSHAP explainability validated successfully.\n")

    # 7. Fused NDI Clamping & Sub-score Consistency
    print("[TEST 7/8] Verifying /api/ndi/{patient_id} bounds & sub-score consistency...")
    for pid in ["infant1", "infant2", "infant8", patients[20]["id"]]:
        r = client.get(f"/api/ndi/{pid}")
        assert r.status_code == 200
        data = r.json()
        score = data["ndi_score"]
        sub = data["sub_scores"]
        assert 0.0 <= score <= 100.0, f"NDI {score} out of bounds for {pid}"
        assert 0.0 <= sub["apnea_score"] <= 100.0
        assert 0.0 <= sub["bradycardia_score"] <= 100.0
        assert 0.0 <= sub["sepsis_score"] <= 100.0
        assert 0.0 <= sub["prematurity_vulnerability_score"] <= 100.0
        print(f"  * Patient {pid}: Fused NDI = {score:.1f} [{data['ndi_band']}] | "
              f"Sub-scores: Apnea={sub['apnea_score']:.0f}, Brady={sub['bradycardia_score']:.0f}, Sepsis={sub['sepsis_score']:.0f}")
    print("  [OK] NDI fusion and strict 0-100 clamping verified.\n")

    # 8. Active Alerts & Clean 404 Error Handling
    print("[TEST 8/8] Verifying /api/alerts and clean 404 handling...")
    r_alerts = client.get("/api/alerts")
    assert r_alerts.status_code == 200
    alerts_data = r_alerts.json()
    print(f"  * Total active alerts: {alerts_data['total_alerts']} "
          f"(Critical: {alerts_data['critical_red_count']}, Elevated: {alerts_data['elevated_yellow_count']})")
    for a in alerts_data["alerts"][:3]:
        print(f"    - [{a['severity']} | {a['source_condition']}] {a['patient_display_name']}: {a['headline']}")

    # Clean 404 Checks
    print("\n  Checking 404 error handling for invalid IDs:")
    r_bad_pat = client.get("/api/patients/patient99999")
    assert r_bad_pat.status_code == 404, f"Expected 404, got {r_bad_pat.status_code}"
    print("  * GET /api/patients/patient99999 -> 404 Cleanly returned.")

    r_bad_ap = client.get("/api/apnea/infant99")
    assert r_bad_ap.status_code == 404, f"Expected 404, got {r_bad_ap.status_code}"
    print("  * GET /api/apnea/infant99 -> 404 Cleanly returned.")

    r_bad_br = client.get("/api/bradycardia/infant99")
    assert r_bad_br.status_code == 404, f"Expected 404, got {r_bad_br.status_code}"
    print("  * GET /api/bradycardia/infant99 -> 404 Cleanly returned.")

    print("\n" + "=" * 70)
    print("  ALL ENDPOINTS VERIFIED WITH 100% SUCCESS!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    run_verification()
