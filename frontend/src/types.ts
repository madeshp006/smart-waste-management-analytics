export type Role = 'Admin' | 'Ward_Officer' | 'Analyst';

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
  ward_id?: number | null;
  ward_name?: string | null;
}

export interface Ward {
  id: number;
  code: string;
  name: string;
  zone: string;
  target_capacity_kg: number;
  area_sq_km: number;
  current_population: number;
}

export interface WasteType {
  id: number;
  code: string;
  name: string;
  category: string;
  density_kg_m3: number;
}

export interface Vehicle {
  id: number;
  registration_number: string;
  vehicle_type: string;
  capacity_kg: number;
  status: string;
}

export interface CollectionRecord {
  id: number;
  collection_date: string;
  ward_id: number;
  ward_name: string;
  zone: string;
  collection_point_name?: string;
  waste_type_name: string;
  waste_category: string;
  vehicle_registration: string;
  weight_kg: number;
  created_at: string;
}

export interface PaginatedRecords {
  total: number;
  page: number;
  size: number;
  items: CollectionRecord[];
}

export interface DashboardKPIs {
  total_waste_collected_kg: number;
  total_waste_collected_tons: number;
  avg_daily_waste_kg: number;
  active_wards_count: number;
  avg_per_capita_waste_g: number;
  highest_waste_ward: string;
  etl_last_run: string;
}

export interface WasteTrendItem {
  date: string;
  total_weight_kg: number;
  total_weight_tons: number;
  total_collections: number;
  avg_per_capita_g: number;
}

export interface WasteCompositionItem {
  waste_type: string;
  category: string;
  total_weight_kg: number;
  percentage: number;
}

export interface WardPerformanceItem {
  ward_id: number;
  ward_name: string;
  zone: string;
  population: number;
  target_capacity_kg: number;
  total_waste_kg: number;
  avg_daily_per_capita_g: number;
  avg_daily_waste_kg: number;
  capacity_utilization_pct: number;
}

export interface ModelMetrics {
  model_name: string;
  mae: number;
  rmse: number;
  mape_pct: number;
  training_samples: number;
}

export interface ForecastSummary {
  total_forecasted_kg: number;
  total_forecasted_tons: number;
  avg_daily_forecasted_kg: number;
  peak_date: string;
  peak_kg: number;
}

export interface ForecastPoint {
  date: string;
  predicted_kg: number;
  lower_bound_kg: number;
  upper_bound_kg: number;
}

export interface HistoricalPoint {
  date: string;
  actual_kg: number;
}

export interface ForecastResponse {
  ward_id?: number | null;
  horizon_days: number;
  metrics: ModelMetrics;
  summary: ForecastSummary;
  historical: HistoricalPoint[];
  forecast: ForecastPoint[];
}
