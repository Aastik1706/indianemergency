// ============================================================================
// PUNE EMERGENCY RESPONSE - HIGH-PERFORMANCE APPLE CUPERTINO JAVASCRIPT
// Features:
// 1. In-memory client prediction cache for sub-millisecond response.
// 2. Debounced live recalculation as sliders move (dynamic real-time simulation).
// 3. Dynamic traffic friction surge meter reflecting diurnal road physics.
// 4. Interactive CartoDB Voyager map with route polyline and proximity bounds.
// 5. Server-side paginated, filterable & sortable incident explorer (11,973 records).
// 6. One-click "Copy Dispatch Briefing" for emergency control room logging.
// ============================================================================

let map;
let stationMarkers = {};
let wardMarkers = {};
let userMarker = null;
let routeLine = null;

let selectedRain = 20.0;
let selectedMonsoon = 1;
let stationsData = [];
let wardsData = [];
let landmarksData = [];

// Client-side LRU prediction cache to eliminate repeat network round-trips
const clientPredictionCache = new Map();

// Table state for Dataset Explorer
let tableState = {
    page: 1,
    limit: 25,
    totalPages: 1,
    totalCount: 0,
    search: "",
    sortBy: "dispatch_timestamp",
    sortOrder: "desc"
};

// Current operational mode: 'location' or 'manual'
let currentMode = "location";

// Active location state for location-based auto dispatch
let activeDispatch = {
    locationName: "Fergusson College (FC) Road, Deccan",
    lat: 18.5196,
    lon: 73.8415,
    stationId: "FS-02",
    stationName: "Erandwane Fire Station",
    stationLat: 18.5074,
    stationLon: 73.834,
    wardId: "WD-01",
    wardName: "Shivaji Nagar - Ghole Road",
    wardZone: "Central Zone",
    roadDistanceKm: 2.1,
    fleetCapacity: 5
};

// Last prediction result snapshot for clipboard copy
let lastPredictionResult = null;

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

const debouncedTriggerPrediction = debounce(() => triggerPrediction(), 150);
const debouncedTableSearch = debounce((query) => {
    tableState.search = query;
    tableState.page = 1;
    fetchIncidents();
}, 250);

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initModeSwitcher();
    initSliders();
    initWeatherToggles();
    initPresetScenarios();
    loadMetadata();
    initLocationSearch();
    initLocalityChips();
    initGPSButton();
    initPredictButton();
    initCopyBriefingButton();
    initTablePaginationAndSort();
    initHeaderAction();
    updateTrafficMeter(18);
});

// ----------------------------------------------------------------------------
// 1. Navigation & Segmented Bar Switching
// ----------------------------------------------------------------------------
function initNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const topNavLinks = document.querySelectorAll("[data-tab-target]");

    function switchTab(targetId) {
        navButtons.forEach(btn => {
            btn.classList.toggle("active", btn.getAttribute("data-tab") === targetId);
        });

        topNavLinks.forEach(link => {
            link.classList.toggle("active", link.getAttribute("data-tab-target") === targetId);
        });

        document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
            targetContent.classList.add("active");
        }

        if (targetId === "simulator-tab" && map) {
            setTimeout(() => map.invalidateSize(), 200);
        }

        if (targetId === "explorer-tab" && tableState.totalCount === 0) {
            fetchIncidents();
        }
    }

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => switchTab(btn.getAttribute("data-tab")));
    });

    topNavLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = link.getAttribute("data-tab-target");
            switchTab(targetId);

            const mainElem = document.querySelector(".apple-segmented-bar-wrapper");
            if (mainElem) {
                mainElem.scrollIntoView({ behavior: "smooth" });
            }
        });
    });
}

function initHeaderAction() {
    const headerBtn = document.getElementById("header-simulate-btn");
    if (headerBtn) {
        headerBtn.addEventListener("click", () => {
            const simBtn = document.querySelector('[data-tab="simulator-tab"]');
            if (simBtn) simBtn.click();
            
            const locInput = document.getElementById("location-search-input");
            if (locInput) {
                locInput.scrollIntoView({ behavior: "smooth", block: "center" });
                locInput.focus();
            }
        });
    }
}

