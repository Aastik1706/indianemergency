"""
data_validation.py - Comprehensive Data Quality and Validation Engine

WHAT are we doing?
We are implementing automated sanity checks and integrity tests on the raw Indian
emergency dataset prior to any data manipulation or cleaning.

WHY are we doing it?
Data validation is the critical step that prevents silent downstream errors. In real-world
Indian municipal datasets, system clock desynchronizations, operator transcription typos,
and re-dispatch duplicates frequently corrupt analytical metrics if not systematically audited.

HOW does it help?
It produces a transparent Data Quality Audit Report (quantifying missing rates, invalid
timestamps, duplicate keys, and out-of-boundary anomalies) that serves as the factual justification
for every cleaning action taken in Phase 4.
"""

import os
import pandas as pd
import numpy as np

def validate_emergency_data(filepath="data/raw/pune_emergency_incidents_raw.csv"):
    """
    Performs comprehensive validation checks on raw incident dataset.
    Returns a dictionary of quality metrics and a structured validation report dataframe.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found at: {filepath}")

    df = pd.read_csv(filepath)
    total_records = len(df)

    validation_results = []

    # 1. Total records and columns
    validation_results.append({
        "Check Category": "Dataset Dimension",
        "Metric / Test Description": "Total Row Count",
        "Finding / Count": total_records,
        "Status / Assessment": "Baseline"
    })
    validation_results.append({
        "Check Category": "Dataset Dimension",
        "Metric / Test Description": "Total Feature Columns",
        "Finding / Count": len(df.columns),
        "Status / Assessment": "Baseline"
    })

    # 2. Duplicate Check
    duplicate_ids = df["incident_id"].duplicated().sum()
    validation_results.append({
        "Check Category": "Primary Key Integrity",
        "Metric / Test Description": "Duplicate Incident IDs",
        "Finding / Count": f"{duplicate_ids} ({duplicate_ids/total_records*100:.2f}%)",
        "Status / Assessment": "FAILED - Duplicate incidents must be deduplicated" if duplicate_ids > 0 else "PASSED"
    })

    # 3. Missing Value Audit
    missing_counts = df.isnull().sum()
    for col, count in missing_counts.items():
        if count > 0:
            validation_results.append({
                "Check Category": "Completeness",
                "Metric / Test Description": f"Missing values in '{col}'",
                "Finding / Count": f"{count} ({count/total_records*100:.2f}%)",
                "Status / Assessment": "FLAGGED - Requires imputation or handling"
            })

    # 4. Timestamp Ordering and Validity
    df["dt_dispatch"] = pd.to_datetime(df["dispatch_timestamp"], errors="coerce")
    df["dt_arrival"] = pd.to_datetime(df["arrival_timestamp"], errors="coerce")

    invalid_timestamps = df["dt_dispatch"].isnull().sum() + df["dt_arrival"].isnull().sum()
    validation_results.append({
        "Check Category": "Timestamp Integrity",
        "Metric / Test Description": "Unparseable / Malformed Timestamps",
        "Finding / Count": invalid_timestamps,
        "Status / Assessment": "PASSED" if invalid_timestamps == 0 else "FAILED"
    })

    # Arrival prior to or equal to dispatch
    time_order_violation = (df["dt_arrival"] <= df["dt_dispatch"]).sum()
    validation_results.append({
        "Check Category": "Temporal Logic",
        "Metric / Test Description": "Arrival time <= Dispatch time",
        "Finding / Count": f"{time_order_violation} ({time_order_violation/total_records*100:.2f}%)",
        "Status / Assessment": "FAILED - Chronological violation (Negative transit duration)" if time_order_violation > 0 else "PASSED"
    })

    # 5. Negative Response Times
    negative_response_times = (df["response_time_minutes"] < 0).sum()
    validation_results.append({
        "Check Category": "Target Variable Sanity",
        "Metric / Test Description": "Negative Response Times (< 0 mins)",
        "Finding / Count": f"{negative_response_times} ({negative_response_times/total_records*100:.2f}%)",
        "Status / Assessment": "FAILED - Physical impossibility" if negative_response_times > 0 else "PASSED"
    })

    # 6. Ultra-fast False Alarms (< 2.0 minutes for full municipal dispatch)
    sub_two_min_records = ((df["response_time_minutes"] >= 0) & (df["response_time_minutes"] < 2.0)).sum()
    validation_results.append({
        "Check Category": "Target Variable Sanity",
        "Metric / Test Description": "Suspiciously Short Response Times (< 2.0 mins)",
        "Finding / Count": f"{sub_two_min_records} ({sub_two_min_records/total_records*100:.2f}%)",
        "Status / Assessment": "REVIEW - Likely on-station false alarms / cancelled en-route"
    })

    # 7. Extreme Outliers (> 120 minutes)
    extreme_outliers = (df["response_time_minutes"] > 120.0).sum()
    validation_results.append({
        "Check Category": "Target Variable Sanity",
        "Metric / Test Description": "Extreme Duration Outliers (> 120.0 mins)",
        "Finding / Count": f"{extreme_outliers} ({extreme_outliers/total_records*100:.2f}%)",
        "Status / Assessment": "FLAGGED - Represent multi-day fire damping logs, not acute transit" if extreme_outliers > 0 else "PASSED"
    })

    # 8. Distance Sanity Check
    unrealistic_distances = ((df["network_distance_km"] <= 0) | (df["network_distance_km"] > 50.0)).sum()
    validation_results.append({
        "Check Category": "Geospatial Sanity",
        "Metric / Test Description": "Unrealistic Distance (<= 0 or > 50 km in Pune)",
        "Finding / Count": unrealistic_distances,
        "Status / Assessment": "PASSED" if unrealistic_distances == 0 else "FAILED"
    })

    # 9. Categorical Casing Consistency
    unique_emergency_types = df["emergency_type"].unique()
    inconsistent_casing = len(unique_emergency_types) > len(set(et.lower() for et in unique_emergency_types))
    validation_results.append({
        "Check Category": "Categorical Integrity",
        "Metric / Test Description": "Inconsistent Emergency Type Casing",
        "Finding / Count": f"{len(unique_emergency_types)} raw categories vs {len(set(et.lower() for et in unique_emergency_types))} normalized",
        "Status / Assessment": "FAILED - Mixed casing detected" if inconsistent_casing else "PASSED"
    })

    report_df = pd.DataFrame(validation_results)
    return report_df

def print_validation_report():
    report_df = validate_emergency_data()
    print("=" * 80)
    print("      DATA VALIDATION & QUALITY AUDIT REPORT - PUNE EMERGENCY DATASET")
    print("=" * 80)
    print(report_df.to_string(index=False))
    print("=" * 80)

if __name__ == "__main__":
    print_validation_report()
