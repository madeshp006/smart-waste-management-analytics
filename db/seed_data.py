import os
import random
import sys
from datetime import datetime, timedelta
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configurable database URL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "waste_dw_db")
DB_USER = os.getenv("POSTGRES_USER", "waste_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "waste_password")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def seed_database():
    print("🌱 Connecting to database to seed synthetic municipal data...")
    conn = get_connection()
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

    cursor.execute("DELETE FROM public.waste_collection_records;")
    cursor.execute("DELETE FROM public.population_census;")
    cursor.execute("DELETE FROM public.collection_points;")
    cursor.execute("DELETE FROM public.users;")
    cursor.execute("DELETE FROM public.vehicles;")
    cursor.execute("DELETE FROM public.waste_types;")
    cursor.execute("DELETE FROM public.wards;")
    cursor.execute("ALTER SEQUENCE public.wards_id_seq RESTART WITH 1;")
    cursor.execute("ALTER SEQUENCE public.users_id_seq RESTART WITH 1;")
    cursor.execute("ALTER SEQUENCE public.waste_types_id_seq RESTART WITH 1;")
    cursor.execute("ALTER SEQUENCE public.vehicles_id_seq RESTART WITH 1;")
    cursor.execute("ALTER SEQUENCE public.collection_points_id_seq RESTART WITH 1;")
    cursor.execute("ALTER SEQUENCE public.waste_collection_records_id_seq RESTART WITH 1;")

    ward_insert_sql = """
        INSERT INTO public.wards (code, name, zone, target_capacity_kg, area_sq_km)
        VALUES (%s, %s, %s, %s, %s) RETURNING id, code;
    """
    ward_id_map = {}
    for code, name, zone, target_cap, area in wards:
        cursor.execute(ward_insert_sql, (code, name, zone, target_cap, area))
        row = cursor.fetchone()
        ward_id_map[code] = row[0]

    print(f"✅ Inserted {len(ward_id_map)} wards.")

    # 2. Population Census (2024, 2025, 2026)
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
    
    cursor.executemany("""
        INSERT INTO public.population_census (ward_id, year, population, growth_rate)
        VALUES (%s, %s, %s, %s);
    """, census_data)
    print(f"✅ Inserted census records for 2024-2026.")

    # 3. Users (Admin, Officer, Analyst)
    hashed_pwd = hash_password("password123")
    users = [
        ("admin", "admin@metro.gov.in", hashed_pwd, "Admin", None),
        ("analyst", "analyst@metro.gov.in", hashed_pwd, "Analyst", None),
    ]
    for code, w_id in ward_id_map.items():
        users.append((f"officer_{code.lower()}", f"officer_{code.lower()}@metro.gov.in", hashed_pwd, "Ward_Officer", w_id))
    
    cursor.executemany("""
        INSERT INTO public.users (username, email, hashed_password, role, ward_id)
        VALUES (%s, %s, %s, %s, %s);
    """, users)
    print(f"✅ Inserted {len(users)} users (Admin, Analyst, 15 Ward Officers). Password: 'password123'.")

    # 4. Waste Types
    waste_types = [
        ("ORG", "Organic Waste", "Organic", "Food waste, garden waste, agricultural biodegradable waste", 400.0),
        ("REC", "Recyclable Waste", "Recyclable", "Paper, plastics, glass, aluminium cans, cardboard", 150.0),
        ("GEN", "General Solid Waste", "General", "Non-recyclable inert domestic waste", 300.0),
        ("HAZ", "Hazardous Waste", "Hazardous", "Chemical containers, medical waste, batteries, paints", 500.0),
        ("EWA", "E-Waste", "E-Waste", "Discarded electronics, circuit boards, small appliances", 250.0),
    ]
    wt_id_map = {}
    for code, name, category, desc, density in waste_types:
        cursor.execute("""
            INSERT INTO public.waste_types (code, name, category, description, density_kg_m3)
            VALUES (%s, %s, %s, %s, %s) RETURNING id, code;
        """, (code, name, category, desc, density))
        row = cursor.fetchone()
        wt_id_map[code] = row[0]

    print(f"✅ Inserted {len(wt_id_map)} waste types.")

    # 5. Vehicles
    vehicles = [
        ("TRK-101", "Compactor Truck", 10000.0, "Active"),
        ("TRK-102", "Compactor Truck", 10000.0, "Active"),
        ("TRK-103", "Compactor Truck", 12000.0, "Active"),
        ("TRK-104", "Compactor Truck", 12000.0, "Active"),
        ("TRK-201", "Tipper Lorry", 8000.0, "Active"),
        ("TRK-202", "Tipper Lorry", 8000.0, "Active"),
        ("CRT-301", "Electric Cart", 2000.0, "Active"),
        ("CRT-302", "Electric Cart", 2000.0, "Active"),
        ("TRK-401", "Hook Loader", 15000.0, "Active"),
        ("TRK-402", "Hook Loader", 15000.0, "Active"),
    ]
    vehicle_ids = []
    for reg, v_type, cap, status in vehicles:
        cursor.execute("""
            INSERT INTO public.vehicles (registration_number, vehicle_type, capacity_kg, status)
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (reg, v_type, cap, status))
        vehicle_ids.append(cursor.fetchone()[0])
    
    print(f"✅ Inserted {len(vehicle_ids)} collection vehicles.")

    # 6. Collection Points
    collection_points = []
    cp_id_list = []
    for code, w_id in ward_id_map.items():
        base_lat = 19.0760 + random.uniform(-0.05, 0.05)
        base_lng = 72.8777 + random.uniform(-0.05, 0.05)
        for i in range(1, 4):
            cp_name = f"{code} Bin Station #{i}"
            cursor.execute("""
                INSERT INTO public.collection_points (ward_id, name, latitude, longitude, bin_capacity_kg)
                VALUES (%s, %s, %s, %s, %s) RETURNING id;
            """, (w_id, cp_name, base_lat + (i*0.002), base_lng + (i*0.002), 3000.0))
            cp_id_list.append(cursor.fetchone()[0])
    
    print(f"✅ Inserted {len(cp_id_list)} collection points.")

    # 7. Waste Collection Records (Jan 1, 2024 to Aug 25, 2026 ~ 968 days)
    print("⏳ Generating daily historical collection transactions (Jan 2024 to Aug 2026)...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 8, 25)
    delta = timedelta(days=1)
    
    records = []
    current_date = start_date

    # Category base weight factors
    cat_weights = {
        "ORG": 1200.0,  # Organic ~1200kg per ward/day average
        "REC": 450.0,   # Recyclable ~450kg
        "GEN": 300.0,   # General ~300kg
        "HAZ": 45.0,    # Hazardous ~45kg
        "EWA": 25.0,    # E-Waste ~25kg
    }

    # Ward size multiplier
    ward_mult = {
        "W01": 1.1, "W02": 0.8, "W03": 1.0, "W04": 0.9, "W05": 1.3,
        "W06": 1.6, "W07": 1.2, "W08": 0.95, "W09": 1.4, "W10": 1.0,
        "W11": 1.35, "W12": 0.85, "W13": 1.8, "W14": 0.8, "W15": 0.7
    }

    random.seed(42)
    np.random.seed(42)

    total_records_inserted = 0
    batch_size = 5000

    record_batch = []
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday() # 0 = Mon, 6 = Sun
        month = current_date.month

        # Day of week factor (Weekend organic/recyclables higher)
        dow_factor = 1.15 if day_of_week in (5, 6) else 0.95
        # Seasonal factor (Summer higher beverage/recyclable, Winter higher organic)
        summer_factor = 1.10 if month in (5, 6, 7) else 1.0
        festival_factor = 1.25 if (month == 10 and current_date.day in range(15, 25)) or (month == 12 and current_date.day > 20) else 1.0

        for w_code, w_id in ward_id_map.items():
            w_factor = ward_mult[w_code]
            for wt_code, wt_id in wt_id_map.items():
                base_w = cat_weights[wt_code]
                
                # Combine factors with Gaussian noise
                noise = np.random.normal(1.0, 0.08)
                weight = base_w * w_factor * dow_factor * summer_factor * festival_factor * noise
                weight = round(max(5.0, weight), 2)
                
                vehicle_id = random.choice(vehicle_ids)
                cp_id = random.choice(cp_id_list)
                
                record_batch.append((date_str, w_id, cp_id, wt_id, vehicle_id, weight, 1))

                if len(record_batch) >= batch_size:
                    execute_batch(cursor, """
                        INSERT INTO public.waste_collection_records 
                        (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, record_batch)
                    total_records_inserted += len(record_batch)
                    record_batch = []

        current_date += delta

    if record_batch:
        execute_batch(cursor, """
            INSERT INTO public.waste_collection_records 
            (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, record_batch)
        total_records_inserted += len(record_batch)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"🎉 Successfully seeded {total_records_inserted} waste collection records into OLTP database!")

if __name__ == "__main__":
    seed_database()
