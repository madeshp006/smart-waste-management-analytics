import React, { useState, useEffect } from 'react';
import { User } from './types';
import { api, getAuthToken, removeAuthToken } from './services/api';
import { Navbar } from './components/Navbar';
import { Sidebar, TabType } from './components/Sidebar';
import { LoginPage } from './components/LoginPage';
import { OverviewView } from './components/OverviewView';
import { PredictionView } from './components/PredictionView';
import { ReportsView } from './components/ReportsView';
import { AdminView } from './components/AdminView';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  useEffect(() => {
    const checkAuth = async () => {
      const token = getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const u = await api.getCurrentUser();
        setUser(u);
      } catch (err) {
        removeAuthToken();
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const handleLogout = () => {
    removeAuthToken();
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex justify-center items-center text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-semibold">Initializing Municipal Analytics Platform...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLoginSuccess={() => window.location.reload()} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar user={user} onLogout={handleLogout} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} userRole={user.role} />

        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          {activeTab === 'overview' && <OverviewView />}
          {activeTab === 'predictions' && <PredictionView />}
          {activeTab === 'reports' && <ReportsView />}
          {activeTab === 'admin' && <AdminView userRole={user.role} />}
        </main>
      </div>
    </div>
  );
};

export default App;
