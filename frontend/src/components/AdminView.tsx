import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Ward, WasteType, Vehicle, CollectionRecord } from '../types';
import { Sliders, PlusCircle, Database, RefreshCw, CheckCircle, AlertCircle, Layers } from 'lucide-react';

interface AdminViewProps {
  userRole: string;
}

export const AdminView: React.FC<AdminViewProps> = ({ userRole }) => {
  const [wards, setWards] = useState<Ward[]>([]);
  const [wasteTypes, setWasteTypes] = useState<WasteType[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [recentCollections, setRecentCollections] = useState<CollectionRecord[]>([]);

  // New Record Form State
  const [collectionDate, setCollectionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [selectedWardId, setSelectedWardId] = useState<number>(1);
  const [selectedWasteTypeId, setSelectedWasteTypeId] = useState<number>(1);
  const [selectedVehicleId, setSelectedVehicleId] = useState<number>(1);
  const [weightKg, setWeightKg] = useState<number>(1250.0);
  const [submitting, setSubmitting] = useState(false);
  const [formMsg, setFormMsg] = useState<string | null>(null);

  // ETL & ML Trigger State
  const [etlRunning, setEtlRunning] = useState(false);
  const [etlResult, setEtlResult] = useState<any>(null);

  const loadData = async () => {
    try {
      const [wList, wtList, vList, cList] = await Promise.all([
        api.getWards(),
        api.getWasteTypes(),
        api.getVehicles(),
        api.getCollections({ page: 1, size: 10 })
      ]);
      setWards(wList);
      setWasteTypes(wtList);
      setVehicles(vList);
      setRecentCollections(cList.items);
      if (wList.length > 0) setSelectedWardId(wList[0].id);
      if (wtList.length > 0) setSelectedWasteTypeId(wtList[0].id);
      if (vList.length > 0) setSelectedVehicleId(vList[0].id);
    } catch (err) {
      console.error('Failed to load admin entity data:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setFormMsg(null);
    try {
      await api.createCollection({
        collection_date: collectionDate,
        ward_id: selectedWardId,
        waste_type_id: selectedWasteTypeId,
        vehicle_id: selectedVehicleId,
        weight_kg: Number(weightKg)
      });
      setFormMsg('✅ Collection record logged successfully in OLTP database!');
      await loadData();
    } catch (err: any) {
      setFormMsg(`❌ Error logging collection record: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTriggerETL = async () => {
    setEtlRunning(true);
    setEtlResult(null);
    try {
      const res = await api.triggerETL(false);
      setEtlResult(res);
    } catch (err: any) {
      setEtlResult({ status: 'error', message: err.message });
    } finally {
      setEtlRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Sliders className="w-6 h-6 text-emerald-400" />
            Admin & Data Operations Control Panel
          </h2>
          <p className="text-xs text-slate-400">Log operational collection transactions and manage Data Warehouse ETL triggers</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form: Log New Waste Collection (1 Col) */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-100">
            <PlusCircle className="w-4 h-4 text-emerald-400" /> Log Waste Collection Transaction (OLTP)
          </div>

          {formMsg && (
            <div className={`p-3 rounded-xl text-xs ${
              formMsg.includes('✅') 
                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400' 
                : 'bg-rose-500/10 border border-rose-500/30 text-rose-400'
            }`}>
              {formMsg}
            </div>
          )}

          <form onSubmit={handleCreateCollection} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Collection Date</label>
              <input
                type="date"
                value={collectionDate}
                onChange={(e) => setCollectionDate(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Ward Location</label>
              <select
                value={selectedWardId}
                onChange={(e) => setSelectedWardId(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {wards.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.code} - {w.name} ({w.zone})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Waste Classification</label>
              <select
                value={selectedWasteTypeId}
                onChange={(e) => setSelectedWasteTypeId(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {wasteTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.code} - {t.name} ({t.category})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Assigned Vehicle</label>
              <select
                value={selectedVehicleId}
                onChange={(e) => setSelectedVehicleId(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {vehicles.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.registration_number} - {v.vehicle_type} ({v.capacity_kg}kg cap)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Measured Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                value={weightKg}
                onChange={(e) => setWeightKg(Number(e.target.value))}
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs shadow-lg shadow-emerald-950/40 transition-all flex items-center justify-center gap-2"
            >
              {submitting ? 'Submitting Record...' : 'Log Collection Record'}
            </button>
          </form>
        </div>

        {/* Data Warehouse ETL Pipeline Control (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Database className="w-4 h-4 text-purple-400" /> Data Warehouse ETL Sync Engine
                </h3>
                <p className="text-xs text-slate-400">Extracts OLTP transactions, transforms surrogate keys, and upserts dw.fact_waste_generation</p>
              </div>

              {userRole === 'Admin' && (
                <button
                  onClick={handleTriggerETL}
                  disabled={etlRunning}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-950/40 transition-all"
                >
                  <RefreshCw className={`w-4 h-4 ${etlRunning ? 'animate-spin' : ''}`} />
                  {etlRunning ? 'Executing ETL Pipeline...' : 'Run ETL Sync Now'}
                </button>
              )}
            </div>

            {etlResult && (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center gap-2 font-bold text-emerald-400">
                  <CheckCircle className="w-4 h-4" /> ETL Execution Result: {etlResult.status}
                </div>
                <div className="grid grid-cols-3 gap-2 text-slate-300 pt-1">
                  <div>Extract Rows: <span className="font-semibold text-slate-100">{etlResult.stats?.oltp_records_extracted || 0}</span></div>
                  <div>DW Fact Upserts: <span className="font-semibold text-slate-100">{etlResult.stats?.fact_rows_upserted || 0}</span></div>
                  <div>Duration: <span className="font-semibold text-slate-100">{etlResult.stats?.duration_seconds || 0}s</span></div>
                </div>
              </div>
            )}
          </div>

          {/* Recent Collection Transactions Table */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-slate-100">Recent OLTP Waste Collection Transactions</h3>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Ward</th>
                    <th className="px-3 py-2">Waste Category</th>
                    <th className="px-3 py-2">Vehicle</th>
                    <th className="px-3 py-2 text-right">Weight (kg)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {recentCollections.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/40">
                      <td className="px-3 py-2 text-slate-400">{c.collection_date}</td>
                      <td className="px-3 py-2 font-medium text-slate-200">{c.ward_name}</td>
                      <td className="px-3 py-2 text-emerald-400">{c.waste_type_name}</td>
                      <td className="px-3 py-2 text-slate-400">{c.vehicle_registration}</td>
                      <td className="px-3 py-2 text-right font-bold text-slate-100">{c.weight_kg} kg</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