// ----------------------------------------------------------------------------
// 2. Input Mode Switcher: "Enter My Location" vs "Manual Parameters"
// ----------------------------------------------------------------------------
function initModeSwitcher() {
    const locBtn = document.getElementById("mode-location-btn");
    const manBtn = document.getElementById("mode-manual-btn");
    const locSection = document.getElementById("location-mode-section");
    const manSection = document.getElementById("manual-mode-section");

    if (!locBtn || !manBtn) return;

    locBtn.addEventListener("click", () => {
        currentMode = "location";
        locBtn.classList.add("active");
        manBtn.classList.remove("active");
        locSection.style.display = "block";
        manSection.style.display = "none";
        
        updateLocationRoute();
        triggerPrediction();
    });

    manBtn.addEventListener("click", () => {
        currentMode = "manual";
        manBtn.classList.add("active");
        locBtn.classList.remove("active");
        locSection.style.display = "none";
        manSection.style.display = "block";

        if (userMarker && map) {
            map.removeLayer(userMarker);
            userMarker = null;
        }
        updateManualRoute();
        triggerPrediction();
    });
}

// ----------------------------------------------------------------------------
// 3. Interactive macOS/iOS Style Sliders & Dynamic Traffic Surge
// ----------------------------------------------------------------------------
function initSliders() {
    const distSlider = document.getElementById("distance-slider");
    const distVal = document.getElementById("distance-val");
    if (distSlider && distVal) {
        distSlider.addEventListener("input", (e) => {
            distVal.textContent = `${parseFloat(e.target.value).toFixed(1)} km`;
            if (currentMode === "manual") {
                debouncedTriggerPrediction();
            }
        });
    }

    const hourSlider = document.getElementById("hour-slider");
    const hourVal = document.getElementById("hour-val");
    if (hourSlider && hourVal) {
        hourSlider.addEventListener("input", (e) => {
            const h = parseInt(e.target.value);
            let label = `${h.toString().padStart(2, '0')}:00 hrs`;
            if (h >= 8 && h <= 11) {
                label += " (Morning Peak Rush)";
            } else if (h >= 17 && h <= 21) {
                label += " (Evening Peak Rush)";
            } else if (h >= 12 && h <= 16) {
                label += " (Afternoon)";
            } else {
                label += " (Night Off-Peak)";
            }
            hourVal.textContent = label;
            updateTrafficMeter(h);
            debouncedTriggerPrediction();
        });
    }

    // Emergency Type Selector Change -> Live Recalculate
    const emSelect = document.getElementById("emergency-select");
    if (emSelect) {
        emSelect.addEventListener("change", () => triggerPrediction());
    }
}

function updateTrafficMeter(hour) {
    const dot = document.getElementById("traffic-surge-dot");
    const text = document.getElementById("traffic-surge-text");
    if (!dot || !text) return;

    if (hour >= 17 && hour <= 21) {
        dot.className = "surge-meter-dot red";
        text.textContent = "Traffic Friction: Evening Peak Congestion (+45% Municipal Surcharge)";
    } else if (hour >= 8 && hour <= 11) {
        dot.className = "surge-meter-dot orange";
        text.textContent = "Traffic Friction: Morning Commute Rush (+35% Corridor Surcharge)";
    } else if (hour >= 12 && hour <= 16) {
        dot.className = "surge-meter-dot yellow";
        text.textContent = "Traffic Friction: Moderate Afternoon Transit (1.30x Baseline Flow)";
    } else {
        dot.className = "surge-meter-dot green";
        text.textContent = "Traffic Friction: Free-Flow Off-Peak Corridor (1.05x Minimal Friction)";
    }
}

// ----------------------------------------------------------------------------
// 4. Apple Weather Segmented Controls
// ----------------------------------------------------------------------------
function initWeatherToggles() {
    const btns = document.querySelectorAll(".weather-btn");
    btns.forEach(btn => {
        btn.addEventListener("click", () => {
            btns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            selectedRain = parseFloat(btn.getAttribute("data-rain"));
            selectedMonsoon = parseInt(btn.getAttribute("data-monsoon"));
            debouncedTriggerPrediction();
        });
    });
}

// ----------------------------------------------------------------------------
// 5. Quick Scenario Presets
// ----------------------------------------------------------------------------
function initPresetScenarios() {
    const presetBtns = document.querySelectorAll(".preset-btn");
    presetBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            presetBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const preset = btn.getAttribute("data-preset");
            applyPreset(preset);
        });
    });
}

