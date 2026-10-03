"""
app.py - Lightweight Interactive Web Application & Decision-Support Server

WHAT are we doing?
We are launching a web application that provides an intuitive visual interface
for the emergency response prediction system:
1. Location-based ETA prediction: Users can enter their Pune location (or click on the map)
   to automatically find the nearest PMC fire station and get an accurate arrival time (ETA).
2. Real-time interactive scenario simulator with sliders and Leaflet map of Pune.
3. Operational Analytics dashboard showing city KPIs and diurnal curves.
4. Clean dataset explorer to search and inspect raw incident rows.
5. Plain English guide explaining the system without confusing technical jargon.
"""

import os
import sys
import re
import math
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.predict import predict_emergency_response_time

app = Flask(__name__, static_folder="static", template_folder="templates")

# Load reference metadata
STATIONS_CSV = "data/raw/pune_fire_stations.csv"
WARDS_CSV = "data/raw/pune_municipal_wards.csv"
CLEAN_INCIDENTS_CSV = "data/processed/pune_emergency_incidents_clean.csv"

stations_df = pd.read_csv(STATIONS_CSV)
wards_df = pd.read_csv(WARDS_CSV)
incidents_df = pd.read_csv(CLEAN_INCIDENTS_CSV)

# Curated reference database of major Pune localities and landmarks with aliases
PUNE_LANDMARKS = [
    {
        "name": "Fergusson College (FC) Road, Deccan",
        "aliases": ["fc road", "fergusson", "fergusson college", "deccan", "deccan gymkhana", "fc", "jm road"],
        "category": "Prominent Arterial",
        "lat": 18.5196,
        "lon": 73.8415,
        "ward_id": "WD-01"
    },
    {
        "name": "Shaniwar Wada, Kasba Peth",
        "aliases": ["shaniwar wada", "kasba peth", "budhwar peth", "old city", "shaniwarwada", "historic core"],
        "category": "Historic Heritage Core",
        "lat": 18.5196,
        "lon": 73.8553,
        "ward_id": "WD-02"
    },
    {
        "name": "Kothrud Stand / Karve Road",
        "aliases": ["kothrud", "karve road", "paud road", "kothrud stand", "vanaz", "mit college", "karvenagar road"],
        "category": "Residential Hub",
        "lat": 18.5074,
        "lon": 73.8077,
        "ward_id": "WD-04"
    },
    {
        "name": "Phoenix Marketcity, Viman Nagar",
        "aliases": ["viman nagar", "phoenix mall", "phoenix marketcity", "symbiosis", "vimannagar", "airport road"],
        "category": "Commercial & IT Hub",
        "lat": 18.5621,
        "lon": 73.9168,
        "ward_id": "WD-07"
    },
    {
        "name": "Magarpatta Cybercity, Hadapsar",
        "aliases": ["magarpatta", "magarpatta city", "hadapsar", "cybercity", "amanora", "hadapsar bypass"],
        "category": "Major IT Township",
        "lat": 18.5144,
        "lon": 73.9288,
        "ward_id": "WD-08"
    },
    {
        "name": "Hinjewadi IT Park Phase 1",
        "aliases": ["hinjewadi", "hinjawadi", "it park", "wakad", "phase 1", "infotech park", "wipro circle"],
        "category": "Tech Corridor",
        "lat": 18.5913,
        "lon": 73.7389,
        "ward_id": "WD-05"
    },
    {
        "name": "Bremen Chowk, Aundh",
        "aliases": ["aundh", "bremen chowk", "westend", "westend mall", "sp university", "parihar chowk"],
        "category": "Commercial & Residential",
        "lat": 18.5590,
        "lon": 73.8075,
        "ward_id": "WD-05"
    },
    {
        "name": "Balewadi High Street, Baner",
        "aliases": ["baner", "balewadi", "balewadi high street", "high street", "baner road", "pashan baner link"],
        "category": "Dining & Commercial",
        "lat": 18.5726,
        "lon": 73.7745,
        "ward_id": "WD-05"
    },
    {
        "name": "Swargate Bus Terminal & Metro",
        "aliases": ["swargate", "sarasbaug", "swargate bus stand", "parvati", "mitramandal"],
        "category": "Central Transit Interchange",
        "lat": 18.5018,
        "lon": 73.8580,
        "ward_id": "WD-02"
    },
    {
        "name": "Pune Railway Station (Central)",
        "aliases": ["pune station", "railway station", "pune railway station", "station", "sassoon"],
        "category": "Railway & Transit Core",
        "lat": 18.5284,
        "lon": 73.8744,
        "ward_id": "WD-15"
    },
    {
        "name": "Koregaon Park (North Main Road)",
        "aliases": ["koregaon park", "kp", "north main road", "south main road", "osho ashram", "bund garden"],
        "category": "High-Density Residential",
        "lat": 18.5362,
        "lon": 73.8940,
        "ward_id": "WD-15"
    },
    {
        "name": "Senapati Bapat (SB) Road / ICC Towers",
        "aliases": ["senapati bapat road", "sb road", "icc towers", "symbiosis sb road", "marriott", "chatushrungi"],
        "category": "Corporate & Education",
        "lat": 18.5308,
        "lon": 73.8296,
        "ward_id": "WD-01"
    },
    {
        "name": "Katraj Snake Park / Bharati Vidyapeeth",
        "aliases": ["katraj", "snake park", "bharati vidyapeeth", "katraj ghat", "rajiv gandhi park", "katraj chowk"],
        "category": "South Pune Hub",
        "lat": 18.4575,
        "lon": 73.8580,
        "ward_id": "WD-09"
    },
    {
        "name": "Kondhwa Khurd / NIBM Road",
        "aliases": ["kondhwa", "nibm", "nibm road", "kondhwa khurd", "undri", "salunke vihar"],
        "category": "Residential Corridor",
        "lat": 18.4720,
        "lon": 73.8910,
        "ward_id": "WD-13"
    },
    {
        "name": "MG Road / Pune Camp",
        "aliases": ["camp", "mg road", "pune camp", "east street", "cantonment", "main street"],
        "category": "Cantonment Commercial",
        "lat": 18.5167,
        "lon": 73.8790,
        "ward_id": "WD-03"
    },
    {
        "name": "Bhavani Peth Timber Market",
        "aliases": ["bhavani peth", "timber market", "central fire brigade", "peth market"],
        "category": "Wholesale Commercial",
        "lat": 18.5050,
        "lon": 73.8710,
        "ward_id": "WD-03"
    },
    {
        "name": "Sinhagad Road / Anand Nagar",
        "aliases": ["sinhagad road", "dhayari", "anand nagar", "vadgaon budruk", "manikbaug", "hingne"],
        "category": "Congested Arterial Corridor",
        "lat": 18.4780,
        "lon": 73.8290,
        "ward_id": "WD-11"
    },
    {
        "name": "Warje Flyover / Karvenagar",
        "aliases": ["warje", "karvenagar", "warje flyover", "cummins", "bavdhan warje"],
        "category": "Highway Interchange",
        "lat": 18.4830,
        "lon": 73.7950,
        "ward_id": "WD-12"
    },
    {
        "name": "Pashan Lake / Circle",
        "aliases": ["pashan", "pashan circle", "pashan lake", "sutarwadi", "sus road"],
        "category": "West Residential",
        "lat": 18.5415,
        "lon": 73.7925,
        "ward_id": "WD-05"
    },
    {
        "name": "Kalyani Nagar / East Avenue",
        "aliases": ["kalyani nagar", "kalyaninagar", "east avenue", "bishop school", "aditi gardens"],
        "category": "Commercial & IT Corridor",
        "lat": 18.5475,
        "lon": 73.9030,
        "ward_id": "WD-07"
    },
    {
        "name": "Bavdhan Chandani Chowk",
        "aliases": ["bavdhan", "chandani chowk", "bavdhan khurd", "highway junction"],
        "category": "Highway Bypass Junction",
        "lat": 18.5080,
        "lon": 73.7920,
        "ward_id": "WD-04"
    },
    {
        "name": "Yerawada / Pune Golf Course",
        "aliases": ["yerawada", "yerwada", "commerzone", "golf course", "deccan college"],
        "category": "North Core",
        "lat": 18.5529,
        "lon": 73.8797,
        "ward_id": "WD-06"
    },
    {
        "name": "Dhankawadi / Sahakarnagar",
        "aliases": ["dhankawadi", "sahakarnagar", "sahakar nagar", "padmavati", "aranyeshwar"],
        "category": "South Residential",
        "lat": 18.4700,
        "lon": 73.8450,
        "ward_id": "WD-10"
    },
    {
        "name": "Wanowrie / Command Hospital",
        "aliases": ["wanowrie", "wanawadi", "command hospital", "fatima nagar", "kedari nagar"],
        "category": "South-East Sector",
        "lat": 18.4950,
        "lon": 73.8950,
        "ward_id": "WD-14"
    },
    {
        "name": "Vadgaon Sheri / Anand Park",
        "aliases": ["vadgaon sheri", "vadgaonsheri", "chandan nagar", "kharadi bypass", "somnath nagar"],
        "category": "North-East Corridor",
        "lat": 18.5500,
        "lon": 73.9350,
        "ward_id": "WD-07"
    }
]

