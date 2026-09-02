import os
import random
import sys
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "waste_dw_db")
DB_USER = os.getenv("POSTGRES_USER", "waste_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "waste_password")

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "waste_dw.db")

def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=2
        )
        return conn, "postgres"
    except Exception as e:
        print(f"Could not connect to PostgreSQL. Initializing local SQLite database at: {SQLITE_PATH}")
        conn = sqlite3.connect(SQLITE_PATH)
        return conn, "sqlite"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def init_sqlite_tables(conn):
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS wards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            zone TEXT NOT NULL,
            target_capacity_kg REAL NOT NULL DEFAULT 50000.00,
            area_sq_km REAL NOT NULL DEFAULT 15.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL,
            ward_id INTEGER REFERENCES wards(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS population_census (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER NOT NULL REFERENCES wards(id) ON DELETE CASCADE,
            year INTEGER NOT NULL,
            population INTEGER NOT NULL,
            growth_rate REAL DEFAULT 1.5,
            UNIQUE(ward_id, year)
        );

        CREATE TABLE IF NOT EXISTS waste_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            density_kg_m3 REAL DEFAULT 300.00
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_number TEXT UNIQUE NOT NULL,
            vehicle_type TEXT NOT NULL,
            capacity_kg REAL NOT NULL DEFAULT 8000.00,
            status TEXT DEFAULT 'Active'
        );

        CREATE TABLE IF NOT EXISTS collection_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER NOT NULL REFERENCES wards(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            bin_capacity_kg REAL NOT NULL DEFAULT 2000.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS waste_collection_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_date TEXT NOT NULL,
            ward_id INTEGER NOT NULL REFERENCES wards(id),
            collection_point_id INTEGER REFERENCES collection_points(id),
            waste_type_id INTEGER NOT NULL REFERENCES waste_types(id),
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            weight_kg REAL NOT NULL,
            collected_by_user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- DW Star Schema Tables
        CREATE TABLE IF NOT EXISTS dim_date (
            date_key INTEGER PRIMARY KEY,
            full_date TEXT UNIQUE NOT NULL,
            day_of_week INTEGER NOT NULL,
            day_name TEXT NOT NULL,
            day_of_month INTEGER NOT NULL,
            month INTEGER NOT NULL,
            month_name TEXT NOT NULL,
            quarter INTEGER NOT NULL,
            year INTEGER NOT NULL,
            is_weekend INTEGER NOT NULL,
            is_holiday INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS dim_ward (
            ward_key INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER NOT NULL UNIQUE,
            ward_name TEXT NOT NULL,
            zone TEXT NOT NULL,
            area_sq_km REAL,
            population INTEGER DEFAULT 0,
            target_capacity_kg REAL
        );

        CREATE TABLE IF NOT EXISTS dim_waste_type (
            waste_type_key INTEGER PRIMARY KEY AUTOINCREMENT,
            waste_type_id INTEGER NOT NULL UNIQUE,
            waste_type_name TEXT NOT NULL,
            category TEXT NOT NULL,
            density_kg_m3 REAL
        );

        CREATE TABLE IF NOT EXISTS dim_vehicle (
            vehicle_key INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL UNIQUE,
            registration_number TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            capacity_kg REAL
        );

        CREATE TABLE IF NOT EXISTS fact_waste_generation (
            fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
            ward_key INTEGER NOT NULL REFERENCES dim_ward(ward_key),
            waste_type_key INTEGER NOT NULL REFERENCES dim_waste_type(waste_type_key),
            vehicle_key INTEGER NOT NULL REFERENCES dim_vehicle(vehicle_key),
            weight_kg REAL NOT NULL DEFAULT 0,
            collection_count INTEGER NOT NULL DEFAULT 1,
            per_capita_waste_g REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (date_key, ward_key, waste_type_key, vehicle_key)
        );
    """)
    conn.commit()
    cursor.close()

def seed_database():
    print("Initializing municipal dataset...")
    conn, engine_type = get_connection()
    
    if engine_type == "sqlite":
        init_sqlite_tables(conn)

    cursor = conn.cursor()

    # 1. Wards Data
    wards = [
        ("W01", "Civic Center", "North Zone", 65000, 12.4),
        ("W02", "Industrial Haven", "North Zone", 42000, 18.2),
        ("W03", "Green Park", "North Zone", 58000, 15.0),
        ("W04", "Highland Heights", "North Zone", 49000, 11.5),
        ("W05", "Bayview Shores", "South Zone", 75000, 14.8),
        ("W06", "Tech Corridor", "South Zone", 92000, 22.0),
        ("W07", "Riverside", "South Zone", 68000, 13.5),
        ("W08", "Southern Palms", "South Zone", 53000, 16.1),
        ("W09", "Eastside Market", "East Zone", 81000, 10.5),
        ("W10", "Sunrise Colony", "East Zone", 60000, 14.0),
        ("W11", "University Hub", "East Zone", 78000, 12.8),
        ("W12", "Heritage Quarter", "East Zone", 51000, 9.2),
        ("W13", "Westend Commercial", "West Zone", 105000, 25.0),
        ("W14", "Suburban Meadow", "West Zone", 46000, 19.5),
        ("W15", "Valley Springs", "West Zone", 39000, 17.0),
    ]

    p = "%s" if engine_type == "postgres" else "?"

    cursor.execute("DELETE FROM waste_collection_records;" if engine_type == "sqlite" else "DELETE FROM public.waste_collection_records;")
    cursor.execute("DELETE FROM population_census;" if engine_type == "sqlite" else "DELETE FROM public.population_census;")
    cursor.execute("DELETE FROM collection_points;" if engine_type == "sqlite" else "DELETE FROM public.collection_points;")
    cursor.execute("DELETE FROM users;" if engine_type == "sqlite" else "DELETE FROM public.users;")
    cursor.execute("DELETE FROM vehicles;" if engine_type == "sqlite" else "DELETE FROM public.vehicles;")
    cursor.execute("DELETE FROM waste_types;" if engine_type == "sqlite" else "DELETE FROM public.waste_types;")
    cursor.execute("DELETE FROM wards;" if engine_type == "sqlite" else "DELETE FROM public.wards;")

    ward_table = "wards" if engine_type == "sqlite" else "public.wards"
    ward_id_map = {}

    for code, name, zone, target_cap, area in wards:
        if engine_type == "postgres":
            cursor.execute(f"INSERT INTO {ward_table} (code, name, zone, target_capacity_kg, area_sq_km) VALUES (%s, %s, %s, %s, %s) RETURNING id;", (code, name, zone, target_cap, area))
            ward_id_map[code] = cursor.fetchone()[0]
        else:
            cursor.execute(f"INSERT INTO {ward_table} (code, name, zone, target_capacity_kg, area_sq_km) VALUES (?, ?, ?, ?, ?);", (code, name, zone, target_cap, area))
            ward_id_map[code] = cursor.lastrowid

    print(f"Inserted {len(ward_id_map)} wards.")

    # 2. Population Census
    census_table = "population_census" if engine_type == "sqlite" else "public.population_census"
    census_data = []
    base_populations = {
        "W01": 55000, "W02": 38000, "W03": 51000, "W04": 44000, "W05": 68000,
        "W06": 85000, "W07": 62000, "W08": 48000, "W09": 74000, "W10": 54000,
        "W11": 71000, "W12": 46000, "W13": 96000, "W14": 41000, "W15": 35000
    }
    for code, w_id in ward_id_map.items():
        base_pop = base_populations[code]
        for idx, year in enumerate([2024, 2025, 2026]):
            pop = int(base_pop * ((1.018) ** idx))
            census_data.append((w_id, year, pop, 1.8))
    
    cursor.executemany(f"INSERT INTO {census_table} (ward_id, year, population, growth_rate) VALUES ({p}, {p}, {p}, {p});", census_data)
    print(f"Inserted census records for 2024-2026.")

    # 3. Users
    users_table = "users" if engine_type == "sqlite" else "public.users"
    hashed_pwd = hash_password("password123")
    users = [
        ("admin", "admin@metro.gov.in", hashed_pwd, "Admin", None),
        ("analyst", "analyst@metro.gov.in", hashed_pwd, "Analyst", None),
    ]
    for code, w_id in ward_id_map.items():
        users.append((f"officer_{code.lower()}", f"officer_{code.lower()}@metro.gov.in", hashed_pwd, "Ward_Officer", w_id))
    
    cursor.executemany(f"INSERT INTO {users_table} (username, email, hashed_password, role, ward_id) VALUES ({p}, {p}, {p}, {p}, {p});", users)

    # 4. Waste Types
    wt_table = "waste_types" if engine_type == "sqlite" else "public.waste_types"
    waste_types = [
        ("ORG", "Organic Waste", "Organic", "Food waste, garden waste", 400.0),
        ("REC", "Recyclable Waste", "Recyclable", "Paper, plastics, glass", 150.0),
        ("GEN", "General Solid Waste", "General", "Non-recyclable domestic waste", 300.0),
        ("HAZ", "Hazardous Waste", "Hazardous", "Chemicals, batteries", 500.0),
        ("EWA", "E-Waste", "E-Waste", "Electronics, small appliances", 250.0),
    ]
    wt_id_map = {}
    for code, name, category, desc, density in waste_types:
        if engine_type == "postgres":
            cursor.execute(f"INSERT INTO {wt_table} (code, name, category, description, density_kg_m3) VALUES (%s, %s, %s, %s, %s) RETURNING id;", (code, name, category, desc, density))
            wt_id_map[code] = cursor.fetchone()[0]
        else:
            cursor.execute(f"INSERT INTO {wt_table} (code, name, category, description, density_kg_m3) VALUES (?, ?, ?, ?, ?);", (code, name, category, desc, density))
            wt_id_map[code] = cursor.lastrowid

    # 5. Vehicles
    v_table = "vehicles" if engine_type == "sqlite" else "public.vehicles"
    vehicles = [
        ("TRK-101", "Compactor Truck", 10000.0, "Active"),
        ("TRK-102", "Compactor Truck", 10000.0, "Active"),
        ("TRK-201", "Tipper Lorry", 8000.0, "Active"),
        ("CRT-301", "Electric Cart", 2000.0, "Active"),
        ("TRK-401", "Hook Loader", 15000.0, "Active"),
    ]
    vehicle_ids = []
    for reg, v_type, cap, status in vehicles:
        if engine_type == "postgres":
            cursor.execute(f"INSERT INTO {v_table} (registration_number, vehicle_type, capacity_kg, status) VALUES (%s, %s, %s, %s) RETURNING id;", (reg, v_type, cap, status))
            vehicle_ids.append(cursor.fetchone()[0])
        else:
            cursor.execute(f"INSERT INTO {v_table} (registration_number, vehicle_type, capacity_kg, status) VALUES (?, ?, ?, ?);", (reg, v_type, cap, status))
            vehicle_ids.append(cursor.lastrowid)

    # 6. Collection Points
    cp_table = "collection_points" if engine_type == "sqlite" else "public.collection_points"
    cp_id_list = []
    for code, w_id in ward_id_map.items():
        if engine_type == "postgres":
            cursor.execute(f"INSERT INTO {cp_table} (ward_id, name, latitude, longitude, bin_capacity_kg) VALUES (%s, %s, %s, %s, %s) RETURNING id;", (w_id, f"{code} Station", 19.07, 72.87, 3000.0))
            cp_id_list.append(cursor.fetchone()[0])
        else:
            cursor.execute(f"INSERT INTO {cp_table} (ward_id, name, latitude, longitude, bin_capacity_kg) VALUES (?, ?, ?, ?, ?);", (w_id, f"{code} Station", 19.07, 72.87, 3000.0))
            cp_id_list.append(cursor.lastrowid)

    # 7. Collection Records (Jan 2024 to Aug 2026)
    rec_table = "waste_collection_records" if engine_type == "sqlite" else "public.waste_collection_records"
    print("Generating historical collection records...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 8, 25)
    delta = timedelta(days=1)

    cat_weights = {"ORG": 1200.0, "REC": 450.0, "GEN": 300.0, "HAZ": 45.0, "EWA": 25.0}
    ward_mult = {"W01": 1.1, "W02": 0.8, "W03": 1.0, "W04": 0.9, "W05": 1.3, "W06": 1.6, "W07": 1.2, "W08": 0.95, "W09": 1.4, "W10": 1.0, "W11": 1.35, "W12": 0.85, "W13": 1.8, "W14": 0.8, "W15": 0.7}

    random.seed(42)
    np.random.seed(42)

    curr_date = start_date
    record_batch = []
    total_count = 0

    while curr_date <= end_date:
        date_str = curr_date.strftime("%Y-%m-%d")
        dow_factor = 1.15 if curr_date.weekday() in (5, 6) else 0.95
        summer_factor = 1.10 if curr_date.month in (5, 6, 7) else 1.0

        for w_code, w_id in ward_id_map.items():
            w_factor = ward_mult[w_code]
            for wt_code, wt_id in wt_id_map.items():
                base_w = cat_weights[wt_code]
                weight = round(max(5.0, base_w * w_factor * dow_factor * summer_factor * np.random.normal(1.0, 0.08)), 2)
                record_batch.append((date_str, w_id, cp_id_list[0], wt_id, vehicle_ids[0], weight, 1))
                total_count += 1

                if len(record_batch) >= 2000:
                    if engine_type == "postgres":
                        execute_batch(cursor, f"INSERT INTO {rec_table} (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id) VALUES (%s, %s, %s, %s, %s, %s, %s);", record_batch)
                    else:
                        cursor.executemany(f"INSERT INTO {rec_table} (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id) VALUES (?, ?, ?, ?, ?, ?, ?);", record_batch)
                    record_batch = []

        curr_date += delta

    if record_batch:
        if engine_type == "postgres":
            execute_batch(cursor, f"INSERT INTO {rec_table} (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id) VALUES (%s, %s, %s, %s, %s, %s, %s);", record_batch)
        else:
            cursor.executemany(f"INSERT INTO {rec_table} (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id) VALUES (?, ?, ?, ?, ?, ?, ?);", record_batch)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Successfully seeded {total_count} collection records into {engine_type.upper()} database!")

if __name__ == "__main__":
    seed_database()