function applyPreset(preset) {
    const distSlider = document.getElementById("distance-slider");
    const distVal = document.getElementById("distance-val");
    const hourSlider = document.getElementById("hour-slider");
    const hourVal = document.getElementById("hour-val");
    const weatherBtns = document.querySelectorAll(".weather-btn");

    if (preset === "typical") {
        if (distSlider) distSlider.value = "3.5";
        if (distVal) distVal.textContent = "3.5 km";
        if (hourSlider) hourSlider.value = "11";
        if (hourVal) hourVal.textContent = "11:00 hrs (Morning Off-Peak)";
        updateTrafficMeter(11);
        if (weatherBtns[0]) weatherBtns[0].click();
        selectLocationByQuery("FC Road");
    } else if (preset === "evening-peak") {
        if (distSlider) distSlider.value = "4.8";
        if (distVal) distVal.textContent = "4.8 km";
        if (hourSlider) hourSlider.value = "18";
        if (hourVal) hourVal.textContent = "18:00 hrs (Evening Peak Rush)";
        updateTrafficMeter(18);
        if (weatherBtns[0]) weatherBtns[0].click();
        selectLocationByQuery("Shaniwar Wada");
    } else if (preset === "monsoon-rain") {
        if (distSlider) distSlider.value = "4.0";
        if (distVal) distVal.textContent = "4.0 km";
        if (hourSlider) hourSlider.value = "19";
        if (hourVal) hourVal.textContent = "19:00 hrs (Evening Peak Rush)";
        updateTrafficMeter(19);
        if (weatherBtns[2]) weatherBtns[2].click();
        selectLocationByQuery("Swargate");
    } else if (preset === "long-haul") {
        if (distSlider) distSlider.value = "9.5";
        if (distVal) distVal.textContent = "9.5 km";
        if (hourSlider) hourSlider.value = "14";
        if (hourVal) hourVal.textContent = "14:00 hrs (Afternoon)";
        updateTrafficMeter(14);
        if (weatherBtns[0]) weatherBtns[0].click();
        selectLocationByQuery("Hinjewadi");
    }

    triggerPrediction();
}

// ----------------------------------------------------------------------------
// 6. Load Stations & Wards Metadata & Initialize Map
// ----------------------------------------------------------------------------
async function loadMetadata() {
    try {
        const res = await fetch("/api/metadata");
        const data = await res.json();
        stationsData = data.stations;
        wardsData = data.wards;
        landmarksData = data.landmarks || [];

        populateDropdowns();
        initMap();
        
        // Initial location: FC Road
        selectLocationByCoordinates(18.5196, 73.8415, "Fergusson College (FC) Road, Deccan");
    } catch (err) {
        console.error("Failed to load metadata:", err);
    }
}

function populateDropdowns() {
    const stSelect = document.getElementById("station-select");
    if (stSelect) {
        stSelect.innerHTML = "";
        stationsData.forEach(st => {
            const opt = document.createElement("option");
            opt.value = st.station_id;
            opt.textContent = `${st.station_name} (${st.fleet_capacity} tenders)`;
            stSelect.appendChild(opt);
        });

        stSelect.addEventListener("change", () => {
            const cur = stationsData.find(s => s.station_id === stSelect.value);
            if (cur) {
                document.getElementById("station-fleet-badge").textContent = `Fleet: ${cur.fleet_capacity} tenders`;
            }
            if (currentMode === "manual") {
                updateManualRoute();
                triggerPrediction();
            }
        });
    }

    const wdSelect = document.getElementById("ward-select");
    if (wdSelect) {
        wdSelect.innerHTML = "";
        wardsData.forEach(wd => {
            const opt = document.createElement("option");
            opt.value = wd.ward_id;
            opt.textContent = `${wd.ward_name} (${wd.zone})`;
            wdSelect.appendChild(opt);
        });

        wdSelect.addEventListener("change", () => {
            const cur = wardsData.find(w => w.ward_id === wdSelect.value);
            if (cur) {
                document.getElementById("ward-zone-badge").textContent = `Zone: ${cur.zone}`;
            }
            if (currentMode === "manual") {
                updateManualRoute();
                triggerPrediction();
            }
        });
    }
}

