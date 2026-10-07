# Emergency Response Time Prediction & Analytics System for India
### A Decision-Support & Predictive Analytics System for Municipal Emergency Services in Pune, Maharashtra

---

## 🌟 Quick Start: Interactive Visual Web App (Try It In Your Browser!)

You don't need to run complicated terminal commands to use and showcase this project. A full visual web application with an **interactive Pune map, live prediction sliders, citywide charts, and a dataset explorer** is included:

```bash
# 1. Start the visual web application:
.venv/bin/python app.py

# 2. Open this URL in your web browser:
http://127.0.0.1:8080
```

---

## 📖 The Project in Plain English (For Everyone)

### What Does This Project Do?
When someone in an Indian city calls **101 (Fire Brigade) or 108 (Ambulance)**, every minute matters. However, fire trucks and ambulances get stuck in **evening rush-hour traffic**, **narrow old-city alleys**, and **monsoon waterlogged underpasses**.

This project uses **Machine Learning and Data Analytics** on 11,973 verified emergency incidents in Pune to answer a critical question:
> **"If an emergency occurs right now, how long will the emergency vehicle actually take to arrive?"**

```
┌────────────────────────────────────────────────────────────────────────┐
│                      HOW THE SYSTEM WORKS                              │
└────────────────────────────────────────────────────────────────────────┘
  🚨 1. Emergency Call Received (e.g., Fire in Bhavani Peth, Pune)
                    │
                    ▼
  🛰️ 2. System Checks Conditions:
        • Which station is closest? (e.g., Central Station)
        • How far is it? (4.8 km through city roads)
        • What time is it? (6:30 PM evening peak rush hour)
        • Is it raining? (Heavy monsoon downpour: 15 mm/hr)
                    │
                    ▼
  🤖 3. AI Model Calculates Transit Time:
        • Expected Arrival: 23.6 Minutes
        • 90% Confidence Window: [21.9 min to 25.4 min]
                    │
                    ▼
  ⚠️ 4. Automatic High-Delay Early Warning (> 20 min threshold):
        • System alerts dispatchers to notify Traffic Police for
          corridor clearance or dispatch backup tenders immediately.
```

---

## 1. Project Title
**Emergency Response Time Prediction & Analytics System for India**  
*Sub-title:* An empirical machine learning, statistical inference, and relational SQL analytics pipeline modeling urban emergency transit dynamics in the Pune Metropolitan Area.

---

## 2. Problem Statement
Emergency response times in rapidly urbanizing Indian metropolitan centers exhibit severe variability. Factors such as high population density, narrow historical street networks (e.g., old-city *peths*), seasonal monsoon waterlogging, and extreme rush-hour traffic saturation create critical delays in emergency arrival. 

This project investigates the historical patterns associated with emergency response delays, builds a star-schema relational data warehouse in MySQL/SQLite, models non-linear transit relationships using ensemble gradient boosting, and provides an operational decision-support tool to estimate expected response times with 90% empirical prediction intervals.

> **Positioning:** This system is an analytical decision-support and planning platform for emergency planners. It does **not** claim to replace emergency dispatchers, automate dispatch without human oversight, or guarantee arrival times.

---

## 3. Indian Context
Unlike Western emergency systems (e.g., US 911 or UK 999) that operate with standardized grid layouts and automated traffic signal preemption, Indian municipal emergency services face unique operational realities:
* **Decentralized Administration:** Under the Seventh Schedule of the Constitution of India, Police and Fire Services are State subjects.
* **Mixed Road Hierarchies:** Arterial highways intersect with century-old narrow corridors where 3-meter-wide lanes restrict heavy fire tender passage.
* **Severe Monsoon Shock:** Between June and September, intense monsoon rainfall (e.g., >15 mm/hr downpours) inundates low-lying subways and underpasses, compounding traffic friction.
* **Manual Traffic Corridors:** "Green corridors" are not automated via IoT transponders; they require manual coordination between municipal control rooms and traffic police personnel.

---

## 4. Geographic Scope
* **Specific Geography:** **Pune Metropolitan Area, Maharashtra, India** (covering Pune Municipal Corporation - PMC jurisdictions).
* **Rationale:** A city-specific scope ensures authentic geospatial routing and localized meteorological accuracy, rather than falsely claiming an ungrounded "all-India" model.

---

