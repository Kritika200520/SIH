/**
 * BHOOMI-RAKSHA DASHBOARD CONTROLLER
 * Fullscreen Map Hero & Linear / Apple Titanium Glass HUD
 * Featuring Dynamic Pathfinding & Road Evacuation Routing Engine
 */

// Global Map & UI State
function updateBarColor(elementId, valuePct, thresholdAmber, thresholdDanger) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.className = el.className.replace(/\bbg-(safe|amber|danger)\b/g, '').trim();
  if (valuePct >= thresholdDanger) {
    el.classList.add('bg-danger');
  } else if (valuePct >= thresholdAmber) {
    el.classList.add('bg-amber');
  } else {
    el.classList.add('bg-safe');
  }
}

let map = null;
let currentLayers = {
  traffic: [],
  routes: [],
  insar: [],
  evac: [],
  pins: []
};
let layerVisibility = {
  traffic: true,
  routes: true,
  insar: true,
  evac: true,
  pins: true
};
let currentEvacMode = "vehicle";
let isAudioPlaying = false;
let audioElement = null;

// Cloud Offline Sync & Service Worker Registration
// Remove Service Worker (Bypass HTTP LAN restrictions for mobile)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function (registrations) {
    for (let registration of registrations) {
      registration.unregister();
    }
  });
}

function updateNetworkStatus() {
  const syncChip = document.getElementById('stat-sync');
  const chipContainer = document.getElementById('sync-chip');
  if (!syncChip) return;

  if (navigator.onLine) {
    syncChip.innerHTML = '[PASS] CLOUD ONLINE';
    syncChip.className = 'chip-v text-safe';
    chipContainer.style.borderColor = 'rgba(16, 185, 129, 0.4)';
  } else {
    syncChip.innerHTML = '[BLOCK] OFFLINE (CACHED)';
    syncChip.className = 'chip-v text-danger';
    chipContainer.style.borderColor = 'rgba(255, 42, 95, 0.4)';
  }
}
window.addEventListener('online', updateNetworkStatus);
window.addEventListener('offline', updateNetworkStatus);
document.addEventListener('DOMContentLoaded', updateNetworkStatus);

let activeScenario = "chamoli_fissure";

