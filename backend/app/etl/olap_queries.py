import os
import psycopg2
from typing import List, Dict, Any

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "waste_dw_db")
DB_USER = os.getenv("POSTGRES_USER", "waste_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "waste_password")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )

def query_waste_trend(start_date: str, end_date: str, ward_id: int = None, zone: str = None) -> List[Dict[str, Any]]:
    """OLAP Query 1: Waste generation trend over time (Daily / Monthly)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    where_clauses = ["d.full_date >= %s", "d.full_date <= %s"]
    params = [start_date, end_date]

    if ward_id:
        where_clauses.append("w.ward_id = %s")
        params.append(ward_id)
    if zone:
        where_clauses.append("w.zone = %s")
        params.append(zone)

    where_str = " AND ".join(where_clauses)

    sql = f"""
        SELECT 
            d.full_date,
            ROUND(SUM(f.weight_kg), 2) as total_weight_kg,
            ROUND(SUM(f.weight_kg) / 1000.0, 2) as total_weight_tons,
            SUM(f.collection_count) as total_collections,
            ROUND(AVG(f.per_capita_waste_g), 2) as avg_per_capita_g
        FROM dw.fact_waste_generation f
        JOIN dw.dim_date d ON f.date_key = d.date_key
        JOIN dw.dim_ward w ON f.ward_key = w.ward_key
        WHERE {where_str}
        GROUP BY d.full_date
        ORDER BY d.full_date ASC;
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "date": row[0].strftime("%Y-%m-%d"),
            "total_weight_kg": float(row[1]),
            "total_weight_tons": float(row[2]),
            "total_collections": int(row[3]),
            "avg_per_capita_g": float(row[4])
        }
        for row in rows
    ]

def query_waste_composition(start_date: str, end_date: str, ward_id: int = None, zone: str = None) -> List[Dict[str, Any]]:
    """OLAP Query 2: Waste composition breakdown by waste type & category."""
    conn = get_db_connection()
    cursor = conn.cursor()

    where_clauses = ["d.full_date >= %s", "d.full_date <= %s"]
    params = [start_date, end_date]

    if ward_id:
        where_clauses.append("w.ward_id = %s")
        params.append(ward_id)
    if zone:
        where_clauses.append("w.zone = %s")
        params.append(zone)

    where_str = " AND ".join(where_clauses)

    sql = f"""
        SELECT 
            t.waste_type_name,
            t.category,
            ROUND(SUM(f.weight_kg), 2) as total_weight_kg,
            ROUND((SUM(f.weight_kg) / NULLIF(SUM(SUM(f.weight_kg)) OVER(), 0)) * 100.0, 2) as percentage
        FROM dw.fact_waste_generation f
        JOIN dw.dim_date d ON f.date_key = d.date_key
        JOIN dw.dim_ward w ON f.ward_key = w.ward_key
        JOIN dw.dim_waste_type t ON f.waste_type_key = t.waste_type_key
        WHERE {where_str}
        GROUP BY t.waste_type_name, t.category
        ORDER BY total_weight_kg DESC;
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "waste_type": row[0],
            "category": row[1],
            "total_weight_kg": float(row[2]),
            "percentage": float(row[3]) if row[3] else 0.0
        }
        for row in rows
    ]

def query_ward_performance(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """OLAP Query 3: Ward performance and per-capita waste ranking."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT 
            w.ward_id,
            w.ward_name,
            w.zone,
            w.population,
            w.target_capacity_kg,
            ROUND(SUM(f.weight_kg), 2) as total_waste_kg,
            ROUND(AVG(f.per_capita_waste_g), 2) as avg_daily_per_capita_g,
            ROUND((SUM(f.weight_kg) / NULLIF(COUNT(DISTINCT d.full_date), 0)), 2) as avg_daily_waste_kg
        FROM dw.fact_waste_generation f
        JOIN dw.dim_date d ON f.date_key = d.date_key
        JOIN dw.dim_ward w ON f.ward_key = w.ward_key
        WHERE d.full_date >= %s AND d.full_date <= %s
        GROUP BY w.ward_id, w.ward_name, w.zone, w.population, w.target_capacity_kg
        ORDER BY total_waste_kg DESC;
    """

    cursor.execute(sql, [start_date, end_date])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "ward_id": row[0],
            "ward_name": row[1],
            "zone": row[2],
            "population": row[3],
            "target_capacity_kg": float(row[4]) if row[4] else 0.0,
            "total_waste_kg": float(row[5]),
            "avg_daily_per_capita_g": float(row[6]),
            "avg_daily_waste_kg": float(row[7]),
            "capacity_utilization_pct": round((float(row[7]) / float(row[4])) * 100.0, 1) if row[4] and float(row[4]) > 0 else 0.0
        }
        for row in rows
    ]

def query_seasonal_patterns(year: int = 2025) -> List[Dict[str, Any]]:
    """OLAP Query 4: Monthly seasonal waste generation patterns."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT 
            d.month,
            d.month_name,
            ROUND(SUM(f.weight_kg) / 1000.0, 2) as total_tons,
            ROUND(AVG(f.per_capita_waste_g), 2) as avg_per_capita_g
        FROM dw.fact_waste_generation f
        JOIN dw.dim_date d ON f.date_key = d.date_key
        WHERE d.year = %s
        GROUP BY d.month, d.month_name
        ORDER BY d.month ASC;
    """

    cursor.execute(sql, [year])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "month": row[0],
            "month_name": row[1],
            "total_tons": float(row[2]),
            "avg_per_capita_g": float(row[3])
        }
        for row in rows
    ]
