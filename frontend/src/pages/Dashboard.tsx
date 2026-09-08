import React, { useState } from 'react';
import { PatientSummary } from '../types';
import { Search, ChevronRight, Activity, Users, AlertCircle, CheckCircle, Clock, Play, RotateCcw, AlertTriangle } from 'lucide-react';

interface DashboardProps {
  patients: PatientSummary[];
  loading: boolean;
  error: string | null;
  onSelectPatient: (patientId: string) => void;
  isSimulating?: boolean;
  simulatedPatientId?: string | null;
  onStartSimulation?: () => void;
  onResetSimulation?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  patients,
  loading,
  error,
  onSelectPatient,
  isSimulating = false,
  simulatedPatientId = null,
  onStartSimulation,
  onResetSimulation
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'WAVEFORM' | 'CRITICAL' | 'ELEVATED'>('ALL');

  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.sex.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.patient_number.toString().includes(searchTerm);

    if (!matchesSearch) return false;

    if (activeFilter === 'WAVEFORM') return p.has_waveform;
    if (activeFilter === 'CRITICAL') return p.ndi_badge.status === 'RED';
    if (activeFilter === 'ELEVATED') return p.ndi_badge.status === 'YELLOW';
    return true;
  });

  const redCount = patients.filter((p) => p.ndi_badge.status === 'RED').length;
  const yellowCount = patients.filter((p) => p.ndi_badge.status === 'YELLOW').length;
  const greenCount = patients.filter((p) => p.ndi_badge.status === 'GREEN').length;

  const getStatusDot = (status: 'GREEN' | 'YELLOW' | 'RED') => {
    if (status === 'RED') return 'bg-rose-500';
    if (status === 'YELLOW') return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="space-y-6">
      {/* Simulation Control Toolbar Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-2xs transition-colors duration-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg ${isSimulating ? 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 animate-pulse' : 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400'}`}>
            {isSimulating ? <AlertTriangle className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Clinical Simulation Mode
              </h3>
              {isSimulating && (
                <span className="text-[10px] uppercase font-extrabold px-2 py-0.5 rounded-full bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
                  Demo Active
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {isSimulating
                ? `Simulating rapid cardiorespiratory decompensation on ${simulatedPatientId?.toUpperCase()} for presentation demo.`
                : 'Test automated alert triage and NDI escalation by simulating an acute infant decompensation event.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
          {!isSimulating ? (
            <button
              onClick={onStartSimulation}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Simulate Critical Event</span>
            </button>
          ) : (
            <button
              onClick={onResetSimulation}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 transition cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Simulation</span>
            </button>
          )}
        </div>
      </div>

      {/* Top Clinical Triage Summary Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-2xs transition-colors duration-200">
          <div>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Total Monitored Infants</span>
            <div id="metric-total" className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{patients.length}</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700/60 flex items-center justify-center text-slate-600 dark:text-slate-300">
            <Users className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 border-l-4 border-l-rose-500 rounded-xl p-4 flex items-center justify-between shadow-2xs transition-colors duration-200">
          <div>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Critical Risk (RED)</span>
            <div className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1">{redCount}</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-rose-50 dark:bg-rose-950/50 flex items-center justify-center text-rose-600 dark:text-rose-400">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 border-l-4 border-l-amber-500 rounded-xl p-4 flex items-center justify-between shadow-2xs transition-colors duration-200">
          <div>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Elevated Risk (YELLOW)</span>
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">{yellowCount}</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 border-l-4 border-l-emerald-500 rounded-xl p-4 flex items-center justify-between shadow-2xs transition-colors duration-200">
          <div>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Stable Infants (GREEN)</span>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{greenCount}</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-3 transition-colors duration-200">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by ID, sex, gestational age..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          <button
            onClick={() => setActiveFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
              activeFilter === 'ALL'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white border border-slate-200/60 dark:border-slate-700'
            }`}
          >
            All Patients ({patients.length})
          </button>
          <button
            onClick={() => setActiveFilter('WAVEFORM')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 cursor-pointer ${
              activeFilter === 'WAVEFORM'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white border border-slate-200/60 dark:border-slate-700'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Waveform Cohort (10)
          </button>
          <button
            onClick={() => setActiveFilter('CRITICAL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
              activeFilter === 'CRITICAL'
                ? 'bg-rose-600 text-white shadow-2xs'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white border border-slate-200/60 dark:border-slate-700'
            }`}
          >
            Critical Only ({redCount})
          </button>
          <button
            onClick={() => setActiveFilter('ELEVATED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
              activeFilter === 'ELEVATED'
                ? 'bg-amber-600 text-white shadow-2xs'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white border border-slate-200/60 dark:border-slate-700'
            }`}
          >
            Elevated Only ({yellowCount})
          </button>
        </div>
      </div>

      {/* Loading / Error States */}
      {loading && (
        <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Connecting to clinical telemetry stream...</p>
          <p className="text-xs text-slate-400 mt-1">Extracting multi-condition scores</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-rose-700 dark:text-rose-300 text-xs">
          <strong>Connection Error: </strong>
          {error}
        </div>
      )}

      {/* Patient Cards Grid */}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredPatients.map((patient) => {
            const isRed = patient.ndi_badge.status === 'RED';
            const isYellow = patient.ndi_badge.status === 'YELLOW';
            const leftBorder = isRed ? 'border-l-4 border-l-rose-500' : isYellow ? 'border-l-4 border-l-amber-500' : 'border-l-4 border-l-emerald-500';

            const ndiScore = patient.ndi_badge.label.replace('NDI: ', '');
            const isSimulatedCard = patient.is_simulated;

            return (
              <div
                key={patient.id}
                onClick={() => onSelectPatient(patient.id)}
                className={`bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200/90 dark:border-slate-800 shadow-2xs hover:shadow-md transition-all duration-200 cursor-pointer ${leftBorder} ${
                  isSimulatedCard ? 'ring-2 ring-rose-500/70 shadow-rose-100 dark:shadow-rose-950/40' : ''
                }`}
              >
                {/* Header info */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        {patient.id.toUpperCase()}
                      </h3>
                      {patient.has_waveform && (
                        <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-100 dark:border-blue-800/60">
                          Waveform
                        </span>
                      )}
                      {isSimulatedCard && (
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-700 animate-pulse">
                          Demo Simulation
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      GA: <strong className="text-slate-700 dark:text-slate-300 font-medium">{patient.gestational_age_weeks.toFixed(0)} wks</strong> | BW:{' '}
                      <strong className="text-slate-700 dark:text-slate-300 font-medium">{patient.birth_weight_kg.toFixed(2)} kg</strong> | Sex:{' '}
                      {patient.sex}
                    </p>
                  </div>

                  {/* ONE Dominant Focal NDI Badge */}
                  <div className="text-right">
                    <span
                      className={`text-xs px-2.5 py-1 rounded-md font-bold inline-block border transition-colors duration-200 ${
                        isRed
                          ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/60'
                          : isYellow
                          ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60'
                          : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60'
                      }`}
                    >
                      NDI {ndiScore}
                    </span>
                    <span className="text-[10px] text-slate-400 font-medium block mt-0.5">
                      {isRed ? 'Critical' : isYellow ? 'Elevated' : 'Stable'}
                    </span>
                  </div>
                </div>

                {/* Clean Sub-Condition Indicator Row */}
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2 text-xs text-slate-600 dark:text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${getStatusDot(patient.apnea_badge.status)} shrink-0 transition-colors duration-200`} />
                    <span className="truncate">Apnea</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${getStatusDot(patient.bradycardia_badge.status)} shrink-0 transition-colors duration-200`} />
                    <span className="truncate">Brady</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${getStatusDot(patient.sepsis_badge.status)} shrink-0 transition-colors duration-200`} />
                    <span className="truncate">Sepsis</span>
                  </div>
                </div>

                {/* Footer clinical telemetry tags */}
                <div className="mt-3.5 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <div className="flex items-center gap-2">
                    <span>{patient.temp_celsius.toFixed(1)}°C</span>
                    {patient.intubated && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] font-medium border border-slate-200/60 dark:border-slate-700">
                        Vent
                      </span>
                    )}
                    {patient.central_line && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] font-medium border border-slate-200/60 dark:border-slate-700">
                        CVL
                      </span>
                    )}
                  </div>
                  <span className="flex items-center text-blue-600 dark:text-blue-400 font-medium hover:text-blue-700 dark:hover:text-blue-300 text-xs">
                    Inspect <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