// Coordinates and Mountain Road Networks
const SECTOR_DATA = {
  "chamoli_fissure": {
    lat: 30.5562,
    lng: 79.5636,
    zoom: 14,
    name: "Chamoli - Joshimath Corridor, Uttarakhand",
    roads: [
      {
        id: "rd-nh58-1",
        name: "NH-58 Badrinath Highway (Marwari Ward 9)",
        status: "BLOCKED",
        severity: "CRITICAL",
        color: "#ff2a5f",
        weight: 7,
        opacity: 0.95,
        cause: "8.4cm Tension Fissure & Active Slope Slump",
        detour: "Divert uphill via Auli High Ridge B-4 Bypass",
        delay: "+4.5 hrs (Road Blocked)",
        points: [
          [30.5520, 79.5580],
          [30.5545, 79.5610],
          [30.5562, 79.5636],
          [30.5580, 79.5665]
        ]
      },
      {
        id: "rd-josh-2",
        name: "Joshimath Lower Bazaar Road (Downslope Ravine)",
        status: "SLOW",
        severity: "WARNING",
        color: "#f59e0b",
        weight: 6,
        opacity: 0.9,
        cause: "Subsurface Subsidence 14.8mm/yr & Pavement Buckling",
        detour: "Single lane open for light emergency vehicles only",
        delay: "+45 mins",
        points: [
          [30.5580, 79.5665],
          [30.5605, 79.5700],
          [30.5620, 79.5740]
        ]
      },
      {
        id: "rd-auli-evac",
        name: "Auli High Ridge Evacuation Corridor (Safe Route)",
        status: "CLEAR",
        severity: "SAFE",
        color: "#10b981",
        weight: 6,
        opacity: 0.9,
        cause: "Stable Bedrock Quartzite (Elevation +2800m)",
        detour: "Primary Designated Green Evacuation Corridor",
        delay: "0 mins (Flowing)",
        points: [
          [30.5545, 79.5610],
          [30.5570, 79.5580],
          [30.5610, 79.5560],
          [30.5650, 79.5540]
        ]
      }
    ],
    shelter: { lat: 30.5650, lng: 79.5540, name: "Auli High Ridge Relief Camp & Helipad" },
    fissurePoint: { lat: 30.5562, lng: 79.5636, label: "Tension Scarp: 8.4cm Depth" }
  },

  "wayanad_flood": {
    lat: 11.5332,
    lng: 76.1320,
    zoom: 14,
    name: "Meppadi - Chooralmala - Mundakkai, Wayanad",
    roads: [
      {
        id: "rd-choor-1",
        name: "Chooralmala Bridge & River Highway (Iruvaipuzha Basin)",
        status: "BLOCKED",
        severity: "CRITICAL",
        color: "#ff2a5f",
        weight: 7,
        opacity: 0.95,
        cause: "Massive Debris Flow Slurry (Turbidity 94.8%) & Bridge Damage",
        detour: "Halt all traffic; evacuate upstream towards Chembra Peak Camp",
        delay: "BRIDGE CUT-OFF",
        points: [
          [11.5280, 76.1260],
          [11.5310, 76.1290],
          [11.5332, 76.1320],
          [11.5350, 76.1350]
        ]
      },
      {
        id: "rd-mund-2",
        name: "Mundakkai Tea Estate Access Road",
        status: "SLOW",
        severity: "WARNING",
        color: "#f59e0b",
        weight: 6,
        opacity: 0.9,
        cause: "Heavy Water Inundation & Silt Accumulation (145mm Rain)",
        detour: "Emergency rescue convoys only",
        delay: "+1.2 hrs",
        points: [
          [11.5350, 76.1350],
          [11.5370, 76.1390],
          [11.5390, 76.1430]
        ]
      },
      {
        id: "rd-mep-evac",
        name: "Meppadi Higher Secondary School Evacuation Corridor",
        status: "CLEAR",
        severity: "SAFE",
        color: "#10b981",
        weight: 6,
        opacity: 0.9,
        cause: "Elevated Ridge Safe Zone",
        detour: "Primary Designated Safe Corridor",
        delay: "0 mins (Flowing)",
        points: [
          [11.5310, 76.1290],
          [11.5350, 76.1250],
          [11.5390, 76.1220],
          [11.5430, 76.1200]
        ]
      }
    ],
    shelter: { lat: 11.5430, lng: 76.1200, name: "Meppadi High Ground Relief Camp" },
    fissurePoint: { lat: 11.5332, lng: 76.1320, label: "Debris Slurry Dam Breach Zone" }
  },

  "shimla_subsidence": {
    lat: 31.1048,
    lng: 77.1734,
    zoom: 14,
    name: "Shimla Urban Ridge & Tutikandi, Himachal Pradesh",
    roads: [
      {
        id: "rd-cart-1",
        name: "Summer Hill - Cart Road Link (Near University)",
        status: "BLOCKED",
        severity: "CRITICAL",
        color: "#ff2a5f",
        weight: 7,
        opacity: 0.95,
        cause: "RCC Retaining Wall 16.2 deg Outward Bulge & Road Sinking",
        detour: "Divert via The Ridge Municipal Plaza bypass",
        delay: "+3 hrs (Closed)",
        points: [
          [31.1000, 77.1680],
          [31.1025, 77.1705],
          [31.1048, 77.1734],
          [31.1070, 77.1760]
        ]
      },
      {
        id: "rd-krish-2",
        name: "Krishna Nagar Downhill Road",
        status: "SLOW",
        severity: "WARNING",
        color: "#f59e0b",
        weight: 6,
        opacity: 0.9,
        cause: "Subsurface Creep & Slope Surcharge",
        detour: "Strictly one-way light vehicles",
        delay: "+30 mins",
        points: [
          [31.1070, 77.1760],
          [31.1090, 77.1790],
          [31.1110, 77.1820]
        ]
      },
      {
        id: "rd-ridge-evac",
        name: "The Ridge Municipal Plaza Evacuation Corridor",
        status: "CLEAR",
        severity: "SAFE",
        color: "#10b981",
        weight: 6,
        opacity: 0.9,
        cause: "Stable Jutogh Quartzite Bedrock",
        detour: "Safe Highland Assembly Area",
        delay: "0 mins (Flowing)",
        points: [
          [31.1025, 77.1705],
          [31.1060, 77.1680],
          [31.1100, 77.1650]
        ]
      }
    ],
    shelter: { lat: 31.1100, lng: 77.1650, name: "The Ridge Municipal Plaza Assembly Point" },
    fissurePoint: { lat: 31.1048, lng: 77.1734, label: "Retaining Wall Shear Failure (7.1cm)" }
  },

  "false_alarm_normal": {
    lat: 30.5562,
    lng: 79.5636,
    zoom: 14,
    name: "NH-58 Highway Sector B (Safe Baseline)",
    roads: [
      {
        id: "rd-norm-1",
        name: "NH-58 Rishikesh-Devprayag Mountain Highway",
        status: "CLEAR",
        severity: "SAFE",
        color: "#10b981",
        weight: 6,
        opacity: 0.9,
        cause: "Nominal Dry Road (Fs = 2.1)",
        detour: "Normal flow across all lanes",
        delay: "0 mins (On Schedule)",
        points: [
          [30.5520, 79.5580],
          [30.5545, 79.5610],
          [30.5562, 79.5636],
          [30.5580, 79.5665],
          [30.5605, 79.5700]
        ]
      }
    ],
    shelter: { lat: 30.5650, lng: 79.5540, name: "NH-58 Patrol Outpost" },
    fissurePoint: { lat: 30.5562, lng: 79.5636, label: "Highway Patrol Checkpoint (Nominal)" }
  }
};

