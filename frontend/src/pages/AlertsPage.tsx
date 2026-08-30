import React from 'react';
import { AlertItem } from '../types';
import { AlertOctagon, AlertTriangle, Wind, HeartPulse, Bug, Activity, ArrowRight } from 'lucide-react';

interface AlertsPageProps {
  alerts: AlertItem[];
  loading: boolean;
  onSelectPatient: (patientId: string) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({
  alerts,
  loading,
  onSelectPatient
}) => {
  const getConditionIcon = (condition: string) => {
    switch (condition) {
      case 'APNEA':
        return <Wind className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />;
      case 'BRADYCARDIA':
        return <HeartPulse className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />;
      case 'SEPSIS':
        return <Bug className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />;
      case 'COMBINED':
      default:
        return <Activity className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />;
    }
  };

  const redCount = alerts.filter(a => a.severity === 'RED').length;
  const yellowCount = alerts.filter(a => a.severity === 'YELLOW').length;

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-2xs transition-colors duration-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <AlertOctagon className="w-5 h-5 text-rose-600 dark:text-rose-400" />
              Active Clinical Decompensation Alerts
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Prioritized by severity. Each alert is explicitly tagged with its underlying physiological trigger.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60">
              {redCount} Critical (RED)
            </span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
              {yellowCount} Elevated (YELLOW)
            </span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
          <div className="w-8 h-8 border-2 border-blue-600 dark:border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Scanning patient cohorts for active alarms...</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 shadow-2xs">
          <p className="text-sm">No active Yellow or Red condition alarms. All monitored neonates are within baseline limits.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => {
            const isRed = alert.severity === 'RED';
            const leftBorder = isRed ? 'border-l-4 border-l-rose-500' : 'border-l-4 border-l-amber-500';

            return (
              <div
                key={alert.id}
                onClick={() => onSelectPatient(alert.patient_id)}
                className={`bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs hover:shadow-md transition-all duration-150 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${leftBorder}`}
              >
                <div className="flex items-start gap-3.5">
                  <div className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                    isRed ? 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400' : 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400'
                  }`}>
                    {isRed ? <AlertOctagon className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                        {alert.patient_display_name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                        {getConditionIcon(alert.source_condition)}
                        {alert.source_condition}
                      </span>
                      <span className="text-xs font-mono text-slate-400 dark:text-slate-500">
                        {alert.timestamp}
                      </span>
                    </div>

                    <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-200">{alert.headline}</h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{alert.explanation}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-center shrink-0">
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 block">NDI Score</span>
                    <span className={`text-xl font-mono font-black ${isRed ? 'text-rose-600 dark:text-rose-400' : 'text-amber-600 dark:text-amber-400'}`}>
                      {alert.ndi_score.toFixed(0)}
                    </span>
                  </div>

                  <button className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 text-xs font-medium transition cursor-pointer">
                    Inspect <ArrowRight className="w-3 h-3 ml-1" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
