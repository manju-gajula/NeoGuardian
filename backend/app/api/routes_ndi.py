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
    return loader.get_cached_alerts()


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
