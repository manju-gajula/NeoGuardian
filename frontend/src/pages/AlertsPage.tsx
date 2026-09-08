import React, { useState } from 'react';
import { AlertItem } from '../types';
import { AlertOctagon, AlertTriangle, Wind, HeartPulse, Bug, Activity, ArrowRight, CheckCircle2, RotateCcw, Clock } from 'lucide-react';

interface AlertsPageProps {
  activeAlerts: AlertItem[];
  resolvedAlerts: AlertItem[];
  loading: boolean;
  onSelectPatient: (patientId: string) => void;
  onAcknowledgeAlert: (alertId: string) => void;
  onReopenAlert?: (alertId: string) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({
  activeAlerts,
  resolvedAlerts,
  loading,
  onSelectPatient,
  onAcknowledgeAlert,
  onReopenAlert
}) => {
  const [activeTab, setActiveTab] = useState<'ACTIVE' | 'RESOLVED'>('ACTIVE');

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

  const redCount = activeAlerts.filter(a => a.severity === 'RED').length;
  const yellowCount = activeAlerts.filter(a => a.severity === 'YELLOW').length;

  const currentList = activeTab === 'ACTIVE' ? activeAlerts : resolvedAlerts;

  return (
    <div className="space-y-6">
      {/* Header Banner with Tabs */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-2xs transition-colors duration-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <AlertOctagon className="w-5 h-5 text-rose-600 dark:text-rose-400" />
              Clinical Decompensation Alerts & Alarm Feed
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Multi-condition threshold alerts with bedside acknowledgement tracking.
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

        {/* Tab Switcher */}
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
          <button
            onClick={() => setActiveTab('ACTIVE')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-2 ${
              activeTab === 'ACTIVE'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <span>Active Alarms</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
              activeTab === 'ACTIVE' ? 'bg-blue-500 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
            }`}>
              {activeAlerts.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('RESOLVED')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-2 ${
              activeTab === 'RESOLVED'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Resolved / Acknowledged</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
              activeTab === 'RESOLVED' ? 'bg-blue-500 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
            }`}>
              {resolvedAlerts.length}
            </span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
          <div className="w-8 h-8 border-2 border-blue-600 dark:border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Scanning patient cohorts for active alarms...</p>
        </div>
      ) : currentList.length === 0 ? (
        <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 shadow-2xs">
          {activeTab === 'ACTIVE' ? (
            <div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">No Active Clinical Alarms</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">All monitored neonates are within acceptable baseline bounds or acknowledged.</p>
            </div>
          ) : (
            <div>
              <Clock className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">No Resolved Alarms in Current Session</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">When active alerts are acknowledged, they will appear in this history tab.</p>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {currentList.map((alert) => {
            const isRed = alert.severity === 'RED';
            const isResolved = activeTab === 'RESOLVED';
            const leftBorder = isResolved
              ? 'border-l-4 border-l-emerald-500'
              : isRed
              ? 'border-l-4 border-l-rose-500'
              : 'border-l-4 border-l-amber-500';

            return (
              <div
                key={alert.id}
                className={`bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs hover:shadow-md transition-all duration-150 flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${leftBorder}`}
              >
                <div className="flex items-start gap-3.5">
                  <div className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                    isResolved
                      ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400'
                      : isRed
                      ? 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400'
                      : 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400'
                  }`}>
                    {isResolved ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : isRed ? (
                      <AlertOctagon className="w-5 h-5" />
                    ) : (
                      <AlertTriangle className="w-5 h-5" />
                    )}
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                        {alert.patient_display_name}
                      </span>
                      {alert.is_simulated && (
                        <span className="text-[10px] uppercase font-extrabold px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800">
                          Demo Simulation
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                        {getConditionIcon(alert.source_condition)}
                        {alert.source_condition}
                      </span>
                      <span className="text-xs font-mono text-slate-400 dark:text-slate-500">
                        Triggered: {alert.timestamp}
                      </span>
                      {isResolved && alert.acknowledged_at && (
                        <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                          • Acknowledged at {alert.acknowledged_at}
                        </span>
                      )}
                    </div>

                    <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-200">{alert.headline}</h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{alert.explanation}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-center shrink-0">
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 block">NDI Score</span>
                    <span className={`text-xl font-mono font-black ${
                      isResolved
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : isRed
                        ? 'text-rose-600 dark:text-rose-400'
                        : 'text-amber-600 dark:text-amber-400'
                    }`}>
                      {alert.ndi_score.toFixed(0)}
                    </span>
                  </div>

                  {!isResolved ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onAcknowledgeAlert(alert.id);
                      }}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 text-xs font-semibold transition cursor-pointer"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Acknowledge</span>
                    </button>
                  ) : onReopenAlert ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onReopenAlert(alert.id);
                      }}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-medium transition cursor-pointer"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Reopen</span>
                    </button>
                  ) : null}

                  <button
                    onClick={() => onSelectPatient(alert.patient_id)}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 text-xs font-medium transition cursor-pointer"
                  >
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