def normalize_text(text):
    """Strips punctuation and lowercases text for flexible fuzzy matching."""
    return re.sub(r'[^a-z0-9 ]', ' ', str(text).lower()).strip()

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates spherical surface distance in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route("/")
def index():
    """Serves the main dashboard page."""
    return render_template("index.html")

@app.route("/api/metadata")
def get_metadata():
    """Returns station, ward, and landmark metadata for dropdowns, search, and map."""
    stations = stations_df.to_dict(orient="records")
    wards = wards_df.to_dict(orient="records")
    return jsonify({
        "stations": stations,
        "wards": wards,
        "landmarks": PUNE_LANDMARKS
    })

@app.route("/api/landmarks")
def get_landmarks():
    """Returns list of curated Pune landmarks and localities for search."""
    return jsonify(PUNE_LANDMARKS)

@app.route("/api/locate", methods=["POST"])
def locate():
    """
    Given a latitude & longitude or search query in Pune:
    1. Resolves coordinates.
    2. Identifies the nearest Pune Fire Station & calculated road network distance.
    3. Identifies the closest municipal ward centroid.
    4. Returns sorted station proximity and dispatch routing details.
    """
    data = request.get_json() or {}
    lat = data.get("lat")
    lon = data.get("lon")
    query = data.get("query", "").strip()

    resolved_name = "Custom Pune Location"

    # If query string is passed without coordinates, search in landmarks
    if (lat is None or lon is None) and query:
        q_norm = normalize_text(query)
        best_match = None
        for lm in PUNE_LANDMARKS:
            # Check aliases
            aliases = [normalize_text(a) for a in lm.get("aliases", [])]
            if any(a in q_norm or q_norm in a for a in aliases):
                best_match = lm
                break
            # Check name or category
            name_norm = normalize_text(lm["name"])
            if q_norm in name_norm or name_norm in q_norm:
                best_match = lm
                break

        if best_match:
            lat = best_match["lat"]
            lon = best_match["lon"]
            resolved_name = best_match["name"]
        else:
            # Default to Central Pune if unmapped query
            lat = 18.5204
            lon = 73.8567
            resolved_name = f"Pune Location ({query.title()})"
    elif lat is not None and lon is not None:
        lat = float(lat)
        lon = float(lon)
        # Check if coordinates closely match any landmark
        closest_lm = min(PUNE_LANDMARKS, key=lambda lm: haversine_distance(lat, lon, lm["lat"], lm["lon"]))
        dist_to_lm = haversine_distance(lat, lon, closest_lm["lat"], closest_lm["lon"])
        if dist_to_lm <= 0.8:
            resolved_name = f"{closest_lm['name']} (approx)"
        else:
            resolved_name = f"Location at {lat:.4f}°N, {lon:.4f}°E"

    # Calculate distance to all 14 fire stations
    stations_list = stations_df.to_dict(orient="records")
    for st in stations_list:
        straight_km = haversine_distance(lat, lon, st["latitude"], st["longitude"])
        # Apply Pune road circuity factor 1.35x
        road_km = max(0.8, round(straight_km * 1.35, 1))
        st["straight_distance_km"] = round(straight_km, 2)
        st["road_distance_km"] = road_km

    # Sort by proximity
    stations_list.sort(key=lambda s: s["straight_distance_km"])
    nearest_station = stations_list[0]
    backup_station = stations_list[1] if len(stations_list) > 1 else stations_list[0]

    # Find closest ward centroid
    wards_list = wards_df.to_dict(orient="records")
    for wd in wards_list:
        wd["distance_km"] = round(haversine_distance(lat, lon, wd["centroid_lat"], wd["centroid_lon"]), 2)
    wards_list.sort(key=lambda w: w["distance_km"])
    nearest_ward = wards_list[0]

    return jsonify({
        "location": {
            "name": resolved_name,
            "latitude": lat,
            "longitude": lon
        },
        "nearest_station": nearest_station,
        "backup_station": backup_station,
        "nearest_ward": nearest_ward,
        "road_distance_km": nearest_station["road_distance_km"]
    })

