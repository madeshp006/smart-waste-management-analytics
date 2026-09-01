from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import require_roles
from app.etl import pipeline

router = APIRouter()

@router.post("/run-etl")
def run_manual_etl(
    incremental: bool = False,
    current_user: dict = Depends(require_roles(["Admin"]))
):
    """Triggers the ETL pipeline to sync OLTP transactions into DW Star Schema."""
    try:
        stats = pipeline.run_etl_pipeline(incremental=incremental)
        return {
            "status": "success",
            "message": "Data Warehouse ETL execution completed successfully",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ETL execution error: {str(e)}"
        )

@router.get("/status")
def system_health_status(current_user: dict = Depends(require_roles(["Admin", "Analyst"]))):
    return {
        "status": "online",
        "services": {
            "oltp_database": "connected",
            "data_warehouse": "connected",
            "etl_pipeline": "idle",
            "ml_engine": "ready"
        }
    }
