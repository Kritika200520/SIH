/**
 * BHOOMI-RAKSHA DASHBOARD CONTROLLER
 * Disaster Management: Landslide & Flash-Flood Early Warning System
 */

// Global State
let map = null;
let currentMarkers = [];
let isAudioPlaying = false;
let audioElement = null;
let activeScenario = "chamoli_fissure";

// Coordinates for Hazard Sectors
const SECTOR_COORDS = {
  "chamoli_joshimath": { lat: 30.5562, lng: 79.5636, zoom: 14, name: "Chamoli - Joshimath Corridor" },
  "wayanad_meppadi": { lat: 11.5332, lng: 76.1320, zoom: 14, name: "Meppadi - Chooralmala, Wayanad" },
  "shimla_ridge": { lat: 31.1048, lng: 77.1734, zoom: 14, name: "Shimla Urban Ridge" },
  "darjeeling_tindharia": { lat: 26.8580, lng: 88.3360, zoom: 14, name: "Tindharia, Darjeeling" }
};

// Scenario Images
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
  // Poll every 3 seconds
  setInterval(fetchDashboardStatus, 3000);
});

/**
 * Initialize Leaflet Geospatial Map
 */
function initMap() {
  const defaultCoord = SECTOR_COORDS["chamoli_joshimath"];
  map = L.map('hazard-map', {
    zoomControl: true,
    attributionControl: false
  }).setView([defaultCoord.lat, defaultCoord.lng], defaultCoord.zoom);

  // High-Contrast Dark Matter Tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd'
  }).addTo(map);

  updateMapSector("chamoli_joshimath");
}

/**
 * Update Leaflet Map Layers & Pins for Selected Region
 */
