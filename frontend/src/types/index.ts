export interface ConditionBadge {
  status: 'GREEN' | 'YELLOW' | 'RED';
  label: string;
  metric: string;
}

export interface PatientSummary {
  id: string;
  patient_number: number;
  infant_record_id?: string | null;
  has_waveform: boolean;
  gestational_age_weeks: number;
  birth_weight_kg: number;
  sex: string;
  current_age_days: number;
  temp_celsius: number;
  intubated: boolean;
  central_line: boolean;
  apnea_badge: ConditionBadge;
  bradycardia_badge: ConditionBadge;
  sepsis_badge: ConditionBadge;
  ndi_badge: ConditionBadge;
  is_simulated?: boolean;
}

export interface PatientDetail extends PatientSummary {
  period?: string | null;
  time_to_antibiotics?: number | null;
  blood_culture_positive?: number | null;
  sepsis_group?: number | null;
  comorbidities: Record<string, boolean>;
  ndi_score: number;
  ndi_band: 'GREEN' | 'YELLOW' | 'RED';
  clinical_summary: string;
}

export interface WaveformPoint {
  time_sec: number;
  value: number;
}

export interface ApneaEvent {
  id: number;
  start_sec: number;
  end_sec: number;
  duration_sec: number;
  severity: 'MILD' | 'MODERATE' | 'SEVERE';
  suppression_ratio: number;
  source: string;
}

export interface ApneaResponse {
  infant_id: string;
  status: 'GREEN' | 'YELLOW' | 'RED';
  events_per_hour: number;
  total_events_detected: number;
  mean_event_duration_sec: number;
  max_event_duration_sec: number;
  window_start_sec: number;
  window_duration_sec: number;
  events: ApneaEvent[];
  respiration_waveform: WaveformPoint[];
  clinical_interpretation: string;
}

export interface BradycardiaSpell {
  id: number;
  start_sec: number;
  end_sec: number;
  duration_sec: number;
  min_heart_rate_bpm: number;
  mean_heart_rate_bpm: number;
  classification: string;
}

export interface BradycardiaResponse {
  infant_id: string;
  status: 'GREEN' | 'YELLOW' | 'RED';
  spells_per_hour: number;
  total_spells_detected: number;
  lowest_heart_rate_bpm: number;
  mean_baseline_hr_bpm: number;
  threshold_bpm: number;
  window_start_sec: number;
  window_duration_sec: number;
  spells: BradycardiaSpell[];
  heart_rate_trend: WaveformPoint[];
  clinical_interpretation: string;
}

export interface FeatureContribution {
  feature: string;
  label: string;
  impact: string;
  direction: 'INCREASES_RISK' | 'DECREASES_RISK';
}

export interface SepsisPredictionRequest {
  gestational_age_at_birth_weeks: number;
  birth_weight_kg: number;
  sex: number;
  onset_age_in_days: number;
  onset_hour_of_day: number;
  temp_celsius: number;
  intubated_at_time_of_sepsis_evaluation: number;
  inotrope_at_time_of_sepsis_eval: number;
  central_venous_line: number;
  umbilical_arterial_line: number;
  ecmo: number;
  comorbidity_necrotizing_enterocolitis: number;
  comorbidity_chronic_lung_disease: number;
  comorbidity_cardiac: number;
  comorbidity_surgical: number;
  comorbidity_ivh_or_shunt: number;
}

export interface SepsisPredictionResponse {
  sepsis_probability: number;
  sepsis_risk_percentage: number;
  status: 'GREEN' | 'YELLOW' | 'RED';
  risk_level: string;
  top_contributing_features: FeatureContribution[];
  clinical_recommendation: string;
}

export interface MortalityPredictionResponse {
  mortality_probability: number;
  mortality_risk_percentage: number;
  status: 'GREEN' | 'YELLOW' | 'RED';
  risk_level: string;
  top_contributing_features: FeatureContribution[];
  clinical_recommendation: string;
}

export interface NDISubScores {
  apnea_score: number;
  bradycardia_score: number;
  sepsis_score: number;
  prematurity_vulnerability_score: number;
}

export interface NDIResponse {
  patient_id: string;
  ndi_score: number;
  ndi_band: 'GREEN' | 'YELLOW' | 'RED';
  sub_scores: NDISubScores;
  primary_driver: string;
  triage_action: string;
  clinical_rationale: string;
}

export interface AlertItem {
  id: string;
  patient_id: string;
  patient_display_name: string;
  severity: 'RED' | 'YELLOW';
  source_condition: 'APNEA' | 'BRADYCARDIA' | 'SEPSIS' | 'COMBINED';
  contributing_conditions?: string[];
  headline: string;
  explanation: string;
  ndi_score: number;
  timestamp: string;
  is_simulated?: boolean;
  acknowledged?: boolean;
  acknowledged_at?: string;
}

export interface AlertsResponse {
  total_alerts: number;
  critical_red_count: number;
  elevated_yellow_count: number;
  alerts: AlertItem[];
}

export interface HealthResponse {
  status: string;
  backend_version: string;
  models_loaded: boolean;
  sepsis_cohort_loaded: boolean;
  waveform_records_count: number;
}
