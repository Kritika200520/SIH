/**
 * BHOOMI-RAKSHA DASHBOARD CONTROLLER
 * Disaster Management: Landslide & Flash-Flood Early Warning System
 * Featuring Interactive Google Maps-Style Traffic/Hazard Corridors
 */

// Global Map & UI State
let map = null;
let currentLayers = {
  traffic: [],
  insar: [],
  evac: [],
  pins: []
};
let layerVisibility = {
  traffic: true,
  insar: true,
  evac: true,
  pins: true
};
let isAudioPlaying = false;
let audioElement = null;
let activeScenario = "chamoli_fissure";

// Coordinates and Realistic Mountain Road Network Waypoints
const SECTOR_DATA = {
  "chamoli_joshimath": {
    lat: 30.5562,
    lng: 79.5636,
    zoom: 14,
    name: "Chamoli - Joshimath Corridor, Uttarakhand",
    roads: [
      {
        id: "rd-nh58-1",
        name: "NH-58 Badrinath National Highway (Marwari Ward 9)",
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
        color: "#ffb703",
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
        color: "#00f5a0",
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

  "wayanad_meppadi": {
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
        delay: "ROAD CUT-OFF",
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
        color: "#ffb703",
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
        color: "#00f5a0",
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

  "shimla_ridge": {
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
        cause: "RCC Retaining Wall 16.2? Outward Bulge & Road Sinking",
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
        color: "#ffb703",
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
        color: "#00f5a0",
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
        color: "#00f5a0",
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
 * Initialize Leaflet Map with Custom Cyber Dark Tiles & Click Interactivity
 */
function initMap() {
  const defaultCoord = SECTOR_DATA["chamoli_joshimath"];
  map = L.map('hazard-map', {
    zoomControl: true,
    attributionControl: false
  }).setView([defaultCoord.lat, defaultCoord.lng], defaultCoord.zoom);

  // High-Contrast CartoDB Voyager Map Layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd'
  }).addTo(map);

  // Map Click Listener to simulate dynamic report placement
  map.on('click', (e) => {
    handleMapClick(e.latlng);
  });

  renderMapCorridors("chamoli_joshimath");
}

/**
 * Render Interactive Color-Coded Road Corridors & Hazard Overlays
 */
function renderMapCorridors(sectorKey) {
  if (!map) return;
  const sector = SECTOR_DATA[sectorKey] || SECTOR_DATA["chamoli_joshimath"];

  // Clear existing layers
  Object.keys(currentLayers).forEach(k => {
    currentLayers[k].forEach(layer => map.removeLayer(layer));
    currentLayers[k] = [];
  });

  map.flyTo([sector.lat, sector.lng], sector.zoom, { duration: 1.0 });

  // 1. Render Google Maps-style Road Polylines
  sector.roads.forEach(road => {
    const polyline = L.polyline(road.points, {
      color: road.color,
      weight: road.weight,
      opacity: road.opacity,
      lineCap: 'round',
      lineJoin: 'round',
      className: road.status === 'BLOCKED' ? 'traffic-road-blocked' : (road.status === 'SLOW' ? 'traffic-road-slow' : 'traffic-road-clear')
    });

    // Interactive Hover & Click
    polyline.on('mouseover', () => updateRoadHUD(road));
    polyline.on('click', () => {
      updateRoadHUD(road);
      polyline.bindPopup(`
        <div style="font-family: sans-serif; font-size: 13px;">
          <strong style="color: ${road.color}; font-size: 14px;">${road.status === 'BLOCKED' ? '? ' : (road.status === 'SLOW' ? '?? ' : '? ')}${road.name}</strong><br><br>
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

  // Set initial HUD with first blocked or active road
  if (sector.roads.length > 0) {
    updateRoadHUD(sector.roads[0]);
  }

  // 2. Sentinel-1 InSAR Deformation Heat Radar Ring
  const insarCircle = L.circle([sector.lat + 0.0015, sector.lng - 0.002], {
    color: '#00f0ff',
    fillColor: '#00f0ff',
    fillOpacity: 0.18,
    radius: 650,
    weight: 2,
    dashArray: '4, 6'
  });
  insarCircle.bindPopup(`
    <b>??? SENTINEL-1 InSAR RADAR DETECTOR</b><br>
    Ground Displacement: <b>+14.8 mm/yr LOS creep</b><br>
    Coherence Index: <b>0.82 (High Confidence)</b>
  `);
  if (layerVisibility.insar) {
    insarCircle.addTo(map);
  }
  currentLayers.insar.push(insarCircle);

  // 3. Safe Highland Shelter Marker (Green Shield)
  if (sector.shelter) {
    const shelterPin = L.circleMarker([sector.shelter.lat, sector.shelter.lng], {
      radius: 10,
      fillColor: "#00f5a0",
      color: "#ffffff",
      weight: 3,
      opacity: 1,
      fillOpacity: 0.95
    });
    shelterPin.bindPopup(`<b>??? DESIGNATED SAFE RIDGE SHELTER</b><br>${sector.shelter.name}<br>High Ground Elevation Safe Zone`);
    if (layerVisibility.evac) {
      shelterPin.addTo(map);
    }
    currentLayers.evac.push(shelterPin);
  }

  // 4. Critical Citizen Photo Pin (Red Pulsing Marker)
  if (sector.fissurePoint) {
    const photoPin = L.circleMarker([sector.fissurePoint.lat, sector.fissurePoint.lng], {
      radius: 11,
      fillColor: "#ff2a5f",
      color: "#ffffff",
      weight: 3,
      opacity: 1,
      fillOpacity: 0.95,
      className: "pulse-fissure-marker"
    });
    photoPin.bindPopup(`<b>?? CITIZEN PHOTO VERIFIED</b><br>${sector.fissurePoint.label}<br>VLM Ground Tension Failure Confirmed`);
    if (layerVisibility.pins) {
      photoPin.addTo(map);
    }
    currentLayers.pins.push(photoPin);
  }
}

/**
 * Update the Road Segment HUD Card on Hover/Click
 */
function updateRoadHUD(road) {
  document.getElementById("hud-road-name").innerText = road.name;
  
  const statusEl = document.getElementById("hud-status");
  if (road.status === "BLOCKED") {
    statusEl.innerHTML = `? 94% BLOCKED (CRITICAL HAZARD)`;
    statusEl.className = "hud-v text-danger";
  } else if (road.status === "SLOW") {
    statusEl.innerHTML = `?? SLOW TRAFFIC (${road.delay})`;
    statusEl.className = "hud-v text-warning";
  } else {
    statusEl.innerHTML = `? CLEAR & OPEN (EVACUATION CORRIDOR)`;
    statusEl.className = "hud-v text-safe";
  }

  document.getElementById("hud-cause").innerText = road.cause;
  document.getElementById("hud-detour").innerText = road.detour;
}

/**
 * Toggle Map Layers (Traffic, InSAR, Evac, Pins)
 */
function toggleMapLayer(layerName) {
  layerVisibility[layerName] = !layerVisibility[layerName];
  const btn = document.getElementById(`tog-${layerName}`);
  
  if (layerVisibility[layerName]) {
    btn.classList.add("layer-btn--active");
    currentLayers[layerName].forEach(l => l.addTo(map));
  } else {
    btn.classList.remove("layer-btn--active");
    currentLayers[layerName].forEach(l => map.removeLayer(l));
  }
}

/**
 * Handle Map Click: Simulate User Dropping Citizen Report Pin
 */
async function handleMapClick(latlng) {
  const newPin = L.circleMarker([latlng.lat, latlng.lng], {
    radius: 9,
    fillColor: "#ff2a5f",
    color: "#fff",
    weight: 2,
    fillOpacity: 0.9
  }).addTo(map);
  
  newPin.bindPopup(`<b>?? NEW CITIZEN UPLOAD PROCESSED</b><br>Lat: ${latlng.lat.toFixed(4)}, Lng: ${latlng.lng.toFixed(4)}<br>VLM Depth: 8.1cm Fissure Detected!`).openPopup();
  currentLayers.pins.push(newPin);

  // Send to backend API
  try {
    await fetch("/api/citizen/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        location: `Mountain Sector (${latlng.lat.toFixed(4)}?N, ${latlng.lng.toFixed(4)}?E)`,
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

  // 1. Header Telemetry
  const trafficStat = document.getElementById("stat-traffic");
  if (data.severity_score >= 70) {
    trafficStat.innerHTML = `?? SEVERE ROAD BLOCKAGES`;
    trafficStat.className = "stat-v text-danger";
  } else if (data.severity_score >= 40) {
    trafficStat.innerHTML = `?? CAUTION / SLOW TRAFFIC`;
    trafficStat.className = "stat-v text-warning";
  } else {
    trafficStat.innerHTML = `?? ROADS CLEAR & OPEN`;
    trafficStat.className = "stat-v text-safe";
  }

  document.getElementById("stat-sar").innerText = `${telem.sar_insar_displacement_mm || 14.8} mm/yr SHIFT`;
  document.getElementById("stat-fs").innerText = `Fs = ${fs.safety_factor_fs || 0.84} (${fs.stability_status || "CRITICAL"})`;
  document.getElementById("map-target-name").innerText = `SECTOR: ${(profile.region_name || "JOSHIMATH").toUpperCase()}`;

  // 2. VLM Vision Panel (Voice memo removed, focused on visual diagnostics)
  document.getElementById("vlm-tag-depth").innerText = `DEPTH: ${vlm.fissure_depth_cm || 8.4} cm`;
  document.getElementById("vlm-tag-class").innerText = (vlm.hazard_classification || "TENSION SCARP").replace(/_/g, " ");
  document.getElementById("vlm-tag-conf").innerText = `${vlm.confidence_score_pct || 93.5}% CONFIDENCE`;
  document.getElementById("reporter-loc").innerText = vlm.location_name || "Marwari Ward 9, Joshimath";
  document.getElementById("reporter-name").innerText = vlm.reporter_info || "WhatsApp Verified Citizen Node";

  // VLM Metrics
  document.getElementById("metric-depth").innerHTML = `${vlm.fissure_depth_cm || 0} <small>cm</small>`;
  document.getElementById("bar-depth").style.width = `${Math.min(100, (vlm.fissure_depth_cm || 0) * 10)}%`;
  
  document.getElementById("metric-width").innerHTML = `${vlm.fissure_width_cm || 0} <small>cm</small>`;
  document.getElementById("bar-width").style.width = `${Math.min(100, (vlm.fissure_width_cm || 0) * 5)}%`;

  document.getElementById("metric-turbidity").innerHTML = `${vlm.turbidity_index_pct || 0} <small>%</small>`;
  document.getElementById("bar-turbidity").style.width = `${vlm.turbidity_index_pct || 0}%`;
  
  document.getElementById("metric-sat").innerHTML = `${vlm.soil_saturation_pct || 0} <small>%</small>`;
  document.getElementById("bar-sat").style.width = `${vlm.soil_saturation_pct || 0}%`;

  document.getElementById("vlm-explanation").innerText = vlm.geotechnical_explanation || "";

  // 3. Multi-Factor Risk Gauge
  const score = risk.composite_risk_score || data.severity_score || 87;
  document.getElementById("risk-score-num").innerText = score;
  document.getElementById("composite-score-badge").innerText = `RISK: ${score} / 100`;
  document.getElementById("threat-status-tag").innerText = risk.status ? risk.status.replace(/_/g, " ") : "CRITICAL IMMINENT";

  // Radial Fill
  const circle = document.getElementById("gauge-fill-circle");
  const dashOffset = 314 - (314 * (score / 100));
  circle.style.strokeDashoffset = dashOffset;
  if (score >= 70) {
    circle.style.stroke = "#ff2a5f";
  } else if (score >= 40) {
    circle.style.stroke = "#ffb703";
  } else {
    circle.style.stroke = "#00f5a0";
  }

  // Risk Breakdown
  const bk = risk.breakdown || {};
  document.getElementById("bk-vlm").innerText = `${bk.vlm_vision_score || 84}%`;
  document.getElementById("prog-vlm").style.width = `${bk.vlm_vision_score || 84}%`;
  document.getElementById("bk-sar").innerText = `${bk.insar_radar_score || 74}%`;
  document.getElementById("prog-sar").style.width = `${bk.insar_radar_score || 74}%`;
  document.getElementById("bk-fs").innerText = `${bk.geotechnical_fs_score || 90}%`;
  document.getElementById("prog-fs").style.width = `${bk.geotechnical_fs_score || 90}%`;
  document.getElementById("bk-rain").innerText = `${bk.imd_rainfall_score || 78}%`;
  document.getElementById("prog-rain").style.width = `${bk.imd_rainfall_score || 78}%`;

  // GSI RAG Snippets
  const ragList = document.getElementById("rag-excerpts-list");
  if (profile.geology) {
    ragList.innerHTML = `
      <li>[GSI Hazard Atlas]: Region categorized under High Landslide Zone (${profile.state}).</li>
      <li>[Geological Stratigraphy]: Bedrock: ${profile.geology}. Critical slope: ${profile.critical_slope_angle_deg}?.</li>
      <li>[Hydrological Trigger]: 24-Hour precipitation trigger threshold is ${profile.rainfall_threshold_24h_mm} mm.</li>
    `;
    document.getElementById("rag-sector-tag").innerText = `GSI SHEET #${profile.id ? profile.id.toUpperCase() : "CHAMOLI"}`;
  }

  // 4. Dialect Broadcast Panel
  if (bc.dialect) {
    document.getElementById("bc-dialect-tag").innerText = `DIALECT: ${(bc.dialect_name || bc.dialect).toUpperCase()}`;
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

  // 5. Event Logs
  if (data.event_log && data.event_log.length > 0) {
    const logBox = document.getElementById("audit-log-box");
    logBox.innerHTML = data.event_log.slice(0, 5).map(e => `
      <div class="log-entry ${e.type === 'CRITICAL' || e.type === 'ALERT' ? 'log-entry--critical' : 'log-entry--alert'}">
        <span class="log-t">${e.time}</span>
        <span class="log-badge">${e.type || 'INFO'}</span>
        <span class="log-msg">${e.event}</span>
      </div>
    `).join("");
  }
}

/**
 * Select Demo Scenario
 */
async function selectScenario(scenarioId) {
  activeScenario = scenarioId;
  
  document.querySelectorAll(".sc-btn").forEach(b => b.classList.remove("sc-btn--active"));
  const activeBtn = document.getElementById(`btn-sc-${scenarioId.split('_')[0]}`);
  if (activeBtn) activeBtn.classList.add("sc-btn--active");

  if (SCENARIO_IMAGES[scenarioId]) {
    document.getElementById("vlm-preview-img").src = SCENARIO_IMAGES[scenarioId];
  }

  // Render Google Maps Style Corridors for this Scenario
  renderMapCorridors(scenarioId);

  try {
    const res = await fetch("/api/scenario/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId })
    });
    const data = await res.json();
    if (data.success && data.telemetry) {
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
      document.getElementById("bc-dialect-tag").innerText = `DIALECT: ${data.broadcast.dialect_name.toUpperCase()}`;
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
      alert("?? EVACUATION ALERT CONFIRMED!\n\nHyper-localized voice alert dispatched via WhatsApp & IVR blast to village Gram Pradhans.\nRoad corridors updated with red congestion blockages.");
      toggleAudioPlayback();
    } else {
      alert("??? System calibrated. False alarm registered in forensic audit log.");
    }
    fetchDashboardStatus();
  } catch (e) {
    console.error("Operator action error:", e);
  }
}
