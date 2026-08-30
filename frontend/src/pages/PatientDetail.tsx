import React, { useState, useEffect } from 'react';
import {
  PatientDetail as PatientDetailType,
  ApneaResponse,
  BradycardiaResponse,
  NDIResponse,
  SepsisPredictionResponse,
  MortalityPredictionResponse
} from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { NdiGauge } from '../components/NdiGauge';
import { WaveformChart } from '../components/WaveformChart';
import {
  ArrowLeft,
  Wind,
  HeartPulse,
  Bug,
  AlertCircle,
  Stethoscope,
  Info
} from 'lucide-react';

interface PatientDetailProps {
  patientId: string;
  onBack: () => void;
  isDark?: boolean;
}

export const PatientDetail: React.FC<PatientDetailProps> = ({ patientId, onBack, isDark = false }) => {
  const [patient, setPatient] = useState<PatientDetailType | null>(null);
  const [apneaData, setApneaData] = useState<ApneaResponse | null>(null);
  const [bradyData, setBradyData] = useState<BradycardiaResponse | null>(null);
  const [ndiData, setNdiData] = useState<NDIResponse | null>(null);
  const [sepsisPred, setSepsisPred] = useState<SepsisPredictionResponse | null>(null);
  const [mortalityPred, setMortalityPred] = useState<MortalityPredictionResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'apnea' | 'bradycardia' | 'sepsis'>('apnea');

  // Window selection for waveforms
  const [windowStart] = useState<number>(13080); // ~218 min

  useEffect(() => {
    loadPatientAllData();
  }, [patientId, windowStart]);

  const loadPatientAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Load patient profile
      const p = await api.getPatientDetail(patientId);
      setPatient(p);

      // 2. Load NDI
      const ndi = await api.getPatientNDI(patientId);
      setNdiData(ndi);

      // 3. Load Waveforms if available (infant1 - infant10)
      const infantKey = p.infant_record_id || (p.has_waveform ? p.id : 'infant1');
      if (p.has_waveform || infantKey) {
        try {
          const ap = await api.getApneaDiagnostics(infantKey, windowStart, 180);
          setApneaData(ap);

          const br = await api.getBradycardiaDiagnostics(infantKey, windowStart, 180);
          setBradyData(br);
        } catch (waveErr) {
          console.warn('Waveform load warning:', waveErr);
        }
      }

      // 4. Compute ML Sepsis & Mortality Predictions
      const clinReq = {
        gestational_age_at_birth_weeks: p.gestational_age_weeks,
        birth_weight_kg: p.birth_weight_kg,
        sex: p.sex === 'Male' ? 1 : 0,
        onset_age_in_days: p.current_age_days,
        onset_hour_of_day: 12,
        temp_celsius: p.temp_celsius,
        intubated_at_time_of_sepsis_evaluation: p.intubated ? 1 : 0,
        inotrope_at_time_of_sepsis_eval: p.comorbidities['cardiac_defect'] ? 1 : 0,
        central_venous_line: p.central_line ? 1 : 0,
        umbilical_arterial_line: 0,
        ecmo: 0,
        comorbidity_necrotizing_enterocolitis: p.comorbidities['necrotizing_enterocolitis'] ? 1 : 0,
        comorbidity_chronic_lung_disease: p.comorbidities['chronic_lung_disease'] ? 1 : 0,
        comorbidity_cardiac: p.comorbidities['cardiac_defect'] ? 1 : 0,
        comorbidity_surgical: p.comorbidities['surgical_abdomen'] ? 1 : 0,
        comorbidity_ivh_or_shunt: p.comorbidities['ivh_or_shunt'] ? 1 : 0,
      };

      const sPred = await api.predictSepsisRisk(clinReq);
      setSepsisPred(sPred);

      const mPred = await api.predictMortalityRisk(clinReq);
      setMortalityPred(mPred);
    } catch (err: any) {
      setError(err.message || 'Failed to load patient diagnostics.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-24 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
        <div className="w-8 h-8 border-2 border-blue-600 dark:border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Loading multimodal patient telemetry...</p>
        <p className="text-xs text-slate-400 mt-1">Filtering 500 Hz respiration and 250 Hz ECG signals</p>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="p-6 bg-white dark:bg-slate-900 rounded-xl border border-rose-200 dark:border-rose-800 shadow-2xs space-y-3">
        <div className="flex items-center gap-2.5 text-rose-600 dark:text-rose-400">
          <AlertCircle className="w-5 h-5" />
          <h3 className="text-sm font-bold">Diagnostic Retrieval Notice</h3>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400">{error || 'Patient data could not be retrieved.'}</p>
        <button
          onClick={onBack}
          className="px-3.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Clinical Patient Summary Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-2xs transition-colors duration-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <button
              onClick={onBack}
              className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-700 transition cursor-pointer"
              title="Return to patient list"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  {patient.id.toUpperCase()}
                </h2>
                {patient.has_waveform ? (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60">
                    Waveform Monitored
                  </span>
                ) : (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                    Clinical Cohort
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                GA: <strong className="text-slate-800 dark:text-slate-200 font-medium">{patient.gestational_age_weeks.toFixed(0)} wks</strong> | Birth Weight:{' '}
                <strong className="text-slate-800 dark:text-slate-200 font-medium">{patient.birth_weight_kg.toFixed(2)} kg</strong> | Sex: {patient.sex} | Post-natal Age:{' '}
                <strong className="text-slate-800 dark:text-slate-200 font-medium">{patient.current_age_days.toFixed(0)} days</strong>
              </p>
            </div>
          </div>

          {/* Condition Status Badges */}
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge
              status={patient.apnea_badge.status}
              label="Apnea"
              metric={patient.apnea_badge.metric}
              iconType="apnea"
              size="sm"
            />
            <StatusBadge
              status={patient.bradycardia_badge.status}
              label="Bradycardia"
              metric={patient.bradycardia_badge.metric}
              iconType="bradycardia"
              size="sm"
            />
            <StatusBadge
              status={patient.sepsis_badge.status}
              label="Sepsis"
              metric={patient.sepsis_badge.metric}
              iconType="sepsis"
              size="sm"
            />
            <StatusBadge
              status={patient.ndi_badge.status}
              label="NDI Index"
              iconType="ndi"
              size="sm"
            />
          </div>
        </div>

        {patient.has_waveform && (
          <div className="mt-3.5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/60 px-3 py-2 rounded-lg border border-slate-200/60 dark:border-slate-800">
            <Info className="w-4 h-4 shrink-0 text-blue-600 dark:text-blue-400" />
            <span>
              <strong>Demo Multimodal Linkage:</strong> Synchronized PhysioNet PICSDB continuous signals ({patient.infant_record_id}) paired with matched clinical sepsis evaluation parameters.
            </span>
          </div>
        )}
      </div>

      {/* FUSED NDI GAUGE: THE VISUAL CENTERPIECE */}
      {ndiData && (
        <NdiGauge
          score={ndiData.ndi_score}
          band={ndiData.ndi_band}
          subScores={ndiData.sub_scores}
          primaryDriver={ndiData.primary_driver}
        />
      )}

      {/* THREE CONDITION PANELS AS CLEAN TABS */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-2xs transition-colors duration-200">
        <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/80 px-4 pt-1.5 gap-2">
          <button
            onClick={() => setActiveTab('apnea')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition cursor-pointer ${
              activeTab === 'apnea'
                ? 'border-blue-600 dark:border-blue-400 text-blue-700 dark:text-blue-300 bg-white dark:bg-slate-900 rounded-t-lg shadow-2xs'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Wind className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
            1. Apnea Waveform
          </button>

          <button
            onClick={() => setActiveTab('bradycardia')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition cursor-pointer ${
              activeTab === 'bradycardia'
                ? 'border-blue-600 dark:border-blue-400 text-blue-700 dark:text-blue-300 bg-white dark:bg-slate-900 rounded-t-lg shadow-2xs'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <HeartPulse className="w-3.5 h-3.5 text-rose-500 dark:text-rose-400" />
            2. Bradycardia Trend
          </button>

          <button
            onClick={() => setActiveTab('sepsis')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition cursor-pointer ${
              activeTab === 'sepsis'
                ? 'border-blue-600 dark:border-blue-400 text-blue-700 dark:text-blue-300 bg-white dark:bg-slate-900 rounded-t-lg shadow-2xs'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Bug className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            3. Sepsis ML & TreeSHAP
          </button>
        </div>

        <div className="p-6">
          {/* TAB 1: APNEA */}
          {activeTab === 'apnea' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 dark:bg-slate-950/60 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    Respiratory Waveform & Apnea Segmentation
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Source: PICSDB plethysmography signal filtered at 0.08–1.2 Hz with Hilbert amplitude suppression
                  </p>
                </div>

                <div className="flex items-center gap-5">
                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 block">Apnea Rate</span>
                    <span className="text-lg font-bold font-mono text-slate-800 dark:text-slate-100">
                      {apneaData?.events_per_hour.toFixed(1) || '0.0'} / hr
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 block">Max Duration</span>
                    <span className="text-lg font-bold font-mono text-amber-600 dark:text-amber-400">
                      {apneaData?.max_event_duration_sec.toFixed(1) || '0.0'}s
                    </span>
                  </div>
                </div>
              </div>

              {/* Waveform Chart */}
              {apneaData && (
                <WaveformChart
                  type="respiration"
                  data={apneaData.respiration_waveform}
                  apneaEvents={apneaData.events}
                  title="Abdominal Respiration Waveform"
                  subtitle={`Window: ${windowStart.toFixed(0)}s to ${(windowStart + 180).toFixed(0)}s (~${(windowStart / 60).toFixed(1)}m elapsed)`}
                  unit=" a.u."
                  isDark={isDark}
                />
              )}

              {/* Detected Apnea Events Table */}
              <div className="bg-slate-50 dark:bg-slate-950/60 rounded-xl p-4 border border-slate-200 dark:border-slate-800">
                <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-3">
                  Detected Apnea Episodes in Current Window:
                </h5>
                {apneaData && apneaData.events.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                        <tr>
                          <th className="pb-2">Event</th>
                          <th className="pb-2">Start Time</th>
                          <th className="pb-2">End Time</th>
                          <th className="pb-2">Duration</th>
                          <th className="pb-2">Severity</th>
                          <th className="pb-2">Suppression Ratio</th>
                          <th className="pb-2">Detection Source</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200/80 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                        {apneaData.events.map((evt) => (
                          <tr key={evt.id}>
                            <td className="py-2.5 font-semibold">#{evt.id}</td>
                            <td className="py-2.5 font-mono">{evt.start_sec.toFixed(1)}s ({(evt.start_sec / 60).toFixed(2)}m)</td>
                            <td className="py-2.5 font-mono">{evt.end_sec.toFixed(1)}s ({(evt.end_sec / 60).toFixed(2)}m)</td>
                            <td className="py-2.5 font-bold text-amber-700 dark:text-amber-400">{evt.duration_sec.toFixed(1)} sec</td>
                            <td className="py-2.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                evt.severity === 'SEVERE'
                                  ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60'
                                  : evt.severity === 'MODERATE'
                                  ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60'
                                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                              }`}>
                                {evt.severity}
                              </span>
                            </td>
                            <td className="py-2.5 font-mono">{evt.suppression_ratio.toFixed(3)}</td>
                            <td className="py-2.5 text-slate-500 dark:text-slate-400">{evt.source}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 dark:text-slate-400 py-2">No respiratory pause episodes detected in this window.</p>
                )}

                {apneaData && (
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-800">
                    <strong>Interpretation: </strong> {apneaData.clinical_interpretation}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: BRADYCARDIA */}
          {activeTab === 'bradycardia' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 dark:bg-slate-950/60 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    ECG Heart Rate & Bradycardia Deceleration Spells
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Source: PICSDB ECG QRS R-peaks (.qrsc) with 100 BPM pediatric threshold
                  </p>
                </div>

                <div className="flex items-center gap-5">
                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 block">Lowest Heart Rate</span>
                    <span className="text-lg font-bold font-mono text-rose-600 dark:text-rose-400">
                      {bradyData?.lowest_heart_rate_bpm.toFixed(1) || '140'} BPM
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 block">Deceleration Spells</span>
                    <span className="text-lg font-bold font-mono text-slate-800 dark:text-slate-100">
                      {bradyData?.spells_per_hour.toFixed(1) || '0.0'} / hr
                    </span>
                  </div>
                </div>
              </div>

              {/* Heart Rate Chart */}
              {bradyData && (
                <WaveformChart
                  type="heart_rate"
                  data={bradyData.heart_rate_trend}
                  bradycardiaSpells={bradyData.spells}
                  title="Instantaneous Heart Rate Trend"
                  subtitle="Dashed line represents clinical neonatal bradycardia alarm limit (100 BPM)"
                  unit=" BPM"
                  isDark={isDark}
                />
              )}

              {/* Bradycardia Spells Table */}
              <div className="bg-slate-50 dark:bg-slate-950/60 rounded-xl p-4 border border-slate-200 dark:border-slate-800">
                <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-3">
                  Documented Decelerations Below 100 BPM:
                </h5>
                {bradyData && bradyData.spells.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                        <tr>
                          <th className="pb-2">Spell</th>
                          <th className="pb-2">Start Time</th>
                          <th className="pb-2">Duration</th>
                          <th className="pb-2">Lowest Heart Rate</th>
                          <th className="pb-2">Mean HR</th>
                          <th className="pb-2">Classification</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200/80 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                        {bradyData.spells.map((sp) => (
                          <tr key={sp.id}>
                            <td className="py-2.5 font-semibold">#{sp.id}</td>
                            <td className="py-2.5 font-mono">{sp.start_sec.toFixed(1)}s ({(sp.start_sec / 60).toFixed(2)}m)</td>
                            <td className="py-2.5 font-bold text-rose-600 dark:text-rose-400">{sp.duration_sec.toFixed(1)}s</td>
                            <td className="py-2.5 font-bold text-rose-600 dark:text-rose-400 font-mono">{sp.min_heart_rate_bpm.toFixed(1)} BPM</td>
                            <td className="py-2.5 font-mono">{sp.mean_heart_rate_bpm.toFixed(1)} BPM</td>
                            <td className="py-2.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                sp.classification === 'STRONG BRADYCARDIA'
                                  ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60'
                                  : 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60'
                              }`}>
                                {sp.classification}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 dark:text-slate-400 py-2">No heart rate deceleration episodes under 100 BPM in this window.</p>
                )}

                {bradyData && (
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-800">
                    <strong>Interpretation: </strong> {bradyData.clinical_interpretation}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: SEPSIS & MORTALITY (TreeSHAP) */}
          {activeTab === 'sepsis' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Sepsis Probability Card */}
                <div className="bg-slate-50 dark:bg-slate-950/60 p-5 rounded-xl border border-slate-200 dark:border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                      <Bug className="w-4 h-4 text-amber-600 dark:text-amber-400" /> Culture-Confirmed Sepsis Probability
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                      sepsisPred?.status === 'RED' 
                        ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60' 
                        : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60'
                    }`}>
                      {sepsisPred?.risk_level} RISK
                    </span>
                  </div>
                  <div className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 font-mono mt-3">
                    {sepsisPred?.sepsis_risk_percentage.toFixed(1)}%
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                    {sepsisPred?.clinical_recommendation}
                  </p>
                </div>

                {/* 30-Day Mortality Risk Card */}
                <div className="bg-slate-50 dark:bg-slate-950/60 p-5 rounded-xl border border-slate-200 dark:border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                      <HeartPulse className="w-4 h-4 text-rose-500 dark:text-rose-400" /> 30-Day Mortality Risk
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                      mortalityPred?.status === 'RED' 
                        ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60' 
                        : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60'
                    }`}>
                      {mortalityPred?.risk_level}
                    </span>
                  </div>
                  <div className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 font-mono mt-3">
                    {mortalityPred?.mortality_risk_percentage.toFixed(1)}%
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                    {mortalityPred?.clinical_recommendation}
                  </p>
                </div>
              </div>

              {/* TreeSHAP Feature Attribution Breakdown */}
              <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Stethoscope className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    TreeSHAP Feature Attributions (Local Explainability)
                  </h4>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">shap.TreeExplainer (Random Forest)</span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                  Exact mathematical contribution of each clinical variable shifting this infant's risk away from the cohort baseline.
                </p>

                <div className="space-y-2">
                  {sepsisPred?.top_contributing_features.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800 text-xs"
                    >
                      <span className="font-medium text-slate-700 dark:text-slate-300">{item.label}</span>
                      <div className="flex items-center gap-3">
                        <span className="font-mono font-semibold text-slate-600 dark:text-slate-400">{item.impact}</span>
                        <span
                          className={`px-2 py-0.5 rounded font-semibold text-[11px] ${
                            item.direction === 'INCREASES_RISK'
                              ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60'
                              : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60'
                          }`}
                        >
                          {item.direction === 'INCREASES_RISK' ? '▲ Increases Risk' : '▼ Decreases Risk'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
