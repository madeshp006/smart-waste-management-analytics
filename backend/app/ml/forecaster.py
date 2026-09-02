import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from app.db.connection import get_db

logging.basicConfig(level=logging.INFO)

def fetch_daily_time_series(ward_id: Optional[int] = None) -> pd.DataFrame:
    conn, engine_type = get_db()
    
    where_clause = ""
    params = []
    if ward_id:
        where_clause = "WHERE w.ward_id = %s" if engine_type == "postgres" else "WHERE w.ward_id = ?"
        params.append(ward_id)

    fact_table = "dw.fact_waste_generation" if engine_type == "postgres" else "fact_waste_generation"
    dim_date = "dw.dim_date" if engine_type == "postgres" else "dim_date"
    dim_ward = "dw.dim_ward" if engine_type == "postgres" else "dim_ward"

    query = f"""
        SELECT 
            d.full_date as date,
            SUM(f.weight_kg) as weight_kg
        FROM {fact_table} f
        JOIN {dim_date} d ON f.date_key = d.date_key
        JOIN {dim_ward} w ON f.ward_key = w.ward_key
        {where_clause}
        GROUP BY d.full_date
        ORDER BY d.full_date ASC;
    """
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()

    if df.empty:
        conn, engine_type = get_db()
        rec_table = "public.waste_collection_records" if engine_type == "postgres" else "waste_collection_records"
        where_clause_oltp = ""
        params_oltp = []
        if ward_id:
            where_clause_oltp = "WHERE ward_id = %s" if engine_type == "postgres" else "WHERE ward_id = ?"
            params_oltp.append(ward_id)

        query_oltp = f"""
            SELECT 
                collection_date as date,
                SUM(weight_kg) as weight_kg
            FROM {rec_table}
            {where_clause_oltp}
            GROUP BY collection_date
            ORDER BY collection_date ASC;
        """
        df = pd.read_sql(query_oltp, conn, params=params_oltp)
        conn.close()

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["day_of_week"] = data["date"].dt.dayofweek
    data["day_of_month"] = data["date"].dt.day
    data["month"] = data["date"].dt.month
    data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)
    data["day_of_year"] = data["date"].dt.dayofyear

    data["lag_1"] = data["weight_kg"].shift(1)
    data["lag_7"] = data["weight_kg"].shift(7)
    data["lag_14"] = data["weight_kg"].shift(14)
    data["rolling_mean_7"] = data["weight_kg"].shift(1).rolling(7).mean()
    data["rolling_std_7"] = data["weight_kg"].shift(1).rolling(7).std()
    data["rolling_mean_30"] = data["weight_kg"].shift(1).rolling(30).mean()

    data = data.dropna().reset_index(drop=True)
    return data

def train_and_forecast(ward_id: Optional[int] = None, horizon_days: int = 30) -> Dict[str, Any]:
    df_raw = fetch_daily_time_series(ward_id)
    if len(df_raw) < 60:
        raise ValueError(f"Insufficient historical data ({len(df_raw)} records) for ML training. Need at least 60 days.")

    df_feats = build_features(df_raw)

    feature_cols = [
        "day_of_week", "day_of_month", "month", "is_weekend", "day_of_year",
        "lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_std_7", "rolling_mean_30"
    ]
    target_col = "weight_kg"

    split_idx = max(len(df_feats) - 45, int(len(df_feats) * 0.8))
    train_df = df_feats.iloc[:split_idx]
    test_df = df_feats.iloc[split_idx:]

    X_train, y_train = train_df[feature_cols], train_df[target_col]
    X_test, y_test = test_df[feature_cols], test_df[target_col]

    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_train, y_train)

    test_preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, test_preds)
    rmse = np.sqrt(mean_squared_error(y_test, test_preds))
    mape = mean_absolute_percentage_error(y_test, test_preds) * 100.0

    residuals = y_test - test_preds
    std_residual = np.std(residuals)

    model.fit(df_feats[feature_cols], df_feats[target_col])

    last_known_date = df_raw["date"].max()
    future_predictions = []
    current_date = last_known_date + timedelta(days=1)
    full_weights = list(df_raw["weight_kg"].values)

    for i in range(horizon_days):
        dow = current_date.weekday()
        dom = current_date.day
        month = current_date.month
        is_wk = 1 if dow in (5, 6) else 0
        doy = current_date.timetuple().tm_yday

        lag1 = full_weights[-1]
        lag7 = full_weights[-7] if len(full_weights) >= 7 else full_weights[-1]
        lag14 = full_weights[-14] if len(full_weights) >= 14 else full_weights[-1]
        
        r_mean7 = np.mean(full_weights[-7:]) if len(full_weights) >= 7 else np.mean(full_weights)
        r_std7 = np.std(full_weights[-7:]) if len(full_weights) >= 7 else 0.0
        r_mean30 = np.mean(full_weights[-30:]) if len(full_weights) >= 30 else np.mean(full_weights)

        feat_vector = np.array([[
            dow, dom, month, is_wk, doy,
            lag1, lag7, lag14, r_mean7, r_std7, r_mean30
        ]])

        pred_val = float(model.predict(feat_vector)[0])
        pred_val = max(100.0, pred_val)

        uncertainty = 1.96 * std_residual * np.sqrt(1 + (i * 0.02))
        lower_bound = max(0.0, pred_val - uncertainty)
        upper_bound = pred_val + uncertainty

        future_predictions.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "predicted_kg": round(pred_val, 2),
            "lower_bound_kg": round(lower_bound, 2),
            "upper_bound_kg": round(upper_bound, 2),
        })

        full_weights.append(pred_val)
        current_date += timedelta(days=1)

    hist_tail = df_raw.tail(60)
    historical_out = [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "actual_kg": round(float(row["weight_kg"]), 2)
        }
        for _, row in hist_tail.iterrows()
    ]

    total_forecasted = sum(p["predicted_kg"] for p in future_predictions)
    avg_daily = total_forecasted / horizon_days
    peak_pred = max(future_predictions, key=lambda x: x["predicted_kg"])

    return {
        "ward_id": ward_id,
        "horizon_days": horizon_days,
        "metrics": {
            "model_name": "RandomForest_Time_Series_Regressor",
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2),
            "mape_pct": round(float(mape), 2),
            "training_samples": len(X_train)
        },
        "summary": {
            "total_forecasted_kg": round(total_forecasted, 2),
            "total_forecasted_tons": round(total_forecasted / 1000.0, 2),
            "avg_daily_forecasted_kg": round(avg_daily, 2),
            "peak_date": peak_pred["date"],
            "peak_kg": peak_pred["predicted_kg"]
        },
        "historical": historical_out,
        "forecast": future_predictions
    }