// Scenario Photos
const SCENARIO_IMAGES = {
  "chamoli_fissure": "https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?auto=format&fit=crop&w=800&q=80",
  "wayanad_flood": "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
  "shimla_subsidence": "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80",
  "false_alarm_normal": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80"
};

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  fetchDashboardStatus();
  setInterval(fetchDashboardStatus, 3000);
});

/**
 * Initialize Fullscreen Leaflet Map
 */
function initMap() {
  const defaultCoord = SECTOR_DATA["chamoli_fissure"];
  map = L.map('hazard-map', {
    zoomControl: false,
    attributionControl: false
  }).setView([defaultCoord.lat, defaultCoord.lng], defaultCoord.zoom);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  L.control.zoom({ position: 'topright' }).addTo(map);

  map.on('click', (e) => {
    handleMapClick(e.latlng);
  });

  renderMapLayers("chamoli_fissure");
}

/**
 * Render Interactive Color-Coded Corridors, InSAR & Dynamic Pathfinding Polylines
 */
function renderMapLayers(scenarioKey, routingData = null) {
  if (!map) return;
  const sector = SECTOR_DATA[scenarioKey] || SECTOR_DATA["chamoli_fissure"];

  // Clear existing layers
  Object.keys(currentLayers).forEach(k => {
    currentLayers[k].forEach(layer => map.removeLayer(layer));
    currentLayers[k] = [];
  });

  map.flyTo([sector.lat, sector.lng], sector.zoom, { duration: 1.0 });

  // 1. Render Base Road Traffic Corridors
  sector.roads.forEach(road => {
    const polyline = L.polyline(road.points, {
      color: road.color,
      weight: road.weight,
      opacity: road.opacity,
      lineCap: 'round',
      lineJoin: 'round',
      className: road.status === 'BLOCKED' ? 'traffic-road-blocked' : (road.status === 'SLOW' ? 'traffic-road-slow' : 'traffic-road-clear')
    });

    polyline.on('click', () => {
      polyline.bindPopup(`
        <div style="font-family: sans-serif; font-size: 13px;">
          <strong style="color: ${road.color}; font-size: 14px;">${road.status === 'BLOCKED' ? '[BLOCKED] ' : (road.status === 'SLOW' ? '[SLOW] ' : '[CLEAR] ')}${road.name}</strong><br><br>
          <b>Status:</b> ${road.status} (${road.delay})<br>
          <b>Hazard Cause:</b> ${road.cause}<br>
          <b>Recommended Detour:</b> ${road.detour}
        </div>
      `).openPopup();
    });

    if (layerVisibility.traffic) {
      polyline.addTo(map);
    }
    currentLayers.traffic.push(polyline);
  });

  // 2. Render Dynamic Pathfinding Polylines (Naive Google Maps vs Bhoomi-Raksha Safe)
  if (routingData) {
    // 2A. Naive Google Maps Route (Red Dashed Line)
    if (routingData.google_maps_naive && routingData.google_maps_naive.waypoints.length > 1) {
      const naivePoly = L.polyline(routingData.google_maps_naive.waypoints, {
        color: "#ef4444",
        weight: 5,
        opacity: 0.9,
        dashArray: "6, 8",
        className: "route-poly-naive"
      });
      naivePoly.bindPopup(`<b>[X] NAIVE GOOGLE MAPS ROUTE</b><br>${routingData.google_maps_naive.warning}`);
      if (layerVisibility.routes) {
        naivePoly.addTo(map);
      }
      currentLayers.routes.push(naivePoly);
    }

    // 2B. Bhoomi-Raksha Safe Evacuation Route (Solid Emerald Glowing Polyline)
    if (routingData.bhoomi_raksha_safe && routingData.bhoomi_raksha_safe.waypoints.length > 1) {
      const safePoly = L.polyline(routingData.bhoomi_raksha_safe.waypoints, {
        color: "#10b981",
        weight: 7,
        opacity: 0.95,
        className: "route-poly-safe"
      });
      safePoly.bindPopup(`<b>[SAFE] BHOOMI-RAKSHA DYNAMIC SAFE CORRIDOR</b><br>${routingData.bhoomi_raksha_safe.safety_clearance}`);
      if (layerVisibility.routes) {
        safePoly.addTo(map);
      }
      currentLayers.routes.push(safePoly);
    }
  }

  // 3. Sentinel-1 InSAR Deformation Heat Radar Ring
  const insarCircle = L.circle([sector.lat + 0.0015, sector.lng - 0.002], {
    color: '#00f0ff',
    fillColor: '#00f0ff',
    fillOpacity: 0.18,
    radius: 650,
    weight: 2,
    dashArray: '4, 6'
  });
  insarCircle.bindPopup(`
    <b>SENTINEL-1 InSAR RADAR DETECTOR</b><br>
    Ground Displacement: <b>+14.8 mm/yr LOS creep</b><br>
    Coherence Index: <b>0.82 (High Confidence)</b>
  `);
  if (layerVisibility.insar) {
    insarCircle.addTo(map);
  }
  currentLayers.insar.push(insarCircle);

  // 4. Safe Highland Shelter Marker (Green Shield)
  if (sector.shelter) {
    const shelterPin = L.circleMarker([sector.shelter.lat, sector.shelter.lng], {
      radius: 10,
      fillColor: "#10b981",
      color: "#ffffff",
      weight: 3,
      opacity: 1,
      fillOpacity: 0.95
    });
    shelterPin.bindPopup(`<b>DESIGNATED SAFE RIDGE SHELTER</b><br>${sector.shelter.name}<br>High Ground Elevation Safe Zone`);
    if (layerVisibility.evac) {
      shelterPin.addTo(map);
    }
    currentLayers.evac.push(shelterPin);
  }

  // 5. Critical Citizen Photo Pin (Red Marker)
  if (sector.fissurePoint) {
    const photoPin = L.circleMarker([sector.fissurePoint.lat, sector.fissurePoint.lng], {
      radius: 11,
      fillColor: "#ff2a5f",
      color: "#ffffff",
      weight: 3,
      opacity: 1,
      fillOpacity: 0.95
    });
    photoPin.bindPopup(`<b>CITIZEN PHOTO VERIFIED</b><br>${sector.fissurePoint.label}<br>VLM Ground Tension Failure Confirmed`);
    if (layerVisibility.pins) {
      photoPin.addTo(map);
    }
    currentLayers.pins.push(photoPin);
  }
}

