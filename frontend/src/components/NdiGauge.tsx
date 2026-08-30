import React from 'react';
import { NDISubScores } from '../types';

interface NdiGaugeProps {
  score: number;
  band: 'GREEN' | 'YELLOW' | 'RED';
  subScores?: NDISubScores;
  primaryDriver?: string;
}

export const NdiGauge: React.FC<NdiGaugeProps> = ({
  score,
  band,
  subScores,
  primaryDriver
}) => {
  const clampedScore = Math.min(100, Math.max(0, score));

  const getBandStyles = () => {
    switch (band) {
      case 'RED':
        return {
          text: 'text-rose-600 dark:text-rose-400',
          bg: 'bg-rose-500',
          pill: 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/60',
          label: 'Critical Risk',
          description: 'Immediate clinical evaluation & sepsis protocol recommended.'
        };
      case 'YELLOW':
        return {
          text: 'text-amber-600 dark:text-amber-400',
          bg: 'bg-amber-500',
          pill: 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60',
          label: 'Elevated Risk',
          description: 'Intensify monitoring; investigate primary contributing factor.'
        };
      case 'GREEN':
      default:
        return {
          text: 'text-emerald-600 dark:text-emerald-400',
          bg: 'bg-emerald-500',
          pill: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60',
          label: 'Stable Range',
          description: 'Cardiorespiratory stability and baseline sepsis indicators.'
        };
    }
  };

  const style = getBandStyles();

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200/90 dark:border-slate-800 p-6 shadow-sm transition-colors duration-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Neonatal Decompensation Index (NDI)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Fused cardiorespiratory, microbiological & clinical risk score
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-3 py-1 rounded-full font-bold uppercase border ${style.pill}`}>
            {style.label} ({band})
          </span>
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-8 py-6">
        {/* Large Focal Gauge Circle */}
        <div className="relative w-36 h-36 rounded-full bg-slate-50 dark:bg-slate-950 border-6 border-slate-100 dark:border-slate-800 flex flex-col items-center justify-center shrink-0 shadow-inner">
          <span className={`text-5xl font-black font-mono tracking-tight ${style.text}`}>
            {clampedScore.toFixed(0)}
          </span>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mt-0.5">
            out of 100
          </span>
        </div>

        {/* Progress & Risk Description */}
        <div className="flex-1 w-full space-y-4">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-medium text-slate-600 dark:text-slate-300">
              <span>Risk Scale</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">
                {clampedScore < 40 ? '0–39 Normal' : clampedScore < 65 ? '40–64 Elevated' : '65–100 Critical Alert'}
              </span>
            </div>

            {/* Visual multi-zone risk bar */}
            <div className="w-full bg-slate-100 dark:bg-slate-800 h-3 rounded-full overflow-hidden flex border border-slate-200/60 dark:border-slate-700 relative">
              <div
                className={`h-full transition-all duration-500 rounded-full ${style.bg}`}
                style={{ width: `${clampedScore}%` }}
              />
            </div>

            <div className="flex justify-between text-[10px] text-slate-500 dark:text-slate-400 font-mono pt-0.5">
              <span>0 Stable</span>
              <span>40 Elevated</span>
              <span>65 Critical</span>
              <span>100</span>
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-950/60 rounded-lg p-3 border border-slate-100 dark:border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div>
              <span className="text-slate-500 dark:text-slate-400">Clinical Interpretation: </span>
              <span className="text-slate-700 dark:text-slate-300 font-medium">{style.description}</span>
            </div>
            {primaryDriver && (
              <div className="shrink-0 bg-white dark:bg-slate-900 px-2.5 py-1 rounded border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs">
                <span className="text-slate-500 dark:text-slate-400">Primary Driver: </span>
                <strong className="text-slate-900 dark:text-white">{primaryDriver}</strong>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sub-Score Breakdown Columns */}
      {subScores && (
        <div className="mt-2 pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
          <div className="bg-slate-50 dark:bg-slate-950/60 rounded-lg p-3 border border-slate-100 dark:border-slate-800/80">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium block">🫁 Apnea Component (30%)</span>
            <span className="text-2xl font-bold font-mono text-slate-800 dark:text-slate-100 mt-1 block">
              {subScores.apnea_score.toFixed(0)}
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">Respiration suppression</span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-950/60 rounded-lg p-3 border border-slate-100 dark:border-slate-800/80">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium block">❤️ Bradycardia Component (30%)</span>
            <span className="text-2xl font-bold font-mono text-slate-800 dark:text-slate-100 mt-1 block">
              {subScores.bradycardia_score.toFixed(0)}
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">Heart rate decelerations</span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-950/60 rounded-lg p-3 border border-slate-100 dark:border-slate-800/80">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium block">🦠 Sepsis Component (25%)</span>
            <span className="text-2xl font-bold font-mono text-slate-800 dark:text-slate-100 mt-1 block">
              {subScores.sepsis_score.toFixed(0)}
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">Clinical laboratory & ML risk</span>
          </div>
        </div>
      )}
    </div>
  );
};
