-- ============================================================================
-- DATABASE SCHEMA: PUNE EMERGENCY RESPONSE TIME ANALYTICS SYSTEM
-- Engine: MySQL 8.0+ / SQLite 3 Dual Compatible
-- Character Set: utf8mb4 / utf8mb4_unicode_ci
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. DIMENSION TABLE: dim_fire_stations
-- Description: Master dimension of Pune Municipal Corporation fire brigade stations
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_emergency_incidents;
DROP TABLE IF EXISTS dim_fire_stations;
DROP TABLE IF EXISTS dim_municipal_wards;
DROP TABLE IF EXISTS dim_emergency_types;

CREATE TABLE dim_fire_stations (
    station_id VARCHAR(10) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    fleet_capacity INT NOT NULL,
    established_year INT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. DIMENSION TABLE: dim_municipal_wards
-- Description: Administrative electoral wards and geospatial zones of Pune
-- ----------------------------------------------------------------------------
CREATE TABLE dim_municipal_wards (
    ward_id VARCHAR(10) PRIMARY KEY,
    ward_name VARCHAR(100) NOT NULL,
    zone VARCHAR(50) NOT NULL,
    centroid_lat DECIMAL(9, 6) NOT NULL,
    centroid_lon DECIMAL(9, 6) NOT NULL,
    area_sqkm DECIMAL(6, 2) NOT NULL,
    density_tier VARCHAR(20) NOT NULL,
    road_congestion_baseline DECIMAL(4, 2) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. DIMENSION TABLE: dim_emergency_types
-- Description: Standard operational emergency classifications and priorities
-- ----------------------------------------------------------------------------
CREATE TABLE dim_emergency_types (
    type_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    priority VARCHAR(50) NOT NULL,
    severity_weight DECIMAL(4, 2) NOT NULL,
    tenders_required INT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. FACT TABLE: fact_emergency_incidents
-- Description: Incident-level emergency calls with response times and conditions
-- ----------------------------------------------------------------------------
CREATE TABLE fact_emergency_incidents (
    incident_id VARCHAR(20) PRIMARY KEY,
    dispatch_timestamp DATETIME NOT NULL,
    arrival_timestamp DATETIME NOT NULL,
    response_time_minutes DECIMAL(6, 2) NOT NULL,
    station_id VARCHAR(10) NOT NULL,
    ward_id VARCHAR(10) NOT NULL,
    emergency_type_id VARCHAR(10) NOT NULL,
    network_distance_km DECIMAL(6, 2) NOT NULL,
    traffic_congestion_factor DECIMAL(5, 3) NOT NULL,
    weather_condition VARCHAR(50) NOT NULL,
    temperature_c DECIMAL(4, 1) NOT NULL,
    rainfall_mm DECIMAL(5, 1) NOT NULL,
    is_monsoon TINYINT(1) NOT NULL,
    is_weekend TINYINT(1) NOT NULL,
    is_peak_hour TINYINT(1) NOT NULL,
    incident_hour INT NOT NULL,
    day_of_week VARCHAR(15) NOT NULL,
    high_delay_flag TINYINT(1) NOT NULL,
    CONSTRAINT fk_incident_station FOREIGN KEY (station_id) REFERENCES dim_fire_stations(station_id),
    CONSTRAINT fk_incident_ward FOREIGN KEY (ward_id) REFERENCES dim_municipal_wards(ward_id),
    CONSTRAINT fk_incident_type FOREIGN KEY (emergency_type_id) REFERENCES dim_emergency_types(type_id)
);

-- ----------------------------------------------------------------------------
-- 5. PERFORMANCE INDEXES
-- Optimizes high-frequency analytical filter, join, and grouping queries
-- ----------------------------------------------------------------------------
CREATE INDEX idx_incidents_dispatch_dt ON fact_emergency_incidents(dispatch_timestamp);
CREATE INDEX idx_incidents_station ON fact_emergency_incidents(station_id);
CREATE INDEX idx_incidents_ward ON fact_emergency_incidents(ward_id);
CREATE INDEX idx_incidents_type ON fact_emergency_incidents(emergency_type_id);
CREATE INDEX idx_incidents_hour_peak ON fact_emergency_incidents(incident_hour, is_peak_hour);
CREATE INDEX idx_incidents_monsoon ON fact_emergency_incidents(is_monsoon);

-- ----------------------------------------------------------------------------
-- 6. ANALYTICAL REPORTING VIEWS
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_station_operational_performance;
CREATE VIEW v_station_operational_performance AS
SELECT 
    s.station_id,
    s.station_name,
    s.fleet_capacity,
    COUNT(f.incident_id) AS total_calls_handled,
    ROUND(AVG(f.response_time_minutes), 2) AS avg_response_time_min,
    ROUND(MIN(f.response_time_minutes), 2) AS min_response_time_min,
    ROUND(MAX(f.response_time_minutes), 2) AS max_response_time_min,
    ROUND(AVG(f.network_distance_km), 2) AS avg_distance_km,
    SUM(f.high_delay_flag) AS high_delay_call_count,
    ROUND(SUM(f.high_delay_flag) * 100.0 / COUNT(f.incident_id), 2) AS high_delay_percentage
FROM dim_fire_stations s
JOIN fact_emergency_incidents f ON s.station_id = f.station_id
GROUP BY s.station_id, s.station_name, s.fleet_capacity;

DROP VIEW IF EXISTS v_ward_risk_profiles;
CREATE VIEW v_ward_risk_profiles AS
SELECT 
    w.ward_id,
    w.ward_name,
    w.zone,
    w.density_tier,
    COUNT(f.incident_id) AS total_incidents,
    ROUND(AVG(f.response_time_minutes), 2) AS avg_response_time_min,
    ROUND(AVG(f.traffic_congestion_factor), 3) AS avg_congestion_factor,
    ROUND(SUM(f.high_delay_flag) * 100.0 / COUNT(f.incident_id), 2) AS high_delay_rate_pct
FROM dim_municipal_wards w
JOIN fact_emergency_incidents f ON w.ward_id = f.ward_id
GROUP BY w.ward_id, w.ward_name, w.zone, w.density_tier;