/**
 * Toggle Map Layers (Traffic, Routes, InSAR, Evac, Pins)
 */
function toggleMapLayer(layerName) {
  layerVisibility[layerName] = !layerVisibility[layerName];
  const btn = document.getElementById(`tog-${layerName}`);

  if (layerVisibility[layerName]) {
    btn.classList.add("layer-pill--active");
    currentLayers[layerName].forEach(l => l.addTo(map));
  } else {
    btn.classList.remove("layer-pill--active");
    currentLayers[layerName].forEach(l => map.removeLayer(l));
  }
}

/**
 * Switch Evacuation Mode (Vehicle vs Foot Trail)
 */
async function switchEvacMode(mode) {
  currentEvacMode = mode;
  document.getElementById("btn-mode-veh").classList.toggle("mode-btn--active", mode === "vehicle");
  document.getElementById("btn-mode-foot").classList.toggle("mode-btn--active", mode === "foot");

  try {
    const res = await fetch("/api/routing/navigate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: mode, vlm_depth_cm: 8.4, turbidity_pct: 45.0 })
    });
    const data = await res.json();
    if (data.success && data.routing) {
      updateRoutingUI(data.routing);
      renderMapLayers(activeScenario, data.routing);
    }
  } catch (e) {
    console.error("Evac mode switch error:", e);
  }
}

/**
 * Update Routing Side-by-Side Comparison UI
 */
function updateRoutingUI(routing) {
  if (!routing) return;
  const naive = routing.google_maps_naive || {};
  const safe = routing.bhoomi_raksha_safe || {};

  document.getElementById("naive-dist").innerText = `${naive.distance_km || 3.6} km | ${naive.status === 'BLOCKED' || naive.hazard_exposure_pct > 50 ? '+4.5h DELAY' : '8 mins'}`;
  document.getElementById("naive-warn").innerText = naive.warning || "Routes directly into active tension scarp collapse!";

  document.getElementById("safe-dist").innerText = `${safe.distance_km || 4.2} km | ${safe.eta_minutes || 12} mins (OPEN)`;
  document.getElementById("safe-desc").innerText = safe.safety_clearance || "Hazard Cost Surface Algorithm penalizes valley shear plane; dynamically routes via Auli High Ridge bypass.";
}

/**
 * Handle Map Click: Drop Simulated Report Pin
 */
