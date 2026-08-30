# NeoGuardian: AI-Based Intelligent Neonatal Health Monitoring & Early Warning System

## Quickstart: One-Click Run

> ### **Double-click `run_neoguardian.bat` to start NeoGuardian.**
>
> That's it! Double-clicking `run_neoguardian.bat` automatically:
> 1. Activates the Python virtual environment (`.venv`)
> 2. Starts the FastAPI server serving both the live API and the full React 18 dashboard on `http://127.0.0.1:8000/`
> 3. Polls the `/api/health` endpoint until models and cohorts are verified ready
> 4. Automatically opens your default web browser to **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**
> 5. Keeps the console window open to stream live server telemetry. To stop the application, simply close the window.

---

## System Overview & Architecture

**NeoGuardian** is an intelligent neonatal monitoring and early-warning system engineered for the Neonatal Intensive Care Unit (NICU). It continuously monitors and predicts **THREE distinct neonatal conditions**, each surfaced explicitly to clinicians, and fuses them into a composite **Neonatal Decompensation Index (NDI)**:

```
                    ┌──────────────────────────────────────────────────────────┐
                    │               Raw Continuous Inputs                      │
                    │   Respiration (500 Hz)   |   ECG / R-Peaks (250 Hz)      │
                    │   PhysioNet PICSDB Waveform Stream (10 Preterm Infants)  │
                    └──────────────┬────────────────────────────┬──────────────┘
                                   │                            │
                                   ▼                            ▼
                    ┌─────────────────────────┐  ┌─────────────────────────┐
                    │  CONDITION 1: APNEA     │  │ CONDITION 2: BRADYCARDIA│
                    ├─────────────────────────┤  ├─────────────────────────┤
                    │ • 0.08–1.2 Hz Bandpass  │  │ • Instantaneous HR:     │
                    │ • Hilbert Envelope      │  │     HR = 60 / RR        │
                    │ • Pauses ≥ 15s / 20s    │  │ • Spells < 100 BPM      │
                    │ • Output: Events/Hour   │  │ • Output: Spells/Hour,  │
                    │   & Duration Severity   │  │   Lowest Recorded BPM   │
                    └──────────────┬──────────┘  └──────────────┬──────────┘
                                   │                            │
                                   │   ┌────────────────────┐   │
                                   │   │  CLINICAL COHORT   │   │
                                   │   │ 1,946 NICU Sepsis  │   │
                                   │   │ Evaluation Records │   │
                                   │   └─────────┬──────────┘   │
                                   │             │              │
                                   │             ▼              │
                                   │  ┌──────────────────────┐  │
                                   │  │ CONDITION 3: SEPSIS  │  │
                                   │  ├──────────────────────┤  │
                                   │  │ • Random Forest ML   │  │
                                   │  │ • Culture Confirmed  │  │
                                   │  │ • 30-Day Mortality   │  │
                                   │  │ • TreeSHAP Local     │  │
                                   │  │   Feature Attribution│  │
                                   │  └──────────┬───────────┘  │
                                   │             │              │
                                   └─────────────┼──────────────┘
                                                 ▼
                    ┌──────────────────────────────────────────────────────────┐
                    │        FUSED NEONATAL DECOMPENSATION INDEX (NDI)         │
                    ├──────────────────────────────────────────────────────────┤
                    │   NDI = 0.30·Apnea + 0.30·Brady + 0.25·Sepsis + 0.15·Vuln│
                    │                                                          │
                    │   • 0–39   GREEN   (Stable Neonate)                      │
                    │   • 40–64  YELLOW  (Elevated Risk / Intensify Alarms)    │
                    │   • 65–100 RED     (Critical Alert / Septic Workup Stat) │
                    └──────────────────────────────────────────────────────────┘
```

