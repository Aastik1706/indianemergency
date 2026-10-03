"""
feature_engineering.py - Feature Transformation and Preprocessing Pipeline

WHAT are we doing?
We are engineering predictive features from raw temporal timestamps, spatial distances,
traffic factors, meteorological flags, and operational categorical attributes.
We implement a strictly leakage-free chronological train/test split.

WHY are we doing it?
Emergency response operations operate chronologically; deploying a model in the real world
means training on past incidents and predicting future ones. Using random train_test_split()
causes severe lookahead leakage and inflates performance artificially.

HOW does it help?
It ensures an interview-defensible evaluation setup where encoders and scalers are fitted
exclusively on historical training data, generating validated feature matrices (X_train, X_test,
y_train, y_test) along with serialized preprocessing artifacts.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def engineer_features(df):
    """
    Transforms raw columns into analytical machine learning features.
    """
    df = df.copy()

    # 1. Cyclical Temporal Encodings (Hour of Day & Month)
    # Sine/Cosine transformations capture the circular nature of 24h clock and 12-month calendar
    df["sin_hour"] = np.sin(2 * np.pi * df["incident_hour"] / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * df["incident_hour"] / 24.0)
    
    # Extract month from dispatch timestamp
    dispatch_dt = pd.to_datetime(df["dispatch_timestamp"])
    df["month"] = dispatch_dt.dt.month
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)

    # 2. Time-of-day bucketing
    def get_time_bucket(hour):
        if 8 <= hour <= 11:
            return "Morning_Peak"
        elif 12 <= hour <= 16:
            return "Afternoon"
        elif 17 <= hour <= 21:
            return "Evening_Peak"
        else:
            return "Night_Offpeak"

    df["time_of_day_bucket"] = df["incident_hour"].apply(get_time_bucket)

    # 3. Distance Tiers (Domain categorized)
    def get_dist_tier(km):
        if km < 2.0:
            return "Vicinity_Sub2km"
        elif km < 5.0:
            return "Short_2to5km"
        else:
            return "Medium_Above5km"

    df["distance_tier"] = df["network_distance_km"].apply(get_dist_tier)

    # 4. Traffic & Weather Interaction Term
    # When heavy rain and high traffic coincide, delay compounds non-linearly
    df["traffic_rain_interaction"] = df["traffic_congestion_factor"] * (1.0 + df["rainfall_mm"] / 10.0)

    # 5. Heavy rain binary indicator
    df["heavy_rain_flag"] = (df["rainfall_mm"] >= 15.0).astype(int)

    return df

def prepare_train_test_data(
    data_path="data/processed/pune_emergency_incidents_clean.csv",
    train_ratio=0.80,
    artifacts_dir="models"
):
    """
    Executes chronological train/test split and builds scikit-learn preprocessing pipeline.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    df = pd.read_csv(data_path)
    
    # Sort strictly chronologically by dispatch timestamp to prevent lookahead leakage
    df = df.sort_values("dispatch_timestamp").reset_index(drop=True)
    df = engineer_features(df)

    split_idx = int(len(df) * train_ratio)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    split_date = test_df["dispatch_timestamp"].iloc[0]
    print(f"✔ Chronological Split Boundary: {split_date}")
    print(f"  • Training Incidents: {len(train_df):,} ({train_df['dispatch_timestamp'].min()} to {train_df['dispatch_timestamp'].max()})")
    print(f"  • Testing Incidents:  {len(test_df):,} ({test_df['dispatch_timestamp'].min()} to {test_df['dispatch_timestamp'].max()})")

    # Define Feature Sets
    numeric_features = [
        "network_distance_km",
        "traffic_congestion_factor",
        "rainfall_mm",
        "temperature_c",
        "sin_hour",
        "cos_hour",
        "sin_month",
        "cos_month",
        "traffic_rain_interaction"
    ]

    binary_features = [
        "is_monsoon",
        "is_weekend",
        "is_peak_hour",
        "heavy_rain_flag"
    ]

    categorical_features = [
        "station_id",
        "ward_id",
        "emergency_type",
        "time_of_day_bucket",
        "distance_tier"
    ]

    feature_cols = numeric_features + binary_features + categorical_features
    target_col = "response_time_minutes"

    X_train = train_df[feature_cols]
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols]
    y_test = test_df[target_col].values

    # Preprocessor: StandardScaler for numeric features, OneHotEncoder for categoricals
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("bin", "passthrough", binary_features),
            ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), categorical_features)
        ]
    )

    # Fit ONLY on training data
    preprocessor.fit(X_train)

    # Save preprocessor artifact
    preprocessor_path = os.path.join(artifacts_dir, "preprocessor.joblib")
    joblib.dump(preprocessor, preprocessor_path)
    print(f"✔ Fitted preprocessor saved to: {preprocessor_path}")

    return X_train, X_test, y_train, y_test, preprocessor, train_df, test_df

if __name__ == "__main__":
    X_train, X_test, y_train, y_test, preprocessor, train_df, test_df = prepare_train_test_data()
    print("✔ Feature engineering and chronological splitting pipeline verified.")