async function handleMapClick(latlng) {
  const newPin = L.circleMarker([latlng.lat, latlng.lng], {
    radius: 9,
    fillColor: "#ff2a5f",
    color: "#fff",
    weight: 2,
    fillOpacity: 0.9
  }).addTo(map);

  newPin.bindPopup(`<b>NEW CITIZEN UPLOAD PROCESSED</b><br>Lat: ${latlng.lat.toFixed(4)}, Lng: ${latlng.lng.toFixed(4)}<br>VLM Depth: 8.1cm Fissure Detected!`).openPopup();
  currentLayers.pins.push(newPin);

  try {
    await fetch("/api/citizen/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        location: `Mountain Sector (${latlng.lat.toFixed(4)}N, ${latlng.lng.toFixed(4)}E)`,
        voice_memo: "New tension fissure crack reported by field observer.",
        reporter_name: "Citizen WhatsApp Ingestion"
      })
    });
    fetchDashboardStatus();
  } catch (e) {
    console.error("Map click submission error:", e);
  }
}

function simulateNewCitizenClick() {
  if (!map) return;
  const center = map.getCenter();
  const offsetLat = center.lat + (Math.random() - 0.5) * 0.004;
  const offsetLng = center.lng + (Math.random() - 0.5) * 0.004;
  handleMapClick({ lat: offsetLat, lng: offsetLng });
}

/**
 * Fetch Live Dashboard Status from Flask API
 */
async function fetchDashboardStatus() {
  try {
    const res = await fetch("/api/dashboard/status");
    if (!res.ok) return;
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.warn("Backend poll fallback:", err);
  }
}

/**
 * Render Complete Dashboard UI from API Data
 */
