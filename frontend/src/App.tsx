import React, { useState, useEffect, useRef } from 'react';
import { api } from './api/client';
import { PatientSummary, AlertItem } from './types';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { PatientDetail } from './pages/PatientDetail';
import { AlertsPage } from './pages/AlertsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { RiskCalculator } from './pages/RiskCalculator';

export const App: React.FC = () => {
  // Theme state: 'light' | 'dark' initialized from localStorage (defaulting to 'light')
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const savedTheme = localStorage.getItem('neoguardian_theme');
    return savedTheme === 'dark' ? 'dark' : 'light';
  });

  const [currentTab, setCurrentTab] = useState<'dashboard' | 'alerts' | 'analytics' | 'calculator'>('dashboard');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  const [rawPatients, setRawPatients] = useState<PatientSummary[]>([]);
  const [rawAlerts, setRawAlerts] = useState<AlertItem[]>([]);
  const [systemStatus, setSystemStatus] = useState<string>('ONLINE');

  // Emergency Simulation State
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulatedPatient, setSimulatedPatient] = useState<PatientSummary | null>(null);
  const [simulatedAlert, setSimulatedAlert] = useState<AlertItem | null>(null);
  const simulationTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  // Alert Acknowledgment State (alertId -> timestamp)
  const [acknowledgedMap, setAcknowledgedMap] = useState<Record<string, string>>({});

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Sync theme with document element and localStorage
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('neoguardian_theme', theme);
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  const fetchAllData = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [pList, aList, h] = await Promise.all([
        api.getPatients(),
        api.getAlerts(),
        api.getHealth()
      ]);

      setRawPatients(pList);
      setRawAlerts(aList.alerts);
      setSystemStatus(h.status);
    } catch (err: any) {
      console.error('Failed to load NeoGuardian data:', err);
      setError(err.message || 'Could not connect to FastAPI server at http://127.0.0.1:8000.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  // Cleanup simulation timers on unmount
  useEffect(() => {
    return () => {
      simulationTimers.current.forEach(clearTimeout);
    };
  }, []);

  // 1. Emergency Simulation Handlers
  const handleStartSimulation = () => {
    // Clear any existing simulation timers
    simulationTimers.current.forEach(clearTimeout);
    simulationTimers.current = [];

    // Find a stable green patient to simulate (prefer infant2 or first green patient)
    const targetPatient = rawPatients.find(p => p.id === 'infant2' && p.ndi_badge.status === 'GREEN')
      || rawPatients.find(p => p.ndi_badge.status === 'GREEN')
      || rawPatients[0];

    if (!targetPatient) return;

    setIsSimulating(true);

    // Initial Stage (0s): Immediate warning indication
    const initialSimPatient: PatientSummary = {
      ...targetPatient,
      is_simulated: true,
      temp_celsius: 37.8
    };
    setSimulatedPatient(initialSimPatient);

    // Step 1 (~1.2s): Transition to YELLOW (Elevated)
    const timer1 = setTimeout(() => {
      const yellowSimPatient: PatientSummary = {
        ...targetPatient,
        is_simulated: true,
        temp_celsius: 38.2,
        apnea_badge: { status: 'YELLOW', label: 'Moderate Apneas', metric: '2.4 / hr (max 22.0s)' },
        bradycardia_badge: { status: 'YELLOW', label: 'Occasional Decels', metric: 'Lowest 92 BPM' },
        sepsis_badge: { status: 'YELLOW', label: 'Elevated Risk', metric: '38.5% Prob' },
        ndi_badge: { status: 'YELLOW', label: 'NDI: 54', metric: 'YELLOW Alert Band' }
      };
      setSimulatedPatient(yellowSimPatient);
    }, 1200);

    // Step 2 (~2.8s): Transition to RED (Critical Rapid Decompensation)
    const timer2 = setTimeout(() => {
      const redSimPatient: PatientSummary = {
        ...targetPatient,
        is_simulated: true,
        temp_celsius: 38.9,
        apnea_badge: { status: 'RED', label: 'Frequent Apneas', metric: '4.6 / hr (max 48.2s)' },
        bradycardia_badge: { status: 'RED', label: 'Severe Decelerations', metric: 'Lowest 72 BPM' },
        sepsis_badge: { status: 'RED', label: 'High Sepsis Risk', metric: '68.4% Prob' },
        ndi_badge: { status: 'RED', label: 'NDI: 84', metric: 'RED Alert Band' }
      };
      setSimulatedPatient(redSimPatient);

      // Create new critical alert in the alerts feed
      const newSimAlert: AlertItem = {
        id: `SIM-ALERT-${Date.now()}`,
        patient_id: targetPatient.id,
        patient_display_name: `${targetPatient.id.toUpperCase()} (DEMO)`,
        severity: 'RED',
        source_condition: 'COMBINED',
        contributing_conditions: ['APNEA', 'BRADYCARDIA', 'SEPSIS'],
        headline: 'Critical Cardiorespiratory & Thermal Decompensation',
        explanation: 'DEMO SIMULATION: Rapid escalation triggered. Prolonged respiratory cessation >45s with heart rate drop to 72 BPM and pyrexia (38.9°C).',
        ndi_score: 84,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        is_simulated: true
      };
      setSimulatedAlert(newSimAlert);
    }, 2800);

    simulationTimers.current = [timer1, timer2];
  };

  const handleResetSimulation = () => {
    simulationTimers.current.forEach(clearTimeout);
    simulationTimers.current = [];
    setIsSimulating(false);
    setSimulatedPatient(null);
    setSimulatedAlert(null);
  };

  // 2. Alert Acknowledgment Handlers
  const handleAcknowledgeAlert = (alertId: string) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setAcknowledgedMap(prev => ({
      ...prev,
      [alertId]: timestamp
    }));
  };

  const handleReopenAlert = (alertId: string) => {
    setAcknowledgedMap(prev => {
      const updated = { ...prev };
      delete updated[alertId];
      return updated;
    });
  };

  // Merge patients with simulation state
  const effectivePatients: PatientSummary[] = rawPatients.map(p => {
    if (isSimulating && simulatedPatient && p.id === simulatedPatient.id) {
      return simulatedPatient;
    }
    return p;
  });

  // Merge alerts with simulation alert
  const allAlerts: AlertItem[] = [
    ...(simulatedAlert ? [simulatedAlert] : []),
    ...rawAlerts
  ];

  // Partition into Active and Resolved lists
  const activeAlerts: AlertItem[] = allAlerts.filter(a => !acknowledgedMap[a.id]);
  const resolvedAlerts: AlertItem[] = allAlerts
    .filter(a => !!acknowledgedMap[a.id])
    .map(a => ({
      ...a,
      acknowledged: true,
      acknowledged_at: acknowledgedMap[a.id]
    }));

  const redAlertCount = activeAlerts.filter(a => a.severity === 'RED').length;
  const yellowAlertCount = activeAlerts.filter(a => a.severity === 'YELLOW').length;

  const handleSelectPatient = (patientId: string) => {
    setSelectedPatientId(patientId);
  };

  const handleBackToDashboard = () => {
    setSelectedPatientId(null);
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 overflow-hidden font-sans transition-colors duration-200">
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setSelectedPatientId(null);
          setCurrentTab(tab);
        }}
        redAlertCount={redAlertCount}
        yellowAlertCount={yellowAlertCount}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          systemStatus={systemStatus}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          onRefresh={() => fetchAllData(true)}
          isRefreshing={refreshing}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
          <div className="max-w-7xl mx-auto">
            {selectedPatientId ? (
              <PatientDetail
                patientId={selectedPatientId}
                onBack={handleBackToDashboard}
                isDark={theme === 'dark'}
              />
            ) : currentTab === 'dashboard' ? (
              <Dashboard
                patients={effectivePatients}
                loading={loading}
                error={error}
                onSelectPatient={handleSelectPatient}
                isSimulating={isSimulating}
                simulatedPatientId={simulatedPatient?.id}
                onStartSimulation={handleStartSimulation}
                onResetSimulation={handleResetSimulation}
              />
            ) : currentTab === 'alerts' ? (
              <AlertsPage
                activeAlerts={activeAlerts}
                resolvedAlerts={resolvedAlerts}
                loading={loading}
                onSelectPatient={handleSelectPatient}
                onAcknowledgeAlert={handleAcknowledgeAlert}
                onReopenAlert={handleReopenAlert}
              />
            ) : currentTab === 'analytics' ? (
              <AnalyticsPage
                patients={effectivePatients}
                alerts={activeAlerts}
                resolvedAlertsCount={resolvedAlerts.length}
                isDark={theme === 'dark'}
              />
            ) : (
              <RiskCalculator />
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
