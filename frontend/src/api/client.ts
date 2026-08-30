import {
  PatientSummary,
  PatientDetail,
  ApneaResponse,
  BradycardiaResponse,
  SepsisPredictionRequest,
  SepsisPredictionResponse,
  MortalityPredictionResponse,
  NDIResponse,
  AlertsResponse,
  HealthResponse
} from '../types';

const API_BASE_URL = (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_URL) || '';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // Ignore json parse error
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (err: any) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // System Health
  getHealth: () => fetchJson<HealthResponse>('/api/health'),

  // Patients
  getPatients: () => fetchJson<PatientSummary[]>('/api/patients'),
  getPatientDetail: (id: string) => fetchJson<PatientDetail>(`/api/patients/${id}`),

  // Condition 1: Apnea Waveform & Events
  getApneaDiagnostics: (infantId: string, windowStart = 13080, windowDuration = 180) =>
    fetchJson<ApneaResponse>(`/api/apnea/${infantId}?window_start_sec=${windowStart}&window_duration_sec=${windowDuration}`),

  // Condition 2: Bradycardia ECG & Spells
  getBradycardiaDiagnostics: (infantId: string, windowStart = 13080, windowDuration = 180) =>
    fetchJson<BradycardiaResponse>(`/api/bradycardia/${infantId}?window_start_sec=${windowStart}&window_duration_sec=${windowDuration}`),

  // Condition 3: Sepsis & Mortality Predictions
  predictSepsisRisk: (data: SepsisPredictionRequest) =>
    fetchJson<SepsisPredictionResponse>('/api/predict/sepsis-risk', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  predictMortalityRisk: (data: SepsisPredictionRequest) =>
    fetchJson<MortalityPredictionResponse>('/api/predict/mortality-risk', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Fused NDI
  getPatientNDI: (patientId: string) => fetchJson<NDIResponse>(`/api/ndi/${patientId}`),

  // Active Alerts
  getAlerts: () => fetchJson<AlertsResponse>('/api/alerts'),
};
