"""
predict.py - Standalone Inference & Decision-Support Prediction Engine

WHAT are we doing?
We are implementing a production-grade inference interface that loads the trained champion
Gradient Boosting model and preprocessing pipeline, accepts operational parameters
(distance, hour, station, ward, emergency type, rainfall), and outputs the expected response
time alongside an empirical 90% prediction interval and operational risk indicators.

WHY are we doing it?
In an emergency dispatch center, a raw point prediction (e.g., "8.2 minutes") lacks
decision utility without an understanding of uncertainty. Providing a prediction interval
(e.g., "8.2 mins [7.1 - 9.3 mins]") gives dispatchers actionable confidence bounds.

HOW does it help?
It converts machine learning research into an interactive decision-support tool,
demonstrating end-to-end software engineering, CLI argument parsing, input validation,
and responsible AI governance.
"""

import os
import sys
import argparse
import joblib
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.feature_engineering import engineer_features

MODEL_PATH = "models/best_model.joblib"
PREPROCESSOR_PATH = "models/preprocessor.joblib"
METRICS_PATH = "models/model_comparison_metrics.csv"

# Pre-loaded Pune Reference Dimensions
VALID_STATIONS = [f"FS-{i:02d}" for i in range(1, 15)]
VALID_WARDS = [f"WD-{i:02d}" for i in range(1, 16)]
VALID_EMERGENCIES = [
    "Commercial / Industrial Fire",
    "Residential Building Fire",
    "Hazardous Chemical / LPG Leak",
    "Road Traffic Accident & Extrication",
    "Structural / Wada Collapse",
    "Water Rescue / Flood Evacuation",
    "Electrical Transformer / Tree Fall"
]

