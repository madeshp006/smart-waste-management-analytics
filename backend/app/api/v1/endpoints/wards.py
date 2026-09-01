from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
import psycopg2
import psycopg2.extras
from app.core.security import get_current_user, get_db_connection
from app.schemas.schemas import WardOut, WasteTypeOut, VehicleOut

router = APIRouter()

@router.get("/wards", response_model=List[WardOut])
def get_wards(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT 
            w.id, w.code, w.name, w.zone, 
            CAST(w.target_capacity_kg AS FLOAT) as target_capacity_kg, 
            CAST(w.area_sq_km AS FLOAT) as area_sq_km,
            COALESCE(c.population, 50000) as current_population
        FROM public.wards w
        LEFT JOIN public.population_census c ON w.id = c.ward_id AND c.year = 2026
        ORDER BY w.id ASC;
    """)
    wards = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(w) for w in wards]

@router.get("/waste-types", response_model=List[WasteTypeOut])
def get_waste_types(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id, code, name, category, CAST(density_kg_m3 AS FLOAT) as density_kg_m3
        FROM public.waste_types
        ORDER BY id ASC;
    """)
    types = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(t) for t in types]

@router.get("/vehicles", response_model=List[VehicleOut])
def get_vehicles(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id, registration_number, vehicle_type, CAST(capacity_kg AS FLOAT) as capacity_kg, status
        FROM public.vehicles
        ORDER BY id ASC;
    """)
    vehicles = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(v) for v in vehicles]
