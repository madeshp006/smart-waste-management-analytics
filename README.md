# Smart Waste Management Analytics: Municipal Data Warehouse & Garbage Generation Prediction System

A production-quality full-stack analytics platform built to assist municipal authorities in tracking, analyzing, and forecasting solid waste generation across city wards. The platform combines an operational transactional database (OLTP), a PostgreSQL Data Warehouse (OLAP Star Schema), an ETL pipeline, and a Machine Learning forecasting engine, all exposed via FastAPI and a React TypeScript dashboard.

---

## 🏗 System Architecture

```mermaid
flowchart TD
    subgraph Operational Data Ingestion
        A[PostgreSQL OLTP - 'public' schema] -->|Daily Collections & Census| B[Seed Generator / API Ingestion]
    end

    subgraph Data Warehouse & ETL Pipeline
        A -->|Extract OLTP Records| C[Python / Pandas ETL Pipeline]
        C -->|Transform & Generate Surrogate Keys| C
        C -->|Load Aggregated Facts| D[PostgreSQL DW - 'dw' Star Schema]
        D -->|Fact: fact_waste_generation| E[Pre-built OLAP Queries]
    end

    subgraph Machine Learning Forecasting
        A & D -->|Historical Time-Series Data| F[scikit-learn RandomForest & Feature Pipeline]
        F -->|7 / 30 / 90-Day Predictions| G[Confidence Intervals & Accuracy Metrics]
    end

    subgraph FastAPI REST Backend
        H[FastAPI Backend Engine] -->|CRUD & JWT Auth| A
        H -->|OLAP Reports| E
        H -->|Predictive API| G
    end

    subgraph User Dashboard
        I[React + TypeScript + Vite Dashboard] -->|TanStack Query API Client| H
        I -->|Interactive Recharts| J[Overview, ML Forecasts, OLAP Reports & Admin Controls]
    end
```

---

## 🗄 Entity-Relationship (ER) Diagrams

### 1. Operational Database Schema (`public` Schema - OLTP)

```mermaid
erDiagram
    WARDS ||--o{ USERS : "assigned_to"
    WARDS ||--o{ COLLECTION_POINTS : "contains"
    WARDS ||--o{ POPULATION_CENSUS : "tracks"
    WARDS ||--o{ WASTE_COLLECTION_RECORDS : "generates"
    WASTE_TYPES ||--o{ WASTE_COLLECTION_RECORDS : "classifies"
    VEHICLES ||--o{ WASTE_COLLECTION_RECORDS : "collects_via"
    COLLECTION_POINTS ||--o{ WASTE_COLLECTION_RECORDS : "collected_from"

    WARDS {
        int id PK
        string code UK
        string name
        string zone
        numeric target_capacity_kg
        numeric area_sq_km
    }

    USERS {
        int id PK
        string username UK
        string email UK
        string role
        int ward_id FK
    }

    POPULATION_CENSUS {
        int id PK
        int ward_id FK
        int year
        int population
        numeric growth_rate
    }

    WASTE_TYPES {
        int id PK
        string code UK
        string name
        string category
        numeric density_kg_m3
    }

    VEHICLES {
        int id PK
        string registration_number UK
        string vehicle_type
        numeric capacity_kg
        string status
    }

    COLLECTION_POINTS {
        int id PK
        int ward_id FK
        string name
        numeric latitude
        numeric longitude
    }

    WASTE_COLLECTION_RECORDS {
        bigint id PK
        date collection_date
        int ward_id FK
        int waste_type_id FK
        int vehicle_id FK
        numeric weight_kg
    }
```

### 2. Data Warehouse Star Schema (`dw` Schema - OLAP)

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_WASTE_GENERATION : "date_key"
    DIM_WARD ||--o{ FACT_WASTE_GENERATION : "ward_key"
    DIM_WASTE_TYPE ||--o{ FACT_WASTE_GENERATION : "waste_type_key"
    DIM_VEHICLE ||--o{ FACT_WASTE_GENERATION : "vehicle_key"

    DIM_DATE {
        int date_key PK
        date full_date UK
        int day_of_week
        string day_name
        int month
        string month_name
        int year
        boolean is_weekend
        boolean is_holiday
    }

    DIM_WARD {
        int ward_key PK
        int ward_id UK
        string ward_name
        string zone
        int population
        numeric target_capacity_kg
    }

    DIM_WASTE_TYPE {
        int waste_type_key PK
        int waste_type_id UK
        string waste_type_name
        string category
    }

    DIM_VEHICLE {
        int vehicle_key PK
        int vehicle_id UK
        string registration_number
        string vehicle_type
    }

    FACT_WASTE_GENERATION {
        bigint fact_id PK
        int date_key FK
        int ward_key FK
        int waste_type_key FK
        int vehicle_key FK
        numeric weight_kg
        int collection_count
        numeric per_capita_waste_g
    }
```

---

## 🔑 Quick Demo Credentials

All accounts use password: `password123`

| Role | Username | Email | Access Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@metro.gov.in` | Full management, manual ETL execution, model retraining, collection logging |
| **Ward Officer** | `officer_w01` | `officer_w01@metro.gov.in` | Collection entry logging, Ward 1 overview & predictions |
| **Analyst** | `analyst` | `analyst@metro.gov.in` | Data Warehouse OLAP queries, CSV export, prediction inspections |

---

## ⚡ Quick Start with Docker Compose

Spin up PostgreSQL database, FastAPI backend, and React dashboard with a single command:

```bash
# 1. Clone repository & navigate to directory
cd Implementation

# 2. Launch container stack
docker-compose up --build
```

Access services:
- **Frontend Dashboard:** [http://localhost](http://localhost) (or `http://localhost:5173` in local dev mode)
- **FastAPI OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL Database:** `localhost:5432` (`waste_dw_db`)

---

## 💻 Manual Setup & Local Execution

### 1. Database & Seed Data
```bash
# Ensure PostgreSQL is running locally with user 'waste_user' and database 'waste_dw_db'
psql -U waste_user -d waste_dw_db -f db/init_schemas.sql

# Seed 2+ years of realistic daily operational data (~11,000+ records)
python db/seed_data.py
```

### 2. Backend & ETL Pipeline
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run initial ETL to populate Data Warehouse
python app/etl/pipeline.py

# Launch FastAPI Server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

Run backend Pytest suite:
```bash
cd backend
pytest -v
```

---

## 📁 Repository Structure

```
Implementation/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # Auth, Wards, Collections, Analytics, Predictions, Admin
│   │   ├── core/              # Config, Security, JWT Tokens
│   │   ├── etl/               # Pandas ETL Pipeline & OLAP Query Engine
│   │   ├── ml/                # Time-Series Feature Engineering & ML Forecaster
│   │   └── main.py            # FastAPI Entry Point & APScheduler
│   ├── tests/                 # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── db/
│   ├── init_schemas.sql       # DDL for public (OLTP) and dw (OLAP) schemas
│   └── seed_data.py           # 2+ Year synthetic collection dataset generator
├── frontend/
│   ├── src/
│   │   ├── components/        # Navbar, Sidebar, Overview, Prediction, Reports, Admin
│   │   ├── services/          # API Client Layer
│   │   ├── types.ts           # TypeScript interfaces
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```