function updateMapSector(sectorId) {
  if (!map) return;
  const sector = SECTOR_COORDS[sectorId] || SECTOR_COORDS["chamoli_joshimath"];
  map.flyTo([sector.lat, sector.lng], sector.zoom, { duration: 1.2 });

  // Clear previous markers
  currentMarkers.forEach(m => map.removeLayer(m));
  currentMarkers = [];

  // 1. Critical Fissure Cluster Circle (Red Radar)
  const dangerCircle = L.circle([sector.lat, sector.lng], {
    color: '#ff2a5f',
    fillColor: '#ff2a5f',
    fillOpacity: 0.25,
    radius: 400
  }).addTo(map);
  dangerCircle.bindPopup(`<b>CRITICAL HAZARD ZONE</b><br>${sector.name}<br>Active Fissure Depth: 8.4cm`).openPopup();
  currentMarkers.push(dangerCircle);

  // 2. Sentinel-1 InSAR Deformation Ring (Amber)
  const sarRing = L.circle([sector.lat + 0.002, sector.lng - 0.003], {
    color: '#ffb703',
    fillColor: '#ffb703',
    fillOpacity: 0.15,
    radius: 700
  }).addTo(map);
  sarRing.bindPopup(`<b>SENTINEL-1 InSAR</b><br>Ground Shift: +14.8 mm/yr LOS creep`);
  currentMarkers.push(sarRing);

  // 3. Safe Ridge Shelter Pin (Green)
  const safeMarker = L.circleMarker([sector.lat + 0.005, sector.lng + 0.004], {
    radius: 9,
    fillColor: "#00f5a0",
    color: "#fff",
    weight: 2,
    opacity: 1,
    fillOpacity: 0.9
  }).addTo(map);
  safeMarker.bindPopup(`<b>SAFE EVACUATION RIDGE</b><br>Elevation +450m Highland Shelter`);
  currentMarkers.push(safeMarker);

  // 4. Safe Corridor Polyline
  const routeLine = L.polyline([
    [sector.lat, sector.lng],
    [sector.lat + 0.003, sector.lng + 0.002],
    [sector.lat + 0.005, sector.lng + 0.004]
  ], {
    color: '#00f5a0',
    weight: 3,
    dashArray: '5, 8'
  }).addTo(map);
  currentMarkers.push(routeLine);
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
  document.getElementById("stat-sar").innerText = `${telem.sar_insar_displacement_mm || 14.8} mm/yr SHIFT`;
  document.getElementById("stat-fs").innerText = `Fs = ${fs.safety_factor_fs || 0.84} (${fs.stability_status || "CRITICAL"})`;
  document.getElementById("stat-rain").innerText = `${telem.rainfall_24h_mm || 78.5} mm / 24h`;
  document.getElementById("map-target-name").innerText = `SECTOR: ${(profile.region_name || "JOSHIMATH").toUpperCase()}`;

  // 2. VLM Vision Panel
  document.getElementById("vlm-tag-depth").innerText = `DEPTH: ${vlm.fissure_depth_cm || 8.4} cm`;
  document.getElementById("vlm-tag-class").innerText = (vlm.hazard_classification || "TENSION SCARP").replace(/_/g, " ");
  document.getElementById("vlm-tag-conf").innerText = `${vlm.confidence_score_pct || 93.5}% CONFIDENCE`;
  document.getElementById("voice-transcript").innerText = `"${vlm.voice_memo_transcript || ""}"`;
  document.getElementById("reporter-name").innerText = vlm.reporter_info || "Citizen Reporter";
  
  // VLM Metrics
  document.getElementById("metric-depth").innerHTML = `${vlm.fissure_depth_cm || 0} <small>cm</small>`;
  document.getElementById("bar-depth").style.width = `${Math.min(100, (vlm.fissure_depth_cm || 0) * 10)}%`;
  
  document.getElementById("metric-turbidity").innerHTML = `${vlm.turbidity_index_pct || 0} <small>%</small>`;
  document.getElementById("bar-turbidity").style.width = `${vlm.turbidity_index_pct || 0}%`;
  
  document.getElementById("metric-sat").innerHTML = `${vlm.soil_saturation_pct || 0} <small>%</small>`;
  document.getElementById("bar-sat").style.width = `${vlm.soil_saturation_pct || 0}%`;
  
  document.getElementById("metric-tilt").innerHTML = `${vlm.vegetation_tilt_deg || 0} <small>deg</small>`;
  document.getElementById("bar-tilt").style.width = `${Math.min(100, (vlm.vegetation_tilt_deg || 0) * 4)}%`;

  document.getElementById("vlm-explanation").innerText = vlm.geotechnical_explanation || "";

  // 3. Multi-Factor Risk Gauge
  const score = risk.composite_risk_score || data.severity_score || 85;
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
    
    // Set audio element source if available
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
  
  // Highlight active button
  document.querySelectorAll(".sc-btn").forEach(b => b.classList.remove("sc-btn--active"));
  const activeBtn = document.getElementById(`btn-sc-${scenarioId.split('_')[0]}`);
  if (activeBtn) activeBtn.classList.add("sc-btn--active");

  // Update preview image
  if (SCENARIO_IMAGES[scenarioId]) {
    document.getElementById("vlm-preview-img").src = SCENARIO_IMAGES[scenarioId];
  }

  // Post to backend
  try {
    const res = await fetch("/api/scenario/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId })
    });
    const data = await res.json();
    if (data.success && data.telemetry && data.telemetry.sector_profile) {
      updateMapSector(data.telemetry.sector_profile.id);
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
 * Trigger Operator Action (Confirm Dispatch / False Alarm)
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
      alert("?? EVACUATION ALERT CONFIRMED!\n\nHyper-localized voice alert dispatched via WhatsApp & IVR blast to village Gram Pradhans.");
      toggleAudioPlayback();
    } else {
      alert("??? System calibrated. False alarm registered in forensic audit log.");
    }
    fetchDashboardStatus();
  } catch (e) {
    console.error("Operator action error:", e);
  }
}
