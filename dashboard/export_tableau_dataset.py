"""
export_tableau_dataset.py - Generates Denormalized, Enriched CSV for Tableau Public

WHAT are we doing?
We are generating a fully enriched, denormalized analytics dataset specifically formatted
for Tableau Desktop and Tableau Public ingestion.

WHY are we doing it?
Tableau Public performs best on a clean, single-table analytical extract that joins fact incidents
with dimensional attributes (station coordinates, ward centroids, zone boundaries) and precomputed
ML predictions (predicted response time, residual error, high-delay classification).

HOW does it help?
It enables instant, drag-and-drop creation of the 4 requested Tableau dashboards without requiring
complex manual multi-table joins or blending inside Tableau.
"""

import os
import sqlite3
import joblib
import pandas as pd
import numpy as np

# Add project root to sys.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.feature_engineering import engineer_features

def export_for_tableau(
    db_path="emergency_pune.db",
    output_path="dashboard/pune_emergency_tableau_data.csv"
):
    print("=" * 80)
    print("      EXPORTING DENORMALIZED ANALYTICS DATASET FOR TABLEAU PUBLIC")
    print("=" * 80)

    conn = sqlite3.connect(db_path)

    # Denormalized SQL Query joining Fact with All Dimensions
    sql = """
    SELECT 
        f.incident_id,
        f.dispatch_timestamp,
        DATE(f.dispatch_timestamp) AS incident_date,
        TIME(f.dispatch_timestamp) AS incident_time,
        f.arrival_timestamp,
        f.response_time_minutes,
        
        -- Station Attributes
        s.station_id,
        s.station_name,
        s.latitude AS station_latitude,
        s.longitude AS station_longitude,
        s.fleet_capacity,
        s.established_year AS station_established_year,

        -- Ward Attributes
        w.ward_id,
        w.ward_name,
        w.zone AS administrative_zone,
        w.centroid_lat AS ward_centroid_lat,
        w.centroid_lon AS ward_centroid_lon,
        w.area_sqkm AS ward_area_sqkm,
        w.density_tier AS ward_density_tier,
        w.road_congestion_baseline,

        -- Emergency Attributes
        t.type_id AS emergency_type_id,
        t.name AS emergency_category,
        t.priority AS priority_level,
        t.tenders_required,

        -- Operational & Environmental Factors
        f.network_distance_km,
        f.traffic_congestion_factor,
        f.weather_condition,
        f.temperature_c,
        f.rainfall_mm,
        f.is_monsoon,
        f.is_weekend,
        f.is_peak_hour,
        f.incident_hour,
        f.day_of_week,
        f.high_delay_flag,

        -- Derived Transit Metrics
        ROUND(f.response_time_minutes / f.network_distance_km, 2) AS minutes_per_km,
        ROUND(f.network_distance_km / (f.response_time_minutes / 60.0), 1) AS effective_speed_kmh
    FROM fact_emergency_incidents f
    JOIN dim_fire_stations s ON f.station_id = s.station_id
    JOIN dim_municipal_wards w ON f.ward_id = w.ward_id
    JOIN dim_emergency_types t ON f.emergency_type_id = t.type_id
    ORDER BY f.dispatch_timestamp ASC;
    """

    df = pd.read_sql_query(sql, conn)
    conn.close()

    # Load trained ML model to attach predictions
    if os.path.exists("models/best_model.joblib") and os.path.exists("models/preprocessor.joblib"):
        print("✔ Attaching Machine Learning Model Predictions & Residuals...")
        model = joblib.load("models/best_model.joblib")
        preprocessor = joblib.load("models/preprocessor.joblib")

        # Map column names for feature engineering
        df_for_eng = df.rename(columns={"emergency_category": "emergency_type"}).copy()
        df_engineered = engineer_features(df_for_eng)
        
        X_trans = preprocessor.transform(df_engineered)
        preds = model.predict(X_trans)
        
        df["predicted_response_time_min"] = np.round(preds, 2)
        df["residual_error_min"] = np.round(df["response_time_minutes"] - df["predicted_response_time_min"], 2)
        df["predicted_high_delay_flag"] = (df["predicted_response_time_min"] > 20.0).astype(int)
    else:
        print("⚠️ Model artifacts not found. Predictions skipped.")

    # Response Time Tiers for Tableau Slicers
    df["response_time_tier"] = pd.cut(
        df["response_time_minutes"],
        bins=[0, 5, 10, 15, 20, 100],
        labels=["Ultra-Fast (< 5m)", "Standard (5-10m)", "Moderate (10-15m)", "Elevated (15-20m)", "Critical Delay (> 20m)"]
    )

    df.to_csv(output_path, index=False)
    print(f"✔ Denormalized Tableau dataset saved to: {output_path}")
    print(f"  • Total Rows: {len(df):,} | Total Columns: {len(df.columns)}")
    print("=" * 80)

if __name__ == "__main__":
    export_for_tableau()
