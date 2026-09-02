from typing import List
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.db.connection import get_db, execute_query
from app.schemas.schemas import WardOut, WasteTypeOut, VehicleOut

router = APIRouter()

@router.get("/wards", response_model=List[WardOut])
def get_wards(current_user: dict = Depends(get_current_user)):
    conn, engine_type = get_db()
    wards_table = "public.wards" if engine_type == "postgres" else "wards"
    census_table = "public.population_census" if engine_type == "postgres" else "population_census"

    sql = f"""
        SELECT 
            w.id, w.code, w.name, w.zone, 
            w.target_capacity_kg, 
            w.area_sq_km,
            COALESCE(c.population, 50000) as current_population
        FROM {wards_table} w
        LEFT JOIN {census_table} c ON w.id = c.ward_id AND c.year = 2026
        ORDER BY w.id ASC;
    """
    rows = execute_query(sql, fetch="all")
    return [
        {
            "id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "zone": r["zone"],
            "target_capacity_kg": float(r["target_capacity_kg"]),
            "area_sq_km": float(r["area_sq_km"]),
            "current_population": int(r["current_population"])
        }
        for r in rows
    ]

@router.get("/waste-types", response_model=List[WasteTypeOut])
def get_waste_types(current_user: dict = Depends(get_current_user)):
    conn, engine_type = get_db()
    table = "public.waste_types" if engine_type == "postgres" else "waste_types"
    rows = execute_query(f"SELECT id, code, name, category, density_kg_m3 FROM {table} ORDER BY id ASC;", fetch="all")
    return [
        {
            "id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "category": r["category"],
            "density_kg_m3": float(r["density_kg_m3"])
        }
        for r in rows
    ]

@router.get("/vehicles", response_model=List[VehicleOut])
def get_vehicles(current_user: dict = Depends(get_current_user)):
    conn, engine_type = get_db()
    table = "public.vehicles" if engine_type == "postgres" else "vehicles"
    rows = execute_query(f"SELECT id, registration_number, vehicle_type, capacity_kg, status FROM {table} ORDER BY id ASC;", fetch="all")
    return [
        {
            "id": r["id"],
            "registration_number": r["registration_number"],
            "vehicle_type": r["vehicle_type"],
            "capacity_kg": float(r["capacity_kg"]),
            "status": r["status"]
        }
        for r in rows
    ]
