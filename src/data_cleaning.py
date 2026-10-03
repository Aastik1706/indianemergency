"""
data_cleaning.py - Robust Data Cleaning & Preprocessing Pipeline

WHAT are we doing?
We are executing a justified, transparent cleaning pipeline on the raw Pune emergency
incident dataset to eliminate duplicates, chronological impossibilities, non-acute duration
outliers, and categorical inconsistencies, while imputing missing environmental attributes.

WHY are we doing it?
Statistical models and machine learning algorithms are sensitive to corrupted target values
(such as negative transit minutes or multi-day damping logs) and duplicate rows. In an interview
setting, blindly running df.dropna() or arbitrary trimming without operational domain justification
is considered poor practice.

HOW does it help?
It produces a clean, consistent, audit-compliant dataset with 100% valid target values,
consistent relational keys, and clean categories, ready for MySQL ingestion, SQL analysis,
and ML modeling.
"""

import os
import pandas as pd
import numpy as np

def clean_emergency_dataset(
    raw_filepath="data/raw/pune_emergency_incidents_raw.csv",
    processed_filepath="data/processed/pune_emergency_incidents_clean.csv"
):
    """
    Executes justified data cleaning on raw incident dataset.
    Logs each transformation with WHAT, WHY, WHAT WE DID, and IMPACT.
    """
    os.makedirs(os.path.dirname(processed_filepath), exist_ok=True)
    df = pd.read_csv(raw_filepath)
    initial_rows = len(df)
    
    audit_log = []
    print("\n" + "=" * 80)
    print("           STARTING JUSTIFIED DATA CLEANING PIPELINE")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # STEP 1: Duplicate Incident Deduplication
    # -------------------------------------------------------------------------
    dupes_count = df.duplicated(subset=["incident_id"], keep="first").sum()
    df = df.drop_duplicates(subset=["incident_id"], keep="first").copy()
    
    audit_log.append({
        "Cleaning Step": "1. Primary Key Deduplication",
        "What Happened": f"Found {dupes_count} duplicate incident_id records.",
        "Why Problematic": "Duplicate entries artificially inflate incident frequency and introduce duplicate rows into train/test splits.",
        "What We Did": "Dropped duplicate instances, retaining the first recorded instance.",
        "Rows Affected": dupes_count,
        "Analytical Impact": "Ensures entity integrity for database primary keys and prevents data leakage across train/test splits."
    })
    print(f"✔ Step 1: Removed {dupes_count} duplicate incidents. Remaining rows: {len(df)}")

    # -------------------------------------------------------------------------
    # STEP 2: Standardizing Categorical Casing & Whitespace
    # -------------------------------------------------------------------------
    # In raw logs: "residential building fire", "COMMERCIAL / INDUSTRIAL FIRE", etc.
    raw_categories_before = df["emergency_type"].nunique()
    df["emergency_type"] = df["emergency_type"].astype(str).str.strip().str.title()
    
    # Specific normalization to canonical PMC naming
    canonical_map = {
        "Commercial / Industrial Fire": "Commercial / Industrial Fire",
        "Residential Building Fire": "Residential Building Fire",
        "Hazardous Chemical / Lpg Leak": "Hazardous Chemical / LPG Leak",
        "Road Traffic Accident & Extrication": "Road Traffic Accident & Extrication",
        "Structural / Wada Collapse": "Structural / Wada Collapse",
        "Water Rescue / Flood Evacuation": "Water Rescue / Flood Evacuation",
        "Electrical Transformer / Tree Fall": "Electrical Transformer / Tree Fall"
    }
    df["emergency_type"] = df["emergency_type"].replace(canonical_map)
    raw_categories_after = df["emergency_type"].nunique()

    audit_log.append({
        "Cleaning Step": "2. Categorical Standardization",
        "What Happened": f"Emergency type labels contained mixed uppercase, lowercase, and title case variations ({raw_categories_before} raw strings).",
        "Why Problematic": "SQL GROUP BY and One-Hot Encoding would treat 'residential fire' and 'Residential Fire' as distinct categories.",
        "What We Did": "Trimmed whitespace and mapped strings to 7 canonical PMC emergency categories.",
        "Rows Affected": len(df),
        "Analytical Impact": "Ensures correct categorical aggregation in SQL and avoids sparse redundant columns during ML feature encoding."
    })
    print(f"✔ Step 2: Standardized emergency categories from {raw_categories_before} raw forms to {raw_categories_after} canonical forms.")

    # -------------------------------------------------------------------------
    # STEP 3: Removal of Chronological Impossibilities (Negative Response Times)
    # -------------------------------------------------------------------------
    df["dt_dispatch"] = pd.to_datetime(df["dispatch_timestamp"])
    df["dt_arrival"] = pd.to_datetime(df["arrival_timestamp"])
    
    bad_time_mask = (df["response_time_minutes"] < 0) | (df["dt_arrival"] <= df["dt_dispatch"])
    bad_time_count = bad_time_mask.sum()
    df = df[~bad_time_mask].copy()

    audit_log.append({
        "Cleaning Step": "3. Chronological Sanity Filtering",
        "What Happened": f"{bad_time_count} incidents had negative response times or arrival timestamps prior to dispatch.",
        "Why Problematic": "Negative emergency response times violate physical causality; typically caused by operator clock desynchronization or AM/PM entry errors.",
        "What We Did": "Excluded these invalid entries from the dataset.",
        "Rows Affected": bad_time_count,
        "Analytical Impact": "Protects regression metrics (MAE/RMSE) and loss functions from being corrupted by physically impossible negative targets."
    })
    print(f"✔ Step 3: Removed {bad_time_count} records with negative/invalid timestamps. Remaining rows: {len(df)}")

    # -------------------------------------------------------------------------
    # STEP 4: Handling Non-Acute Extreme Outliers (> 120 minutes)
    # -------------------------------------------------------------------------
    # In municipal fire operations, entries > 120 minutes represent multi-day
    # structural cooling/damping operations or salvage phases logged as incident close time.
    extreme_outlier_mask = df["response_time_minutes"] > 120.0
    extreme_outlier_count = extreme_outlier_mask.sum()
    df = df[~extreme_outlier_mask].copy()

    audit_log.append({
        "Cleaning Step": "4. Operational Outlier Filtering",
        "What Happened": f"{extreme_outlier_count} records had response times between 220 and 480 minutes.",
        "Why Problematic": "These represent extended salvage or cooling-down monitoring logs, not acute transit arrival time. Leaving them in distorts linear regression and squared error metrics.",
        "What We Did": "Established an operational cutoff at 120 minutes and filtered out non-acute salvage logs.",
        "Rows Affected": extreme_outlier_count,
        "Analytical Impact": "Focuses the model specifically on acute emergency transit response while preserving heavy-delay incidents up to 120 minutes."
    })
    print(f"✔ Step 4: Removed {extreme_outlier_count} non-acute duration outliers (> 120 mins). Remaining rows: {len(df)}")

    # -------------------------------------------------------------------------
    # STEP 5: Missing Environmental Value Imputation
    # -------------------------------------------------------------------------
    missing_weather_count = df["weather_condition"].isnull().sum()
    # If weather_condition is null, infer from rainfall_mm and is_monsoon
    def impute_weather(row):
        if pd.notnull(row["weather_condition"]):
            return row["weather_condition"]
        if row["rainfall_mm"] >= 15.0:
            return "Heavy Monsoon Rain"
        elif row["rainfall_mm"] > 0:
            return "Moderate Rain"
        elif row["is_monsoon"] == 1:
            return "Overcast"
        else:
            return "Clear / Pleasant"

    df["weather_condition"] = df.apply(impute_weather, axis=1)

    audit_log.append({
        "Cleaning Step": "5. Environmental Missing Imputation",
        "What Happened": f"{missing_weather_count} rows had missing weather condition descriptions due to sensor intermittency.",
        "Why Problematic": "Missing categorical values cause row drops during model fitting or NULL entries in database queries.",
        "What We Did": "Imputed weather condition deterministically based on recorded hourly rainfall_mm and monsoon calendar flag.",
        "Rows Affected": missing_weather_count,
        "Analytical Impact": "Preserves 100% of observations without discarding valuable incident response records."
    })
    print(f"✔ Step 5: Imputed {missing_weather_count} missing weather descriptions using rule-based meteorological mapping.")

    # -------------------------------------------------------------------------
    # STEP 6: Target Recalculation & Type Enforcement
    # -------------------------------------------------------------------------
    # Recompute response_time_minutes directly from timestamps to ensure exact mathematical consistency
    df["calculated_response_time"] = (df["dt_arrival"] - df["dt_dispatch"]).dt.total_seconds() / 60.0
    df["response_time_minutes"] = df["calculated_response_time"].round(2)
    df = df.drop(columns=["dt_dispatch", "dt_arrival", "calculated_response_time"])

    # High-delay operational flag (> 20.0 minutes represents standard urban delay threshold)
    df["high_delay_flag"] = (df["response_time_minutes"] > 20.0).astype(int)

    # Save cleaned dataset
    df.to_csv(processed_filepath, index=False)
    
    final_rows = len(df)
    net_dropped = initial_rows - final_rows
    retention_rate = (final_rows / initial_rows) * 100

    print("=" * 80)
    print(f"CLEANING COMPLETE: {initial_rows:,} raw rows -> {final_rows:,} clean rows")
    print(f"Net dropped records: {net_dropped} ({net_dropped/initial_rows*100:.2f}%) | Data Retention: {retention_rate:.2f}%")
    print(f"Processed file saved to: {processed_filepath}")
    print("=" * 80)

    audit_df = pd.DataFrame(audit_log)
    audit_df.to_csv("data/processed/data_cleaning_audit_log.csv", index=False)
    return df, audit_df

if __name__ == "__main__":
    clean_emergency_dataset()
