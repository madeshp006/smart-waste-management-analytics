import { 
  User, Ward, WasteType, Vehicle, PaginatedRecords, 
  DashboardKPIs, WasteTrendItem, WasteCompositionItem, 
  WardPerformanceItem, ForecastResponse 
} from '../types';

const API_BASE = '/api/v1';

export const getAuthToken = (): string | null => {
  return localStorage.getItem('waste_app_token');
};

export const setAuthToken = (token: string) => {
  localStorage.setItem('waste_app_token', token);
};

export const removeAuthToken = () => {
  localStorage.removeItem('waste_app_token');
};

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeAuthToken();
    window.location.reload();
    throw new Error('Unauthorized. Please log in again.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || 'API request failed');
  }

  return response.json();
}

export const api = {
  // Auth
  login: async (username: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setAuthToken(data.access_token);
    return data;
  },

  getCurrentUser: () => fetchAPI<User>('/auth/me'),

  // Entities
  getWards: () => fetchAPI<Ward[]>('/wards'),
  getWasteTypes: () => fetchAPI<WasteType[]>('/waste-types'),
  getVehicles: () => fetchAPI<Vehicle[]>('/vehicles'),

  // Collection Records (OLTP)
  getCollections: (params: { page?: number; size?: number; ward_id?: number; waste_type_id?: number; start_date?: string; end_date?: string }) => {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page.toString());
    if (params.size) query.append('size', params.size.toString());
    if (params.ward_id) query.append('ward_id', params.ward_id.toString());
    if (params.waste_type_id) query.append('waste_type_id', params.waste_type_id.toString());
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    return fetchAPI<PaginatedRecords>(`/collections?${query.toString()}`);
  },

  createCollection: (data: { collection_date: string; ward_id: number; waste_type_id: number; vehicle_id: number; weight_kg: number }) => {
    return fetchAPI('/collections', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // OLAP DW Analytics
  getKPIs: (startDate?: string, endDate?: string) => {
    const query = new URLSearchParams();
    if (startDate) query.append('start_date', startDate);
    if (endDate) query.append('end_date', endDate);
    return fetchAPI<DashboardKPIs>(`/analytics/kpis?${query.toString()}`);
  },

  getTrend: (params: { start_date?: string; end_date?: string; ward_id?: number; zone?: string }) => {
    const query = new URLSearchParams();
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    if (params.ward_id) query.append('ward_id', params.ward_id.toString());
    if (params.zone) query.append('zone', params.zone);
    return fetchAPI<WasteTrendItem[]>(`/analytics/trend?${query.toString()}`);
  },

  getComposition: (params: { start_date?: string; end_date?: string; ward_id?: number; zone?: string }) => {
    const query = new URLSearchParams();
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    if (params.ward_id) query.append('ward_id', params.ward_id.toString());
    if (params.zone) query.append('zone', params.zone);
    return fetchAPI<WasteCompositionItem[]>(`/analytics/composition?${query.toString()}`);
  },

  getWardPerformance: (startDate?: string, endDate?: string) => {
    const query = new URLSearchParams();
    if (startDate) query.append('start_date', startDate);
    if (endDate) query.append('end_date', endDate);
    return fetchAPI<WardPerformanceItem[]>(`/analytics/wards-performance?${query.toString()}`);
  },

  // ML Predictions
  getForecast: (wardId?: number | null, horizonDays: number = 30) => {
    const query = new URLSearchParams();
    if (wardId) query.append('ward_id', wardId.toString());
    query.append('horizon_days', horizonDays.toString());
    return fetchAPI<ForecastResponse>(`/predictions/forecast?${query.toString()}`);
  },

  retrainModel: (wardId?: number | null) => {
    const query = new URLSearchParams();
    if (wardId) query.append('ward_id', wardId.toString());
    return fetchAPI(`/predictions/retrain?${query.toString()}`, { method: 'POST' });
  },

  // Admin & ETL
  triggerETL: (incremental: boolean = False) => {
    return fetchAPI(`/admin/run-etl?incremental=${incremental}`, { method: 'POST' });
  }
};