function renderDashboard(data) {
  const telem = data.telemetry || {};
  const vlm = telem.vlm || {};
  const fs = telem.geotechnical_fs || {};
  const risk = telem.risk_fusion || {};
  const bc = telem.broadcast || {};
  const profile = telem.sector_profile || {};
  const routing = telem.dynamic_routing || null;

  // 1. Header Telemetry
  document.getElementById("stat-sar").innerText = `${telem.sar_insar_displacement_mm || 14.8} mm/yr`;
  document.getElementById("stat-fs").innerText = `${fs.safety_factor_fs || 0.84} (${fs.stability_status ? fs.stability_status.split('_')[0] : "CRITICAL"})`;

  if (document.getElementById("stat-weather")) {
    document.getElementById("stat-weather").innerText = `${telem.rainfall_24h_mm !== undefined ? telem.rainfall_24h_mm.toFixed(1) : '--'} mm`;
  }

  // 2. Routing Comparison UI & Polyline Overlays
  if (routing) {
    updateRoutingUI(routing);
  }

  // 3. VLM Vision Panel
  document.getElementById("vlm-tag-depth").innerText = `DEPTH: ${vlm.fissure_depth_cm || 8.4} cm`;
  document.getElementById("vlm-tag-class").innerText = (vlm.hazard_classification || "TENSION SCARP").replace(/_/g, " ");
  document.getElementById("vlm-tag-conf").innerText = `${vlm.confidence_score_pct || 93.5}% CONFIDENCE`;
  document.getElementById("reporter-loc").innerText = vlm.location_name || "Marwari Ward 9, Joshimath";
  document.getElementById("reporter-name").innerText = vlm.reporter_info || "WhatsApp Citizen Ingestion API";

  document.getElementById("metric-depth").innerHTML = `${vlm.fissure_depth_cm || 0} <small>cm</small>`;
  const depthPct = Math.min(100, (vlm.fissure_depth_cm || 0) * 10);
  document.getElementById("bar-depth").style.width = `${depthPct}%`;
  updateBarColor("bar-depth", depthPct, 40, 75);

  document.getElementById("metric-width").innerHTML = `${vlm.fissure_width_cm || 0} <small>cm</small>`;
  const widthPct = Math.min(100, (vlm.fissure_width_cm || 0) * 5);
  document.getElementById("bar-width").style.width = `${widthPct}%`;
  updateBarColor("bar-width", widthPct, 40, 75);

  document.getElementById("metric-turbidity").innerHTML = `${vlm.turbidity_index_pct || 0} <small>%</small>`;
  const turbPct = vlm.turbidity_index_pct || 0;
  document.getElementById("bar-turbidity").style.width = `${turbPct}%`;
  updateBarColor("bar-turbidity", turbPct, 30, 60);

  document.getElementById("metric-sat").innerHTML = `${vlm.soil_saturation_pct || 0} <small>%</small>`;
  const satPct = vlm.soil_saturation_pct || 0;
  document.getElementById("bar-sat").style.width = `${satPct}%`;
  updateBarColor("bar-sat", satPct, 50, 80);

  document.getElementById("vlm-explanation").innerText = vlm.geotechnical_explanation || "";

  // 4. Multi-Factor Risk Gauge
  const score = risk.composite_risk_score || data.severity_score || 87;
  document.getElementById("risk-score-num").innerText = score;
  document.getElementById("composite-score-badge").innerText = `RISK: ${score}/100`;

  const circle = document.getElementById("gauge-fill-circle");
  const dashOffset = 264 - (264 * (score / 100));
  circle.style.strokeDashoffset = dashOffset;
  if (score >= 70) {
    circle.style.stroke = "#ff2a5f";
  } else if (score >= 40) {
    circle.style.stroke = "#f59e0b";
  } else {
    circle.style.stroke = "#10b981";
  }

  const bk = risk.breakdown || {};
  document.getElementById("bk-vlm").innerText = `${bk.vlm_vision_score || 84}%`;
  let vlmScore = bk.vlm_vision_score || 84;
  document.getElementById("prog-vlm").style.width = `${vlmScore}%`;
  updateBarColor("prog-vlm", vlmScore, 50, 75);

  document.getElementById("bk-sar").innerText = `${bk.insar_radar_score || 74}%`;
  let sarScore = bk.insar_radar_score || 74;
  document.getElementById("prog-sar").style.width = `${sarScore}%`;
  updateBarColor("prog-sar", sarScore, 50, 75);

  document.getElementById("bk-fs").innerText = `${bk.geotechnical_fs_score || 90}%`;
  let fsScore = bk.geotechnical_fs_score || 90;
  document.getElementById("prog-fs").style.width = `${fsScore}%`;
  updateBarColor("prog-fs", fsScore, 50, 75);

  document.getElementById("bk-rain").innerText = `${bk.imd_rainfall_score || 78}%`;
  let rainScore = bk.imd_rainfall_score || 78;
  document.getElementById("prog-rain").style.width = `${rainScore}%`;
  updateBarColor("prog-rain", rainScore, 50, 75);

  // GSI RAG Snippets
  const ragList = document.getElementById("rag-excerpts-list");
  if (profile.geology) {
    ragList.innerHTML = `
      <li>[GSI Atlas]: High Landslide Zone (${profile.state}).</li>
      <li>[Stratigraphy]: Bedrock: ${profile.geology}. Critical slope: ${profile.critical_slope_angle_deg} deg.</li>
      <li>[Threshold]: 24h Rainfall Trigger: ${profile.rainfall_threshold_24h_mm} mm.</li>
    `;
    document.getElementById("rag-sector-tag").innerText = `SHEET #${profile.id ? profile.id.toUpperCase() : "CHAMOLI"}`;
  }

  // AI Predictive Forecast UI
  const ai = telem.ai_prediction;
  if (ai) {
    document.getElementById("ai-model-tag").innerText = ai.model_type || "XGBoost Ensemble";
    document.getElementById("ai-prob").innerHTML = `${ai.ai_probability_pct} <small>%</small>`;
    document.getElementById("ai-timeline").innerText = `${ai.predicted_timeline} | Action: ${ai.recommended_action}`;

    const probEl = document.getElementById("ai-prob");
    const timelineEl = document.getElementById("ai-timeline");
    if (ai.ai_probability_pct >= 75) {
      probEl.className = "cell-val text-danger";
      timelineEl.className = "cell-val text-danger";
    } else if (ai.ai_probability_pct >= 50) {
      probEl.className = "cell-val text-amber";
      timelineEl.className = "cell-val text-amber";
    } else {
      probEl.className = "cell-val text-safe";
      timelineEl.className = "cell-val text-safe";
    }
  }

  // 5. Dialect Broadcast Panel
  if (bc.dialect) {
    document.getElementById("bc-script-text").innerText = bc.speech_script || bc.broadcast_text;
    document.getElementById("bc-route-text").innerText = bc.evacuation_route || "";
    document.getElementById("audio-label").innerText = `Emergency Broadcast Voice Note (${bc.dialect})`;

    if (bc.audio_url) {
      if (!audioElement || audioElement.dataset.url !== bc.audio_url) {
        audioElement = new Audio(bc.audio_url);
        audioElement.dataset.url = bc.audio_url;
        audioElement.onended = () => stopAudioUI();
      }
    }
  }

  // 6. AI Anti-Spam & Image Authenticity Protocol
  if (telem.spam_filter) {
    updateSpamFilterUI(telem.spam_filter);
  }

  // 7. Mini Audit Ticker
  if (data.event_log && data.event_log.length > 0) {
    const latestEvent = data.event_log[0];
    document.getElementById("audit-ticker-msg").innerText = `[${latestEvent.time}] ${latestEvent.event}`;
  }

  // 8. Real-Time WhatsApp Citizen SOS Modal Popup
  if (data.latest_whatsapp_alert) {
    handleWhatsAppAlertPopup(data.latest_whatsapp_alert);
  }
}

let lastSeenSosTimestamp = null;

function playAlertChime() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    osc.frequency.setValueAtTime(1174.66, audioCtx.currentTime + 0.15);
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.45);
  } catch (e) {
    console.log("Audio chime info:", e);
  }
}

