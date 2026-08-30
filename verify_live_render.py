"""
Verification of Public Live Render Deployment
Target: https://neoguardian.onrender.com
"""

import httpx
import json
import time

LIVE_URL = "https://neoguardian.onrender.com"

print("=" * 70)
print(f"  VERIFYING LIVE RENDER DEPLOYMENT: {LIVE_URL}")
print("=" * 70)

client = httpx.Client(base_url=LIVE_URL, timeout=60.0, follow_redirects=True)
results = {}

# 1. Health Check
print("\n[1/6] Probing /api/health...")
start_t = time.time()
try:
    r_health = client.get("/api/health")
    dur = time.time() - start_t
    print(f"  -> Status: {r_health.status_code} (responded in {dur:.2f}s)")
    print(f"  -> Body: {r_health.text}")
    assert r_health.status_code == 200, f"Expected 200, got {r_health.status_code}"
    health_json = r_health.json()
    assert health_json.get("status") == "HEALTHY", "Health status is not HEALTHY"
    results["health"] = f"PASSED (HTTP 200 in {dur:.2f}s, status: HEALTHY, models_loaded: {health_json.get('models_loaded')})"
except Exception as e:
    results["health"] = f"FAILED: {e}"

# 2. Root HTML & SPA Assets
print("\n[2/6] Probing / (Root React 18 SPA)...")
try:
    r_root = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    print(f"  -> Status: {r_root.status_code} (length: {len(r_root.text)} chars)")
    assert r_root.status_code == 200
    assert '<div id="root"></div>' in r_root.text
    assert "/assets/index-" in r_root.text
    results["root_spa"] = "PASSED (HTTP 200, React root div & dynamic bundle verified)"
except Exception as e:
    results["root_spa"] = f"FAILED: {e}"

# 3. Swagger OpenAPI Docs
print("\n[3/6] Probing /docs (OpenAPI Swagger UI)...")
try:
    r_docs = client.get("/docs")
    print(f"  -> Status: {r_docs.status_code}")
    assert r_docs.status_code == 200
    assert "Swagger UI" in r_docs.text or "swagger-ui" in r_docs.text.lower()
    results["swagger_docs"] = "PASSED (HTTP 200, Swagger UI loaded)"
except Exception as e:
    results["swagger_docs"] = f"FAILED: {e}"

# 4. Patients Registry List
print("\n[4/6] Probing /api/patients...")
try:
    r_patients = client.get("/api/patients")
    print(f"  -> Status: {r_patients.status_code}")
    assert r_patients.status_code == 200
    patients = r_patients.json()
    print(f"  -> Total patients returned: {len(patients)}")
    assert len(patients) >= 10
    p1 = patients[0]
    print(f"  -> First patient: {p1['id']} | NDI: {p1['ndi_badge']['label']} | Apnea: {p1['apnea_badge']['status']}")
    results["patients_api"] = f"PASSED (HTTP 200, {len(patients)} patients loaded with condition badges)"
except Exception as e:
    results["patients_api"] = f"FAILED: {e}"

# 5. Multimodal Condition Endpoints
print("\n[5/6] Probing Condition Telemetry (/api/apnea/infant1, /api/bradycardia/infant1)...")
try:
    r_apnea = client.get("/api/apnea/infant1")
    assert r_apnea.status_code == 200
    ap_data = r_apnea.json()
    print(f"  -> Apnea: Rate={ap_data['events_per_hour']}/hr, Points={len(ap_data['respiration_waveform'])}")

    r_brady = client.get("/api/bradycardia/infant1")
    assert r_brady.status_code == 200
    br_data = r_brady.json()
    print(f"  -> Bradycardia: Lowest HR={br_data['lowest_heart_rate_bpm']} BPM, Trend Points={len(br_data['heart_rate_trend'])}")

    results["telemetry_api"] = f"PASSED (Apnea={ap_data['events_per_hour']}/hr, Brady Lowest={br_data['lowest_heart_rate_bpm']} BPM)"
except Exception as e:
    results["telemetry_api"] = f"FAILED: {e}"

# 6. ML Inference & Fused NDI Endpoint
print("\n[6/6] Probing ML Sepsis & /api/ndi/infant1...")
try:
    r_ndi = client.get("/api/ndi/infant1")
    assert r_ndi.status_code == 200
    ndi_data = r_ndi.json()
    print(f"  -> Fused NDI: Score={ndi_data['ndi_score']:.1f}/100 [{ndi_data['ndi_band']}] | Primary Driver: {ndi_data['primary_driver']}")

    sepsis_req = {
        "gestational_age_at_birth_weeks": 26.0,
        "birth_weight_kg": 0.85,
        "sex": 1,
        "onset_age_in_days": 10.0,
        "onset_hour_of_day": 12,
        "temp_celsius": 38.5,
        "intubated_at_time_of_sepsis_evaluation": 1,
        "inotrope_at_time_of_sepsis_eval": 0,
        "central_venous_line": 1,
        "umbilical_arterial_line": 0,
        "ecmo": 0,
        "comorbidity_necrotizing_enterocolitis": 0,
        "comorbidity_chronic_lung_disease": 0,
        "comorbidity_cardiac": 0,
        "comorbidity_surgical": 0,
        "comorbidity_ivh_or_shunt": 0
    }
    r_pred = client.post("/api/predict/sepsis-risk", json=sepsis_req)
    assert r_pred.status_code == 200
    pred_data = r_pred.json()
    print(f"  -> Sepsis ML: Risk={pred_data['sepsis_risk_percentage']:.1f}% [{pred_data['status']}]")

    results["ml_and_ndi"] = f"PASSED (NDI={ndi_data['ndi_score']:.1f}, Sepsis Risk={pred_data['sepsis_risk_percentage']:.1f}%)"
except Exception as e:
    results["ml_and_ndi"] = f"FAILED: {e}"

print("\n" + "=" * 70)
print("  FINAL LIVE DEPLOYMENT VERIFICATION SUMMARY")
print("=" * 70)
for k, v in results.items():
    print(f"  * {k.upper():15}: {v}")
print("=" * 70)