def load_artifacts():
    """Loads champion model and preprocessing pipeline."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(PREPROCESSOR_PATH):
        raise FileNotFoundError("Model artifacts not found. Please run 'python src/train_model.py' first.")
    
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    return model, preprocessor

def estimate_traffic_factor(hour, ward_id, is_weekend):
    """Estimates baseline traffic congestion multiplier based on Pune traffic patterns."""
    # Peak Hours (08-11, 17-21)
    if 8 <= hour <= 11:
        base = 1.85
    elif 17 <= hour <= 21:
        base = 2.10
    elif 12 <= hour <= 16:
        base = 1.30
    else:
        base = 1.05

    # Wards in dense commercial cores experience higher baseline friction
    if ward_id in ["WD-02", "WD-03", "WD-15"]:
        base *= 1.15
    elif ward_id in ["WD-07", "WD-11"]:
        base *= 1.10

    if is_weekend and (17 <= hour <= 21):
        base *= 1.08

    return round(base, 3)

def predict_emergency_response_time(
    network_distance_km: float,
    incident_hour: int,
    station_id: str,
    ward_id: str,
    emergency_type: str,
    rainfall_mm: float = 0.0,
    is_weekend: int = 0,
    is_monsoon: int = 0
):
    """
    Computes predicted response time with 90% prediction interval.
    """
    model, preprocessor = load_artifacts()

    # Input sanitization
    if station_id not in VALID_STATIONS:
        raise ValueError(f"Invalid station_id: '{station_id}'. Valid: {VALID_STATIONS}")
    if ward_id not in VALID_WARDS:
        raise ValueError(f"Invalid ward_id: '{ward_id}'. Valid: {VALID_WARDS}")
    if emergency_type not in VALID_EMERGENCIES:
        # fuzzy match or default
        matched = [e for e in VALID_EMERGENCIES if emergency_type.lower() in e.lower()]
        if matched:
            emergency_type = matched[0]
        else:
            raise ValueError(f"Invalid emergency_type: '{emergency_type}'. Valid: {VALID_EMERGENCIES}")

    # Estimate traffic congestion
    traffic_factor = estimate_traffic_factor(incident_hour, ward_id, is_weekend)

    # Ambient temperature proxy based on monsoon / season
    temp_c = 26.0 if is_monsoon else (33.0 if 3 <= incident_hour <= 5 else 24.0)

    # Build single-row DataFrame
    raw_dict = {
        "incident_id": ["INFERENCE-QUERY"],
        "dispatch_timestamp": [f"2024-09-15 {incident_hour:02d}:30:00"],
        "network_distance_km": [float(network_distance_km)],
        "traffic_congestion_factor": [traffic_factor],
        "rainfall_mm": [float(rainfall_mm)],
        "temperature_c": [temp_c],
        "is_monsoon": [int(is_monsoon)],
        "is_weekend": [int(is_weekend)],
        "is_peak_hour": [1 if (8 <= incident_hour <= 11 or 17 <= incident_hour <= 21) else 0],
        "incident_hour": [int(incident_hour)],
        "station_id": [station_id],
        "ward_id": [ward_id],
        "emergency_type": [emergency_type],
        "response_time_minutes": [0.0] # dummy placeholder for engineer_features
    }

    df_single = pd.DataFrame(raw_dict)
    df_engineered = engineer_features(df_single)

    # Transform through fitted preprocessor
    X_processed = preprocessor.transform(df_engineered)

    # Generate Point Prediction
    predicted_time = float(model.predict(X_processed)[0])
    predicted_time = max(2.5, round(predicted_time, 2))

    # Calculate 90% Empirical Prediction Interval based on Test Set RMSE (~1.04 mins)
    # Z-score for 90% two-tailed interval ~ 1.645
    margin = round(1.645 * 1.043, 2)
    interval_lower = max(2.0, round(predicted_time - margin, 2))
    interval_upper = round(predicted_time + margin, 2)

    # High-delay risk status
    is_high_delay_risk = predicted_time >= 20.0 or interval_upper >= 22.0

    return {
        "predicted_response_time_minutes": predicted_time,
        "prediction_interval_90_pct": (interval_lower, interval_upper),
        "traffic_congestion_factor": traffic_factor,
        "high_delay_risk": is_high_delay_risk,
        "input_parameters": {
            "network_distance_km": network_distance_km,
            "incident_hour": incident_hour,
            "station_id": station_id,
            "ward_id": ward_id,
            "emergency_type": emergency_type,
            "rainfall_mm": rainfall_mm,
            "is_weekend": bool(is_weekend),
            "is_monsoon": bool(is_monsoon)
        }
    }

def cli_interface():
    """Command-line interface for emergency dispatch simulation."""
    parser = argparse.ArgumentParser(
        description="Pune Emergency Response Time Decision-Support System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--distance", type=float, default=4.5, help="Network driving distance from station to incident scene in km")
    parser.add_argument("--hour", type=int, default=18, help="Hour of dispatch (0-23, e.g., 18 for 6:00 PM peak)")
    parser.add_argument("--station", type=str, default="FS-01", help="Responding Fire Station ID (FS-01 to FS-14)")
    parser.add_argument("--ward", type=str, default="WD-03", help="Destination Municipal Ward ID (WD-01 to WD-15)")
    parser.add_argument("--emergency", type=str, default="Commercial / Industrial Fire", help="Emergency incident category")
    parser.add_argument("--rain", type=float, default=12.0, help="Preceding hourly rainfall in mm (e.g., 0.0 for clear, 20.0 for downpour)")
    parser.add_argument("--weekend", type=int, default=0, choices=[0, 1], help="1 if Weekend (Sat/Sun), 0 if Weekday")
    parser.add_argument("--monsoon", type=int, default=1, choices=[0, 1], help="1 if Monsoon Season (June-Sept), 0 otherwise")

    args = parser.parse_args()

    result = predict_emergency_response_time(
        network_distance_km=args.distance,
        incident_hour=args.hour,
        station_id=args.station,
        ward_id=args.ward,
        emergency_type=args.emergency,
        rainfall_mm=args.rain,
        is_weekend=args.weekend,
        is_monsoon=args.monsoon
    )

    print("\n" + "=" * 80)
    print("      PUNE EMERGENCY RESPONSE TIME PREDICTION & DECISION-SUPPORT REPORT")
    print("=" * 80)
    print("OPERATIONAL PARAMETERS RECEIVED:")
    print(f"  • Responding Station:         {args.station}")
    print(f"  • Destination Ward:           {args.ward}")
    print(f"  • Driving Distance:           {args.distance:.2f} km")
    print(f"  • Dispatch Hour:              {args.hour:02d}:00 hrs ({'PEAK RUSH HOUR' if (8<=args.hour<=11 or 17<=args.hour<=21) else 'Off-Peak'})")
    print(f"  • Emergency Category:         {result['input_parameters']['emergency_type']}")
    print(f"  • Weather Conditions:         {args.rain:.1f} mm rain ({'Monsoon Season' if args.monsoon else 'Dry Season'})")
    print(f"  • Estimated Corridor Traffic: {result['traffic_congestion_factor']:.2f}x Free-Flow Baseline")

    print("\nMODEL PREDICTION & CONFIDENCE INTERVAL:")
    print(f"  ▶ ESTIMATED RESPONSE TIME:    {result['predicted_response_time_minutes']:.2f} MINUTES")
    print(f"  ▶ 90% PREDICTION INTERVAL:    [{result['prediction_interval_90_pct'][0]:.2f} min  ---  {result['prediction_interval_90_pct'][1]:.2f} min]")

    if result["high_delay_risk"]:
        print("\n  [⚠️ OPERATIONAL ALERT]: HIGH-DELAY BOTTLENECK PREDICTED (> 20 Minutes).")
        print("  Recommendation: Consider auxiliary unit pre-dispatch or traffic police corridor clearance.")
    else:
        print("\n  [✔ STATUS]: Response time within standard municipal operational thresholds.")

    print("\n" + "-" * 80)
    print("RESPONSIBLE USE & GOVERNANCE DISCLAIMER:")
    print("Predictions are statistical estimates generated from historical municipal emergency")
    print("data and road network routing. They do not represent guaranteed arrival times and")
    print("must NOT replace trained emergency dispatch judgment or emergency vehicle drivers.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    cli_interface()
