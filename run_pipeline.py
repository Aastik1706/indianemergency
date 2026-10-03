"""
run_pipeline.py - Master Pipeline Execution Script
Runs the entire end-to-end Emergency Response Analytics & ML pipeline sequentially.
"""

import os
import sys
import subprocess

def run_step(step_num, title, script_path):
    print("\n" + "=" * 80)
    print(f"[{step_num}/7] RUNNING: {title}")
    print(f"      Script: {script_path}")
    print("=" * 80)
    
    python_bin = sys.executable
    result = subprocess.run([python_bin, script_path], capture_output=False)
    if result.returncode != 0:
        print(f"\n❌ Error encountered in step {step_num} ({script_path})")
        sys.exit(result.returncode)
    print(f"✔ Step {step_num} completed successfully.")

def main():
    print("=" * 80)
    print("   STARTING END-TO-END PUNE EMERGENCY RESPONSE ANALYTICS PIPELINE")
    print("=" * 80)

    # Step 1: Data Generation
    run_step(1, "Authentic Dataset Generation", "src/data_generation.py")

    # Step 2: Data Validation Audit
    run_step(2, "Data Integrity & Quality Audit", "src/data_validation.py")

    # Step 3: Data Cleaning
    run_step(3, "Justified Data Cleaning & Imputation", "src/data_cleaning.py")

    # Step 4: Database Setup & SQL Analytics
    run_step(4, "Database Ingestion & Schema Build", "src/database_manager.py")
    run_step(5, "Advanced SQL Query Execution", "src/run_sql_analysis.py")

    # Step 5: Statistical Hypothesis Testing & EDA
    run_step(6, "Statistical Testing & EDA Visualization", "src/eda_statistics.py")

    # Step 6: ML Model Training & Subgroup Error Analysis
    run_step(7, "Machine Learning Training & Scorecard", "src/train_model.py")

    # Step 7: Export Tableau Dataset
    print("\n" + "=" * 80)
    print("[BONUS] Exporting Denormalized Tableau Public Dataset...")
    print("=" * 80)
    subprocess.run([sys.executable, "dashboard/export_tableau_dataset.py"])

    print("\n" + "=" * 80)
    print("🎉 FULL PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("You can now:")
    print("  1. Run interactive predictions: python src/predict.py --distance 4.5 --hour 18")
    print("  2. Inspect charts in: dashboard/eda_plots/")
    print("  3. View Tableau dataset in: dashboard/pune_emergency_tableau_data.csv")
    print("  4. Open notebooks in: notebooks/")
    print("=" * 80)

if __name__ == "__main__":
    main()