function initMap() {
    map = L.map("pune-map", {
        center: [18.5196, 73.8415],
        zoom: 13,
        zoomControl: true,
        preferCanvas: true
    });

    // Clean, modern CartoDB Voyager tiles with Retina support
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
        maxZoom: 19,
        detectRetina: true
    }).addTo(map);

    // Add Fire Stations (Apple Red circular pins)
    stationsData.forEach(st => {
        const marker = L.circleMarker([st.latitude, st.longitude], {
            radius: 7,
            fillColor: "#ff3b30",
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.95
        }).addTo(map);

        marker.bindPopup(`<strong>🚒 ${st.station_name}</strong><br>Fleet Capacity: ${st.fleet_capacity} tenders<br>Established: ${st.established_year}`);
        stationMarkers[st.station_id] = marker;
    });

    // Add Ward Centroids (Apple Blue subtle pins)
    wardsData.forEach(wd => {
        const marker = L.circleMarker([wd.centroid_lat, wd.centroid_lon], {
            radius: 5,
            fillColor: "#0071e3",
            color: "#ffffff",
            weight: 1.5,
            opacity: 0.8,
            fillOpacity: 0.6
        }).addTo(map);

        marker.bindPopup(`<strong>📍 ${wd.ward_name}</strong><br>Zone: ${wd.zone}<br>Density Tier: ${wd.density_tier}`);
        wardMarkers[wd.ward_id] = marker;
    });

    // Map Click: Drop pin anywhere in Pune
    map.on("click", async (e) => {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;

        if (currentMode !== "location") {
            const locBtn = document.getElementById("mode-location-btn");
            if (locBtn) locBtn.click();
        }

        await selectLocationByCoordinates(lat, lon);
    });
}

// ----------------------------------------------------------------------------
// 7. Location Search, Autocomplete & Landmark Chips
// ----------------------------------------------------------------------------
function initLocationSearch() {
    const input = document.getElementById("location-search-input");
    const dropdown = document.getElementById("location-suggestions-dropdown");
    const clearBtn = document.getElementById("btn-clear-search");

    if (!input || !dropdown) return;

    input.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        
        if (clearBtn) {
            clearBtn.style.display = query ? "flex" : "none";
        }

        if (!query) {
            dropdown.style.display = "none";
            return;
        }

        const matches = landmarksData.filter(lm => {
            const nameMatch = lm.name.toLowerCase().includes(query);
            const catMatch = lm.category.toLowerCase().includes(query);
            const aliasMatch = (lm.aliases || []).some(a => a.toLowerCase().includes(query));
            return nameMatch || catMatch || aliasMatch;
        });

        if (matches.length === 0) {
            dropdown.innerHTML = `<div class="suggestion-item"><span class="suggestion-name">Search Pune address for "${e.target.value}"...</span></div>`;
            dropdown.style.display = "block";
            return;
        }

        dropdown.innerHTML = matches.slice(0, 7).map(lm => `
            <div class="suggestion-item" data-name="${lm.name}" data-lat="${lm.lat}" data-lon="${lm.lon}">
                <span class="suggestion-name">📍 ${lm.name}</span>
                <span class="suggestion-category">${lm.category}</span>
            </div>
        `).join("");

        dropdown.style.display = "block";

        dropdown.querySelectorAll(".suggestion-item").forEach(item => {
            item.addEventListener("click", () => {
                const name = item.getAttribute("data-name");
                const lat = parseFloat(item.getAttribute("data-lat"));
                const lon = parseFloat(item.getAttribute("data-lon"));
                
                input.value = name;
                dropdown.style.display = "none";
                if (clearBtn) clearBtn.style.display = "flex";

                updateActiveLocalityChip(name);
                selectLocationByCoordinates(lat, lon, name);
            });
        });
    });

    input.addEventListener("keydown", async (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            dropdown.style.display = "none";
            const query = input.value.trim();
            if (query) {
                await selectLocationByQuery(query);
            }
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            input.value = "";
            clearBtn.style.display = "none";
            dropdown.style.display = "none";
            input.focus();
        });
    }

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".location-input-wrapper") && !e.target.closest("#location-suggestions-dropdown")) {
            dropdown.style.display = "none";
        }
    });
}

