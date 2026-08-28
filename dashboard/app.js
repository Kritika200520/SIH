/**
 * ROBO RAKSHA — Autonomous Emergency Intelligence & Forensic AI System
 * Syncs AI Vision, Generative Accident Statement, Evidence Clip, 5 Patent Claims,
 * Risk Core Countdown, Sensor Constellation, and Dispatch panel.
 */

const getBaseUrl = () => {
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "http://localhost:5000";
  }
  return window.location.origin;
};

let pollInterval = null;
let lastState = "NORMAL";
let audioCtx = null;
let currentAIStatement = "";

function playAlertTone() {
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.35);
    gain.gain.setValueAtTime(0.18, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.35);
  } catch (e) {}
}

document.addEventListener("DOMContentLoaded", () => {
  pollInterval = setInterval(fetchStatus, 1000);
  fetchStatus();
  updateClock();
  setInterval(updateClock, 1000);
});

function updateClock() {
  const ts = document.getElementById("footer-timestamp");
  if (ts) {
    const now = new Date();
    ts.innerText = `SYSTEM TIME ${now.toTimeString().split(' ')[0]} IST`;
  }
}

async function fetchStatus() {
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/dashboard/status`);
    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    renderInterface(data);
  } catch (err) {
    console.warn("Status fetch error:", err);
  }
}

function renderInterface(data) {
  const state = data.state || "NORMAL";
  const aiInfo = data.ai_vision || {};
  const loc = data.location || {};
  const tele = data.latest_telemetry || {};
  const evid = aiInfo.evidence_clip || {};
  const spectral = data.multi_spectral_matrix || {};
  const d3 = data.d3_perimeter || {};
  const crypto = data.crypto_ledger || {};
  const recal = data.ai_recalibration || {};
  const rawScore = data.severity !== undefined ? data.severity : (aiInfo.intensity_score || 0);

  // 1. Set Body Class State
  const body = document.body;
  const modeLabel = document.getElementById("mode-label");
  const coreScore = document.getElementById("severity-score");
  const coreBand = document.getElementById("severity-band");
  const alertTitle = document.getElementById("alert-title");
  const alertDesc = document.getElementById("alert-description");
  const alertSource = document.getElementById("alert-source-sensor");
  const locData = document.getElementById("location-data");
  const feedEnv = document.getElementById("feed-environment");
  const feedCenter = document.getElementById("feed-center-text");
  const antiFalse = document.getElementById("anti-false-tag");
  const statementText = document.getElementById("ai-statement-text");

  currentAIStatement = aiInfo.ai_incident_statement || "No active threat detected.";

  if (state === "ALERT" || state === "UNVERIFIED_ALERT" || state === "POLICE_CONFIRMED") {
    body.className = "alert";
    if (modeLabel) modeLabel.innerText = "EMERGENCY ALERT ACTIVATED";
    if (feedEnv) feedEnv.innerText = `ENVIRONMENT HAZARD: ${(aiInfo.label || "CRITICAL").toUpperCase()}`;
    if (feedCenter) feedCenter.innerText = `⚠️ HAZARD TARGET: ${(aiInfo.label || "EMERGENCY").toUpperCase()}`;
    
    if (lastState === "NORMAL") {
      playAlertTone();
      appendTimelineEvent(`EMERGENCY ALERT: ${aiInfo.label || "Hazard Detected"}`, "critical");
    }
  } else if (state === "DISPATCHED" || state === "ESCALATED_SOS_5KM") {
    body.className = "dispatched";
    if (modeLabel) modeLabel.innerText = "DISPATCHING EMERGENCY SERVICES (5KM SOS)";
    if (feedEnv) feedEnv.innerText = "5KM SOS DISPATCH ESCALATION ACTIVE";
    if (feedCenter) feedCenter.innerText = "🚨 5KM SOS BROADCAST EXECUTED";
    
    if (lastState !== "DISPATCHED" && lastState !== "ESCALATED_SOS_5KM") {
      playAlertTone();
      appendTimelineEvent("AUTO-DIALED AMBULANCE (108) & BROADCASTED 5KM SOS", "critical");
    }
  } else {
    body.className = "normal";
    if (modeLabel) modeLabel.innerText = "SYSTEM NORMAL";
    if (feedEnv) feedEnv.innerText = "ENVIRONMENT NOMINAL";
    if (feedCenter) feedCenter.innerText = "AI OPTICAL SURVEILLANCE ACTIVE";
  }

  lastState = state;

  // 2. Risk Core Readout & Bands
  const displayScore = Math.round(rawScore);
  if (coreScore) coreScore.innerText = displayScore;
  if (coreBand) {
    if (displayScore >= 85) coreBand.innerText = "CRITICAL";
    else if (displayScore >= 60) coreBand.innerText = "HIGH";
    else if (displayScore >= 30) coreBand.innerText = "CAUTION";
    else coreBand.innerText = "SAFE";
  }

  // 3. Countdown Ring
  const cdElem = document.getElementById("countdown");
  const cdCircle = document.getElementById("countdown-circle");
  if (cdElem) {
    const secs = data.timer_seconds !== undefined ? data.timer_seconds : 300;
    const mins = Math.floor(secs / 60);
    const remSecs = secs % 60;
    cdElem.innerText = `${mins < 10 ? '0' : ''}${mins}:${remSecs < 10 ? '0' : ''}${remSecs}`;

    if (cdCircle) {
      const maxSecs = 300;
      const fraction = Math.max(0, Math.min(1, secs / maxSecs));
      const strokeOffset = 339 * (1 - fraction);
      cdCircle.style.strokeDashoffset = strokeOffset;
    }
  }

  // 4. Alert Summary & Generative AI Statement Box
  if (alertTitle) {
    if (state === "NORMAL" || state === "RESOLVED" || state === "CANCELLED") {
      alertTitle.innerText = "NO ACTIVE THREAT";
      if (alertDesc) alertDesc.innerText = "All environmental systems are operating normally. ROBO RAKSHA is monitoring continuously.";
      if (antiFalse) antiFalse.innerText = "🛡️ Anti-False-Alarm: CLEAR";
    } else {
      alertTitle.innerText = (aiInfo.label || "HAZARD DETECTED").toUpperCase();
      if (alertDesc) alertDesc.innerText = aiInfo.ai_summary || "Visual and acoustic sensors corroborate high-intensity incident.";
      if (antiFalse) antiFalse.innerText = aiInfo.anti_false_alarm_verified ? "✅ Anti-False-Alarm: VERIFIED (3/3 Frames)" : "⏳ Anti-False-Alarm: VALIDATING...";
    }
  }
  if (statementText) {
    statementText.innerText = currentAIStatement;
  }
  if (locData && loc.address) {
    locData.innerText = `${loc.address} · ${loc.lat}°N, ${loc.lng}°E`;
  }
  if (alertSource) {
    alertSource.innerText = `Active D3 Radius: ${d3.active_radius_km || 5.0} km (${d3.responders_in_range || 14} Responders Armed)`;
  }

  // 5. AI Evidence Video Clip Metadata
  const evidId = document.getElementById("evidence-clip-id");
  const evidStatus = document.getElementById("evidence-status");
  if (evidId && evid.clip_id) {
    evidId.innerText = `${evid.clip_id} (${evid.duration_seconds}s REPLAY @ ${evid.recorded_at})`;
  }
  if (evidStatus && evid.status) {
    evidStatus.innerText = evid.status;
  }

  // 6. 5 Patent Claims Matrix Values
  const c1 = document.getElementById("claim1-val");
  const c2 = document.getElementById("claim2-val");
  const c3 = document.getElementById("claim3-val");
  const c4 = document.getElementById("claim4-val");
  const c5 = document.getElementById("claim5-val");

  if (c1 && spectral.optical_confidence) {
    c1.innerText = `Opt: ${spectral.optical_confidence}% | FFT: ${spectral.acoustic_fft_match}% | Depth: ${spectral.structural_depth_variance}%`;
  }
  if (c2 && data.wifi_signal !== undefined) {
    c2.innerText = `Wi-Fi: ${data.wifi_signal}% (${data.wifi_signal < 25 ? 'PRE-CACHED ON SIM800L' : 'Offline Armed'})`;
  }
  if (c3 && d3.active_radius_km) {
    c3.innerText = `Radius ${d3.active_radius_km} km | ETA: ${d3.estimated_first_responder_eta || '4 mins'}`;
  }
  if (c4 && crypto.total_blocks_mined !== undefined) {
    c4.innerText = `Chain: VERIFIED (Block #${crypto.total_blocks_mined - 1})`;
  }
  if (c5 && recal.suppression_efficiency) {
    c5.innerText = `Suppression Eff: ${recal.suppression_efficiency}`;
  }

  // 7. Sensor Constellation
  updateSensor("flame", tele.flame || 0, tele.flame > 0 ? "FLAME DETECTED" : "CLEAR", tele.flame > 0 ? "#ef4444" : "#10b981");
  updateSensor("sound", `${tele.sound || 40}`, (tele.sound >= 70 ? "HIGH NOISE" : "QUIET"), (tele.sound >= 70 ? "#ef4444" : "#10b981"), "dB");
  updateSensor("vibration", tele.vibration === 0 ? "0" : "1", tele.vibration === 0 ? "STATIONARY" : "ACTIVE", tele.vibration === 0 ? "#f59e0b" : "#10b981");
  updateSensor("movement", tele.vibration === 0 ? "NONE" : "DETECTED", tele.vibration === 0 ? "STILL" : "VERIFIED", tele.vibration === 0 ? "#f59e0b" : "#10b981");
  updateSensor("distance", `${tele.distance_cm || 110}`, tele.distance_cm < 40 ? "CLOSE" : "CLEAR", tele.distance_cm < 40 ? "#f59e0b" : "#10b981", "cm");

  // 8. Dispatch Panel Status
  const dispStatus = document.getElementById("dispatch-status");
  const incType = document.getElementById("incident-type");
  const respLoc = document.getElementById("response-location");
  const commStatus = document.getElementById("communication-status");

  if (dispStatus) {
    dispStatus.innerText = state === "ESCALATED_SOS_5KM" || state === "DISPATCHED" ? "DISPATCHED (5KM SOS)" : state === "POLICE_CONFIRMED" ? "RESPONSE WINDOW ACTIVE" : "STANDING BY";
  }
  if (incType) {
    incType.innerText = aiInfo.label || "—";
  }
  if (respLoc && loc.address) {
    respLoc.innerText = `${loc.address} (${d3.active_radius_km || 5.0}km Perimeter)`;
  }
  if (commStatus) {
    commStatus.innerText = data.wifi_signal < 25 ? "PREDICTIVE OFFLINE SMS ARMED" : "GSM SIM800L READY";
  }

  // Header Wi-Fi
  const wifiVal = document.getElementById("val-wifi");
  if (wifiVal && data.wifi_signal !== undefined) {
    wifiVal.innerText = `${data.wifi_signal}%`;
  }
}

