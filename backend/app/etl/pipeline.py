import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "waste_dw_db")
DB_USER = os.getenv("POSTGRES_USER", "waste_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "waste_password")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def populate_dim_date(conn, start_year=2024, end_year=2027):
    """Populates dw.dim_date dimension table for given year range."""
    cursor = conn.cursor()
    logging.info(f"Populating dw.dim_date from {start_year} to {end_year}...")
    
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    curr_date = start_date

    date_rows = []
    # Indian / International major holidays list for demo
    holidays = {
        (1, 26), (8, 15), (10, 2), (10, 24), (11, 1), (12, 25), (1, 1)
    }

    while curr_date <= end_date:
        date_key = int(curr_date.strftime("%Y%m%d"))
        full_date = curr_date.date()
        day_of_week = curr_date.isoweekday() # 1=Mon, 7=Sun
        day_name = curr_date.strftime("%A")
        day_of_month = curr_date.day
        month = curr_date.month
        month_name = curr_date.strftime("%B")
        quarter = (curr_date.month - 1) // 3 + 1
        year = curr_date.year
        is_weekend = day_of_week in (6, 7)
        is_holiday = (month, day_of_month) in holidays

        date_rows.append((
            date_key, full_date, day_of_week, day_name, day_of_month,
            month, month_name, quarter, year, is_weekend, is_holiday
        ))
        curr_date += timedelta(days=1)

    execute_batch(cursor, """
        INSERT INTO dw.dim_date (date_key, full_date, day_of_week, day_name, day_of_month, month, month_name, quarter, year, is_weekend, is_holiday)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date_key) DO NOTHING;
    """, date_rows)
    conn.commit()
    cursor.close()
    logging.info(f"✅ dw.dim_date updated successfully ({len(date_rows)} total date entries).")

def sync_dimension_tables(conn):
    """Syncs OLTP wards, waste types, and vehicles into DW dimension tables."""
    cursor = conn.cursor()
    logging.info("Syncing OLTP entity tables into dw.dim_ward, dw.dim_waste_type, dw.dim_vehicle...")

    # Sync Wards
    cursor.execute("""
        INSERT INTO dw.dim_ward (ward_id, ward_name, zone, area_sq_km, population, target_capacity_kg)
        SELECT 
            w.id, 
            w.name, 
            w.zone, 
            w.area_sq_km, 
            COALESCE(c.population, 50000) as population,
            w.target_capacity_kg
        FROM public.wards w
        LEFT JOIN public.population_census c ON w.id = c.ward_id AND c.year = 2026
        ON CONFLICT (ward_id) DO UPDATE SET
            ward_name = EXCLUDED.ward_name,
            zone = EXCLUDED.zone,
            area_sq_km = EXCLUDED.area_sq_km,
            population = EXCLUDED.population,
            target_capacity_kg = EXCLUDED.target_capacity_kg;
    """)

    # Sync Waste Types
    cursor.execute("""
        INSERT INTO dw.dim_waste_type (waste_type_id, waste_type_name, category, density_kg_m3)
        SELECT id, name, category, density_kg_m3
        FROM public.waste_types
        ON CONFLICT (waste_type_id) DO UPDATE SET
            waste_type_name = EXCLUDED.waste_type_name,
            category = EXCLUDED.category,
            density_kg_m3 = EXCLUDED.density_kg_m3;
    """)

    # Sync Vehicles
    cursor.execute("""
        INSERT INTO dw.dim_vehicle (vehicle_id, registration_number, vehicle_type, capacity_kg)
        SELECT id, registration_number, vehicle_type, capacity_kg
        FROM public.vehicles
        ON CONFLICT (vehicle_id) DO UPDATE SET
            registration_number = EXCLUDED.registration_number,
            vehicle_type = EXCLUDED.vehicle_type,
            capacity_kg = EXCLUDED.capacity_kg;
    """)

    conn.commit()
    cursor.close()
    logging.info("✅ DW Dimension tables synced successfully.")

def run_etl_pipeline(incremental: bool = False):
    """
    Executes ETL pipeline:
    Extracts raw collection transactions from OLTP 'public' schema.
    Transforms data (joins with dimensions, calculates per-capita waste g/person/day).
    Loads transformed aggregations into DW 'dw.fact_waste_generation' star schema.
    """
    start_time = datetime.now()
    logging.info(f"Starting ETL Pipeline run (Incremental={incremental})...")
    conn = get_db_connection()

    try:
        # 1. Ensure dimensions are initialized
        populate_dim_date(conn)
        sync_dimension_tables(conn)

        # 2. Extract OLTP data into Pandas DataFrame
        extract_query = """
            SELECT 
                r.collection_date,
                r.ward_id,
                r.waste_type_id,
                r.vehicle_id,
                r.weight_kg,
                EXTRACT(YEAR FROM r.collection_date)::INT as year
            FROM public.waste_collection_records r;
        """
        logging.info("Extracting collection transactions from OLTP...")
        df_records = pd.read_sql(extract_query, conn)

        if df_records.empty:
            logging.warning("No records found in OLTP database to process.")
            return {"status": "warning", "message": "No records found", "rows_processed": 0}

        # Extract Census Population mapping (ward_id, year -> population)
        census_query = "SELECT ward_id, year, population FROM public.population_census;"
        df_census = pd.read_sql(census_query, conn)

        # Extract Dimension Surrogate Key Mappings
        df_dim_ward = pd.read_sql("SELECT ward_key, ward_id FROM dw.dim_ward;", conn)
        df_dim_waste = pd.read_sql("SELECT waste_type_key, waste_type_id FROM dw.dim_waste_type;", conn)
        df_dim_vehicle = pd.read_sql("SELECT vehicle_key, vehicle_id FROM dw.dim_vehicle;", conn)

        # 3. Transform Data
        df_records["date_key"] = df_records["collection_date"].apply(lambda d: int(d.strftime("%Y%m%d")))
        
        # Merge with Census for per-capita calculations
        df_merged = pd.merge(df_records, df_census, on=["ward_id", "year"], how="left")
        df_merged["population"] = df_merged["population"].fillna(50000)

        # Merge with DW Dimension Surrogate Keys
        df_merged = pd.merge(df_merged, df_dim_ward, on="ward_id", how="inner")
        df_merged = pd.merge(df_merged, df_dim_waste, on="waste_type_id", how="inner")
        df_merged = pd.merge(df_merged, df_dim_vehicle, on="vehicle_id", how="inner")

        # Aggregate at the Fact Table grain: (date_key, ward_key, waste_type_key, vehicle_key)
        df_fact = df_merged.groupby(
            ["date_key", "ward_key", "waste_type_key", "vehicle_key", "population"]
        ).agg(
            weight_kg=("weight_kg", "sum"),
            collection_count=("weight_kg", "count")
        ).reset_index()

        # Compute per-capita waste generation in grams per person: (weight_kg * 1000) / population
        df_fact["per_capita_waste_g"] = (df_fact["weight_kg"] * 1000.0) / df_fact["population"]
        df_fact["per_capita_waste_g"] = df_fact["per_capita_waste_g"].round(2)
        df_fact["weight_kg"] = df_fact["weight_kg"].round(2)

        # Prepare tuples for bulk loading
        fact_tuples = [
            (
                int(row["date_key"]),
                int(row["ward_key"]),
                int(row["waste_type_key"]),
                int(row["vehicle_key"]),
                float(row["weight_kg"]),
                int(row["collection_count"]),
                float(row["per_capita_waste_g"])
            )
            for _, row in df_fact.iterrows()
        ]

        # 4. Load into DW Fact Table
        cursor = conn.cursor()
        logging.info(f"Loading {len(fact_tuples)} aggregated rows into dw.fact_waste_generation...")

        upsert_query = """
            INSERT INTO dw.fact_waste_generation 
            (date_key, ward_key, waste_type_key, vehicle_key, weight_kg, collection_count, per_capita_waste_g)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date_key, ward_key, waste_type_key, vehicle_key) 
            DO UPDATE SET
                weight_kg = EXCLUDED.weight_kg,
                collection_count = EXCLUDED.collection_count,
                per_capita_waste_g = EXCLUDED.per_capita_waste_g;
        """

        execute_batch(cursor, upsert_query, fact_tuples, page_size=2000)
        conn.commit()
        cursor.close()

        duration = (datetime.now() - start_time).total_seconds()
        logging.info(f"🎉 ETL completed in {duration:.2f} seconds. Processed {len(fact_tuples)} DW fact records.")

        return {
            "status": "success",
            "duration_seconds": round(duration, 2),
            "oltp_records_extracted": len(df_records),
            "fact_rows_upserted": len(fact_tuples)
        }

    except Exception as e:
        conn.rollback()
        logging.error(f"❌ ETL Pipeline Error: {str(e)}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    run_etl_pipeline()