function handleWhatsAppAlertPopup(alertData) {
  if (!alertData) return;
  const alertKey = alertData.id || `${alertData.sender}_${alertData.text}_${alertData.timestamp}`;
  if (alertKey === lastSeenSosTimestamp) return;
  lastSeenSosTimestamp = alertKey;

  console.log("[BHOOMI-RAKSHA] Emergency WhatsApp Alert Triggered:", alertData);

  const modal = document.getElementById("whatsapp-sos-modal");
  const senderPhone = document.getElementById("sos-sender-phone");
  const messageContent = document.getElementById("sos-message-content");
  const timestampEl = document.getElementById("sos-timestamp");

  const displayName = alertData.contact_name ? `${alertData.contact_name} (+${alertData.sender})` : `+${alertData.sender}`;
  if (senderPhone) senderPhone.innerText = displayName;
  if (messageContent) messageContent.innerText = `"${alertData.text}"`;
  if (timestampEl) timestampEl.innerText = `Live Alert • Received at ${alertData.timestamp}`;

  if (modal) {
    modal.style.setProperty("display", "flex", "important");
    modal.classList.add("sos-modal--active");
    playAlertChime();
  }
}

function dismissSosModal() {
  const modal = document.getElementById("whatsapp-sos-modal");
  if (modal) {
    modal.style.setProperty("display", "none", "important");
    modal.classList.remove("sos-modal--active");
  }
}

/**
 * 1-Click Simulator to test WhatsApp SOS modal popup
 */
async function simulateIncomingWhatsApp() {
  const testPhone = "919773834230";
  const testMsg = "Emergency SOS: Flash flood water rising rapidly near bridge, road cracked!";
  
  handleWhatsAppAlertPopup({
    sender: testPhone,
    text: testMsg,
    timestamp: new Date().toLocaleTimeString(),
    msg_type: "text"
  });

  try {
    await fetch("/api/webhook/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sender: testPhone,
        text: testMsg
      })
    });
  } catch (e) {
    console.warn("Simulate webhook call:", e);
  }
}

/**
 * Render AI Anti-Spam & Authenticity Protocol HUD
 */
function updateSpamFilterUI(verif) {
  if (!verif) return;

  const badge = document.getElementById("spam-status-badge");
  const reasonBox = document.getElementById("spam-reason-box");
  const reasonText = document.getElementById("spam-decision-reason");
  const gpsDelta = document.getElementById("spam-gps-delta");
  const towerCid = document.getElementById("spam-tower-cid");
  const dhashMatch = document.getElementById("spam-dhash-match");
  const elaScore = document.getElementById("spam-ela-score");

  const isPassed = (verif.verification_status === "VERIFIED_AUTHENTIC");
  const isFlagged = (verif.verification_status === "SUSPICIOUS_FLAGGED");

  if (badge) {
    badge.innerText = `${verif.status_badge} (${verif.composite_trust_score}%)`;
    badge.className = isPassed ? "badge-mini badge-mini--safe" : (isFlagged ? "badge-mini badge-mini--amber" : "badge-mini badge-mini--danger");
  }

  if (reasonBox) {
    reasonBox.className = isPassed ? "spam-reason-box" : "spam-reason-box spam-reason-box--blocked";
  }

  if (reasonText) {
    const icon = isPassed ? "[PASS]" : (isFlagged ? "[WARN]" : "[BLOCK]");
    reasonText.innerHTML = `<strong>${icon} Decision:</strong> ${verif.decision_reason}`;
  }

  const geo = verif.geolocation_check || {};
  if (gpsDelta) {
    if (geo.exif_gps_status === "MATCH") {
      gpsDelta.innerHTML = `<span class="text-safe">${geo.gps_delta_meters}m Delta (MATCH - Ward 9)</span>`;
    } else if (geo.exif_gps_status === "STRIPPED_OR_MISSING") {
      gpsDelta.innerHTML = `<span class="text-amber">Stripped / WhatsApp WebP</span>`;
    } else {
      gpsDelta.innerHTML = `<span class="text-danger">${geo.distance_to_sector_km}km (OUT OF BOUNDS)</span>`;
    }
  }

  const tower = verif.cell_tower_check || {};
  if (towerCid) {
    if (tower.telecom_circle_valid) {
      towerCid.innerHTML = `<span class="text-safe">Circle Valid (LAC:${tower.lac} / CID:${tower.cid})</span>`;
    } else {
      towerCid.innerHTML = `<span class="text-danger">MISMATCH (Non-Disaster Circle)</span>`;
    }
  }

  const auth = verif.authenticity_check || {};
  if (dhashMatch) {
    if (auth.duplicate_detected) {
      dhashMatch.innerHTML = `<span class="text-danger">${auth.similarity_match_pct}% Match (${auth.matched_archive_record})</span>`;
    } else {
      dhashMatch.innerHTML = `<span class="text-safe">0% Duplicate (Unique Field Frame)</span>`;
    }
  }

  if (elaScore) {
    if (auth.tampering_software_flag) {
      elaScore.innerHTML = `<span class="text-danger">TAMPERED (${auth.software_signature})</span>`;
    } else if (auth.ela_compression_score >= 80) {
      elaScore.innerHTML = `<span class="text-safe">${auth.ela_compression_score}% Raw Sensor Consistency</span>`;
    } else {
      elaScore.innerHTML = `<span class="text-amber">${auth.ela_compression_score}% Recompressed</span>`;
    }
  }
}