function initLocalityChips() {
    const chips = document.querySelectorAll(".locality-chip");
    chips.forEach(chip => {
        chip.addEventListener("click", async () => {
            chips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");

            const landmarkName = chip.getAttribute("data-landmark");
            const searchInput = document.getElementById("location-search-input");
            if (searchInput) searchInput.value = landmarkName;

            const clearBtn = document.getElementById("btn-clear-search");
            if (clearBtn) clearBtn.style.display = "flex";

            await selectLocationByQuery(landmarkName);
        });
    });
}

function updateActiveLocalityChip(selectedName) {
    const chips = document.querySelectorAll(".locality-chip");
    chips.forEach(chip => {
        const name = chip.getAttribute("data-landmark");
        chip.classList.toggle("active", name === selectedName || selectedName.includes(chip.textContent.trim()));
    });
}

function initGPSButton() {
    const gpsBtn = document.getElementById("btn-use-gps");
    if (!gpsBtn) return;

    gpsBtn.addEventListener("click", () => {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        gpsBtn.innerHTML = `<span>Locating...</span>`;
        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                gpsBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polygon points="12 2 15 11 12 9 9 11 12 2"/></svg> <span>Use My GPS</span>`;
                
                const isPune = (lat >= 18.35 && lat <= 18.75 && lon >= 73.65 && lon <= 74.05);
                if (isPune) {
                    await selectLocationByCoordinates(lat, lon, "Your Current GPS Location");
                } else {
                    alert(`Your current GPS position (${lat.toFixed(4)}, ${lon.toFixed(4)}) is outside Pune. Defaulting to Central Pune.`);
                    await selectLocationByCoordinates(18.5196, 73.8415, "FC Road, Deccan (Pune Default)");
                }
            },
            (err) => {
                gpsBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polygon points="12 2 15 11 12 9 9 11 12 2"/></svg> <span>Use My GPS</span>`;
                console.warn("GPS lookup denied or unavailable:", err.message);
                selectLocationByCoordinates(18.5196, 73.8415, "FC Road, Deccan");
            },
            { timeout: 7000 }
        );
    });
}

// ----------------------------------------------------------------------------
// 8. Core Location Resolution via /api/locate
// ----------------------------------------------------------------------------
async function selectLocationByCoordinates(lat, lon, customName = null) {
    try {
        const res = await fetch("/api/locate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat, lon })
        });
        const data = await res.json();
        updateActiveDispatchState(data, customName);
        updateLocationRoute();
        triggerPrediction();
    } catch (err) {
        console.error("Locate API failed:", err);
    }
}

async function selectLocationByQuery(query) {
    try {
        const res = await fetch("/api/locate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query })
        });
        const data = await res.json();
        updateActiveDispatchState(data);
        updateLocationRoute();
        triggerPrediction();
    } catch (err) {
        console.error("Query locate failed:", err);
    }
}

function updateActiveDispatchState(data, customName = null) {
    const loc = data.location;
    const st = data.nearest_station;
    const backup = data.backup_station;
    const wd = data.nearest_ward;

    activeDispatch = {
        locationName: customName || loc.name,
        lat: loc.latitude,
        lon: loc.longitude,
        stationId: st.station_id,
        stationName: st.station_name,
        stationLat: st.latitude,
        stationLon: st.longitude,
        wardId: wd.ward_id,
        wardName: wd.ward_name,
        wardZone: wd.zone,
        roadDistanceKm: data.road_distance_km,
        fleetCapacity: st.fleet_capacity
    };

    const nameElem = document.getElementById("match-location-name");
    const stElem = document.getElementById("match-station-name");
    const fleetElem = document.getElementById("match-station-fleet");
    const distElem = document.getElementById("match-distance-val");
    const wdElem = document.getElementById("match-ward-name");
    const zoneElem = document.getElementById("match-ward-zone");
    const backupElem = document.getElementById("match-backup-station");
    const backupDistElem = document.getElementById("match-backup-dist");

    if (nameElem) nameElem.textContent = activeDispatch.locationName;
    if (stElem) stElem.textContent = `${st.station_name} (${st.station_id})`;
    if (fleetElem) fleetElem.textContent = `Fleet: ${st.fleet_capacity} tenders ready`;
    if (distElem) distElem.textContent = `${activeDispatch.roadDistanceKm} km`;
    if (wdElem) wdElem.textContent = wd.ward_name;
    if (zoneElem) zoneElem.textContent = `Zone: ${wd.zone}`;
    if (backupElem) backupElem.textContent = backup.station_name;
    if (backupDistElem) backupDistElem.textContent = `${backup.road_distance_km} km road distance`;

    const searchInput = document.getElementById("location-search-input");
    if (searchInput && !searchInput.value) {
        searchInput.value = activeDispatch.locationName;
    }
}