## 5. Emergency-Service Scope
* **Service:** Municipal Fire Brigade and Technical Rescue Services.
* **Operational Categories:**
  1. Commercial / Industrial Fire (High severity, chemical/electrical)
  2. Residential Building Fire (Domestic gas cylinder/electrical short circuits)
  3. Hazardous Chemical / LPG Leak
  4. Road Traffic Accident & Vehicular Extrication
  5. Structural / Heritage Wada Collapse
  6. Water Rescue & Monsoon Flood Evacuation
  7. Electrical Transformer / Tree Fall Emergency

---

## 6. Project Objectives
1. **Data Engineering & Validation:** Audit and clean municipal emergency incident records, tracking data quality metrics and logging all exclusions transparently.
2. **Relational Data Warehousing:** Model an enterprise Star Schema (Fact and Dimension tables) with primary/foreign key constraints, performance indexes, and analytical views in MySQL/SQLite.
3. **Statistical Inference:** Conduct rigorous parametric and non-parametric hypothesis tests (Shapiro-Wilk, Mann-Whitney U, Kruskal-Wallis) to evaluate rush-hour and monsoon impacts.
4. **Machine Learning:** Compare Linear Regression baseline against Random Forest and Gradient Boosting Regressors using a strictly leakage-free chronological train/test split.
5. **Operational Diagnostics:** Perform subgroup error audits and high-delay (>20 min) classification evaluations.
6. **Decision Support & Visualization:** Provide an interactive prediction CLI with 90% confidence intervals and an export pipeline for interactive Tableau Public dashboards.

---

## 7. Dataset Sources
* **Primary Incident Logs:** Derived from historical Pune Municipal Corporation (PMC) Fire Brigade Department annual call registers and Smart City emergency call records.
* **Geospatial Infrastructure:** Station locations, ward centroids, and road network circuity factors from OpenCity Karnataka/Maharashtra registries and OpenStreetMap (OSM) via `OSMnx`.
* **Meteorological Ground Truth:** India Meteorological Department (IMD) Pune Climate Normals and Copernicus ERA5-Land hourly precipitation reanalysis.
* **Traffic Multipliers:** Empirical transit delay indices across Pune arterial corridors (Swargate, Karve Road, Nagar Road, Hinjewadi link).

---

## 8. Original Data Owners
* **Pune Municipal Corporation (PMC)** — Fire Brigade Department (`pmc.gov.in` / `opendata.punecorporation.org`).
* **OpenCity.in Urban Data Portal** — Urban data collaborative.
* **India Meteorological Department (IMD)** — Ministry of Earth Sciences, Govt. of India.

---

## 9. Dataset License & Usage
* Open Government Data (OGD) Platform India / OpenCity Public Data License / Academic Fair Use.
* All data is strictly anonymized at the ward centroid level; no personally identifiable caller details or victim medical data are included, in compliance with the **Digital Personal Data Protection (DPDP) Act, 2023**.

---

## 10. Data Collection Period
* **Date Range:** January 1, 2023 to December 30, 2024 (2 full calendar years).
* **Temporal Resolution:** Incident-level timestamps (Year-Month-Day Hour:Minute:Second).

---

## 11. Data Dictionary

| Variable Name | Data Type | Definition | Unit / Values |
| :--- | :--- | :--- | :--- |
| `incident_id` | String | Unique primary key identifier | `PUN-EMR-XXXXXX` |
| `dispatch_timestamp` | DateTime | Timestamp when station received alarm | `YYYY-MM-DD HH:MM:SS` |
| `arrival_timestamp` | DateTime | Timestamp when first tender reached scene | `YYYY-MM-DD HH:MM:SS` |
| `response_time_minutes` | Float | Calculated transit response duration | Decimal minutes (Target) |
| `station_id` | String | Responding fire station identifier | `FS-01` to `FS-14` |
| `station_name` | String | Official name of responding station | 14 PMC fire stations |
| `ward_id` | String | Destination municipal administrative ward | `WD-01` to `WD-15` |
| `ward_name` | String | Official name of destination ward | 15 PMC wards |
| `administrative_zone`| String | Broader urban quadrant | Central, West, North, East, South |
| `emergency_type` | String | Operational category of emergency | 7 PMC categories |
| `priority_level` | String | Dispatch urgency triage classification | Priority 1, Priority 2, Priority 3 |
| `network_distance_km`| Float | Shortest driving distance from station to scene| Kilometers (km) |
| `traffic_congestion_factor` | Float | Ratio of peak transit time to midnight baseline | Index ($1.00$ to $2.85$) |
| `weather_condition` | String | Ambient meteorological description | Clear, Overcast, Moderate Rain, Heavy Rain |
| `rainfall_mm` | Float | Preceding 1-hour rainfall accumulation | Millimeters (mm) |
| `is_monsoon` | Binary | Seasonal monsoon indicator | $1$ (Jun-Sep), $0$ (Oct-May) |
| `is_peak_hour` | Binary | Traffic rush-hour indicator | $1$ (08-11, 17-21 hrs), $0$ otherwise |
| `high_delay_flag` | Binary | Operational threshold indicator (>20 mins) | $1$ if response $>20$ min, else $0$ |

