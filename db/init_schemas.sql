-- SQL Initializer Script for Smart Waste Management Analytics
-- Creates both OLTP schema ('public') and Data Warehouse schema ('dw')

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. OPERATIONAL DATABASE SCHEMA (OLTP - 'public')
-- ============================================================================

-- Wards table
CREATE TABLE IF NOT EXISTS public.wards (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    zone VARCHAR(50) NOT NULL,
    target_capacity_kg NUMERIC(12, 2) NOT NULL DEFAULT 50000.00,
    area_sq_km NUMERIC(8, 2) NOT NULL DEFAULT 15.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users table (Role-Based Access)
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('Admin', 'Ward_Officer', 'Analyst')),
    ward_id INT REFERENCES public.wards(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Population Census table (Ward population per year)
CREATE TABLE IF NOT EXISTS public.population_census (
    id SERIAL PRIMARY KEY,
    ward_id INT NOT NULL REFERENCES public.wards(id) ON DELETE CASCADE,
    year INT NOT NULL,
    population INT NOT NULL,
    growth_rate NUMERIC(5, 2) DEFAULT 1.5,
    UNIQUE(ward_id, year)
);

-- Waste Types table
CREATE TABLE IF NOT EXISTS public.waste_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('Organic', 'Recyclable', 'Hazardous', 'E-Waste', 'General')),
    description TEXT,
    density_kg_m3 NUMERIC(8, 2) DEFAULT 300.00
);

-- Vehicles table
CREATE TABLE IF NOT EXISTS public.vehicles (
    id SERIAL PRIMARY KEY,
    registration_number VARCHAR(30) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL CHECK (vehicle_type IN ('Compactor Truck', 'Tipper Lorry', 'Electric Cart', 'Hook Loader')),
    capacity_kg NUMERIC(10, 2) NOT NULL DEFAULT 8000.00,
    status VARCHAR(30) DEFAULT 'Active' CHECK (status IN ('Active', 'Maintenance', 'Decommissioned'))
);

-- Collection Points table
CREATE TABLE IF NOT EXISTS public.collection_points (
    id SERIAL PRIMARY KEY,
    ward_id INT NOT NULL REFERENCES public.wards(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    bin_capacity_kg NUMERIC(10, 2) NOT NULL DEFAULT 2000.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Waste Collection Records (Operational transactions)
CREATE TABLE IF NOT EXISTS public.waste_collection_records (
    id BIGSERIAL PRIMARY KEY,
    collection_date DATE NOT NULL,
    ward_id INT NOT NULL REFERENCES public.wards(id) ON DELETE RESTRICT,
    collection_point_id INT REFERENCES public.collection_points(id) ON DELETE SET NULL,
    waste_type_id INT NOT NULL REFERENCES public.waste_types(id) ON DELETE RESTRICT,
    vehicle_id INT NOT NULL REFERENCES public.vehicles(id) ON DELETE RESTRICT,
    weight_kg NUMERIC(10, 2) NOT NULL CHECK (weight_kg >= 0),
    collected_by_user_id INT REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_waste_records_date ON public.waste_collection_records(collection_date);
CREATE INDEX IF NOT EXISTS idx_waste_records_ward ON public.waste_collection_records(ward_id);

-- ============================================================================
-- 2. DATA WAREHOUSE SCHEMA (OLAP - 'dw' Star Schema)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key INT PRIMARY KEY, -- YYYYMMDD
    full_date DATE UNIQUE NOT NULL,
    day_of_week INT NOT NULL, -- 1-7
    day_name VARCHAR(15) NOT NULL,
    day_of_month INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- Dimension: Ward
CREATE TABLE IF NOT EXISTS dw.dim_ward (
    ward_key SERIAL PRIMARY KEY,
    ward_id INT NOT NULL UNIQUE,
    ward_name VARCHAR(100) NOT NULL,
    zone VARCHAR(50) NOT NULL,
    area_sq_km NUMERIC(8, 2),
    population INT DEFAULT 0,
    target_capacity_kg NUMERIC(12, 2)
);

-- Dimension: Waste Type
CREATE TABLE IF NOT EXISTS dw.dim_waste_type (
    waste_type_key SERIAL PRIMARY KEY,
    waste_type_id INT NOT NULL UNIQUE,
    waste_type_name VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    density_kg_m3 NUMERIC(8, 2)
);

-- Dimension: Vehicle
CREATE TABLE IF NOT EXISTS dw.dim_vehicle (
    vehicle_key SERIAL PRIMARY KEY,
    vehicle_id INT NOT NULL UNIQUE,
    registration_number VARCHAR(30) NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    capacity_kg NUMERIC(10, 2)
);

-- Fact Table: Waste Generation
CREATE TABLE IF NOT EXISTS dw.fact_waste_generation (
    fact_id BIGSERIAL PRIMARY KEY,
    date_key INT NOT NULL REFERENCES dw.dim_date(date_key),
    ward_key INT NOT NULL REFERENCES dw.dim_ward(ward_key),
    waste_type_key INT NOT NULL REFERENCES dw.dim_waste_type(waste_type_key),
    vehicle_key INT NOT NULL REFERENCES dw.dim_vehicle(vehicle_key),
    weight_kg NUMERIC(12, 2) NOT NULL DEFAULT 0,
    collection_count INT NOT NULL DEFAULT 1,
    per_capita_waste_g NUMERIC(10, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unq_fact_grain UNIQUE (date_key, ward_key, waste_type_key, vehicle_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_date ON dw.fact_waste_generation(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_ward ON dw.fact_waste_generation(ward_key);
CREATE INDEX IF NOT EXISTS idx_fact_waste_type ON dw.fact_waste_generation(waste_type_key);