function updateLocationRoute() {
    if (!map) return;

    const userLatLng = [activeDispatch.lat, activeDispatch.lon];

    if (userMarker) {
        userMarker.setLatLng(userLatLng);
    } else {
        userMarker = L.circleMarker(userLatLng, {
            radius: 8,
            fillColor: "#0071e3",
            color: "#ffffff",
            weight: 3,
            opacity: 1,
            fillOpacity: 1
        }).addTo(map);
    }

    userMarker.bindPopup(`
        <div style="font-family: -apple-system, sans-serif;">
            <strong style="color: #0071e3;">📍 Your Location</strong><br>
            ${activeDispatch.locationName}<br>
            <span style="color: #6e6e73; font-size: 11px;">Nearest: ${activeDispatch.stationName} (${activeDispatch.roadDistanceKm} km)</span>
        </div>
    `).openPopup();

    if (routeLine) {
        map.removeLayer(routeLine);
    }

    const stationLatLng = [activeDispatch.stationLat, activeDispatch.stationLon];
    const latlngs = [stationLatLng, userLatLng];

    routeLine = L.polyline(latlngs, {
        color: "#0071e3",
        weight: 4,
        opacity: 0.9,
        lineCap: "round",
        lineJoin: "round"
    }).addTo(map);

    map.fitBounds(L.latLngBounds(latlngs), { padding: [55, 55], maxZoom: 15 });
}

function updateManualRoute() {
    if (!map) return;

    const stId = document.getElementById("station-select").value;
    const wdId = document.getElementById("ward-select").value;

    const st = stationsData.find(s => s.station_id === stId);
    const wd = wardsData.find(w => w.ward_id === wdId);

    if (!st || !wd) return;

    if (routeLine) {
        map.removeLayer(routeLine);
    }

    const latlngs = [
        [st.latitude, st.longitude],
        [wd.centroid_lat, wd.centroid_lon]
    ];

    routeLine = L.polyline(latlngs, {
        color: "#0071e3",
        weight: 3.5,
        opacity: 0.85,
        lineCap: "round",
        lineJoin: "round"
    }).addTo(map);

    map.fitBounds(L.latLngBounds(latlngs), { padding: [45, 45] });
}

// ----------------------------------------------------------------------------
// 9. Prediction API Call, Memoization & Result Rendering
// ----------------------------------------------------------------------------
function initPredictButton() {
    const btn = document.getElementById("predict-btn");
    if (!btn) return;
    btn.addEventListener("click", () => triggerPrediction());
}

function triggerPrediction() {
    const btn = document.getElementById("predict-btn");

    let payload;
    if (currentMode === "location") {
        payload = {
            station_id: activeDispatch.stationId,
            ward_id: activeDispatch.wardId,
            emergency_type: document.getElementById("emergency-select").value,
            distance_km: activeDispatch.roadDistanceKm,
            incident_hour: parseInt(document.getElementById("hour-slider").value),
            rainfall_mm: selectedRain,
            is_monsoon: selectedMonsoon,
            is_weekend: 0
        };
    } else {
        payload = {
            station_id: document.getElementById("station-select").value,
            ward_id: document.getElementById("ward-select").value,
            emergency_type: document.getElementById("emergency-select").value,
            distance_km: parseFloat(document.getElementById("distance-slider").value),
            incident_hour: parseInt(document.getElementById("hour-slider").value),
            rainfall_mm: selectedRain,
            is_monsoon: selectedMonsoon,
            is_weekend: 0
        };
    }

    // Check client-side memoization cache
    const cacheKey = JSON.stringify(payload);
    if (clientPredictionCache.has(cacheKey)) {
        renderPredictionResults(clientPredictionCache.get(cacheKey));
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span>Calculating Arrival Time...</span>`;
    }

    fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        clientPredictionCache.set(cacheKey, data);
        renderPredictionResults(data);
    })
    .catch(err => console.error("Prediction failed:", err))
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span>Calculate Arrival Time (ETA)</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>`;
        }
    });
}

