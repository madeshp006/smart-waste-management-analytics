from typing import Optional, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
import psycopg2
import psycopg2.extras
from app.core.security import get_current_user, get_db_connection
from app.etl import olap_queries
from app.schemas.schemas import (
    DashboardKPIs, WasteTrendItem, WasteCompositionItem, WardPerformanceItem
)

router = APIRouter()

@router.get("/kpis", response_model=DashboardKPIs)
def get_dashboard_kpis(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1. Total waste collected & avg per day
    cursor.execute("""
        SELECT 
            COALESCE(SUM(weight_kg), 0) as total_kg,
            COALESCE(AVG(weight_kg), 0) as avg_kg,
            COUNT(DISTINCT collection_date) as active_days
        FROM public.waste_collection_records
        WHERE collection_date >= %s AND collection_date <= %s;
    """, (start_date, end_date))
    kpi_raw = cursor.fetchone()

    # 2. Ward count
    cursor.execute("SELECT COUNT(*) as cnt FROM public.wards;")
    ward_cnt = cursor.fetchone()["cnt"]

    # 3. Highest waste ward
    cursor.execute("""
        SELECT w.name, SUM(r.weight_kg) as total_kg
        FROM public.waste_collection_records r
        JOIN public.wards w ON r.ward_id = w.id
        WHERE r.collection_date >= %s AND r.collection_date <= %s
        GROUP BY w.name
        ORDER BY total_kg DESC LIMIT 1;
    """, (start_date, end_date))
    top_ward = cursor.fetchone()
    top_ward_name = top_ward["name"] if top_ward else "N/A"

    # 4. Avg per capita waste g
    cursor.execute("""
        SELECT AVG(per_capita_waste_g) as avg_g
        FROM dw.fact_waste_generation f
        JOIN dw.dim_date d ON f.date_key = d.date_key
        WHERE d.full_date >= %s AND d.full_date <= %s;
    """, (start_date, end_date))
    per_capita_row = cursor.fetchone()
    avg_per_capita = float(per_capita_row["avg_g"]) if per_capita_row and per_capita_row["avg_g"] else 485.5

    cursor.close()
    conn.close()

    total_kg = float(kpi_raw["total_kg"])
    active_days = max(1, kpi_raw["active_days"])

    return {
        "total_waste_collected_kg": round(total_kg, 2),
        "total_waste_collected_tons": round(total_kg / 1000.0, 2),
        "avg_daily_waste_kg": round(total_kg / active_days, 2),
        "active_wards_count": ward_cnt,
        "avg_per_capita_waste_g": round(avg_per_capita, 2),
        "highest_waste_ward": top_ward_name,
        "etl_last_run": "Synced to DW"
    }

@router.get("/trend", response_model=List[WasteTrendItem])
def get_waste_trend(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    ward_id: Optional[int] = None,
    zone: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=60)

    return olap_queries.query_waste_trend(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        ward_id=ward_id,
        zone=zone
    )

@router.get("/composition", response_model=List[WasteCompositionItem])
def get_waste_composition(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    ward_id: Optional[int] = None,
    zone: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    return olap_queries.query_waste_composition(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        ward_id=ward_id,
        zone=zone
    )

@router.get("/wards-performance", response_model=List[WardPerformanceItem])
def get_ward_performance(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    return olap_queries.query_ward_performance(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )

@router.get("/seasonal")
def get_seasonal_patterns(
    year: int = Query(2025),
    current_user: dict = Depends(get_current_user)
):
    return olap_queries.query_seasonal_patterns(year=year)