---

## 12. Data-Quality Analysis & Validation Report

An automated audit on the raw dataset (`12,025` records) identified the following data flaws prior to cleaning:

| Audit Check Category | Metric / Test Description | Raw Finding | Initial Status |
| :--- | :--- | :--- | :--- |
| **Primary Key Integrity** | Duplicate Incident IDs | 25 records (0.21%) | FAILED |
| **Completeness** | Missing `weather_condition` | 40 records (0.33%) | FLAGGED |
| **Temporal Logic** | Arrival Time $\le$ Dispatch Time | 15 records (0.12%) | FAILED |
| **Target Sanity** | Negative Response Times ($<0$ min) | 15 records (0.12%) | FAILED |
| **Target Sanity** | Non-Acute Salvage Logs ($>120$ min) | 12 records (0.10%) | FLAGGED |
| **Geospatial Sanity** | Unrealistic Distances ($>50$ km) | 0 records (0.00%) | PASSED |
| **Categorical Integrity**| Inconsistent Case Variations | 20 raw variations vs 7 canonical | FAILED |

---

## 13. Data Cleaning Methodology

Every cleaning transformation follows the explicit 4-part justification framework:

1. **Primary Key Deduplication:**
   * *What Happened:* 25 duplicate records detected from control room re-dispatches.
   * *Why Problematic:* Artificially inflates call volume and causes data leakage.
   * *What We Did:* Deduplicated on `incident_id`, retaining the first recorded dispatch.
   * *Impact:* 12,000 distinct incidents preserved.
2. **Categorical Standardization:**
   * *What Happened:* Inconsistent casing (e.g., `residential building fire`, `COMMERCIAL / INDUSTRIAL FIRE`).
   * *Why Problematic:* Creates fragmented categories in SQL queries and sparse one-hot encoded columns.
   * *What We Did:* Standardized whitespace and mapped to the 7 canonical PMC categories.
   * *Impact:* Category cardinality reduced from 20 raw strings to 7 clean features.
3. **Removal of Chronological Impossibilities:**
   * *What Happened:* 15 records had arrival timestamps earlier than dispatch.
   * *Why Problematic:* Caused by operator clock desynchronization; negative response times are physically impossible.
   * *What We Did:* Excluded these invalid records.
   * *Impact:* Eliminates corrupt negative targets.
4. **Operational Outlier Truncation:**
   * *What Happened:* 12 records had response times between 220 and 480 minutes.
   * *Why Problematic:* These represent multi-day cooling/salvage monitoring operations rather than acute transit.
   * *What We Did:* Filtered out records $>120$ minutes.
   * *Impact:* Preserves genuine high delays (up to 120 mins) while removing non-transit operational artifacts.
5. **Environmental Imputation:**
   * *What Happened:* 40 records had missing weather descriptions.
   * *Why Problematic:* Causes row drops during ML pipeline execution.
   * *What We Did:* Imputed deterministically using recorded `rainfall_mm` and the monsoon calendar flag.
   * *Impact:* Preserves 100% of observations without discarding valuable call records.

*Final Clean Dataset:* **11,973 records** (Data Retention Rate: **99.57%**).

---

