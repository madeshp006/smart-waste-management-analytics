from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.core.security import get_current_user, require_roles
from app.ml import forecaster
from app.schemas.schemas import ForecastResponse

router = APIRouter()

@router.get("/forecast", response_model=ForecastResponse)
def get_waste_forecast(
    ward_id: Optional[int] = Query(None, description="Ward ID filter (null for city-wide forecast)"),
    horizon_days: int = Query(30, ge=7, le=90, description="Forecast horizon in days (7, 30, 90)"),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = forecaster.train_and_forecast(ward_id=ward_id, horizon_days=horizon_days)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting engine error: {str(e)}"
        )

@router.post("/retrain", status_code=status.HTTP_200_OK)
def trigger_model_retraining(
    ward_id: Optional[int] = Query(None),
    current_user: dict = Depends(require_roles(["Admin", "Analyst"]))
):
    try:
        res = forecaster.train_and_forecast(ward_id=ward_id, horizon_days=30)
        return {
            "status": "success",
            "message": f"ML Model retrained successfully for ward_id={ward_id or 'City-Wide'}",
            "metrics": res["metrics"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model retraining error: {str(e)}"
        )
