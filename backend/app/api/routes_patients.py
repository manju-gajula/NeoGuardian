"""
Patient API Routes
Provides endpoints for retrieving patient summaries, individual clinical profiles,
and independent condition risk badges (Apnea, Bradycardia, Sepsis, NDI).
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.schemas import PatientSummary, PatientDetail, ConditionBadge
from app.data_loader import DataLoader
from app.ml.ndi_engine import evaluate_patient_telemetry

router = APIRouter(prefix="/api/patients", tags=["Patients"])


def build_patient_summary(p: dict, include_shap: bool = False) -> PatientSummary:
    eval_res = evaluate_patient_telemetry(p, include_shap=include_shap)

    return PatientSummary(
        id=eval_res["id"],
        patient_number=eval_res["patient_number"],
        infant_record_id=eval_res["infant_record_id"],
        has_waveform=eval_res["has_waveform"],
        gestational_age_weeks=eval_res["gestational_age_weeks"],
        birth_weight_kg=eval_res["birth_weight_kg"],
        sex=eval_res["sex"],
        current_age_days=eval_res["current_age_days"],
        temp_celsius=eval_res["temp_celsius"],
        intubated=eval_res["intubated"],
        central_line=eval_res["central_line"],
        apnea_badge=ConditionBadge(**eval_res["apnea_badge"]),
        bradycardia_badge=ConditionBadge(**eval_res["bradycardia_badge"]),
        sepsis_badge=ConditionBadge(**eval_res["sepsis_badge"]),
        ndi_badge=ConditionBadge(**eval_res["ndi_badge"])
    )


@router.get("", response_model=List[PatientSummary])
def list_patients():
    loader = DataLoader.get_instance()
    return loader.get_cached_patient_summaries()


@router.get("/{patient_id}", response_model=PatientDetail)
def get_patient(patient_id: str):
    loader = DataLoader.get_instance()
    p = loader.get_patient(patient_id)
    if not p:
        raise HTTPException(
            status_code=404,
            detail=f"Patient '{patient_id}' not found. Valid IDs include 'infant1' to 'infant10' or numerical patient IDs."
        )

    eval_res = evaluate_patient_telemetry(p, include_shap=True)
    clin = p.get("clinical_data", {})

    comorbidities = {
        "necrotizing_enterocolitis": bool(clin.get("comorbidity_necrotizing_enterocolitis", 0)),
        "chronic_lung_disease": bool(clin.get("comorbidity_chronic_lung_disease", 0)),
        "cardiac_defect": bool(clin.get("comorbidity_cardiac", 0)),
        "surgical_abdomen": bool(clin.get("comorbidity_surgical", 0)),
        "ivh_or_shunt": bool(clin.get("comorbidity_ivh_or_shunt", 0)),
    }

    if eval_res["has_waveform"]:
        summary_txt = f"Patient {eval_res['id'].upper()} (PICSDB Record: {eval_res['infant_record_id']}) is a {eval_res['gestational_age_weeks']:.0f}-week preterm infant with active continuous cardiorespiratory monitoring."
    else:
        summary_txt = f"Patient {eval_res['id']} is part of the NICU Sepsis Clinical Cohort admitted at {eval_res['gestational_age_weeks']:.0f} weeks gestation."

    base = PatientSummary(
        id=eval_res["id"],
        patient_number=eval_res["patient_number"],
        infant_record_id=eval_res["infant_record_id"],
        has_waveform=eval_res["has_waveform"],
        gestational_age_weeks=eval_res["gestational_age_weeks"],
        birth_weight_kg=eval_res["birth_weight_kg"],
        sex=eval_res["sex"],
        current_age_days=eval_res["current_age_days"],
        temp_celsius=eval_res["temp_celsius"],
        intubated=eval_res["intubated"],
        central_line=eval_res["central_line"],
        apnea_badge=ConditionBadge(**eval_res["apnea_badge"]),
        bradycardia_badge=ConditionBadge(**eval_res["bradycardia_badge"]),
        sepsis_badge=ConditionBadge(**eval_res["sepsis_badge"]),
        ndi_badge=ConditionBadge(**eval_res["ndi_badge"])
    )

    return PatientDetail(
        **base.model_dump(),
        period=clin.get("period"),
        time_to_antibiotics=clin.get("time_to_antibiotics"),
        blood_culture_positive=clin.get("blood_culture_positive"),
        sepsis_group=clin.get("sepsis_group"),
        comorbidities=comorbidities,
        ndi_score=eval_res["ndi_result"]["ndi_score"],
        ndi_band=eval_res["ndi_result"]["ndi_band"],
        clinical_summary=summary_txt
    )