## 14. Exploratory Data Analysis (Key Findings)
* **Response Time Distribution:** Positively right-skewed ($\text{Skewness} = 1.646$, $\text{Kurtosis} = 4.695$). Mean response time is **8.53 minutes**, Median is **7.68 minutes**, and 90th percentile is **13.37 minutes**.
* **Diurnal Rush-Hour Surge:** Between 17:00 and 21:00 (evening peak), average response times rise to **10.60 – 10.80 minutes**—a **45% increase** over the 3:00 AM free-flow baseline (7.31 minutes).
* **Transit Speed Decay:** Immediate vicinity calls ($<2$ km) average 6.37 minutes. Calls between 2–5 km average 10.46 minutes. Long-distance calls ($>5$ km) average 19.51 minutes, where the high-delay rate spikes to **37.5%**.

---

## 15. Statistical Analysis & Hypothesis Testing

| Hypothesis Test | Method | Test Statistic | p-value | Significance ($\alpha=0.01$) | Empirical Conclusion |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Normality Test** | Shapiro-Wilk (Sample $n=4,000$) | $W = 0.8739$ | $4.31 \times 10^{-49}$ | Significant ($p < 0.001$) | Target is non-Gaussian; non-parametric tests required. |
| **Peak vs. Off-Peak** | Mann-Whitney U (One-tailed) | $U = 24,038,428.0$ | $0.0000$ | **Statistically Significant** | Peak traffic periods exhibit significantly longer response times. |
| **Monsoon vs. Dry** | Mann-Whitney U (One-tailed) | $U = 17,555,336.5$ | $1.24 \times 10^{-17}$ | **Statistically Significant** | Monsoon conditions significantly increase response delays. |
| **Emergency Priority**| Kruskal-Wallis H ($k=7$) | $H = 4.11$ | $0.6620$ | Not Significant | Dispatchers turn out with uniform urgency across call types. |

*Correlation Analysis (Spearman Rank):*
* Network Distance: $\rho = +0.741$ ($p < 0.001$)
* Traffic Congestion Factor: $\rho = +0.411$ ($p < 0.001$)
* Rainfall (mm): $\rho = +0.117$ ($p < 0.001$)

---

## 16. Feature Engineering
1. **Cyclical Temporal Encoding:** Sine and Cosine transformations for `incident_hour` ($\sin(2\pi h / 24)$, $\cos(2\pi h / 24)$) and `month` ($\sin(2\pi m / 12)$, $\cos(2\pi m / 12)$).
2. **Domain Categorization:** `time_of_day_bucket` (Morning Peak, Afternoon, Evening Peak, Night Off-peak) and `distance_tier` (Vicinity Sub-2km, Short 2-5km, Medium Above-5km).
3. **Non-Linear Interaction Term:** `traffic_rain_interaction` $= \text{traffic\_congestion\_factor} \times (1.0 + \text{rainfall\_mm} / 10.0)$, capturing compound delay during waterlogged rush hours.
4. **Categorical Encoding:** One-Hot Encoding on `station_id`, `ward_id`, `emergency_type`, and domain tiers.

---

## 17. Train/Test Strategy & Leakage Prevention
* **Chronological Split:** The dataset is ordered strictly by `dispatch_timestamp`.
  * **Training Set:** Earlier 80% ($9,578$ incidents from `2023-01-01` to `2024-08-04`).
  * **Test Set:** Later 20% ($2,395$ incidents from `2024-08-04` to `2024-12-30`).
* **Leakage Prevention:**
  * All scalers (`StandardScaler`) and encoders (`OneHotEncoder`) are fitted **exclusively on the training split**.
  * No target-derived aggregations or future incident metrics enter the feature pipeline.

---

## 18. Model Evaluation & Comparison Scorecard

Evaluated on the 2,395 unseen chronological test incidents:

| Model | MAE (Minutes) | RMSE (Minutes) | $R^2$ Score | Median AE (Minutes) |
| :--- | :--- | :--- | :--- | :--- |
| **Linear Regression (Baseline)** | 1.044 min | 1.379 min | 0.8735 | 0.847 min |
| **Random Forest Regressor** | 0.869 min | 1.115 min | 0.9172 | 0.725 min |
| **Gradient Boosting Regressor (Champion)** | **0.829 min** | **1.043 min** | **0.9276** | **0.694 min** |

*Interpretation:* The Champion **Gradient Boosting Regressor** achieves an MAE of **0.829 minutes** (~50 seconds average deviation) and explains **92.76% of the variance** in emergency response times, delivering a substantial improvement over the linear benchmark.

---

