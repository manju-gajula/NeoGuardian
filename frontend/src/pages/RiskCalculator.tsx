import React, { useState } from 'react';
import { api } from '../api/client';
import { SepsisPredictionRequest, SepsisPredictionResponse, MortalityPredictionResponse } from '../types';
import { NdiGauge } from '../components/NdiGauge';
import { Calculator, Sparkles, Bug, HeartPulse } from 'lucide-react';

export const RiskCalculator: React.FC = () => {
  const [formData, setFormData] = useState<SepsisPredictionRequest>({
    gestational_age_at_birth_weeks: 27.0,
    birth_weight_kg: 0.95,
    sex: 1,
    onset_age_in_days: 14.0,
    onset_hour_of_day: 8,
    temp_celsius: 36.2, // Hypothermia
    intubated_at_time_of_sepsis_evaluation: 1,
    inotrope_at_time_of_sepsis_eval: 0,
    central_venous_line: 1,
    umbilical_arterial_line: 0,
    ecmo: 0,
    comorbidity_necrotizing_enterocolitis: 0,
    comorbidity_chronic_lung_disease: 1,
    comorbidity_cardiac: 0,
    comorbidity_surgical: 0,
    comorbidity_ivh_or_shunt: 0
  });

  // Optional cardiorespiratory waveform telemetry inputs
  const [apneaRate, setApneaRate] = useState<number>(3.5);
  const [lowestHr, setLowestHr] = useState<number>(82.0);

  const [sepsisResult, setSepsisResult] = useState<SepsisPredictionResponse | null>(null);
  const [mortalityResult, setMortalityResult] = useState<MortalityPredictionResponse | null>(null);
  const [computing, setComputing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompute = async (e: React.FormEvent) => {
    e.preventDefault();
    setComputing(true);
    setError(null);

    try {
      const [sRes, mRes] = await Promise.all([
        api.predictSepsisRisk(formData),
        api.predictMortalityRisk(formData),
      ]);
      setSepsisResult(sRes);
      setMortalityResult(mRes);
    } catch (err: any) {
      setError(err.message || 'Failed to compute ML risk predictions.');
    } finally {
      setComputing(false);
    }
  };

  // Compute live NDI score from the combination
  const sepsisProb = sepsisResult ? sepsisResult.sepsis_probability : 0.25;
  const s_apnea = Math.min(100, (apneaRate >= 4 ? 60 : apneaRate >= 2.5 ? 40 : 20) + (apneaRate > 3 ? 30 : 15));
  const s_brady = Math.min(100, (lowestHr < 80 ? 70 : lowestHr < 100 ? 45 : 15) + (lowestHr < 85 ? 25 : 10));
  const s_sepsis = Math.min(100, sepsisProb * 65 + (formData.temp_celsius < 36.5 ? 25 : formData.temp_celsius >= 38 ? 20 : 0) + (formData.central_venous_line ? 10 : 0));
  const s_vuln = Math.min(100, (formData.gestational_age_at_birth_weeks < 28 ? 55 : 30) + (formData.birth_weight_kg < 1.0 ? 45 : 20));

  const fusedNdi = Math.min(100, Math.max(0, 0.32 * s_apnea + 0.32 * s_brady + 0.26 * s_sepsis + 0.10 * s_vuln));
  const ndiBand: 'GREEN' | 'YELLOW' | 'RED' = fusedNdi >= 65 ? 'RED' : fusedNdi >= 40 ? 'YELLOW' : 'GREEN';

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-2xs transition-colors duration-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              Bedside Multimodal Risk Calculator
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Simulate or evaluate newly admitted neonates. Runs trained Random Forest + TreeSHAP models and computes the composite NDI score.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Inputs */}
        <form onSubmit={handleCompute} className="lg:col-span-7 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 space-y-6 shadow-2xs transition-colors duration-200">
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-slate-800 pb-2">
              1. Gestational Profile & Vital Signs
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">Gestational Age at Birth (weeks)</label>
                <input
                  type="number"
                  step="1"
                  min="22"
                  max="42"
                  value={formData.gestational_age_at_birth_weeks}
                  onChange={(e) => setFormData({ ...formData, gestational_age_at_birth_weeks: parseFloat(e.target.value) || 28 })}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-slate-900 dark:text-slate-100 font-mono focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">Birth Weight (kg)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0.3"
                  max="6.0"
                  value={formData.birth_weight_kg}
                  onChange={(e) => setFormData({ ...formData, birth_weight_kg: parseFloat(e.target.value) || 1.0 })}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-slate-900 dark:text-slate-100 font-mono focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">Postnatal Age (days)</label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  max="300"
                  value={formData.onset_age_in_days}
                  onChange={(e) => setFormData({ ...formData, onset_age_in_days: parseFloat(e.target.value) || 5 })}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-slate-900 dark:text-slate-100 font-mono focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">Core Body Temperature (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  min="32"
                  max="42"
                  value={formData.temp_celsius}
                  onChange={(e) => setFormData({ ...formData, temp_celsius: parseFloat(e.target.value) || 37.0 })}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-slate-900 dark:text-slate-100 font-mono focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
                />
                <span className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5 block">&lt;36.5°C Hypothermia | &gt;38.0°C Fever</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-slate-800 pb-2">
              2. Invasive Devices & Clinical Support
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
              <label className="flex items-center gap-2.5 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <input
                  type="checkbox"
                  checked={formData.central_venous_line === 1}
                  onChange={(e) => setFormData({ ...formData, central_venous_line: e.target.checked ? 1 : 0 })}
                  className="rounded border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0 cursor-pointer"
                />
                <span className="text-slate-700 dark:text-slate-300 font-medium">Central Venous Line (CVL)</span>
              </label>

              <label className="flex items-center gap-2.5 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <input
                  type="checkbox"
                  checked={formData.intubated_at_time_of_sepsis_evaluation === 1}
                  onChange={(e) => setFormData({ ...formData, intubated_at_time_of_sepsis_evaluation: e.target.checked ? 1 : 0 })}
                  className="rounded border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0 cursor-pointer"
                />
                <span className="text-slate-700 dark:text-slate-300 font-medium">Mechanical Ventilation (Intubated)</span>
              </label>

              <label className="flex items-center gap-2.5 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <input
                  type="checkbox"
                  checked={formData.inotrope_at_time_of_sepsis_eval === 1}
                  onChange={(e) => setFormData({ ...formData, inotrope_at_time_of_sepsis_eval: e.target.checked ? 1 : 0 })}
                  className="rounded border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0 cursor-pointer"
                />
                <span className="text-slate-700 dark:text-slate-300 font-medium">Inotropic Support (Vasopressors)</span>
              </label>

              <label className="flex items-center gap-2.5 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800/60">
                <input
                  type="checkbox"
                  checked={formData.comorbidity_necrotizing_enterocolitis === 1}
                  onChange={(e) => setFormData({ ...formData, comorbidity_necrotizing_enterocolitis: e.target.checked ? 1 : 0 })}
                  className="rounded border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0 cursor-pointer"
                />
                <span className="text-slate-700 dark:text-slate-300 font-medium">Necrotizing Enterocolitis (NEC)</span>
              </label>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-slate-800 pb-2">
              3. Cardiorespiratory Telemetry Inputs
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">Apnea Events per Hour</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="15"
                  value={apneaRate}
                  onChange={(e) => setApneaRate(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-slate-900 dark:text-slate-100 font-mono focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 font-medium mb-1">Lowest Recorded HR (BPM)</label>
                <input
                  type="number"
                  step="1"
                  min="50"
                  max="180"
                  value={lowestHr}
                  onChange={(e) => setLowestHr(parseFloat(e.target.value) || 120)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-slate-900 dark:text-slate-100 font-mono focus:bg-white dark:focus:bg-slate-900 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={computing}
            className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white font-semibold text-xs shadow-xs transition flex items-center justify-center gap-2 cursor-pointer"
          >
            {computing ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Computing TreeSHAP Inference...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" /> Compute Multimodal Risk Predictions
              </>
            )}
          </button>
        </form>

        {/* Prediction Results & NDI Dial */}
        <div className="lg:col-span-5 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg text-rose-700 dark:text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* Fused NDI Gauge Card */}
          <NdiGauge
            score={fusedNdi}
            band={ndiBand}
            subScores={{
              apnea_score: s_apnea,
              bradycardia_score: s_brady,
              sepsis_score: s_sepsis,
              prematurity_vulnerability_score: s_vuln
            }}
            primaryDriver={s_apnea > s_brady && s_apnea > s_sepsis ? 'Apnea Spells' : s_brady > s_sepsis ? 'Bradycardia Decelerations' : 'Sepsis / Thermal Instability'}
          />

          {/* Prediction Outputs */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 shadow-2xs transition-colors duration-200">
              <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <Bug className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" /> Sepsis Prob
              </span>
              <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                {sepsisResult ? `${sepsisResult.sepsis_risk_percentage.toFixed(1)}%` : `${(sepsisProb * 100).toFixed(1)}%`}
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded mt-2 inline-block border ${
                (sepsisResult?.status || 'YELLOW') === 'RED'
                  ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/60'
                  : 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60'
              }`}>
                {sepsisResult?.risk_level || 'ELEVATED'}
              </span>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 shadow-2xs transition-colors duration-200">
              <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <HeartPulse className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" /> 30-Day Mortality
              </span>
              <div className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                {mortalityResult ? `${mortalityResult.mortality_risk_percentage.toFixed(1)}%` : '7.2%'}
              </div>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded mt-2 inline-block bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                {mortalityResult?.risk_level || 'MODERATE'}
              </span>
            </div>
          </div>

          {/* TreeSHAP Contributions */}
          {sepsisResult && sepsisResult.top_contributing_features.length > 0 && (
            <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 shadow-2xs space-y-2 transition-colors duration-200">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Top Model Risk Drivers (TreeSHAP):
              </h4>
              <div className="space-y-1.5">
                {sepsisResult.top_contributing_features.map((f, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-700 dark:text-slate-300 font-medium">{f.label}</span>
                    <span className={`font-mono font-semibold text-[11px] ${f.direction === 'INCREASES_RISK' ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-700 dark:text-emerald-400'}`}>
                      {f.impact}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
