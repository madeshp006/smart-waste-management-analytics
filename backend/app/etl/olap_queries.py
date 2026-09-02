from typing import List, Dict, Any
from app.db.connection import get_db, execute_query

def query_waste_trend(start_date: str, end_date: str, ward_id: int = None, zone: str = None) -> List[Dict[str, Any]]:
    conn, engine_type = get_db()
    
    where_clauses = ["d.full_date >= %s", "d.full_date <= %s"]
    params = [start_date, end_date]

    if ward_id:
        where_clauses.append("w.ward_id = %s")
        params.append(ward_id)
    if zone:
        where_clauses.append("w.zone = %s")
        params.append(zone)

    where_str = " AND ".join(where_clauses)
    fact_table = "dw.fact_waste_generation" if engine_type == "postgres" else "fact_waste_generation"
    dim_date = "dw.dim_date" if engine_type == "postgres" else "dim_date"
    dim_ward = "dw.dim_ward" if engine_type == "postgres" else "dim_ward"

    sql = f"""
        SELECT 
            d.full_date,
            ROUND(SUM(f.weight_kg), 2) as total_weight_kg,
            ROUND(SUM(f.weight_kg) / 1000.0, 2) as total_weight_tons,
            SUM(f.collection_count) as total_collections,
            ROUND(AVG(f.per_capita_waste_g), 2) as avg_per_capita_g
        FROM {fact_table} f
        JOIN {dim_date} d ON f.date_key = d.date_key
        JOIN {dim_ward} w ON f.ward_key = w.ward_key
        WHERE {where_str}
        GROUP BY d.full_date
        ORDER BY d.full_date ASC;
    """

    rows = execute_query(sql, tuple(params), fetch="all")
    return [
        {
            "date": str(r["full_date"]),
            "total_weight_kg": float(r["total_weight_kg"]),
            "total_weight_tons": float(r["total_weight_tons"]),
            "total_collections": int(r["total_collections"]),
            "avg_per_capita_g": float(r["avg_per_capita_g"])
        }
        for r in rows
    ]

def query_waste_composition(start_date: str, end_date: str, ward_id: int = None, zone: str = None) -> List[Dict[str, Any]]:
    conn, engine_type = get_db()

    where_clauses = ["d.full_date >= %s", "d.full_date <= %s"]
    params = [start_date, end_date]

    if ward_id:
        where_clauses.append("w.ward_id = %s")
        params.append(ward_id)
    if zone:
        where_clauses.append("w.zone = %s")
        params.append(zone)

    where_str = " AND ".join(where_clauses)
    fact_table = "dw.fact_waste_generation" if engine_type == "postgres" else "fact_waste_generation"
    dim_date = "dw.dim_date" if engine_type == "postgres" else "dim_date"
    dim_ward = "dw.dim_ward" if engine_type == "postgres" else "dim_ward"
    dim_type = "dw.dim_waste_type" if engine_type == "postgres" else "dim_waste_type"

    sql = f"""
        SELECT 
            t.waste_type_name,
            t.category,
            ROUND(SUM(f.weight_kg), 2) as total_weight_kg
        FROM {fact_table} f
        JOIN {dim_date} d ON f.date_key = d.date_key
        JOIN {dim_ward} w ON f.ward_key = w.ward_key
        JOIN {dim_type} t ON f.waste_type_key = t.waste_type_key
        WHERE {where_str}
        GROUP BY t.waste_type_name, t.category
        ORDER BY total_weight_kg DESC;
    """

    rows = execute_query(sql, tuple(params), fetch="all")
    total_kg = sum(float(r["total_weight_kg"]) for r in rows) or 1.0

    return [
        {
            "waste_type": r["waste_type_name"],
            "category": r["category"],
            "total_weight_kg": float(r["total_weight_kg"]),
            "percentage": round((float(r["total_weight_kg"]) / total_kg) * 100.0, 2)
        }
        for r in rows
    ]

def query_ward_performance(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    conn, engine_type = get_db()
    fact_table = "dw.fact_waste_generation" if engine_type == "postgres" else "fact_waste_generation"
    dim_date = "dw.dim_date" if engine_type == "postgres" else "dim_date"
    dim_ward = "dw.dim_ward" if engine_type == "postgres" else "dim_ward"

    sql = f"""
        SELECT 
            w.ward_id,
            w.ward_name,
            w.zone,
            w.population,
            w.target_capacity_kg,
            ROUND(SUM(f.weight_kg), 2) as total_waste_kg,
            ROUND(AVG(f.per_capita_waste_g), 2) as avg_daily_per_capita_g,
            ROUND(SUM(f.weight_kg) / 30.0, 2) as avg_daily_waste_kg
        FROM {fact_table} f
        JOIN {dim_date} d ON f.date_key = d.date_key
        JOIN {dim_ward} w ON f.ward_key = w.ward_key
        WHERE d.full_date >= %s AND d.full_date <= %s
        GROUP BY w.ward_id, w.ward_name, w.zone, w.population, w.target_capacity_kg
        ORDER BY total_waste_kg DESC;
    """

    rows = execute_query(sql, (start_date, end_date), fetch="all")
    return [
        {
            "ward_id": r["ward_id"],
            "ward_name": r["ward_name"],
            "zone": r["zone"],
            "population": r["population"],
            "target_capacity_kg": float(r["target_capacity_kg"] or 0.0),
            "total_waste_kg": float(r["total_waste_kg"]),
            "avg_daily_per_capita_g": float(r["avg_daily_per_capita_g"]),
            "avg_daily_waste_kg": float(r["avg_daily_waste_kg"]),
            "capacity_utilization_pct": round((float(r["avg_daily_waste_kg"]) / float(r["target_capacity_kg"] or 50000.0)) * 100.0, 1)
        }
        for r in rows
    ]

def query_seasonal_patterns(year: int = 2025) -> List[Dict[str, Any]]:
    conn, engine_type = get_db()
    fact_table = "dw.fact_waste_generation" if engine_type == "postgres" else "fact_waste_generation"
    dim_date = "dw.dim_date" if engine_type == "postgres" else "dim_date"

    sql = f"""
        SELECT 
            d.month,
            d.month_name,
            ROUND(SUM(f.weight_kg) / 1000.0, 2) as total_tons,
            ROUND(AVG(f.per_capita_waste_g), 2) as avg_per_capita_g
        FROM {fact_table} f
        JOIN {dim_date} d ON f.date_key = d.date_key
        WHERE d.year = %s
        GROUP BY d.month, d.month_name
        ORDER BY d.month ASC;
    """

    rows = execute_query(sql, (year,), fetch="all")
    return [
        {
            "month": r["month"],
            "month_name": r["month_name"],
            "total_tons": float(r["total_tons"]),
            "avg_per_capita_g": float(r["avg_per_capita_g"])
        }
        for r in rows
    ]
