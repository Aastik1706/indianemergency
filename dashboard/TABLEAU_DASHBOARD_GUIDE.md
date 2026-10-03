# Tableau Public Dashboard Guide: Pune Emergency Response Analytics System

This guide provides step-by-step instructions for constructing the interactive, multi-tab **Tableau Public** dashboard using the export dataset:
`dashboard/pune_emergency_tableau_data.csv`

---

## Data Source Setup in Tableau Public

1. Open **Tableau Public** (or Tableau Desktop).
2. Under **Connect to a File**, select **Text file** and browse to `dashboard/pune_emergency_tableau_data.csv`.
3. Verify that geographical roles are assigned:
   * `station_latitude` & `ward_centroid_lat` $\rightarrow$ Geographic Role: **Latitude**
   * `station_longitude` & `ward_centroid_lon` $\rightarrow$ Geographic Role: **Longitude**
   * `incident_date` $\rightarrow$ Data Type: **Date**
   * `dispatch_timestamp` $\rightarrow$ Data Type: **Date & Time**

---

## Recommended Calculated Fields in Tableau

Create the following calculated fields in the Data pane (`Analysis > Create Calculated Field`):

```tableau
// 1. High Delay Rate (%)
SUM([High Delay Flag]) / COUNT([Incident Id])

// 2. Average Transit Speed (km/h)
AVG([Effective Speed Kmh])

// 3. Peak Hour Classification
IF [Is Peak Hour] = 1 THEN "Peak Rush Hour (08-11, 17-21)"
ELSE "Off-Peak Hours"
END

// 4. Season Name
IF [Is Monsoon] = 1 THEN "Monsoon Season (Jun - Sep)"
ELSE "Dry / Summer Season (Oct - May)"
END

// 5. Model Prediction Error (Minutes)
AVG([Residual Error Min])
```

---

## Dashboard Specifications

### Dashboard 1 — Emergency Response Executive Overview
* **Target Audience:** Municipal Commissioner, Chief Fire Officer, Smart City Operations Directors.
* **Layout Structure:**
  * **Top KPI Scorecard (4 Big Number Cards):**
    * Total Incidents Attended (`COUNT(Incident Id)`) $\rightarrow$ **11,973**
    * Citywide Average Response Time (`AVG(Response Time Minutes)`) $\rightarrow$ **8.53 Minutes**
    * Median Response Time (`MEDIAN(Response Time Minutes)`) $\rightarrow$ **7.68 Minutes**
    * Critical High Delay Incidents (>20 mins) $\rightarrow$ **148 Incidents (1.24%)**
  * **Main Visual (Left 60%):** Response Time Frequency Distribution (Histogram with reference lines for Median and 90th percentile).
  * **Secondary Visual (Right 40%):** Priority Breakdown: Response time vs. call volume across Priority 1 (Critical), Priority 2 (Urgent), and Priority 3 (Standard).
  * **Global Filters:** Date Range slider, Responding Station dropdown, Emergency Category multi-select.

### Dashboard 2 — Temporal & Congestion Dynamics
* **Target Audience:** Dispatch Planners, Traffic Police Liaisons.
* **Layout Structure:**
  * **Chart 1 (Top):** 24-Hour Diurnal Response Curve (Dual-axis Line Chart: Hour of day on X-axis; Average Response Time on primary Y-axis, Congestion Index on secondary Y-axis). Highlights the 45% delay surge during 17:00–21:00 evening rush hour.
  * **Chart 2 (Bottom Left):** Day of Week & Weekend Variance (Heatmap or Bar Chart comparing Monday–Sunday transit times).
  * **Chart 3 (Bottom Right):** 7-Day Rolling Moving Average (Area chart showing longitudinal drift across 2023–2024).

### Dashboard 3 — Environmental & Monsoon Weather Stress Analysis
* **Target Audience:** Disaster Management Authority, Flood Response Teams.
* **Layout Structure:**
  * **Chart 1:** Monsoon vs. Dry Season Comparative Distribution (Box-and-whisker plots showing the shift from 8.31 min to 8.96 min general monsoon, and 10.49 min during intense downpours).
  * **Chart 2:** Rainfall Intensity Tier Impact (Bar chart: No Rain, Light <5mm, Moderate 5-15mm, Heavy >15mm).
  * **Chart 3:** Traffic $\times$ Rainfall Compound Matrix (Scatter plot: X=Congestion Factor, Y=Response Time, Color=Rainfall mm, Size=Distance km).

### Dashboard 4 — Geospatial Infrastructure & Ward Bottlenecks
* **Target Audience:** Municipal Urban Planners, Infrastructure Engineers.
* **Layout Structure:**
  * **Map Visual:** Dual-axis Municipal Map:
    * Layer 1: Fire Station locations (Distinct red shield icons sized by `fleet_capacity`).
    * Layer 2: Ward centroids (Circles colored by `Average Response Time` using a Green-Amber-Red divergence palette).
  * **Bar Chart (Ranked):** Top 5 Most Vulnerable Wards (Dhole Patil/Pune Station, Nagar Road, Wanowrie, Shivaji Nagar, Dhankawadi).
  * **Scatter Plot:** Station-to-Scene Network Distance vs. Observed Response Time (Fitted trendline showing slope $\approx 1.8\text{ min/km}$).

---

## Publishing to Tableau Public

1. In Tableau, navigate to **Server > Tableau Public > Save to Tableau Public As...**
2. Name the workbook: `Pune_Emergency_Response_Analytics_System`.
3. Enable "Allow others to download the workbook and its data" for open interview portfolio verification.
4. Copy the public dashboard share link and embed it into your project README.
