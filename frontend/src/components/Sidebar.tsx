import React from 'react';
import { LayoutDashboard, TrendingUp, Database, Sliders, Layers } from 'lucide-react';

export type TabType = 'overview' | 'predictions' | 'reports' | 'admin';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  userRole: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, userRole }) => {
  const navItems = [
    {
      id: 'overview' as TabType,
      label: 'Overview Dashboard',
      icon: LayoutDashboard,
      roles: ['Admin', 'Ward_Officer', 'Analyst']
    },
    {
      id: 'predictions' as TabType,
      label: 'ML Waste Forecast',
      icon: TrendingUp,
      roles: ['Admin', 'Ward_Officer', 'Analyst']
    },
    {
      id: 'reports' as TabType,
      label: 'OLAP Data Warehouse',
      icon: Database,
      roles: ['Admin', 'Ward_Officer', 'Analyst']
    },
    {
      id: 'admin' as TabType,
      label: 'ETL & Admin Control',
      icon: Sliders,
      roles: ['Admin', 'Ward_Officer']
    }
  ];

  return (
    <aside className="w-64 glass-panel border-r border-slate-800 p-4 shrink-0 flex flex-col justify-between hidden md:flex">
      <div className="space-y-6">
        <div className="px-3 py-2 text-xs font-semibold uppercase text-slate-400 tracking-wider flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-emerald-400" /> System Modules
        </div>

        <nav className="space-y-1.5">
          {navItems.map((item) => {
            if (!item.roles.includes(userRole)) return null;
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-600/90 to-teal-600/90 text-white shadow-lg shadow-emerald-950/40 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-400 space-y-1">
        <div className="font-semibold text-slate-300 flex items-center justify-between">
          <span>Data Warehouse</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>
        <p className="text-[11px] leading-tight text-slate-400">PostgreSQL dw schema (Star Schema OLAP model)</p>
      </div>
    </aside>
  );
};
