import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from app.db.connection import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def populate_dim_date(conn, engine_type="postgres", start_year=2024, end_year=2027):
    cursor = conn.cursor()
    p = "%s" if engine_type == "postgres" else "?"
    table = "dw.dim_date" if engine_type == "postgres" else "dim_date"

    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    curr_date = start_date

    date_rows = []
    holidays = {(1, 26), (8, 15), (10, 2), (10, 24), (11, 1), (12, 25), (1, 1)}

    while curr_date <= end_date:
        date_key = int(curr_date.strftime("%Y%m%d"))
        full_date = curr_date.strftime("%Y-%m-%d") if engine_type == "sqlite" else curr_date.date()
        day_of_week = curr_date.isoweekday()
        day_name = curr_date.strftime("%A")
        day_of_month = curr_date.day
        month = curr_date.month
        month_name = curr_date.strftime("%B")
        quarter = (curr_date.month - 1) // 3 + 1
        year = curr_date.year
        is_weekend = 1 if day_of_week in (6, 7) else 0
        is_holiday = 1 if (month, day_of_month) in holidays else 0

        date_rows.append((
            date_key, full_date, day_of_week, day_name, day_of_month,
            month, month_name, quarter, year, is_weekend, is_holiday
        ))
        curr_date += timedelta(days=1)

    insert_sql = f"""
        INSERT OR IGNORE INTO {table} (date_key, full_date, day_of_week, day_name, day_of_month, month, month_name, quarter, year, is_weekend, is_holiday)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p});
    """ if engine_type == "sqlite" else f"""
        INSERT INTO {table} (date_key, full_date, day_of_week, day_name, day_of_month, month, month_name, quarter, year, is_weekend, is_holiday)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
        ON CONFLICT (date_key) DO NOTHING;
    """

    cursor.executemany(insert_sql, date_rows)
    conn.commit()
    cursor.close()

def sync_dimension_tables(conn, engine_type="postgres"):
    cursor = conn.cursor()
    if engine_type == "sqlite":
        cursor.execute("INSERT OR REPLACE INTO dim_ward (ward_id, ward_name, zone, area_sq_km, population, target_capacity_kg) SELECT w.id, w.name, w.zone, w.area_sq_km, COALESCE(c.population, 50000), w.target_capacity_kg FROM wards w LEFT JOIN population_census c ON w.id = c.ward_id AND c.year = 2026;")
        cursor.execute("INSERT OR REPLACE INTO dim_waste_type (waste_type_id, waste_type_name, category, density_kg_m3) SELECT id, name, category, density_kg_m3 FROM waste_types;")
        cursor.execute("INSERT OR REPLACE INTO dim_vehicle (vehicle_id, registration_number, vehicle_type, capacity_kg) SELECT id, registration_number, vehicle_type, capacity_kg FROM vehicles;")
    else:
        cursor.execute("INSERT INTO dw.dim_ward (ward_id, ward_name, zone, area_sq_km, population, target_capacity_kg) SELECT w.id, w.name, w.zone, w.area_sq_km, COALESCE(c.population, 50000), w.target_capacity_kg FROM public.wards w LEFT JOIN public.population_census c ON w.id = c.ward_id AND c.year = 2026 ON CONFLICT (ward_id) DO UPDATE SET ward_name = EXCLUDED.ward_name, zone = EXCLUDED.zone, area_sq_km = EXCLUDED.area_sq_km, population = EXCLUDED.population, target_capacity_kg = EXCLUDED.target_capacity_kg;")
        cursor.execute("INSERT INTO dw.dim_waste_type (waste_type_id, waste_type_name, category, density_kg_m3) SELECT id, name, category, density_kg_m3 FROM public.waste_types ON CONFLICT (waste_type_id) DO UPDATE SET waste_type_name = EXCLUDED.waste_type_name, category = EXCLUDED.category, density_kg_m3 = EXCLUDED.density_kg_m3;")
        cursor.execute("INSERT INTO dw.dim_vehicle (vehicle_id, registration_number, vehicle_type, capacity_kg) SELECT id, registration_number, vehicle_type, capacity_kg FROM public.vehicles ON CONFLICT (vehicle_id) DO UPDATE SET registration_number = EXCLUDED.registration_number, vehicle_type = EXCLUDED.vehicle_type, capacity_kg = EXCLUDED.capacity_kg;")
    conn.commit()
    cursor.close()

