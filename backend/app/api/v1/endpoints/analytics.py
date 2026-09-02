from typing import Optional, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from app.core.security import get_current_user
from app.db.connection import get_db, execute_query
from app.etl import olap_queries
from app.schemas.schemas import DashboardKPIs, WasteTrendItem, WasteCompositionItem, WardPerformanceItem

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

    conn, engine_type = get_db()
    rec_table = "public.waste_collection_records" if engine_type == "postgres" else "waste_collection_records"
    wards_table = "public.wards" if engine_type == "postgres" else "wards"
    fact_table = "dw.fact_waste_generation" if engine_type == "postgres" else "fact_waste_generation"
    dim_date = "dw.dim_date" if engine_type == "postgres" else "dim_date"

    kpi_sql = f"""
        SELECT 
            COALESCE(SUM(weight_kg), 0) as total_kg,
            COUNT(DISTINCT collection_date) as active_days
        FROM {rec_table}
        WHERE collection_date >= %s AND collection_date <= %s;
    """
    kpi_raw = execute_query(kpi_sql, (str(start_date), str(end_date)), fetch="one")

    ward_cnt_row = execute_query(f"SELECT COUNT(*) as cnt FROM {wards_table};", fetch="one")
    ward_cnt = ward_cnt_row["cnt"] if ward_cnt_row else 15

    top_ward_sql = f"""
        SELECT w.name, SUM(r.weight_kg) as total_kg
        FROM {rec_table} r
        JOIN {wards_table} w ON r.ward_id = w.id
        WHERE r.collection_date >= %s AND r.collection_date <= %s
        GROUP BY w.name
        ORDER BY total_kg DESC LIMIT 1;
    """
    top_ward = execute_query(top_ward_sql, (str(start_date), str(end_date)), fetch="one")
    top_ward_name = top_ward["name"] if top_ward else "N/A"

    per_capita_sql = f"""
        SELECT AVG(per_capita_waste_g) as avg_g
        FROM {fact_table} f
        JOIN {dim_date} d ON f.date_key = d.date_key
        WHERE d.full_date >= %s AND d.full_date <= %s;
    """
    per_capita_row = execute_query(per_capita_sql, (str(start_date), str(end_date)), fetch="one")
    avg_per_capita = float(per_capita_row["avg_g"]) if per_capita_row and per_capita_row["avg_g"] else 485.5

    total_kg = float(kpi_raw["total_kg"]) if kpi_raw else 0.0
    active_days = max(1, kpi_raw["active_days"] if kpi_raw else 1)

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