### The Three Independent Conditions:
1. **🫁 Apnea of Prematurity (AoP)**: Detected from the 500 Hz abdominal respiration signal using 3rd-order Butterworth filtering (0.08–1.2 Hz) and Hilbert amplitude suppression ($< 0.55$). Classifies episodes into Mild (15–20s), Moderate (20–30s), and Severe (>30s) pauses.
2. **❤️ Neonatal Bradycardia**: Derived from continuous 250 Hz ECG QRS R-peaks (`.qrsc`). Calculates RR intervals, instantaneous heart rate ($60/\text{RR}$), and detects clinical decelerations below the 100 BPM pediatric threshold.
3. **🦠 Late-Onset Neonatal Sepsis**: Predicted using Random Forest machine learning models trained on 1,946 clinical sepsis evaluation episodes. Provides mathematically exact **TreeSHAP feature attributions** ($\phi_i$) showing how temperature, gestational age, birth weight, lines, and ventilatory support shift risk away from the cohort median.
4. **⚡ Fused NDI (0–100)**: Combines all three condition sub-scores into a strictly bounded index ($\min(100.0, \max(0.0, \dots))$) with dedicated clinical triage actions.

---

## Academic Defense & Dataset Linkage Statement

> [!IMPORTANT]
> **Honest Population Linkage (Option B)**:
> - **PhysioNet PICSDB** contains 10 infants (`infant1` to `infant10`) with continuous physiological waveforms.
> - The **NICU Sepsis Cohort** contains 986 de-identified infants (1,946 clinical episodes) without raw waveforms.
> - **In NeoGuardian**: In the UI and API, the 10 waveform infants are designated as the **Multimodal Demonstration Cohort**, coupling PICSDB continuous signals with matched clinical evaluation parameters (clearly highlighted with the `[WAVEFORM STREAM]` badge). Clinicians can also browse the non-waveform Sepsis Clinical Cohort separately.

---

## Advanced / Manual Reference

### Running Automated Verification Tests

Verify all 13 condition-specific endpoints, TreeSHAP outputs, NDI bounds, and 404 error handlers:

```powershell
& ".\.venv\Scripts\Activate.ps1"
pytest backend/tests/test_api.py -v
```

### Manual Backend Launch (CLI)

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Clinical Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Rebuilding the React Frontend (Optional)

If modifying TypeScript files in `frontend/src/`:

```powershell
cd frontend
npm run build
Copy-Item -Path 'dist\*' -Destination '..\backend\app\static' -Recurse -Force
```

### API Reference Table

| Method | Endpoint | Description | Sample Output |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System health & loaded model status | `{"status": "HEALTHY", "models_loaded": true}` |
| `GET` | `/api/patients` | Patients list with 4 independent condition badges | `[{"id": "infant1", "apnea_badge": {"status": "RED", ...}, ...}]` |
| `GET` | `/api/patients/{id}` | Full patient profile & clinical summary | Patient details, comorbidities, NDI |
| `GET` | `/api/apnea/{infant_id}` | Respiration waveform coordinates & apnea pause events | Waveform points + detected events list |
| `GET` | `/api/bradycardia/{infant_id}` | Heart rate trend & bradycardia deceleration spells | Downsampled HR curve + spells under 100 BPM |
| `POST` | `/api/predict/sepsis-risk` | Predicts sepsis probability + TreeSHAP attributions | `{"sepsis_risk_percentage": 31.4, "status": "RED", ...}` |
| `POST` | `/api/predict/mortality-risk` | Predicts 30-day mortality risk + TreeSHAP attributions | `{"mortality_risk_percentage": 8.2, "status": "YELLOW", ...}` |
| `GET` | `/api/ndi/{patient_id}` | Fused NDI score (0–100) + separate sub-scores | `{"ndi_score": 78.5, "ndi_band": "RED", ...}` |
| `GET` | `/api/alerts` | Prioritized active alerts tagged by source condition | List of active RED/YELLOW patient alarms |

---

## Docker Deployment (Optional)

```powershell
docker-compose up --build
```
- Web Application: `http://localhost:8000/`
- OpenAPI Docs: `http://localhost:8000/docs`
