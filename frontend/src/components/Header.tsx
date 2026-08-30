import React from 'react';
import { Activity, RefreshCw, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  systemStatus: string;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  systemStatus,
  theme,
  onToggleTheme,
  onRefresh,
  isRefreshing = false
}) => {
  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-3.5 sticky top-0 z-30 flex items-center justify-between shadow-xs transition-colors duration-200">
      <div className="flex items-center gap-3.5">
        <div className="w-9 h-9 rounded-lg bg-blue-600 dark:bg-blue-500 flex items-center justify-center text-white shadow-xs">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">NeoGuardian</h1>
            <span className="text-[11px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold border border-blue-200/60 dark:border-blue-800/60">
              NICU Monitor
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-normal">
            Intelligent Neonatal Health Monitoring & Early Warning System
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Telemetry Status Indicator */}
        <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700/60 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-slate-600 dark:text-slate-300">
            Telemetry: <strong className="text-slate-900 dark:text-white font-semibold">{systemStatus}</strong>
          </span>
        </div>

        {/* Theme Toggle Button (Sun / Moon) */}
        <button
          onClick={onToggleTheme}
          className="flex items-center justify-center w-8 h-8 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 shadow-2xs transition active:scale-95 cursor-pointer"
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          aria-label="Toggle Theme"
        >
          {theme === 'light' ? (
            <Moon className="w-4 h-4 text-slate-600 hover:text-slate-900" />
          ) : (
            <Sun className="w-4 h-4 text-amber-400 hover:text-amber-300" />
          )}
        </button>

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-medium border border-slate-200 dark:border-slate-700 shadow-2xs transition active:scale-95 cursor-pointer"
            title="Refresh clinical telemetry"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 dark:text-slate-400 ${isRefreshing ? 'animate-spin text-blue-600 dark:text-blue-400' : ''}`} />
            <span>Refresh</span>
          </button>
        )}
      </div>
    </header>
  );
};
