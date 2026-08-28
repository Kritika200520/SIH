/**
 * ROBO RAKSHA — Autonomous Emergency Intelligence System (Person 3 Logic)
 * Toggles body class: "normal" | "alert" | "dispatched"
 * Syncs Risk Core, Countdown Ring, Sensor Constellation, Alert Summary, and Dispatch panel.
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
  const rawScore = data.severity !== undefined ? data.severity : (aiInfo.intensity_score || 0);

  // 1. Set Body Class State: "normal" | "alert" | "dispatched"
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
    if (feedEnv) feedEnv.innerText = "DISPATCH ESCALATION ACTIVE";
    if (feedCenter) feedCenter.innerText = "🚨 5KM SOS BROADCAST EXECUTED";
    
    if (lastState !== "DISPATCHED" && lastState !== "ESCALATED_SOS_5KM") {
      playAlertTone();
      appendTimelineEvent("AUTO-DIALED AMBULANCE (108) & BROADCASTED 5KM SOS", "critical");
    }
  } else {
    body.className = "normal";
    if (modeLabel) modeLabel.innerText = "SYSTEM NORMAL";
    if (feedEnv) feedEnv.innerText = "ENVIRONMENT NOMINAL";
    if (feedCenter) feedCenter.innerText = "AWAITING VISUAL FEED";
  }

  lastState = state;

  // 2. Risk Core Readout & Bands
  const displayScore = Math.round(rawScore);
  if (coreScore) coreScore.innerText = displayScore;
  if (coreBand) {
    if (displayScore >= 10) coreBand.innerText = "CRITICAL";
    else if (displayScore >= 7) coreBand.innerText = "HIGH";
    else if (displayScore >= 4) coreBand.innerText = "CAUTION";
    else coreBand.innerText = "SAFE";
  }

  // 3. Countdown Ring
  const cdElem = document.getElementById("countdown");
  const cdCircle = document.getElementById("countdown-circle");
  if (cdElem) {
    const secs = data.timer_seconds !== undefined ? data.timer_seconds : 30;
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

  // 4. Alert Summary Panel
  if (alertTitle) {
    if (state === "NORMAL" || state === "RESOLVED" || state === "CANCELLED") {
      alertTitle.innerText = "NO ACTIVE THREAT";
      if (alertDesc) alertDesc.innerText = "All environmental systems are operating normally. ROBO RAKSHA is monitoring continuously.";
      if (alertSource) alertSource.innerText = "—";
    } else {
      alertTitle.innerText = (aiInfo.label || "HAZARD DETECTED").toUpperCase();
      if (alertDesc) alertDesc.innerText = aiInfo.ai_summary || "Visual and acoustic sensors corroborate high-intensity incident.";
      if (alertSource) alertSource.innerText = tele.flame > 0 ? "Optical Flame Sensor" : "AI Vision + Acoustics";
    }
  }
  if (locData && loc.address) {
    locData.innerText = `${loc.address} · ${loc.lat}°N, ${loc.lng}°E`;
  }

  // 5. Sensor Constellation
  updateSensor("flame", tele.flame || 0, tele.flame > 0 ? "FLAME DETECTED" : "CLEAR", tele.flame > 0 ? "#ef4444" : "#10b981");
  updateSensor("sound", `${tele.sound || 40}`, (tele.sound >= 70 ? "HIGH NOISE" : "QUIET"), (tele.sound >= 70 ? "#ef4444" : "#10b981"), "dB");
  updateSensor("vibration", tele.vibration === 0 ? "0" : "1", tele.vibration === 0 ? "STATIONARY" : "ACTIVE", tele.vibration === 0 ? "#f59e0b" : "#10b981");
  updateSensor("movement", tele.vibration === 0 ? "NONE" : "DETECTED", tele.vibration === 0 ? "STILL" : "ACTIVE", tele.vibration === 0 ? "#f59e0b" : "#10b981");
  updateSensor("distance", `${tele.distance_cm || 110}`, tele.distance_cm < 40 ? "CLOSE" : "CLEAR", tele.distance_cm < 40 ? "#f59e0b" : "#10b981", "cm");

  // 6. Dispatch Panel Status
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
    respLoc.innerText = `${loc.address} (5km Perimeter)`;
  }
  if (commStatus) {
    commStatus.innerText = data.wifi_signal < 25 ? "PREDICTIVE OFFLINE SMS ARMED" : "GSM SIM800L READY";
  }

  // Wi-Fi Header
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

async function sendAction(actionName) {
  appendTimelineEvent(`Operator Action: ${actionName}`, "caution");
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/dashboard/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionName })
    });
    const result = await res.json();
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