def run_etl_pipeline(incremental: bool = False):
    start_time = datetime.now()
    conn, engine_type = get_db()

    try:
        populate_dim_date(conn, engine_type)
        sync_dimension_tables(conn, engine_type)

        rec_table = "waste_collection_records" if engine_type == "sqlite" else "public.waste_collection_records"
        census_table = "population_census" if engine_type == "sqlite" else "public.population_census"
        dim_ward_table = "dim_ward" if engine_type == "sqlite" else "dw.dim_ward"
        dim_waste_table = "dim_waste_type" if engine_type == "sqlite" else "dw.dim_waste_type"
        dim_vehicle_table = "dim_vehicle" if engine_type == "sqlite" else "dw.dim_vehicle"

        extract_query = f"SELECT collection_date, ward_id, waste_type_id, vehicle_id, weight_kg, strftime('%Y', collection_date) as year FROM {rec_table};" if engine_type == "sqlite" else f"SELECT r.collection_date, r.ward_id, r.waste_type_id, r.vehicle_id, r.weight_kg, EXTRACT(YEAR FROM r.collection_date)::INT as year FROM {rec_table} r;"
        df_records = pd.read_sql(extract_query, conn)

        if df_records.empty:
            return {"status": "warning", "message": "No records found", "rows_processed": 0}

        df_records["year"] = df_records["year"].astype(int)
        df_census = pd.read_sql(f"SELECT ward_id, year, population FROM {census_table};", conn)
        df_census["year"] = df_census["year"].astype(int)

        df_dim_ward = pd.read_sql(f"SELECT ward_key, ward_id FROM {dim_ward_table};", conn)
        df_dim_waste = pd.read_sql(f"SELECT waste_type_key, waste_type_id FROM {dim_waste_table};", conn)
        df_dim_vehicle = pd.read_sql(f"SELECT vehicle_key, vehicle_id FROM {dim_vehicle_table};", conn)

        df_records["date_key"] = pd.to_datetime(df_records["collection_date"]).dt.strftime("%Y%m%d").astype(int)
        
        df_merged = pd.merge(df_records, df_census, on=["ward_id", "year"], how="left")
        df_merged["population"] = df_merged["population"].fillna(50000)

        df_merged = pd.merge(df_merged, df_dim_ward, on="ward_id", how="inner")
        df_merged = pd.merge(df_merged, df_dim_waste, on="waste_type_id", how="inner")
        df_merged = pd.merge(df_merged, df_dim_vehicle, on="vehicle_id", how="inner")

        df_fact = df_merged.groupby(["date_key", "ward_key", "waste_type_key", "vehicle_key", "population"]).agg(
            weight_kg=("weight_kg", "sum"),
            collection_count=("weight_kg", "count")
        ).reset_index()

        df_fact["per_capita_waste_g"] = ((df_fact["weight_kg"] * 1000.0) / df_fact["population"]).round(2)
        df_fact["weight_kg"] = df_fact["weight_kg"].round(2)

        fact_tuples = [
            (int(row["date_key"]), int(row["ward_key"]), int(row["waste_type_key"]), int(row["vehicle_key"]), float(row["weight_kg"]), int(row["collection_count"]), float(row["per_capita_waste_g"]))
            for _, row in df_fact.iterrows()
        ]

        cursor = conn.cursor()
        p = "%s" if engine_type == "postgres" else "?"
        fact_table = "dw.fact_waste_generation" if engine_type == "postgres" else "fact_waste_generation"

        upsert_query = f"INSERT OR REPLACE INTO {fact_table} (date_key, ward_key, waste_type_key, vehicle_key, weight_kg, collection_count, per_capita_waste_g) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p});" if engine_type == "sqlite" else f"INSERT INTO {fact_table} (date_key, ward_key, waste_type_key, vehicle_key, weight_kg, collection_count, per_capita_waste_g) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}) ON CONFLICT (date_key, ward_key, waste_type_key, vehicle_key) DO UPDATE SET weight_kg = EXCLUDED.weight_kg, collection_count = EXCLUDED.collection_count, per_capita_waste_g = EXCLUDED.per_capita_waste_g;"

        cursor.executemany(upsert_query, fact_tuples)
        conn.commit()
        cursor.close()

        duration = (datetime.now() - start_time).total_seconds()
        return {"status": "success", "duration_seconds": round(duration, 2), "oltp_records_extracted": len(df_records), "fact_rows_upserted": len(fact_tuples)}

    except Exception as e:
        conn.rollback()
        logging.error(f"ETL Error: {str(e)}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    run_etl_pipeline()
