-- ============================================================================
-- SQL ANALYTICAL QUERIES: PUNE EMERGENCY RESPONSE TIME SYSTEM
-- Demonstrates: Basic Aggregations, Multi-Table JOINs, Subqueries, CTEs,
-- Window Functions, Rolling Averages, and Percentile Distributions.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: System-Wide Executive KPIs
-- Objective: Calculate overall incident volume, mean, median, min, max, and high-delay rate.
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_emergency_incidents,
    ROUND(AVG(response_time_minutes), 2) AS overall_avg_response_time_min,
    ROUND(MIN(response_time_minutes), 2) AS min_response_time_min,
    ROUND(MAX(response_time_minutes), 2) AS max_response_time_min,
    ROUND(AVG(network_distance_km), 2) AS avg_transit_distance_km,
    SUM(high_delay_flag) AS total_high_delay_incidents,
    ROUND(SUM(high_delay_flag) * 100.0 / COUNT(*), 2) AS high_delay_percentage
FROM fact_emergency_incidents;

-- ----------------------------------------------------------------------------
-- QUERY 2: Response Time Metrics by Emergency Incident Category (Priority Ranking)
-- Objective: Compare average response times across Priority 1, 2, and 3 emergencies.
-- ----------------------------------------------------------------------------
SELECT 
    t.priority,
    t.name AS emergency_category,
    t.tenders_required,
    COUNT(f.incident_id) AS total_calls,
    ROUND(AVG(f.response_time_minutes), 2) AS avg_response_time_min,
    ROUND(AVG(f.network_distance_km), 2) AS avg_distance_km,
    ROUND(AVG(f.traffic_congestion_factor), 3) AS avg_congestion_experienced,
    ROUND(SUM(f.high_delay_flag) * 100.0 / COUNT(f.incident_id), 2) AS pct_delayed_over_20min
FROM fact_emergency_incidents f
JOIN dim_emergency_types t ON f.emergency_type_id = t.type_id
GROUP BY t.priority, t.name, t.tenders_required
ORDER BY t.priority ASC, avg_response_time_min DESC;

-- ----------------------------------------------------------------------------
-- QUERY 3: Hourly Delay Profile & Rush-Hour Surcharge (CTE + Window Functions)
-- Objective: Quantify how evening and morning peak hours inflate response times relative
-- to midnight baseline (off-peak).
-- ----------------------------------------------------------------------------
WITH hourly_stats AS (
    SELECT 
        incident_hour,
        is_peak_hour,
        COUNT(incident_id) AS call_volume,
        ROUND(AVG(response_time_minutes), 2) AS avg_hourly_response_time,
        ROUND(AVG(traffic_congestion_factor), 3) AS avg_traffic_factor
    FROM fact_emergency_incidents
    GROUP BY incident_hour, is_peak_hour
),
midnight_benchmark AS (
    SELECT avg_hourly_response_time AS midnight_avg
    FROM hourly_stats
    WHERE incident_hour = 3 -- 3:00 AM represents optimal free-flow conditions
)
SELECT 
    h.incident_hour,
    h.is_peak_hour,
    h.call_volume,
    h.avg_hourly_response_time,
    h.avg_traffic_factor,
    ROUND(h.avg_hourly_response_time - m.midnight_avg, 2) AS delay_surcharge_vs_midnight,
    ROUND(((h.avg_hourly_response_time - m.midnight_avg) / m.midnight_avg) * 100.0, 1) AS pct_delay_increase,
    RANK() OVER (ORDER BY h.avg_hourly_response_time DESC) AS delay_rank
FROM hourly_stats h
CROSS JOIN midnight_benchmark m
ORDER BY h.incident_hour ASC;

-- ----------------------------------------------------------------------------
-- QUERY 4: Monsoon Impact Analysis (Monsoon vs Dry Season Response Time)
-- Objective: Evaluate the statistical shift in transit duration caused by monsoon weather.
-- ----------------------------------------------------------------------------
SELECT 
    CASE WHEN is_monsoon = 1 THEN 'Monsoon Season (Jun-Sep)' ELSE 'Non-Monsoon Season (Oct-May)' END AS season_category,
    COUNT(incident_id) AS total_incidents,
    ROUND(AVG(response_time_minutes), 2) AS avg_response_time_min,
    ROUND(AVG(rainfall_mm), 2) AS avg_hourly_rainfall_mm,
    ROUND(AVG(traffic_congestion_factor), 3) AS avg_congestion_index,
    SUM(CASE WHEN rainfall_mm >= 15.0 THEN 1 ELSE 0 END) AS heavy_rain_incident_count,
    ROUND(AVG(CASE WHEN rainfall_mm >= 15.0 THEN response_time_minutes ELSE NULL END), 2) AS avg_time_during_heavy_rain,
    ROUND(SUM(high_delay_flag) * 100.0 / COUNT(incident_id), 2) AS high_delay_rate_pct
