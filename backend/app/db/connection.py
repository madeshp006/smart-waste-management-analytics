import os
import logging
import sqlite3
import psycopg2
import psycopg2.extras
from typing import Tuple, Any

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "waste_dw_db")
DB_USER = os.getenv("POSTGRES_USER", "waste_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "waste_password")

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "waste_dw.db")

class DictRowWrapper(dict):
    """Wrapper to make SQLite Row objects behave like psycopg2 RealDictCursor dicts."""
    def __getitem__(self, key):
        return super().__getitem__(key)

def get_db():
    """
    Attempts to connect to PostgreSQL. 
    If PostgreSQL is unreachable or fails authentication, transparently falls back to SQLite.
    """
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
        # Fallback to local SQLite database file
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def execute_query(sql: str, params: tuple = (), fetch: str = "all") -> Any:
    """Helper executing queries consistently across Postgres and SQLite."""
    conn, engine_type = get_db()
    
    # Translate PostgreSQL specific syntax to SQLite if using SQLite
    if engine_type == "sqlite":
        sql = sql.replace("public.", "").replace("dw.", "")
        sql = sql.replace("%s", "?")
        sql = sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sql = sql.replace("BIGSERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sql = sql.replace("CURRENT_TIMESTAMP", "CURRENT_TIMESTAMP")
        sql = sql.replace("ILIKE", "LIKE")
        sql = sql.replace("CAST(w.target_capacity_kg AS FLOAT)", "w.target_capacity_kg")
        sql = sql.replace("CAST(w.area_sq_km AS FLOAT)", "w.area_sq_km")
        sql = sql.replace("CAST(density_kg_m3 AS FLOAT)", "density_kg_m3")
        sql = sql.replace("CAST(capacity_kg AS FLOAT)", "capacity_kg")
        sql = sql.replace("CAST(r.weight_kg AS FLOAT)", "r.weight_kg")
        sql = sql.replace("EXTRACT(YEAR FROM r.collection_date)::INT", "strftime('%Y', r.collection_date)")

    cursor = conn.cursor()
    cursor.execute(sql, params)

    result = None
    if fetch == "all":
        rows = cursor.fetchall()
        if engine_type == "sqlite":
            result = [dict(r) for r in rows]
        else:
            colnames = [desc[0] for desc in cursor.description]
            result = [dict(zip(colnames, row)) for row in rows]
    elif fetch == "one":
        row = cursor.fetchone()
        if row:
            if engine_type == "sqlite":
                result = dict(row)
            else:
                colnames = [desc[0] for desc in cursor.description]
                result = dict(zip(colnames, row))
    elif fetch == "commit":
        conn.commit()
        if engine_type == "postgres":
            try:
                row = cursor.fetchone()
                if row:
                    result = row[0]
            except Exception:
                pass
        else:
            result = cursor.lastrowid

    cursor.close()
    conn.close()
    return result
