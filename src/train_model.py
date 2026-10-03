"""
train_model.py - Machine Learning Model Training, Comparison, Error Analysis & Interpretation

WHAT are we doing?
We are training, cross-evaluating, and diagnosing three distinct regression models:
1. Linear Regression (Interpretable Baseline Benchmark)
2. Random Forest Regressor (Non-linear Bagging Ensemble)
3. Gradient Boosting Regressor (Sequential Gradient Boosted Decision Trees)
All models are evaluated on the strictly holdout chronological test set.

WHY are we doing it?
To establish whether complex tree-based non-linear ensembles deliver genuine, justifiable
improvements over a simple linear baseline, and to rigorously audit where the models make errors
(e.g., peak-hour traffic bottlenecks or heavy monsoon downpours).

HOW does it help?
It produces a comprehensive model comparison scorecard (MAE, RMSE, R², MedAE), feature
importance rankings, residual diagnostic charts, and segmented subgroup error analyses,
which form the core talking points for a Data Science / ML interview.
"""

import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score, median_absolute_error

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.feature_engineering import prepare_train_test_data

def evaluate_predictions(y_true, y_pred, model_name="Model"):
    """Calculates standardized regression metrics and returns dictionary."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    medae = median_absolute_error(y_true, y_pred)
    
    return {
        "Model": model_name,
        "MAE (mins)": round(mae, 3),
        "RMSE (mins)": round(rmse, 3),
        "R2 Score": round(r2, 4),
        "Median AE (mins)": round(medae, 3)
    }

def train_and_evaluate_all():
    print("=" * 80)
    print("      MACHINE LEARNING PIPELINE: TRAINING, EVALUATION & INTERPRETATION")
    print("=" * 80)

    # 1. Load data and split
    X_train_raw, X_test_raw, y_train, y_test, preprocessor, train_df, test_df = prepare_train_test_data()

    X_train = preprocessor.transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)

    print(f"\n✔ Preprocessed Feature Matrix Shapes:")
    print(f"  • X_train: {X_train.shape} | X_test: {X_test.shape}")

    # Extract transformed feature names
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = cat_encoder.get_feature_names_out()
    num_feature_names = preprocessor.transformers[0][2]
    bin_feature_names = preprocessor.transformers[1][2]
    all_feature_names = list(num_feature_names) + list(bin_feature_names) + list(cat_feature_names)

    # -------------------------------------------------------------------------
    # MODEL 1: LINEAR REGRESSION BASELINE
    # -------------------------------------------------------------------------
    print("\n[TRAINING MODEL 1/3] Linear Regression (Baseline Benchmark)...")
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)
    metrics_lr = evaluate_predictions(y_test, y_pred_lr, "Linear Regression (Baseline)")

    # -------------------------------------------------------------------------
    # MODEL 2: RANDOM FOREST REGRESSOR
    # -------------------------------------------------------------------------
    print("[TRAINING MODEL 2/3] Random Forest Regressor (Non-linear Bagging)...")
    rf = RandomForestRegressor(
        n_estimators=150,
        max_depth=14,
        min_samples_split=6,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    metrics_rf = evaluate_predictions(y_test, y_pred_rf, "Random Forest Regressor")

    # -------------------------------------------------------------------------
    # MODEL 3: GRADIENT BOOSTING REGRESSOR
    # -------------------------------------------------------------------------
    print("[TRAINING MODEL 3/3] Gradient Boosting Regressor (Boosted Decision Trees)...")
    gb = GradientBoostingRegressor(
        n_estimators=160,
        learning_rate=0.07,
        max_depth=5,
        subsample=0.85,
        random_state=42
    )
    gb.fit(X_train, y_train)
    y_pred_gb = gb.predict(X_test)
    metrics_gb = evaluate_predictions(y_test, y_pred_gb, "Gradient Boosting Regressor")

    # -------------------------------------------------------------------------
    # MODEL COMPARISON SCORECARD
    # -------------------------------------------------------------------------
    comparison_df = pd.DataFrame([metrics_lr, metrics_rf, metrics_gb])
    print("\n" + "=" * 80)
    print("                  MODEL EVALUATION SCORECARD (TEST SET)")
    print("=" * 80)
    print(comparison_df.to_string(index=False))
    print("=" * 80)

    # Determine Best Model (lowest MAE)
    best_model_name = comparison_df.sort_values("MAE (mins)").iloc[0]["Model"]
    best_model = gb if "Gradient" in best_model_name else rf
    best_preds = y_pred_gb if "Gradient" in best_model_name else y_pred_rf
    print(f"✔ Champion Model Selected: {best_model_name}")

    # Save Models
    joblib.dump(best_model, "models/best_model.joblib")
    joblib.dump(lr, "models/baseline_linear_model.joblib")
    comparison_df.to_csv("models/model_comparison_metrics.csv", index=False)
    print("✔ Model artifacts saved to 'models/' directory.")

    # -------------------------------------------------------------------------
    # SUBGROUP ERROR ANALYSIS
    # -------------------------------------------------------------------------
    test_eval_df = test_df.copy()
    test_eval_df["predicted_response_time"] = best_preds
    test_eval_df["residual_error"] = test_eval_df["response_time_minutes"] - test_eval_df["predicted_response_time"]
    test_eval_df["absolute_error"] = np.abs(test_eval_df["residual_error"])

    print("\n" + "=" * 80)
    print("                  GRANULAR SUBGROUP ERROR ANALYSIS")
    print("=" * 80)

    # Subgroup 1: Peak vs Off-Peak
    peak_err = test_eval_df.groupby("is_peak_hour")["absolute_error"].agg(["count", "mean", "median", "std"]).reset_index()
    peak_err["is_peak_hour"] = peak_err["is_peak_hour"].map({1: "Peak Rush Hours (08-11, 17-21)", 0: "Off-Peak Hours"})
    print("\n1. Error by Traffic Period:")
    print(peak_err.rename(columns={"mean": "MAE (mins)", "median": "MedAE (mins)"}).to_string(index=False))

    # Subgroup 2: Monsoon Season vs Dry Season
    mon_err = test_eval_df.groupby("is_monsoon")["absolute_error"].agg(["count", "mean", "median", "std"]).reset_index()
    mon_err["is_monsoon"] = mon_err["is_monsoon"].map({1: "Monsoon Season (Jun-Sep)", 0: "Dry Season"})
    print("\n2. Error by Season:")
    print(mon_err.rename(columns={"mean": "MAE (mins)", "median": "MedAE (mins)"}).to_string(index=False))

    # Subgroup 3: Distance Tiers
    dist_err = test_eval_df.groupby("distance_tier")["absolute_error"].agg(["count", "mean", "median", "std"]).reset_index()
    print("\n3. Error by Distance Tier:")
    print(dist_err.rename(columns={"mean": "MAE (mins)", "median": "MedAE (mins)"}).to_string(index=False))

    # Subgroup 4: High-Delay Incident Identification (>20 mins)
    actual_high = (test_eval_df["response_time_minutes"] > 20.0).astype(int)
    pred_high = (test_eval_df["predicted_response_time"] > 20.0).astype(int)
    
    tp = ((actual_high == 1) & (pred_high == 1)).sum()
    fp = ((actual_high == 0) & (pred_high == 1)).sum()
    fn = ((actual_high == 1) & (pred_high == 0)).sum()
    tn = ((actual_high == 0) & (pred_high == 0)).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    print("\n4. High-Delay Identification Audit (> 20 Minutes Threshold):")
    print(f"  • True Positives (Correctly Flagged High Delays): {tp}")
    print(f"  • False Negatives (Missed High Delays):           {fn}")
    print(f"  • False Positives (Falsely Alarmed):             {fp}")
    print(f"  • Recall:    {recall*100:.1f}%")
    print(f"  • Precision: {precision*100:.1f}%")
    print(f"  • F1 Score:  {f1:.3f}")

    # -------------------------------------------------------------------------
    # FEATURE IMPORTANCE & INTERPRETATION
    # -------------------------------------------------------------------------
    importances = best_model.feature_importances_
    feat_imp_df = pd.DataFrame({
        "Feature": all_feature_names,
        "Importance": importances
    }).sort_values("Importance", ascending=False)

    print("\n" + "=" * 80)
    print("      TOP 10 MOST INFLUENTIAL PREDICTIVE FEATURES (CHAMPION MODEL)")
    print("=" * 80)
    print(feat_imp_df.head(10).to_string(index=False))
    print("\n[CRITICAL INTERPRETATION NOTE FOR INTERVIEWS]:")
    print("Feature importance quantifies how heavily the decision trees rely on a variable to")
    print("reduce variance in the target. It reflects PREDICTIVE RELEVANCE, NOT CAUSAL PROOF.")
    print("For example, high importance of network distance and traffic congestion indicates that")
    print("spatial routing and time-of-day flow are strongly associated with transit duration.")
    feat_imp_df.to_csv("models/feature_importances.csv", index=False)

    # -------------------------------------------------------------------------
    # RESIDUAL DIAGNOSTICS VISUALIZATION
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Actual vs Predicted
    axes[0].scatter(y_test, best_preds, alpha=0.4, color="#1f77b4", s=20)
    min_val = min(y_test.min(), best_preds.min())
    max_val = max(y_test.max(), best_preds.max())
    axes[0].plot([min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="Perfect Fit (y = x)")
    axes[0].set_title(f"Observed vs. Predicted Response Times ({best_model_name})", fontweight="bold")
    axes[0].set_xlabel("Actual Response Time (Minutes)")
    axes[0].set_ylabel("Predicted Response Time (Minutes)")
    axes[0].legend()

    # Residuals vs Predicted
    residuals = y_test - best_preds
    axes[1].scatter(best_preds, residuals, alpha=0.4, color="#ff7f0e", s=20)
    axes[1].axhline(0, color="black", linestyle="--", linewidth=1.5)
    axes[1].set_title("Residual Plot (Homoscedasticity Audit)", fontweight="bold")
    axes[1].set_xlabel("Predicted Response Time (Minutes)")
    axes[1].set_ylabel("Residual (Actual - Predicted, Minutes)")
    
    plt.tight_layout()
    diag_path = "dashboard/eda_plots/06_model_residuals_diagnostic.png"
    plt.savefig(diag_path, dpi=300)
    plt.close()
    print(f"\n✔ Model diagnostic plot saved to: {diag_path}")

    return comparison_df, feat_imp_df

if __name__ == "__main__":
    train_and_evaluate_all()
