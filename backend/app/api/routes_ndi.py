"""
NDI Fusion, Clinical Alerts & System Health API Router
Computes composite Neonatal Decompensation Index, prioritizes multi-condition
alerts, and provides health status checks.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas import NDIResponse, AlertsResponse, AlertItem, HealthResponse
from app.data_loader import DataLoader
from app.ml.sepsis_model import SepsisModelManager
from app.ml.ndi_engine import compute_fused_ndi, evaluate_patient_telemetry

router = APIRouter(prefix="/api", tags=["NDI, Alerts & System Health"])


@router.get("/ndi/{patient_id}", response_model=NDIResponse)
def get_patient_ndi(patient_id: str):
    loader = DataLoader.get_instance()
    p = loader.get_patient(patient_id)
    if not p:
        raise HTTPException(
            status_code=404,
            detail=f"Patient '{patient_id}' not found. Valid IDs include 'infant1' to 'infant10' or numerical patient IDs."
        )

    eval_res = evaluate_patient_telemetry(p, include_shap=False)

    return NDIResponse(
        patient_id=eval_res["id"],
        **eval_res["ndi_result"]
    )


@router.get("/alerts", response_model=AlertsResponse)
def get_active_alerts():
    loader = DataLoader.get_instance()
    patients = loader.list_patients()
    alerts = []

    for p in patients:
        eval_res = evaluate_patient_telemetry(p, include_shap=False)
        pid = eval_res["id"]
        display_name = eval_res["display_id"]
        ndi_result = eval_res["ndi_result"]
        score = ndi_result["ndi_score"]
        band = ndi_result["ndi_band"]

        apnea_rate = eval_res["apnea_rate"]
        apnea_dur = eval_res["apnea_max"]
        lowest_hr = eval_res["min_hr"]
        brady_rate = eval_res["brady_rate"]
        sepsis_prob = eval_res["sepsis_prob"]
        temp = eval_res["temp_celsius"]
        cvl = eval_res["central_line"]
        intubated = eval_res["intubated"]

        # Only register elevated or critical patients
        if band in ("RED", "YELLOW"):
            # Determine which condition(s) triggered the alert
            triggers = []
            if apnea_rate >= 2.5 or apnea_dur >= 30.0:
                triggers.append("APNEA")
            if lowest_hr < 90.0 or brady_rate >= 1.5:
                triggers.append("BRADYCARDIA")
            if sepsis_prob >= 0.20 or temp < 36.5 or temp >= 38.0:
                triggers.append("SEPSIS")

            if len(triggers) >= 2:
                source_condition = "COMBINED"
                headline = f"Multimodal Cardiorespiratory & Septic Decompensation ({' + '.join(triggers)})"
            elif len(triggers) == 1:
                source_condition = triggers[0]
                headline = f"Isolated {source_condition.title()} Instability Alert"
            else:
                source_condition = "COMBINED"
                headline = "Elevated Neonatal Decompensation Risk"

            explanation = (
                f"NDI {score:.0f}/100. Key vitals: Temp {temp:.1f}°C, lowest HR {lowest_hr:.0f} BPM, "
                f"Apnea rate {apnea_rate:.1f}/hr. CVL: {'Yes' if cvl else 'No'}, Intubated: {'Yes' if intubated else 'No'}."
            )

            alerts.append(AlertItem(
                id=f"ALT-{len(alerts)+1:03d}",
                patient_id=pid,
                patient_display_name=display_name,
                severity=band,
                source_condition=source_condition,
                contributing_conditions=triggers,
                headline=headline,
                explanation=explanation,
                ndi_score=score,
                timestamp=datetime.now().strftime("%H:%M:%S")
            ))

    # Sort alerts: RED first, then descending NDI score
    alerts.sort(key=lambda a: (0 if a.severity == "RED" else 1, -a.ndi_score))

    red_count = sum(1 for a in alerts if a.severity == "RED")
    yellow_count = sum(1 for a in alerts if a.severity == "YELLOW")

    return AlertsResponse(
        total_alerts=len(alerts),
        critical_red_count=red_count,
        elevated_yellow_count=yellow_count,
        alerts=alerts
    )


@router.get("/health", response_model=HealthResponse)
def get_system_health():
    loader = DataLoader.get_instance()
    sepsis_mgr = SepsisModelManager.get_instance()

    models_ready = (sepsis_mgr.sepsis_model is not None and sepsis_mgr.mortality_model is not None)
    cohort_ready = (loader.df_sepsis is not None and not loader.df_sepsis.empty)

    return HealthResponse(
        status="HEALTHY",
        backend_version="1.0.0",
        models_loaded=models_ready,
        sepsis_cohort_loaded=cohort_ready,
        waveform_records_count=len(loader.waveform_records)
    )
