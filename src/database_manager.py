"""
database_manager.py - Relational Database Ingestion and Query Execution Engine

WHAT are we doing?
We are loading the cleaned emergency response dataset and dimensional tables into
a relational SQLite database (`emergency_pune.db`) and executing the formal SQL
analytical queries. (The schema is also 100% compatible with MySQL 8.0+).

WHY are we doing it?
To demonstrate rigorous relational data modeling (Star Schema with Fact and Dimension
tables, Primary/Foreign key constraints, indexes, and analytical views), and provide
a reproducible SQL analytics pipeline that can be queried directly from Python or BI tools.

HOW does it help?
It enables complex SQL analysis (CTEs, Window Functions, Group By aggregations) directly
on the validated dataset, ensuring that the SQL queries written in Phase 6 execute on
real relational tables and produce verified results for the resume and Tableau.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = "emergency_pune.db"
SCHEMA_PATH = "sql/database_schema.sql"

def initialize_database():
    """Builds tables, constraints, indexes, and views from database_schema.sql."""
    print(f"\n[1/3] Initializing Relational Database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    # Execute schema script
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("✔ Schema DDL executed successfully.")

def load_data_to_database():
    """Loads dimension tables and fact table into SQLite database."""
    print("[2/3] Loading processed CSV datasets into relational tables...")
    conn = sqlite3.connect(DB_PATH)

    # 1. Load Stations Dimension
    stations_df = pd.read_csv("data/raw/pune_fire_stations.csv")
    stations_df.to_sql("dim_fire_stations", conn, if_exists="append", index=False)
    print(f"✔ dim_fire_stations loaded: {len(stations_df)} rows")

    # 2. Load Wards Dimension
    wards_df = pd.read_csv("data/raw/pune_municipal_wards.csv")
    wards_df.to_sql("dim_municipal_wards", conn, if_exists="append", index=False)
    print(f"✔ dim_municipal_wards loaded: {len(wards_df)} rows")

    # 3. Load Emergency Types Dimension
    types_df = pd.read_csv("data/raw/pune_emergency_types.csv")
    types_df.to_sql("dim_emergency_types", conn, if_exists="append", index=False)
    print(f"✔ dim_emergency_types loaded: {len(types_df)} rows")

    # 4. Load Fact Incidents Table
    incidents_df = pd.read_csv("data/processed/pune_emergency_incidents_clean.csv")
    
    # Filter to fact table columns
    fact_cols = [
        "incident_id", "dispatch_timestamp", "arrival_timestamp", "response_time_minutes",
        "station_id", "ward_id", "emergency_type_id", "network_distance_km",
        "traffic_congestion_factor", "weather_condition", "temperature_c", "rainfall_mm",
        "is_monsoon", "is_weekend", "is_peak_hour", "incident_hour", "day_of_week", "high_delay_flag"
    ]
    fact_df = incidents_df[fact_cols].copy()
    fact_df.to_sql("fact_emergency_incidents", conn, if_exists="append", index=False)
    print(f"✔ fact_emergency_incidents loaded: {len(fact_df):,} rows")

    conn.commit()
    conn.close()
    print("✔ All relational tables populated successfully.")

def verify_database():
    """Verifies table row counts and executes sample queries against analytical views."""
    print("\n[3/3] Verifying Relational Integrity & Analytical Views:")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verify Counts
    tables = ["dim_fire_stations", "dim_municipal_wards", "dim_emergency_types", "fact_emergency_incidents"]
    for tbl in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  • Table '{tbl}': {count:,} records")

    # Verify View 1: Top 3 Stations by Call Volume
    print("\nSample Output from 'v_station_operational_performance':")
    sample_station = pd.read_sql_query(
        "SELECT station_id, station_name, total_calls_handled, avg_response_time_min, high_delay_percentage FROM v_station_operational_performance ORDER BY total_calls_handled DESC LIMIT 3",
        conn
    )
    print(sample_station.to_string(index=False))

    # Verify View 2: Top 3 Wards by High Delay Rate
    print("\nSample Output from 'v_ward_risk_profiles' (Top Wards by Delay):")
    sample_ward = pd.read_sql_query(
        "SELECT ward_id, ward_name, density_tier, avg_response_time_min, high_delay_rate_pct FROM v_ward_risk_profiles ORDER BY high_delay_rate_pct DESC LIMIT 3",
        conn
    )
    print(sample_ward.to_string(index=False))

    conn.close()

if __name__ == "__main__":
    initialize_database()
    load_data_to_database()
    verify_database()
