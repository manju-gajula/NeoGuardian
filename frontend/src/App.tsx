import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import { PatientSummary, AlertItem } from './types';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { PatientDetail } from './pages/PatientDetail';
import { AlertsPage } from './pages/AlertsPage';
import { RiskCalculator } from './pages/RiskCalculator';

export const App: React.FC = () => {
  // Theme state: 'light' | 'dark' initialized from localStorage (defaulting to 'light')
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const savedTheme = localStorage.getItem('neoguardian_theme');
    return savedTheme === 'dark' ? 'dark' : 'light';
  });

  const [currentTab, setCurrentTab] = useState<'dashboard' | 'alerts' | 'calculator'>('dashboard');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [systemStatus, setSystemStatus] = useState<string>('ONLINE');

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

      setPatients(pList);
      setAlerts(aList.alerts);
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

  const handleSelectPatient = (patientId: string) => {
    setSelectedPatientId(patientId);
  };

  const handleBackToDashboard = () => {
    setSelectedPatientId(null);
  };

  const redAlertCount = alerts.filter(a => a.severity === 'RED').length;
  const yellowAlertCount = alerts.filter(a => a.severity === 'YELLOW').length;

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
                patients={patients}
                loading={loading}
                error={error}
                onSelectPatient={handleSelectPatient}
              />
            ) : currentTab === 'alerts' ? (
              <AlertsPage
                alerts={alerts}
                loading={loading}
                onSelectPatient={handleSelectPatient}
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