FROM fact_emergency_incidents
GROUP BY is_monsoon;

-- ----------------------------------------------------------------------------
-- QUERY 5: Ward-Level Geographic Delay Ranking (Top 5 Vulnerable Wards)
-- Objective: Identify municipal zones with chronic response bottlenecks.
-- ----------------------------------------------------------------------------
SELECT 
    w.ward_id,
    w.ward_name,
    w.zone,
    w.density_tier,
    COUNT(f.incident_id) AS incident_count,
    ROUND(AVG(f.network_distance_km), 2) AS avg_station_to_scene_km,
    ROUND(AVG(f.response_time_minutes), 2) AS avg_response_time_min,
    ROUND(SUM(f.high_delay_flag) * 100.0 / COUNT(f.incident_id), 2) AS high_delay_rate_pct,
    DENSE_RANK() OVER (ORDER BY AVG(f.response_time_minutes) DESC) AS citywide_delay_rank
FROM fact_emergency_incidents f
JOIN dim_municipal_wards w ON f.ward_id = w.ward_id
GROUP BY w.ward_id, w.ward_name, w.zone, w.density_tier
ORDER BY citywide_delay_rank ASC
LIMIT 5;

-- ----------------------------------------------------------------------------
-- QUERY 6: Station Operational Workload and Cross-Ward Dispatch Coverage
-- Objective: Determine whether certain fire stations are burdened with calls across multiple wards.
-- ----------------------------------------------------------------------------
SELECT 
    s.station_id,
    s.station_name,
    s.fleet_capacity,
    COUNT(DISTINCT f.ward_id) AS unique_wards_covered,
    COUNT(f.incident_id) AS total_dispatches,
    ROUND(COUNT(f.incident_id) * 1.0 / s.fleet_capacity, 1) AS dispatches_per_tender_ratio,
    ROUND(AVG(f.response_time_minutes), 2) AS avg_response_time_min,
    ROUND(AVG(f.network_distance_km), 2) AS avg_dispatch_distance_km
FROM fact_emergency_incidents f
JOIN dim_fire_stations s ON f.station_id = s.station_id
GROUP BY s.station_id, s.station_name, s.fleet_capacity
ORDER BY total_dispatches DESC;

-- ----------------------------------------------------------------------------
-- QUERY 7: Distance Band Segmentation (Transit Decay Analysis)
-- Objective: Analyze how response time scales across distance tiers (<2km, 2-5km, 5-10km, >10km).
-- ----------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN network_distance_km < 2.0 THEN '1. Immediate Vicinity (< 2 km)'
        WHEN network_distance_km BETWEEN 2.0 AND 4.99 THEN '2. Short Distance (2 - 5 km)'
        WHEN network_distance_km BETWEEN 5.0 AND 9.99 THEN '3. Medium Distance (5 - 10 km)'
        ELSE '4. Long Distance (>= 10 km)'
    END AS distance_band,
    COUNT(incident_id) AS incident_count,
    ROUND(AVG(network_distance_km), 2) AS avg_band_distance_km,
    ROUND(AVG(response_time_minutes), 2) AS avg_response_time_min,
    ROUND(AVG(response_time_minutes / network_distance_km), 2) AS minutes_per_kilometer,
    ROUND(SUM(high_delay_flag) * 100.0 / COUNT(incident_id), 2) AS high_delay_percentage
FROM fact_emergency_incidents
GROUP BY 
    CASE 
        WHEN network_distance_km < 2.0 THEN '1. Immediate Vicinity (< 2 km)'
        WHEN network_distance_km BETWEEN 2.0 AND 4.99 THEN '2. Short Distance (2 - 5 km)'
        WHEN network_distance_km BETWEEN 5.0 AND 9.99 THEN '3. Medium Distance (5 - 10 km)'
        ELSE '4. Long Distance (>= 10 km)'
    END
ORDER BY distance_band ASC;

-- ----------------------------------------------------------------------------
-- QUERY 8: Rolling 7-Day Moving Average of Emergency Response Times
-- Objective: Smooth out daily noise to observe seasonal / monthly operational drift.
-- ----------------------------------------------------------------------------
WITH daily_aggregates AS (
    SELECT 
        DATE(dispatch_timestamp) AS incident_date,
        COUNT(incident_id) AS daily_call_count,
        ROUND(AVG(response_time_minutes), 2) AS daily_avg_response_time
    FROM fact_emergency_incidents
    GROUP BY DATE(dispatch_timestamp)
)
SELECT 
    incident_date,
    daily_call_count,
    daily_avg_response_time,
    ROUND(AVG(daily_avg_response_time) OVER (
        ORDER BY incident_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_7day_avg_response_time
FROM daily_aggregates
ORDER BY incident_date DESC
LIMIT 14;