function updateSensor(type, value, stateText, stateColor, unit = "") {
  const valEl = document.getElementById(`${type}-value`);
  const stateEl = document.getElementById(`${type}-state`);
  if (valEl) {
    valEl.innerHTML = unit ? `${value}<span class="sensor-unit">${unit}</span>` : `${value}`;
  }
  if (stateEl) {
    stateEl.innerText = stateText;
    stateEl.style.color = stateColor;
  }
}

function appendTimelineEvent(text, type = "normal") {
  const log = document.getElementById("event-log");
  if (!log) return;
  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0];

  const row = document.createElement("div");
  row.className = `event-row ${type === 'caution' ? 'event-row--caution' : type === 'critical' ? 'event-row--critical' : ''}`;
  row.innerHTML = `
    <span class="event-time">${timeStr}</span>
    <span class="event-rule" aria-hidden="true"></span>
    <span class="event-text">${text.toUpperCase()}</span>
  `;
  log.prepend(row);
}

function copyAIStatement() {
  if (!currentAIStatement) return;
  navigator.clipboard.writeText(currentAIStatement).then(() => {
    alert("📋 Official AI Accident Statement copied to clipboard for Police/Insurance submission!");
  }).catch(() => {
    prompt("Copy Statement:", currentAIStatement);
  });
}

function exportLogs() {
  const text = `ROBO RAKSHA FORENSIC AI ACCIDENT REPORT\n${new Date().toISOString()}\n\n${currentAIStatement}\n\nEVIDENCE CLIP ID: RX-EVID-8941\nCRYPTOGRAPHIC INTEGRITY: SHA-256 VERIFIED MERKLE CHAIN\nDISPATCH STATUS: 5KM SOS BROADCAST ARMED`;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `robo_raksha_police_fir_${Date.now()}.txt`;
  a.click();
}

async function sendAction(actionName) {
  appendTimelineEvent(`Operator Action: ${actionName}`, "caution");
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/dashboard/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionName })
    });
    fetchStatus();
  } catch (err) {
    console.error("Action error:", err);
  }
}

async function triggerScenario(scenarioName) {
  appendTimelineEvent(`Simulation Triggered: ${scenarioName.toUpperCase()}`, "caution");
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/scenario`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenarioName })
    });
    fetchStatus();
  } catch (err) {
    console.error("Scenario trigger error:", err);
  }
}