@app.route("/api/predict", methods=["POST"])
def predict():
    """Receives simulation parameters and returns AI model prediction with Clock ETA."""
    data = request.get_json() or {}
    
    distance_km = float(data.get("distance_km", 4.0))
    incident_hour = int(data.get("incident_hour", 18))
    station_id = data.get("station_id", "FS-01")
    ward_id = data.get("ward_id", "WD-03")
    emergency_type = data.get("emergency_type", "Commercial / Industrial Fire")
    rainfall_mm = float(data.get("rainfall_mm", 0.0))
    is_weekend = int(data.get("is_weekend", 0))
    is_monsoon = int(data.get("is_monsoon", 0))

    try:
        result = predict_emergency_response_time(
            network_distance_km=distance_km,
            incident_hour=incident_hour,
            station_id=station_id,
            ward_id=ward_id,
            emergency_type=emergency_type,
            rainfall_mm=rainfall_mm,
            is_weekend=is_weekend,
            is_monsoon=is_monsoon
        )

        # Calculate estimated arrival clock time
        predicted_mins = result["predicted_response_time_minutes"]
        
        # Base dispatch time calculation
        now = datetime.now()
        # If incident_hour matches current hour, use current minute; else use :00 of that hour
        if incident_hour == now.hour:
            base_time = now
        else:
            base_time = now.replace(hour=incident_hour, minute=0, second=0)
        
        arrival_time = base_time + timedelta(minutes=predicted_mins)
        eta_clock_str = arrival_time.strftime("%I:%M %p")
        dispatch_clock_str = base_time.strftime("%I:%M %p")

        result["dispatch_clock_time"] = dispatch_clock_str
        result["eta_clock_time"] = eta_clock_str

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/incidents")
def get_incidents():
    """Returns first N incidents for the dataset explorer."""
    limit = int(request.args.get("limit", 25))
    sample = incidents_df.head(limit).to_dict(orient="records")
    return jsonify(sample)

@app.route("/static/plots/<filename>")
def get_plot(filename):
    """Serves generated EDA plots from dashboard/eda_plots/."""
    return send_from_directory("dashboard/eda_plots", filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("\n" + "=" * 80)
    print("🚒 PUNE EMERGENCY RESPONSE DECISION-SUPPORT SERVER STARTED")
    print(f"🌐 Local URL: http://127.0.0.1:{port}")
    print("=" * 80 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)
