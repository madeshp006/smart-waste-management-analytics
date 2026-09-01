import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.api.v1.endpoints import auth, wards, collections, analytics, predictions, admin
from app.etl import pipeline

logging.basicConfig(level=logging.INFO)

scheduler = BackgroundScheduler()

def scheduled_etl_job():
    logging.info("⏰ APScheduler: Triggering periodic Data Warehouse ETL Sync...")
    try:
        pipeline.run_etl_pipeline(incremental=True)
    except Exception as e:
        logging.error(f"Scheduled ETL Error: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logging.info("🚀 Starting Smart Waste Management Analytics API Server...")
    # Schedule ETL every 6 hours
    scheduler.add_job(scheduled_etl_job, 'interval', hours=6, id="periodic_etl")
    scheduler.start()
    yield
    # Shutdown actions
    logging.info("🛑 Shutting down API Server & Scheduler...")
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(wards.router, prefix=f"{settings.API_V1_STR}", tags=["Entities (Wards/Vehicles/Types)"])
app.include_router(collections.router, prefix=f"{settings.API_V1_STR}", tags=["Waste Collections (OLTP)"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Data Warehouse Analytics (OLAP)"])
app.include_router(predictions.router, prefix=f"{settings.API_V1_STR}/predictions", tags=["ML Forecasting Engine"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin & ETL Operations"])

@app.get("/", tags=["Health Check"])
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