function renderPredictionResults(data) {
    lastPredictionResult = data;

    const minutesElem = document.getElementById("result-minutes");
    const intervalElem = document.getElementById("result-interval");
    const trafficElem = document.getElementById("result-traffic");
    const speedElem = document.getElementById("result-speed");
    const badgeElem = document.getElementById("risk-badge");
    const badgeTextElem = document.getElementById("risk-badge-text");
    const noteElem = document.getElementById("operational-explanation");
    const clockEtaElem = document.getElementById("result-clock-eta");

    const time = data.predicted_response_time_minutes;
    minutesElem.textContent = time.toFixed(1);

    if (clockEtaElem && data.eta_clock_time) {
        clockEtaElem.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span>Expected Arrival at <strong>${data.eta_clock_time}</strong> (Dispatched at ${data.dispatch_clock_time || 'Now'})</span>
        `;
    }

    intervalElem.textContent = `${data.prediction_interval_90_pct[0].toFixed(1)} – ${data.prediction_interval_90_pct[1].toFixed(1)} mins`;
    trafficElem.textContent = `${data.traffic_congestion_factor.toFixed(2)}x Baseline`;

    const effectiveSpeed = (data.input_parameters.network_distance_km / (time / 60.0)).toFixed(1);
    speedElem.textContent = `${effectiveSpeed} km/h`;

    const locationName = (currentMode === "location") ? activeDispatch.locationName : `Ward ${data.input_parameters.ward_id}`;
    const stationName = (currentMode === "location") ? activeDispatch.stationName : `Station ${data.input_parameters.station_id}`;

    if (data.high_delay_risk) {
        badgeElem.className = "apple-status-pill alert";
        badgeTextElem.textContent = "CORRIDOR DELAY LIKELY (>20 MINS)";
        noteElem.innerHTML = `
            <svg class="callout-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d70015" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <div class="callout-content">
                <strong>High Delay Advisory to ${locationName}:</strong> Heavy corridor friction (${data.traffic_congestion_factor}x) and weather delays will extend transit from <strong>${stationName}</strong> past the 20-minute municipal threshold. <em>Recommended action: Contact Pune Traffic Police for manual green corridor clearance or dispatch secondary auxiliary tender.</em>
            </div>
        `;
    } else {
        badgeElem.className = "apple-status-pill normal";
        badgeTextElem.textContent = "RAPID RESPONSE BENCHMARK (<20 MINS)";
        noteElem.innerHTML = `
            <svg class="callout-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#248a3d" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="9 11 12 14 22 4"/></svg>
            <div class="callout-content">
                <strong>Optimal Response Profile to ${locationName}:</strong> Expected tender transit from <strong>${stationName}</strong> (${data.input_parameters.network_distance_km} km) is within the municipal rapid response benchmark of 8–10 minutes.
            </div>
        `;
    }
}

// ----------------------------------------------------------------------------
// 10. Copy Dispatch Briefing to Clipboard
// ----------------------------------------------------------------------------
function initCopyBriefingButton() {
    const btn = document.getElementById("btn-copy-briefing");
    const textSpan = document.getElementById("copy-briefing-text");
    if (!btn) return;

    btn.addEventListener("click", () => {
        if (!lastPredictionResult) {
            alert("Please calculate an arrival time first.");
            return;
        }

        const data = lastPredictionResult;
        const locationName = (currentMode === "location") ? activeDispatch.locationName : `Ward ${data.input_parameters.ward_id}`;
        const stationName = (currentMode === "location") ? activeDispatch.stationName : `Station ${data.input_parameters.station_id}`;

        const briefing = [
            `🚨 PMC EMERGENCY DISPATCH BRIEFING`,
            `────────────────────────────────────`,
            `📍 Destination: ${locationName}`,
            `🚒 Responding Station: ${stationName}`,
            `🛣️ Road Network Distance: ${data.input_parameters.network_distance_km} km`,
            `⏱️ Expected Arrival (ETA): ${data.eta_clock_time} (${data.predicted_response_time_minutes} mins)`,
            `📊 90% Confidence Window: [${data.prediction_interval_90_pct[0]} - ${data.prediction_interval_90_pct[1]} mins]`,
            `🚦 Traffic Congestion: ${data.traffic_congestion_factor}x baseline`,
            `⚠️ Delay Risk Status: ${data.high_delay_risk ? 'HIGH CORRIDOR DELAY' : 'NORMAL / RAPID'}`,
            `Generated via Pune Emergency Response AI Platform`
        ].join('\n');

        navigator.clipboard.writeText(briefing).then(() => {
            if (textSpan) {
                const original = textSpan.textContent;
                textSpan.textContent = "✓ Briefing Copied!";
                setTimeout(() => { textSpan.textContent = original; }, 2200);
            }
        }).catch(err => {
            console.error("Clipboard copy failed:", err);
        });
    });
}

// ----------------------------------------------------------------------------
// 11. Dataset Explorer Table with Server-Side Pagination, Search & Sorting
// ----------------------------------------------------------------------------
function initTablePaginationAndSort() {
    const prevBtn = document.getElementById("btn-prev-page");
    const nextBtn = document.getElementById("btn-next-page");
    const searchInput = document.getElementById("table-search");
    const sortHeaders = document.querySelectorAll(".table-sort-header");

    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (tableState.page > 1) {
                tableState.page--;
                fetchIncidents();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            if (tableState.page < tableState.totalPages) {
                tableState.page++;
                fetchIncidents();
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            debouncedTableSearch(e.target.value.trim());
        });
    }

    sortHeaders.forEach(th => {
        th.addEventListener("click", () => {
            const field = th.getAttribute("data-sort");
            if (tableState.sortBy === field) {
                tableState.sortOrder = (tableState.sortOrder === "asc") ? "desc" : "asc";
            } else {
                tableState.sortBy = field;
                tableState.sortOrder = "asc";
            }
            
            sortHeaders.forEach(h => {
                const icon = h.querySelector(".sort-icon");
                if (icon) icon.textContent = "↕";
            });
            const activeIcon = th.querySelector(".sort-icon");
            if (activeIcon) {
                activeIcon.textContent = (tableState.sortOrder === "asc") ? "↑" : "↓";
            }

            tableState.page = 1;
            fetchIncidents();
        });
    });
}

async function fetchIncidents() {
    const tbody = document.getElementById("table-body");
    const countLabel = document.getElementById("table-record-count");
    const pageLabel = document.getElementById("current-page-label");
    const statusLabel = document.getElementById("pagination-status");
    const prevBtn = document.getElementById("btn-prev-page");
    const nextBtn = document.getElementById("btn-next-page");

    if (!tbody) return;

    try {
        const queryParams = new URLSearchParams({
            page: tableState.page,
            limit: tableState.limit,
            search: tableState.search,
            sort_by: tableState.sortBy,
            sort_order: tableState.sortOrder
        });

        const res = await fetch(`/api/incidents?${queryParams.toString()}`);
        const data = await res.json();

        tableState.totalPages = data.total_pages;
        tableState.totalCount = data.total_count;

        tbody.innerHTML = "";
        data.records.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${row.incident_id}</strong></td>
                <td>${row.dispatch_timestamp}</td>
                <td>${row.station_name}</td>
                <td>${row.ward_name}</td>
                <td><span class="apple-tag">${row.emergency_type}</span></td>
                <td>${row.network_distance_km} km</td>
                <td>${row.traffic_congestion_factor}x</td>
                <td>${row.rainfall_mm} mm</td>
                <td><strong>${row.response_time_minutes} min</strong></td>
            `;
            tbody.appendChild(tr);
        });

        const startIdx = (tableState.page - 1) * tableState.limit + 1;
        const endIdx = Math.min(tableState.page * tableState.limit, tableState.totalCount);

        if (countLabel) countLabel.textContent = `Showing ${tableState.totalCount.toLocaleString()} verified records`;
        if (pageLabel) pageLabel.textContent = `Page ${tableState.page} / ${tableState.totalPages}`;
        if (statusLabel) {
            statusLabel.textContent = (tableState.totalCount > 0)
                ? `Showing ${startIdx}–${endIdx} of ${tableState.totalCount.toLocaleString()} incidents`
                : "No matching incidents found";
        }

        if (prevBtn) prevBtn.disabled = (tableState.page <= 1);
        if (nextBtn) nextBtn.disabled = (tableState.page >= tableState.totalPages);

    } catch (err) {
        console.error("Failed to fetch incidents:", err);
    }
}
