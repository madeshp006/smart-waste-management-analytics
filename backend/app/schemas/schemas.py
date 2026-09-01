from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# Auth Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    ward_id: Optional[int] = None
    ward_name: Optional[str] = None

# Ward Schemas
class WardBase(BaseModel):
    code: str
    name: str
    zone: str
    target_capacity_kg: float = 50000.0
    area_sq_km: float = 15.5

class WardCreate(WardBase):
    pass

class WardOut(WardBase):
    id: int
    current_population: Optional[int] = 50000

# Waste Collection Record Schemas
class CollectionRecordCreate(BaseModel):
    collection_date: date
    ward_id: int
    collection_point_id: Optional[int] = None
    waste_type_id: int
    vehicle_id: int
    weight_kg: float = Field(..., gt=0)

class CollectionRecordOut(BaseModel):
    id: int
    collection_date: date
    ward_id: int
    ward_name: str
    zone: str
    collection_point_name: Optional[str] = None
    waste_type_name: str
    waste_category: str
    vehicle_registration: str
    weight_kg: float
    created_at: datetime

class PaginatedCollectionRecords(BaseModel):
    total: int
    page: int
    size: int
    items: List[CollectionRecordOut]

# Waste Type & Vehicle Schemas
class WasteTypeOut(BaseModel):
    id: int
    code: str
    name: str
    category: str
    density_kg_m3: float

class VehicleOut(BaseModel):
    id: int
    registration_number: str
    vehicle_type: str
    capacity_kg: float
    status: str

# Analytics Schemas
class DashboardKPIs(BaseModel):
    total_waste_collected_kg: float
    total_waste_collected_tons: float
    avg_daily_waste_kg: float
    active_wards_count: int
    avg_per_capita_waste_g: float
    highest_waste_ward: str
    etl_last_run: Optional[str] = "Up to date"

class WasteTrendItem(BaseModel):
    date: str
    total_weight_kg: float
    total_weight_tons: float
    total_collections: int
    avg_per_capita_g: float

class WasteCompositionItem(BaseModel):
    waste_type: str
    category: str
    total_weight_kg: float
    percentage: float

class WardPerformanceItem(BaseModel):
    ward_id: int
    ward_name: str
    zone: str
    population: int
    target_capacity_kg: float
    total_waste_kg: float
    avg_daily_per_capita_g: float
    avg_daily_waste_kg: float
    capacity_utilization_pct: float

# ML Forecast Schemas
class ModelMetrics(BaseModel):
    model_name: str
    mae: float
    rmse: float
    mape_pct: float
    training_samples: int

class ForecastSummary(BaseModel):
    total_forecasted_kg: float
    total_forecasted_tons: float
    avg_daily_forecasted_kg: float
    peak_date: str
    peak_kg: float

class ForecastPoint(BaseModel):
    date: str
    predicted_kg: float
    lower_bound_kg: float
    upper_bound_kg: float

class HistoricalPoint(BaseModel):
    date: str
    actual_kg: float

class ForecastResponse(BaseModel):
    ward_id: Optional[int]
    horizon_days: int
    metrics: ModelMetrics
    summary: ForecastSummary
    historical: List[HistoricalPoint]
    forecast: List[ForecastPoint]
