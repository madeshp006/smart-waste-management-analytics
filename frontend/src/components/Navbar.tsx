import React from 'react';
import { User } from '../types';
import { Recycle, LogOut, Shield, UserCheck, BarChart2 } from 'lucide-react';

interface NavbarProps {
  user: User;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'Admin':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            <Shield className="w-3.5 h-3.5 text-emerald-400" /> Admin
          </span>
        );
      case 'Ward_Officer':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            <UserCheck className="w-3.5 h-3.5 text-cyan-400" /> Ward Officer
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            <BarChart2 className="w-3.5 h-3.5 text-purple-400" /> Data Analyst
          </span>
        );
    }
  };

  return (
    <header className="sticky top-0 z-30 glass-panel border-b border-slate-800 px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-950/50">
          <Recycle className="w-6 h-6 text-slate-950 stroke-[2.5]" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-100 leading-tight tracking-tight flex items-center gap-2">
            Smart Waste Analytics
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
              DW & ML v1.0
            </span>
          </h1>
          <p className="text-xs text-slate-400">Municipal Data Warehouse & Garbage Generation Prediction Platform</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-right">
            <div className="text-xs font-medium text-slate-200">{user.username}</div>
            <div className="text-[10px] text-slate-400">{user.email}</div>
          </div>
          {getRoleBadge(user.role)}
        </div>

        <button
          onClick={onLogout}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium transition-all border border-slate-700"
          title="Sign out of system"
        >
          <LogOut className="w-4 h-4 text-rose-400" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
};
