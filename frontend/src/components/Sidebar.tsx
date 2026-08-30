import React from 'react';
import { LayoutDashboard, AlertTriangle, Calculator, HeartPulse, Wind, Bug, ShieldCheck } from 'lucide-react';

interface SidebarProps {
  currentTab: 'dashboard' | 'alerts' | 'calculator';
  onSelectTab: (tab: 'dashboard' | 'alerts' | 'calculator') => void;
  redAlertCount: number;
  yellowAlertCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  redAlertCount,
  yellowAlertCount
}) => {
  const totalAlerts = redAlertCount + yellowAlertCount;

  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between p-4 shrink-0 shadow-xs transition-colors duration-200">
      <div className="space-y-6">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 px-3">
            Clinical Navigation
          </span>
          <nav className="mt-2.5 space-y-1">
            <button
              onClick={() => onSelectTab('dashboard')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${
                currentTab === 'dashboard'
                  ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              <LayoutDashboard className={`w-4 h-4 ${currentTab === 'dashboard' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}`} />
              <span>Patients Dashboard</span>
            </button>

            <button
              onClick={() => onSelectTab('alerts')}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${
                currentTab === 'alerts'
                  ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className={`w-4 h-4 ${currentTab === 'alerts' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}`} />
                <span>Active Alerts</span>
              </div>
              {totalAlerts > 0 && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    redAlertCount > 0
                      ? 'bg-rose-100 dark:bg-rose-950/80 text-rose-700 dark:text-rose-300'
                      : 'bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300'
                  }`}
                >
                  {totalAlerts}
                </span>
              )}
            </button>

            <button
              onClick={() => onSelectTab('calculator')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${
                currentTab === 'calculator'
                  ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              <Calculator className={`w-4 h-4 ${currentTab === 'calculator' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}`} />
              <span>Bedside Calculator</span>
            </button>
          </nav>
        </div>

        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 px-3">
            Monitored Conditions
          </span>
          <div className="mt-2.5 space-y-2 px-3 text-xs text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-2.5">
              <Wind className="w-4 h-4 text-sky-600 dark:text-sky-400" />
              <span>1. Apnea of Prematurity</span>
            </div>
            <div className="flex items-center gap-2.5">
              <HeartPulse className="w-4 h-4 text-rose-500 dark:text-rose-400" />
              <span>2. Neonatal Bradycardia</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Bug className="w-4 h-4 text-amber-600 dark:text-amber-400" />
              <span>3. Late-Onset Sepsis</span>
            </div>
            <div className="flex items-center gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800">
              <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="font-semibold text-slate-700 dark:text-slate-300">Fused NDI (0–100)</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-50 dark:bg-slate-950/60 rounded-lg p-3 border border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 space-y-0.5">
        <p className="font-medium text-slate-700 dark:text-slate-300">Cohort Database</p>
        <p>10 Continuous Waveforms</p>
        <p>1,946 Clinical Episodes</p>
      </div>
    </aside>
  );
};
