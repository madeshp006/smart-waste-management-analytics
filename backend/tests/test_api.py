import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Smart Waste Management" in data["system"]

@patch("app.api.v1.endpoints.auth.execute_query")
@patch("app.api.v1.endpoints.auth.verify_password")
def test_login_success(mock_verify, mock_execute):
    mock_verify.return_value = True
    mock_execute.return_value = {
        "id": 1,
        "username": "admin",
        "email": "admin@metro.gov.in",
        "hashed_password": "hashed_pass_str",
        "role": "Admin",
        "ward_id": None,
        "ward_name": None
    }

    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "Admin"

@patch("app.api.v1.endpoints.auth.execute_query")
def test_login_invalid_credentials(mock_execute):
    mock_execute.return_value = None

    response = client.post("/api/v1/auth/login", json={"username": "invalid_user", "password": "wrong_password"})
    assert response.status_code == 401
    assert "detail" in response.json()

def test_unauthenticated_protected_route():
    response = client.get("/api/v1/wards")
    assert response.status_code == 401

@patch("app.ml.forecaster.fetch_daily_time_series")
def test_forecasting_pipeline_mock(mock_fetch):
    import pandas as pd
    import numpy as np

    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    weights = np.random.normal(loc=5000, scale=300, size=100)
    mock_df = pd.DataFrame({"date": dates, "weight_kg": weights})
    mock_fetch.return_value = mock_df

    from app.ml import forecaster
    res = forecaster.train_and_forecast(ward_id=1, horizon_days=30)
    
    assert res["horizon_days"] == 30
    assert len(res["forecast"]) == 30
    assert "mae" in res["metrics"]
    assert "rmse" in res["metrics"]
    assert res["summary"]["total_forecasted_kg"] > 0