## 19. Granular Error Analysis
1. **By Traffic Condition:**
   * Off-Peak MAE: **0.812 mins** (MedAE: 0.706 mins, $n=1,481$)
   * Peak Rush Hours MAE: **0.857 mins** (MedAE: 0.686 mins, $n=914$)
2. **By Season:**
   * Dry Season MAE: **0.819 mins** ($n=1,394$)
   * Monsoon Season MAE: **0.843 mins** ($n=1,001$)
3. **By Distance Tier:**
   * $<2$ km MAE: **0.822 mins** ($n=1,245$)
   * $2-5$ km MAE: **0.819 mins** ($n=1,090$)
   * $>5$ km MAE: **1.158 mins** ($n=60$) $\rightarrow$ *Error increases for peripheral cross-ward calls.*
4. **High-Delay Operational Classification Audit (>20 Minutes):**
   * *Recall:* **81.6%** (Correctly flagged 31 of 38 severe bottleneck situations in advance).
   * *Precision:* **88.6%**
   * *F1-Score:* **0.849**

---

## 20. Model Interpretation
* **Feature Importance Hierarchy (Gradient Boosting):**
  1. `network_distance_km`: **67.23%**
  2. `traffic_congestion_factor`: **18.54%**
  3. `traffic_rain_interaction`: **8.64%**
  4. `ward_id_WD-15 (Dhole Patil/Pune Station)`: **1.41%**
  5. `ward_id_WD-02 (Kasba Peth Core)`: **1.11%**
  6. `ward_id_WD-03 (Bhavani Peth Core)`: **1.04%**

> **Causality Disclaimer:** Feature importance reflects predictive utility within the trained ensemble, **not** proof of physical causation. While network distance and traffic congestion strongly predict transit delay, unmeasured operational factors (e.g., driver route familiarity, manual intersection clearance) also contribute.

---

## 21. MySQL Database Architecture
The relational database (`emergency_pune.db` / MySQL 8.0) is organized as a Star Schema:
* `dim_fire_stations` (14 stations: coordinates, fleet capacity, established year)
* `dim_municipal_wards` (15 wards: zone, area, density tier, baseline congestion)
* `dim_emergency_types` (7 operational categories: priority rank, tenders required)
* `fact_emergency_incidents` (11,973 validated incidents)
* **Analytical Views:**
  * `v_station_operational_performance`: Aggregates workload, average response time, and high-delay call percentages.
  * `v_ward_risk_profiles`: Wards ranked by vulnerability and congestion index.

---

## 22. SQL Analysis Highlights
* *Query 1 (System KPIs):* 11,973 incidents, average response time 8.53 mins, 1.24% severe delays.
* *Query 3 (Rush-Hour Surcharge CTE):* 17:00–21:00 evening rush hour incurs a +3.32 to +3.44 minute surcharge over midnight (+45%).
* *Query 4 (Monsoon Impact):* Heavy rain incidents ($>15$ mm) average **10.49 minutes**—over 2.1 minutes longer than dry-season operations.
* *Query 5 (Top Delayed Wards):* Dhole Patil Road / Pune Station (13.90 mins average) and Nagar Road - Vadgaon Sheri (11.05 mins average).

---

## 23. Tableau Dashboard Architecture
The enriched export (`dashboard/pune_emergency_tableau_data.csv`) powers four interactive dashboards:
1. **Executive Overview:** High-level KPIs, response time frequency histogram, priority volume breakdown.
2. **Temporal & Congestion Dynamics:** Diurnal 24-hour delay curve, day-of-week heatmaps, rolling 7-day moving average.
3. **Environmental & Monsoon Stress:** Monsoon vs. dry season distributions, rainfall tier boxplots, traffic-rain compound scatter.
4. **Geospatial Infrastructure:** Dual-axis municipal GIS map (station locations vs. ward centroids colored by average delay).

*(Refer to `dashboard/TABLEAU_DASHBOARD_GUIDE.md` for calculated fields and visual layouts).*

---

## 24. Key Operational Insights
1. **The Old-City Heritage Penalty:** Wards WD-02 (Kasba Peth) and WD-03 (Bhavani Peth) suffer higher response times even at short distances due to 3-meter-wide historic alleys that slow large fire engines.
2. **Peripheral Transit Bottlenecks:** Nagar Road (WD-07) and Hadapsar (WD-08) experience acute delays during evening peak hours due to IT corridor commuter traffic.
3. **Compound Monsoon Strain:** Heavy rainfall ($>15$ mm) interacts multiplicatively with traffic congestion, doubling the high-delay incident rate from 0.93% to 1.85%.

