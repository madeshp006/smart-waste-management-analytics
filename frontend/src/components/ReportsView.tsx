import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { WardPerformanceItem, WasteCompositionItem } from '../types';
import { Database, Download, FileSpreadsheet, Filter, Printer, Layers } from 'lucide-react';

export const ReportsView: React.FC = () => {
  const [wardPerf, setWardPerf] = useState<WardPerformanceItem[]>([]);
  const [composition, setComposition] = useState<WasteCompositionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeReportTab, setActiveReportTab] = useState<'wards' | 'composition'>('wards');

  useEffect(() => {
    const fetchOLAPReports = async () => {
      setLoading(true);
      try {
        const [wRes, cRes] = await Promise.all([
          api.getWardPerformance(),
          api.getComposition({})
        ]);
        setWardPerf(wRes);
        setComposition(cRes);
      } catch (err) {
        console.error('Failed to fetch DW OLAP reports:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchOLAPReports();
  }, []);

  const downloadCSV = () => {
    let headers: string[] = [];
    let rows: (string | number)[][] = [];
    let filename = 'waste_analytics_report.csv';

    if (activeReportTab === 'wards') {
      headers = ['Ward ID', 'Ward Name', 'Zone', 'Population', 'Target Cap (kg)', 'Total Waste (kg)', 'Avg Daily (kg)', 'Per-Capita (g)', 'Capacity Util (%)'];
      rows = wardPerf.map(w => [
        w.ward_id, w.ward_name, w.zone, w.population, w.target_capacity_kg,
        w.total_waste_kg, w.avg_daily_waste_kg, w.avg_daily_per_capita_g, w.capacity_utilization_pct
      ]);
      filename = 'ward_per_capita_performance_report.csv';
    } else {
      headers = ['Waste Type', 'Category', 'Total Weight (kg)', 'Composition Percentage (%)'];
      rows = composition.map(c => [
        c.waste_type, c.category, c.total_weight_kg, c.percentage
      ]);
      filename = 'waste_composition_breakdown_report.csv';
    }

    const csvContent = 'data:text/csv;charset=utf-8,' 
      + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-6 h-6 text-purple-400" />
            Data Warehouse OLAP Analytics & Report Exporter
          </h2>
          <p className="text-xs text-slate-400">Pre-aggregated Star Schema reports with CSV export and printable formatting</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={downloadCSV}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 transition-all"
          >
            <FileSpreadsheet className="w-4 h-4" /> Export CSV
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
          >
            <Printer className="w-4 h-4" /> Print Report
          </button>
        </div>
      </div>

      {/* Report Selector Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveReportTab('wards')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeReportTab === 'wards'
              ? 'bg-purple-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 bg-slate-900/60'
          }`}
        >
          Ward Per-Capita & Capacity Ranking Report
        </button>

        <button
          onClick={() => setActiveReportTab('composition')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeReportTab === 'composition'
              ? 'bg-purple-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 bg-slate-900/60'
          }`}
        >
          Municipal Waste Composition Breakdown
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64 text-slate-400">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-medium">Running DW Star Schema Aggregations...</span>
          </div>
        </div>
      ) : activeReportTab === 'wards' ? (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100">Ward Performance & Per-Capita Waste Ranking</h3>
            <span className="text-xs text-slate-400">Aggregated from dw.fact_waste_generation</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Ward Code & Name</th>
                  <th className="px-4 py-3">Zone</th>
                  <th className="px-4 py-3 text-right">Population</th>
                  <th className="px-4 py-3 text-right">Target Capacity</th>
                  <th className="px-4 py-3 text-right">Total Waste (30D)</th>
                  <th className="px-4 py-3 text-right">Avg Daily Waste</th>
                  <th className="px-4 py-3 text-right">Per-Capita (g/person)</th>
                  <th className="px-4 py-3 text-right">Capacity Util</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {wardPerf.map((w) => (
                  <tr key={w.ward_id} className="hover:bg-slate-800/40 transition-all">
                    <td className="px-4 py-3 font-semibold text-slate-100">{w.ward_name}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300">
                        {w.zone}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-slate-400">{w.population.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right text-slate-400">{w.target_capacity_kg.toLocaleString()} kg</td>
                    <td className="px-4 py-3 text-right font-semibold text-emerald-400">{w.total_waste_kg.toLocaleString()} kg</td>
                    <td className="px-4 py-3 text-right text-slate-200">{w.avg_daily_waste_kg.toLocaleString()} kg</td>
                    <td className="px-4 py-3 text-right font-bold text-purple-300">{w.avg_daily_per_capita_g} g</td>
                    <td className="px-4 py-3 text-right">
                      <span className={`font-semibold px-2 py-0.5 rounded text-[10px] ${
                        w.capacity_utilization_pct > 100 
                          ? 'bg-rose-500/20 text-rose-300' 
                          : 'bg-emerald-500/20 text-emerald-300'
                      }`}>
                        {w.capacity_utilization_pct}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100">Waste Category Composition Breakdown</h3>
            <span className="text-xs text-slate-400">Aggregated from dw.dim_waste_type</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Waste Category / Type</th>
                  <th className="px-4 py-3">Category Group</th>
                  <th className="px-4 py-3 text-right">Total Weight (kg)</th>
                  <th className="px-4 py-3 text-right">Total Weight (Tons)</th>
                  <th className="px-4 py-3 text-right">Composition Percentage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {composition.map((c) => (
                  <tr key={c.waste_type} className="hover:bg-slate-800/40 transition-all">
                    <td className="px-4 py-3 font-semibold text-slate-100">{c.waste_type}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300">
                        {c.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-cyan-400">{c.total_weight_kg.toLocaleString()} kg</td>
                    <td className="px-4 py-3 text-right text-slate-300">{(c.total_weight_kg / 1000.0).toFixed(2)} Tons</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-400">{c.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
