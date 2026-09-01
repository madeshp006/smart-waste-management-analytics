import React, { useState } from 'react';
import { api } from '../services/api';
import { Recycle, Shield, UserCheck, BarChart2, AlertCircle, ArrowRight } from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(username, password);
      onLoginSuccess();
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (u: string) => {
    setUsername(u);
    setPassword('password123');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-cyan-600/20 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center mx-auto shadow-xl shadow-emerald-950/60 ring-4 ring-emerald-500/20">
            <Recycle className="w-9 h-9 text-slate-950 stroke-[2.5]" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Smart Waste Management Analytics</h2>
          <p className="text-xs text-slate-400">Municipal Data Warehouse & Garbage Generation Prediction Platform</p>
        </div>

        {/* Login Box */}
        <div className="glass-panel p-6 rounded-2xl space-y-5 border border-slate-800 shadow-2xl">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Username or Email</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                placeholder="Enter username (e.g. admin)"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-lg shadow-emerald-950/50 transition-all flex items-center justify-center gap-2"
            >
              {loading ? 'Authenticating...' : 'Sign In to Analytics Platform'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="pt-2 border-t border-slate-800/80">
            <p className="text-[11px] font-medium text-slate-400 mb-2.5 text-center">Quick Demo Credentials (Click to fill):</p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin')}
                className="p-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 flex flex-col items-center gap-1 transition-all"
              >
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-semibold">Admin</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('officer_w01')}
                className="p-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 flex flex-col items-center gap-1 transition-all"
              >
                <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-semibold">Ward Officer</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('analyst')}
                className="p-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 flex flex-col items-center gap-1 transition-all"
              >
                <BarChart2 className="w-3.5 h-3.5 text-purple-400" />
                <span className="font-semibold">Analyst</span>
              </button>
            </div>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 text-center">
          Data Warehouse & System Powered by PostgreSQL dw Star Schema & scikit-learn ML Pipeline
        </p>
      </div>
    </div>
  );
};
