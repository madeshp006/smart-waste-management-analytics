import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Ward, ForecastResponse } from '../types';
import { 
  ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis, 
  Tooltip, CartesianGrid, Legend 
} from 'recharts';
import { BrainCircuit, Calendar, Cpu, TrendingUp, AlertTriangle, RefreshCw } from 'lucide-react';

export const PredictionView: React.FC = () => {
  const [wards, setWards] = useState<Ward[]>([]);
  const [selectedWardId, setSelectedWardId] = useState<number | null>(null);
  const [horizonDays, setHorizonDays] = useState<number>(30);
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchWards = async () => {
      try {
        const wList = await api.getWards();
        setWards(wList);
      } catch (err) {
        console.error('Failed to fetch wards:', err);
      }
    };
    fetchWards();
  }, []);

  const loadForecast = async () => {
    setLoading(true);
    try {
      const data = await api.getForecast(selectedWardId, horizonDays);
      setForecastData(data);
    } catch (err) {
      console.error('Forecast retrieval failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, [selectedWardId, horizonDays]);

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainMsg(null);
    try {
      const res: any = await api.retrainModel(selectedWardId);
      setRetrainMsg(res.message || 'Model retrained successfully!');
      await loadForecast();
    } catch (err: any) {
      setRetrainMsg(`Retraining failed: ${err.message}`);
    } finally {
      setRetraining(false);
    }
  };

  // Combine historical and forecast data for seamless Recharts line plot
  const combinedChartData = React.useMemo(() => {
    if (!forecastData) return [];
    
    const hist = forecastData.historical.map(h => ({
      date: h.date,
      actual_kg: h.actual_kg,
      predicted_kg: null as number | null,
      confidence_range: null as [number, number] | null,
      lower_bound_kg: null as number | null,
      upper_bound_kg: null as number | null
    }));

    const fc = forecastData.forecast.map(f => ({
      date: f.date,
      actual_kg: null as number | null,
      predicted_kg: f.predicted_kg,
      confidence_range: [f.lower_bound_kg, f.upper_bound_kg] as [number, number],
      lower_bound_kg: f.lower_bound_kg,
      upper_bound_kg: f.upper_bound_kg
    }));

    return [...hist, ...fc];
  }, [forecastData]);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-emerald-400" />
            Machine Learning Garbage Generation Prediction Engine
          </h2>
          <p className="text-xs text-slate-400">Time-series forecasting with 95% confidence intervals and feature engineering</p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Ward Select */}
          <div>
            <select
              value={selectedWardId || ''}
              onChange={(e) => setSelectedWardId(e.target.value ? Number(e.target.value) : null)}
              className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-medium text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">🌆 City-Wide (All Wards Aggregate)</option>
              {wards.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.code} - {w.name} ({w.zone})
                </option>
              ))}
            </select>
          </div>

          {/* Horizon Select */}
          <div className="flex items-center gap-1 p-1 bg-slate-900 rounded-xl border border-slate-800 text-xs font-medium">
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setHorizonDays(days)}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  horizonDays === days
                    ? 'bg-emerald-600 text-white font-semibold shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {days} Days
              </button>
            ))}
          </div>

          {/* Retrain Model Button */}
          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 text-xs font-semibold border border-slate-700 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${retraining ? 'animate-spin' : ''}`} />
            {retraining ? 'Retraining...' : 'Retrain ML Model'}
          </button>
        </div>
      </div>

      {retrainMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center justify-between">
          <span>{retrainMsg}</span>
          <button onClick={() => setRetrainMsg(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64 text-slate-400">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-medium">Executing Time-Series Feature Engineering & Model Prediction...</span>
          </div>
        </div>
      ) : forecastData ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs font-medium text-slate-400">Projected Total Waste</span>
              <div className="text-2xl font-extrabold text-emerald-400">
                {forecastData.summary.total_forecasted_tons.toLocaleString()} <span className="text-xs text-slate-400">Tons</span>
              </div>
              <p className="text-[11px] text-slate-400">Next {horizonDays} Days Forecast</p>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs font-medium text-slate-400">Daily Projected Average</span>
              <div className="text-2xl font-extrabold text-cyan-400">
                {forecastData.summary.avg_daily_forecasted_kg.toLocaleString()} <span className="text-xs text-slate-400">kg / day</span>
              </div>
              <p className="text-[11px] text-slate-400">Expected baseline generation</p>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs font-medium text-slate-400">Peak Predicted Day</span>
              <div className="text-xl font-extrabold text-amber-400 truncate">
                {forecastData.summary.peak_date}
              </div>
              <p className="text-[11px] text-slate-400">{forecastData.summary.peak_kg.toLocaleString()} kg peak generation</p>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-xs font-medium text-slate-400">Model Forecast Accuracy</span>
              <div className="text-2xl font-extrabold text-purple-400">
                {(100.0 - forecastData.metrics.mape_pct).toFixed(1)}% <span className="text-xs text-slate-400">Accuracy</span>
              </div>
              <p className="text-[11px] text-slate-400">MAPE: {forecastData.metrics.mape_pct}%</p>
            </div>
          </div>

          {/* Main Forecast Chart */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  Waste Generation Time-Series & Multi-Step Prediction
                </h3>
                <p className="text-xs text-slate-400">
                  Historical daily waste overlayed with ML forecast & 95% confidence interval band
                </p>
              </div>

              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-1 bg-cyan-400 rounded-full" />
                  <span className="text-slate-300">Historical Actuals</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-1 bg-emerald-400 rounded-full" />
                  <span className="text-slate-300">ML Forecast</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-emerald-500/20 rounded border border-emerald-500/40" />
                  <span className="text-slate-400">95% Confidence Band</span>
                </div>
              </div>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={combinedChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                    formatter={(value: any, name: string) => {
                      if (name === 'actual_kg' && value !== null) return [`${Number(value).toLocaleString()} kg`, 'Historical Actual'];
                      if (name === 'predicted_kg' && value !== null) return [`${Number(value).toLocaleString()} kg`, 'ML Forecast'];
                      if (name === 'upper_bound_kg' && value !== null) return [`${Number(value).toLocaleString()} kg`, 'Upper 95% Bound'];
                      if (name === 'lower_bound_kg' && value !== null) return [`${Number(value).toLocaleString()} kg`, 'Lower 95% Bound'];
                      return [value, name];
                    }}
                  />
                  {/* Confidence Interval Upper/Lower Area */}
                  <Area
                    type="monotone"
                    dataKey="upper_bound_kg"
                    stroke="none"
                    fill="url(#confidenceGradient)"
                    name="Upper Bound"
                  />
                  <Area
                    type="monotone"
                    dataKey="lower_bound_kg"
                    stroke="none"
                    fill="#0f172a"
                    fillOpacity={0.9}
                    name="Lower Bound"
                  />
                  {/* Actual Historical Line */}
                  <Line
                    type="monotone"
                    dataKey="actual_kg"
                    stroke="#06b6d4"
                    strokeWidth={2}
                    dot={false}
                    name="actual_kg"
                  />
                  {/* Forecast Line */}
                  <Line
                    type="monotone"
                    dataKey="predicted_kg"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    strokeDasharray="4 4"
                    dot={{ r: 3, fill: '#10b981' }}
                    name="predicted_kg"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model Metrics & Architecture Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <Cpu className="w-4 h-4 text-emerald-400" /> Model Architecture
              </div>
              <div className="text-sm font-bold text-slate-100">{forecastData.metrics.model_name}</div>
              <p className="text-xs text-slate-400">Random Forest Regressor with 100 decision trees, lag variables (t-1, t-7, t-14), and 7-day rolling window statistics.</p>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <Calendar className="w-4 h-4 text-cyan-400" /> Feature Engineering
              </div>
              <div className="text-xs text-slate-300 space-y-1">
                <div>• Day of week & weekend flag</div>
                <div>• Day of month & seasonal month index</div>
                <div>• Ward census population scaling</div>
                <div>• Historical lag & rolling window statistics</div>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <AlertTriangle className="w-4 h-4 text-purple-400" /> Evaluation Error Metrics
              </div>
              <div className="grid grid-cols-3 gap-2 text-center pt-1">
                <div className="p-2 rounded-xl bg-slate-900 border border-slate-800">
                  <div className="text-xs text-slate-400">MAE</div>
                  <div className="text-sm font-bold text-slate-200">{forecastData.metrics.mae} kg</div>
                </div>
                <div className="p-2 rounded-xl bg-slate-900 border border-slate-800">
                  <div className="text-xs text-slate-400">RMSE</div>
                  <div className="text-sm font-bold text-slate-200">{forecastData.metrics.rmse} kg</div>
                </div>
                <div className="p-2 rounded-xl bg-slate-900 border border-slate-800">
                  <div className="text-xs text-slate-400">MAPE</div>
                  <div className="text-sm font-bold text-slate-200">{forecastData.metrics.mape_pct}%</div>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
