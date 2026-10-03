"""
run_sql_analysis.py - Executes and validates all analytical SQL queries from analysis_queries.sql
"""

import sqlite3
import pandas as pd

def run_all_queries(db_path="emergency_pune.db", sql_file="sql/analysis_queries.sql"):
    conn = sqlite3.connect(db_path)
    
    with open(sql_file, "r") as f:
        content = f.read()

    # Split on comments that denote queries
    sections = content.split("-- QUERY ")
    print("=" * 80)
    print("      EXECUTING ADVANCED SQL ANALYTICAL SUITE ON EMERGENCY DATABASE")
    print("=" * 80)

    for i, section in enumerate(sections[1:], 1):
        lines = section.strip().split("\n")
        title = lines[0].strip()
        
        # Skip comment lines
        sql_lines = []
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("--") or not stripped:
                continue
            sql_lines.append(line)
            
        sql_text = "\n".join(sql_lines).strip()
        if not sql_text:
            continue

        print(f"\n--- [SQL QUERY {i}] {title} ---")
        try:
            res_df = pd.read_sql_query(sql_text, conn)
            print(res_df.to_string(index=False))
        except Exception as e:
            print(f"Error executing query {i}: {e}")

    conn.close()
    print("\n" + "=" * 80)
    print("✔ All analytical queries executed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    run_all_queries()