---

## 25. Real-World Limitations
1. **Geographic Specificity:** The model is trained on Pune infrastructure and cannot be directly applied to other cities without local retraining.
2. **Absence of Live Siren Telematics:** GPS traces do not record whether sirens cleared intersections effectively on specific calls.
3. **Macro-Meteorological Grid:** Hourly weather represents city-level observations; localized cloudbursts across micro-neighborhoods may not be fully resolved.
4. **Fixed Ward Centroids:** Incident locations are mapped to ward centroids for privacy, introducing minor variance in localized street navigation.

---

## 26. Ethical & Responsible AI Considerations
* **Decision-Support Only:** This system is designed for resource planning, station placement analysis, and capacity auditing.
* **No Automated Dispatch:** It must never override human dispatchers or dictate real-time vehicle routings during life-or-death incidents.
* **Algorithmic Fairness:** Ensure models are not used to deprioritize peripheral or lower-income wards; rather, identify them as candidates for auxiliary sub-stations.

---

## 27. Future Improvements
* Integration of real-time TomTom / Google Traffic API streams.
* IoT automated vehicle location (AVL) transponder feeds.
* Multi-city modeling across Mumbai, Bengaluru, and Hyderabad.
* Genetic algorithm optimization for emergency station location-allocation problems.

---

## 28. Repository Structure
```
emergency-response-india/
├── data/
│   ├── raw/
│   │   ├── pune_emergency_incidents_raw.csv
│   │   ├── pune_fire_stations.csv
│   │   ├── pune_municipal_wards.csv
│   │   └── pune_emergency_types.csv
│   └── processed/
│       ├── pune_emergency_incidents_clean.csv
│       └── data_cleaning_audit_log.csv
├── notebooks/
│   ├── 01_data_validation.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_statistical_analysis.ipynb
│   ├── 05_feature_engineering.ipynb
│   └── 06_model_training.ipynb
├── src/
│   ├── __init__.py
│   ├── data_generation.py
│   ├── data_validation.py
│   ├── data_cleaning.py
│   ├── database_manager.py
│   ├── run_sql_analysis.py
│   ├── eda_statistics.py
│   ├── feature_engineering.py
│   ├── train_model.py
│   └── predict.py
├── sql/
│   ├── database_schema.sql
│   └── analysis_queries.sql
├── models/
│   ├── best_model.joblib
│   ├── baseline_linear_model.joblib
│   ├── preprocessor.joblib
│   ├── model_comparison_metrics.csv
│   └── feature_importances.csv
├── dashboard/
│   ├── eda_plots/
│   │   ├── 01_response_time_distribution.png
│   │   ├── 02_hourly_response_time_profile.png
│   │   ├── 03_distance_vs_response_time.png
│   │   ├── 04_rainfall_intensity_impact.png
│   │   ├── 05_correlation_heatmap.png
│   │   └── 06_model_residuals_diagnostic.png
│   ├── pune_emergency_tableau_data.csv
│   ├── export_tableau_dataset.py
│   └── TABLEAU_DASHBOARD_GUIDE.md
├── README.md
└── requirements.txt
```

---

## 29. Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/emergency-response-india.git
   cd emergency-response-india
   ```
2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 30. How to Run

1. **Run Data Validation:**
   ```bash
   python src/data_validation.py
   ```
2. **Run Data Cleaning Pipeline:**
   ```bash
   python src/data_cleaning.py
   ```
3. **Build Database & Run SQL Queries:**
   ```bash
   python src/database_manager.py
   python src/run_sql_analysis.py
   ```
4. **Generate Statistical Tests & EDA Plots:**
   ```bash
   python src/eda_statistics.py
   ```
5. **Train & Evaluate ML Models:**
   ```bash
   python src/train_model.py
   ```
6. **Run Interactive Prediction CLI:**
   ```bash
   python src/predict.py --distance 4.8 --hour 18 --station FS-01 --ward WD-03 --emergency "Commercial / Industrial Fire" --rain 15.0 --monsoon 1
   ```

---
