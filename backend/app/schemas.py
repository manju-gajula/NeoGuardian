"""
Pydantic Schemas for NeoGuardian API
Defines strongly typed data models for patients, condition-specific diagnostics,
ML predictions, NDI early warning scores, and clinical alerts.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------
# Patient Schemas
# ------------------------------------------------------------

class ConditionBadge(BaseModel):
    status: str = Field(..., description="Risk status: GREEN, YELLOW, or RED")
    label: str = Field(..., description="Human-readable condition label")
    metric: str = Field(..., description="Key diagnostic metric summary")


class PatientSummary(BaseModel):
    id: str = Field(..., description="Unique patient identifier (e.g. INF-001 or infant1)")
    patient_number: int = Field(..., description="Numerical patient id")
    infant_record_id: Optional[str] = Field(None, description="PICSDB record id if waveform exists (e.g. infant1)")
    has_waveform: bool = Field(False, description="Whether continuous waveform data is available")
    gestational_age_weeks: float
    birth_weight_kg: float
    sex: str = Field(..., description="Male / Female")
    current_age_days: float
    temp_celsius: float
    intubated: bool
    central_line: bool
    # 4 explicit, independent status badges
    apnea_badge: ConditionBadge
    bradycardia_badge: ConditionBadge
    sepsis_badge: ConditionBadge
    ndi_badge: ConditionBadge


class PatientDetail(PatientSummary):
    period: Optional[str] = None
    time_to_antibiotics: Optional[float] = None
    blood_culture_positive: Optional[int] = None
    sepsis_group: Optional[int] = None
    comorbidities: Dict[str, bool] = Field(default_factory=dict)
    ndi_score: float
    ndi_band: str
    clinical_summary: str


# ------------------------------------------------------------
# Apnea Diagnostics Schemas (Condition 1)
# ------------------------------------------------------------

class WaveformPoint(BaseModel):
    time_sec: float
    value: float


class ApneaEvent(BaseModel):
    id: int
    start_sec: float
    end_sec: float
    duration_sec: float
    severity: str = Field(..., description="MILD (15-20s), MODERATE (20-30s), SEVERE (>30s)")
    suppression_ratio: float
    source: str


class ApneaResponse(BaseModel):
    infant_id: str
    status: str = Field(..., description="GREEN, YELLOW, RED")
    events_per_hour: float
    total_events_detected: int
    mean_event_duration_sec: float
    max_event_duration_sec: float
    window_start_sec: float
    window_duration_sec: float
    events: List[ApneaEvent]
    respiration_waveform: List[WaveformPoint]
    clinical_interpretation: str


# ------------------------------------------------------------
# Bradycardia Diagnostics Schemas (Condition 2)
# ------------------------------------------------------------

class BradycardiaSpell(BaseModel):
    id: int
    start_sec: float
    end_sec: float
    duration_sec: float
    min_heart_rate_bpm: float
    mean_heart_rate_bpm: float
    classification: str = Field(..., description="STRONG BRADYCARDIA or POSSIBLE BRADYCARDIA")


class BradycardiaResponse(BaseModel):
    infant_id: str
    status: str = Field(..., description="GREEN, YELLOW, RED")
    spells_per_hour: float
    total_spells_detected: int
    lowest_heart_rate_bpm: float
    mean_baseline_hr_bpm: float
    threshold_bpm: float = 100.0
    window_start_sec: float
    window_duration_sec: float
    spells: List[BradycardiaSpell]
    heart_rate_trend: List[WaveformPoint]
    clinical_interpretation: str


# ------------------------------------------------------------
# Sepsis & Mortality Prediction Schemas (Condition 3)
# ------------------------------------------------------------

class SepsisPredictionRequest(BaseModel):
    gestational_age_at_birth_weeks: float = Field(..., ge=20.0, le=45.0, description="Gestational age in weeks")
    birth_weight_kg: float = Field(..., ge=0.3, le=7.0, description="Birth weight in kilograms")
    sex: int = Field(0, description="0=Female, 1=Male")
    onset_age_in_days: float = Field(..., ge=0.0, le=365.0, description="Age at symptom onset")
    onset_hour_of_day: int = Field(12, ge=0, le=23)
    temp_celsius: float = Field(37.0, ge=30.0, le=44.0, description="Body temperature")
    intubated_at_time_of_sepsis_evaluation: int = Field(0, description="1 if intubated/ventilated, else 0")
    inotrope_at_time_of_sepsis_eval: int = Field(0, description="1 if receiving vasopressors, else 0")
    central_venous_line: int = Field(0, description="1 if central line present, else 0")
    umbilical_arterial_line: int = Field(0, description="1 if umbilical arterial line present, else 0")
    ecmo: int = Field(0, description="1 if on ECMO, else 0")
    comorbidity_necrotizing_enterocolitis: int = Field(0)
    comorbidity_chronic_lung_disease: int = Field(0)
    comorbidity_cardiac: int = Field(0)
    comorbidity_surgical: int = Field(0)
    comorbidity_ivh_or_shunt: int = Field(0)


class FeatureContribution(BaseModel):
    feature: str
    label: str
    impact: str
    direction: str = Field(..., description="INCREASES_RISK or DECREASES_RISK")


class SepsisPredictionResponse(BaseModel):
    sepsis_probability: float = Field(..., ge=0.0, le=1.0)
    sepsis_risk_percentage: float
    status: str = Field(..., description="GREEN, YELLOW, RED")
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH")
    top_contributing_features: List[FeatureContribution]
    clinical_recommendation: str


class MortalityPredictionResponse(BaseModel):
    mortality_probability: float = Field(..., ge=0.0, le=1.0)
    mortality_risk_percentage: float
    status: str = Field(..., description="GREEN, YELLOW, RED")
    risk_level: str = Field(..., description="LOW, MODERATE, CRITICAL")
    top_contributing_features: List[FeatureContribution]
    clinical_recommendation: str


# ------------------------------------------------------------
# Fused Neonatal Decompensation Index (NDI)
# ------------------------------------------------------------

class NDISubScores(BaseModel):
    apnea_score: float = Field(..., ge=0.0, le=100.0, description="Sub-score derived from respiration waveform")
    bradycardia_score: float = Field(..., ge=0.0, le=100.0, description="Sub-score derived from ECG/heart rate waveform")
    sepsis_score: float = Field(..., ge=0.0, le=100.0, description="Sub-score derived from ML model & clinical markers")
    prematurity_vulnerability_score: float = Field(..., ge=0.0, le=100.0)


class NDIResponse(BaseModel):
    patient_id: str
    ndi_score: float = Field(..., ge=0.0, le=100.0, description="Composite index 0-100")
    ndi_band: str = Field(..., description="GREEN (0-39), YELLOW (40-64), RED (65-100)")
    sub_scores: NDISubScores
    primary_driver: str
    triage_action: str
    clinical_rationale: str


# ------------------------------------------------------------
# Clinical Alerts Schemas
# ------------------------------------------------------------

class AlertItem(BaseModel):
    id: str
    patient_id: str
    patient_display_name: str
    severity: str = Field(..., description="RED or YELLOW")
    source_condition: str = Field(..., description="APNEA, BRADYCARDIA, SEPSIS, or COMBINED")
    contributing_conditions: Optional[List[str]] = Field(default_factory=list, description="All conditions triggering this alert")
    headline: str
    explanation: str
    ndi_score: float
    timestamp: str


class AlertsResponse(BaseModel):
    total_alerts: int
    critical_red_count: int
    elevated_yellow_count: int
    alerts: List[AlertItem]


# ------------------------------------------------------------
# System Health Schema
# ------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    backend_version: str
    models_loaded: bool
    sepsis_cohort_loaded: bool
    waveform_records_count: int