/**
 * Interactive Spam Filter Preset Trigger
 */
async function testSpamPreset(presetKey) {
  document.querySelectorAll(".spam-pill").forEach(p => {
    p.classList.remove("spam-pill--active");
    p.classList.remove("spam-pill--blocked");
  });

  const activePill = document.getElementById(`btn-spam-${presetKey}`);
  if (activePill) {
    if (presetKey === "live_authentic_field") {
      activePill.classList.add("spam-pill--active");
    } else {
      activePill.classList.add("spam-pill--blocked");
    }
  }

  try {
    const res = await fetch("/api/spam-filter/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preset_key: presetKey })
    });
    const data = await res.json();
    if (data.success && data.verification) {
      updateSpamFilterUI(data.verification);
    }
  } catch (err) {
    console.error("Spam preset test error:", err);
  }
}

/**
 * Select Demo Scenario
 */
async function selectScenario(scenarioId) {
  activeScenario = scenarioId;

  document.querySelectorAll(".sc-pill").forEach(b => b.classList.remove("sc-pill--active"));
  const activeBtn = document.getElementById(`btn-sc-${scenarioId.split('_')[0]}`);
  if (activeBtn) activeBtn.classList.add("sc-pill--active");

  if (SCENARIO_IMAGES[scenarioId]) {
    document.getElementById("vlm-preview-img").src = SCENARIO_IMAGES[scenarioId];
  }

  try {
    const res = await fetch("/api/scenario/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId })
    });
    const data = await res.json();
    if (data.success && data.telemetry) {
      renderMapLayers(scenarioId, data.telemetry.dynamic_routing);
      renderDashboard({ telemetry: data.telemetry });
    }
  } catch (e) {
    console.error("Scenario switch error:", e);
  }
}

/**
 * Change Dialect for Voice Broadcast
 */
async function changeDialect(dialectKey) {
  try {
    const res = await fetch("/api/broadcast/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dialect: dialectKey })
    });
    const data = await res.json();
    if (data.success && data.broadcast) {
      document.getElementById("bc-script-text").innerText = data.broadcast.speech_script;
      document.getElementById("bc-route-text").innerText = data.broadcast.evacuation_route;
      document.getElementById("audio-label").innerText = `Emergency Broadcast Voice Note (${dialectKey})`;

      if (data.broadcast.audio_url) {
        audioElement = new Audio(data.broadcast.audio_url);
        audioElement.dataset.url = data.broadcast.audio_url;
        audioElement.onended = () => stopAudioUI();
      }
    }
  } catch (e) {
    console.error("Dialect change error:", e);
  }
}

/**
 * Toggle Audio Playback
 */
function toggleAudioPlayback() {
  if (isAudioPlaying) {
    if (audioElement) audioElement.pause();
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    stopAudioUI();
  } else {
    startAudioUI();
    if (audioElement) {
      audioElement.play().catch(() => {
        fallbackSpeechSynthesis();
      });
    } else {
      fallbackSpeechSynthesis();
    }
  }
}

function fallbackSpeechSynthesis() {
  const text = document.getElementById("bc-script-text").innerText;
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.onend = () => stopAudioUI();
    window.speechSynthesis.speak(utterance);
  } else {
    setTimeout(stopAudioUI, 4000);
  }
}

function startAudioUI() {
  isAudioPlaying = true;
  document.getElementById("play-icon").innerText = "?";
  document.getElementById("audio-wave-anim").classList.add("playing");
}

function stopAudioUI() {
  isAudioPlaying = false;
  document.getElementById("play-icon").innerText = "?";
  document.getElementById("audio-wave-anim").classList.remove("playing");
}

/**
 * Trigger Operator Action
 */
async function triggerOperatorAction(actionName) {
  try {
    const res = await fetch("/api/action/operator", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionName })
    });
    const data = await res.json();
    if (actionName === "CONFIRM_DISPATCH") {
      alert("?? EVACUATION ALERT CONFIRMED!\n\nHyper-localized voice alert dispatched via WhatsApp & IVR blast to village Gram Pradhans.\nRoad corridors updated with dynamic safe bypasses.");
      toggleAudioPlayback();
    } else {
      alert("??? System calibrated. False alarm registered in forensic audit log.");
    }
    fetchDashboardStatus();
  } catch (e) {
    console.error("Operator action error:", e);
  }
}
