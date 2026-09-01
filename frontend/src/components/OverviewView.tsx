import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { DashboardKPIs, WasteTrendItem, WasteCompositionItem, WardPerformanceItem } from '../types';
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, 
  PieChart, Pie, Cell, BarChart, Bar, CartesianGrid, Legend 
} from 'recharts';
import { Scale, Truck, Users, TrendingUp, Award, Layers } from 'lucide-react';

export const OverviewView: React.FC = () => {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [trendData, setTrendData] = useState<WasteTrendItem[]>([]);
  const [compositionData, setCompositionData] = useState<WasteCompositionItem[]>([]);
  const [wardData, setWardData] = useState<WardPerformanceItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        const [kpiRes, trendRes, compRes, wardRes] = await Promise.all([
          api.getKPIs(),
          api.getTrend({}),
          api.getComposition({}),
          api.getWardPerformance()
        ]);
        setKpis(kpiRes);
        setTrendData(trendRes);
        setCompositionData(compRes);
        setWardData(wardRes);
      } catch (err) {
        console.error('Failed to load overview analytics:', err);
      } finally {
        setLoading(false);
      }
    };
    loadDashboardData();
  }, []);

  const CATEGORY_COLORS: Record<string, string> = {
    'Organic Waste': '#10b981',      // Emerald
    'Recyclable Waste': '#06b6d4',   // Cyan
    'General Solid Waste': '#64748b',// Slate
    'Hazardous Waste': '#f43f5e',    // Rose
    'E-Waste': '#a855f7',            // Purple
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64 text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Querying Data Warehouse Aggregations...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner / Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            Municipal Waste Overview Dashboard
          </h2>
          <p className="text-xs text-slate-400">Real-time Data Warehouse aggregations across 15 Municipal Wards</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <Layers className="w-4 h-4" /> DW OLAP Star Schema Active
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Waste */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Waste Collected (30D)</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <Scale className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-slate-100">
              {kpis?.total_waste_collected_tons.toLocaleString()} <span className="text-xs font-normal text-slate-400">Tons</span>
            </div>
            <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> {(kpis?.total_waste_collected_kg.toLocaleString())} kg total
            </div>
          </div>
        </div>

        {/* Card 2: Daily Average */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Avg Daily Collection</span>
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400">
              <Truck className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-slate-100">
              {(kpis ? kpis.avg_daily_waste_kg / 1000.0 : 0).toFixed(1)} <span className="text-xs font-normal text-slate-400">Tons / day</span>
            </div>
            <div className="text-[11px] text-cyan-400 mt-1">
              {kpis?.avg_daily_waste_kg.toLocaleString()} kg / day avg
            </div>
          </div>
        </div>

        {/* Card 3: Per-Capita Waste */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Avg Per-Capita Waste</span>
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-extrabold text-slate-100">
              {kpis?.avg_per_capita_waste_g} <span className="text-xs font-normal text-slate-400">g / person / day</span>
            </div>
            <div className="text-[11px] text-purple-400 mt-1">
              Across 15 City Wards
            </div>
          </div>
        </div>

        {/* Card 4: Top Ward */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Highest Volume Ward</span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-xl font-extrabold text-slate-100 truncate">
              {kpis?.highest_waste_ward}
            </div>
            <div className="text-[11px] text-amber-400 mt-1">
              {kpis?.active_wards_count} Wards Operational
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart 1: 30-Day City Waste Collection Trend (2 Cols) */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">City-Wide Waste Collection Trend</h3>
              <p className="text-xs text-slate-400">Daily weight in metric tons over time</p>
            </div>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              Historical OLAP
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="wasteGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                  formatter={(value: any) => [`${value} Tons`, 'Total Waste']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Area type="monotone" dataKey="total_weight_tons" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#wasteGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Waste Composition Breakdown (1 Col) */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100">Waste Composition</h3>
            <p className="text-xs text-slate-400">Percentage distribution by category</p>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={compositionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="percentage"
                  nameKey="waste_type"
                >
                  {compositionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.waste_type] || '#10b981'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                  formatter={(value: any) => [`${value}%`, 'Composition']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-slate-800">
            {compositionData.map((item) => (
              <div key={item.waste_type} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[item.waste_type] || '#10b981' }} />
                  <span className="text-slate-300 font-medium">{item.waste_type}</span>
                </div>
                <span className="text-slate-400 font-semibold">{item.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Ward Comparison Bar Chart */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100">Ward Waste Generation Comparison</h3>
            <p className="text-xs text-slate-400">Average daily collection vs. target ward capacity (kg)</p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={wardData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="ward_name" stroke="#94a3b8" fontSize={10} interval={0} angle={-25} textAnchor="end" />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                formatter={(value: any, name: string) => [
                  `${Number(value).toLocaleString()} kg`, 
                  name === 'avg_daily_waste_kg' ? 'Avg Daily Waste' : 'Capacity Limit'
                ]}
              />
              <Bar dataKey="avg_daily_waste_kg" name="avg_daily_waste_kg" fill="#06b6d4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
