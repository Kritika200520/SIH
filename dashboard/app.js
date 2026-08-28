/**
 * Robo Raksha — Tactical Dashboard Logic & Audio Alarm (Person 3)
 * Dynamic polling engine, Web Audio warning siren, dynamic menu renderer, and log exporter.
 */

const getBaseUrl = () => {
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "http://localhost:5000";
  }
  return window.location.origin;
};

const MOCK_FILE_URL = "fake_status.json";
let mode = "live"; // "live" or "mock"
let pollInterval = null;
let lastState = "NORMAL";

// Web Audio API Warning Alarm Synthesizer
let audioCtx = null;

function playWarningBeep() {
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
    osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 tone
    osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.3);
  } catch (e) {
    // Ignore audio autoplay restrictions
  }
}

document.addEventListener("DOMContentLoaded", () => {
  pollInterval = setInterval(fetchStatus, 1000);
  fetchStatus();
});

async function fetchStatus() {
  const baseUrl = getBaseUrl();
  const url = mode === "live" ? `${baseUrl}/api/dashboard/status` : MOCK_FILE_URL;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.warn(`Dashboard fetch error from ${url}:`, err);
    const badge = document.getElementById("statusBadge");
    if (badge) {
      badge.className = "status-badge state-normal";
      badge.innerText = "SERVER CONNECTING...";
    }
  }
}

function renderDashboard(data) {
  const badge = document.getElementById("statusBadge");
  const state = data.state || "NORMAL";
  const hudStatus = document.getElementById("hudStatusText");

  if (badge) {
    badge.className = "status-badge";
    if (state === "ALERT") {
      badge.classList.add("state-alert");
      badge.innerText = `EMERGENCY ALERT: ${(data.event || "FIRE").toUpperCase()}`;
      if (hudStatus) hudStatus.innerText = `⚠️ HAZARD TARGET DETECTED [${(data.event || "FIRE").toUpperCase()}]`;
      
      // Play alert tone on transition or periodic beep
      if (lastState !== "ALERT") {
        playWarningBeep();
        logEvent(`🚨 EMERGENCY ALERT TRIGGERED: Event '${data.event}' (Severity: ${data.severity})`);
      }
    } else if (state === "DISPATCHED") {
      badge.classList.add("state-dispatched");
      badge.innerText = "DISPATCHING EMERGENCY SERVICES";
      if (hudStatus) hudStatus.innerText = "🚨 DISPATCH COMMAND EXECUTED";
    } else if (state === "INVESTIGATING") {
      badge.classList.add("state-alert");
      badge.innerText = "OPERATOR INVESTIGATING (+30s EXTENDED)";
      if (hudStatus) hudStatus.innerText = "🔍 INVESTIGATION IN PROGRESS";
    } else {
      badge.classList.add("state-normal");
      badge.innerText = "SYSTEM OPERATIONAL";
      if (hudStatus) hudStatus.innerText = "TARGET: CLEAR";
    }
  }

  lastState = state;

  // Wi-Fi Signal
  const wifiVal = document.getElementById("wifiVal");
  if (wifiVal && data.wifi_signal !== undefined) {
    wifiVal.innerText = `${data.wifi_signal}%`;
    const wifiInd = document.getElementById("wifiIndicator");
    if (wifiInd) {
      wifiInd.style.color = data.wifi_signal < 30 ? "#ff3b30" : "#34c759";
    }
  }

  // Severity Score Number
  const scoreElem = document.getElementById("severityNum");
  if (scoreElem) {
    scoreElem.innerText = (data.severity || 0.0).toFixed(1);
    const scoreCircle = scoreElem.parentElement;
    if (scoreCircle) {
      scoreCircle.style.borderColor = data.severity >= 7 ? "#ff3b30" : data.severity > 0 ? "#ff9500" : "#34c759";
    }
  }

  // Countdown Clock
  const cdClock = document.getElementById("countdownClock");
  if (cdClock) {
    if (state === "ALERT" || state === "INVESTIGATING") {
      const secs = data.timer_seconds !== undefined ? data.timer_seconds : 45;
      cdClock.innerText = secs < 10 ? `00:0${secs}` : `00:${secs}`;
    } else if (state === "DISPATCHED") {
      cdClock.innerText = "00:00";
    } else {
      cdClock.innerText = "--:--";
    }
  }

  // Telemetry Cards & dB Gauge
  if (data.latest_telemetry) {
    const flameVal = document.getElementById("valFlame");
    const soundVal = document.getElementById("valSound");
    const vibVal = document.getElementById("valVibration");
    const distVal = document.getElementById("valDistance");
    const dBFill = document.getElementById("dBFill");

    if (flameVal) {
      flameVal.innerText = data.latest_telemetry.flame > 0 ? "🔥 FLAME!" : "SAFE";
      flameVal.style.color = data.latest_telemetry.flame > 0 ? "#ff3b30" : "#f0f6fc";
    }
    if (soundVal) {
      const soundDb = data.latest_telemetry.sound || 0;
      soundVal.innerText = `${soundDb} dB`;
      if (dBFill) {
        const pct = Math.min(100, Math.max(0, (soundDb / 120) * 100));
        dBFill.style.width = `${pct}%`;
        dBFill.style.background = soundDb >= 70 ? "#ff3b30" : "#34c759";
      }
    }
    if (vibVal) {
      vibVal.innerText = data.latest_telemetry.vibration === 0 ? "⚠️ STATIONARY" : "MOVING";
      vibVal.style.color = data.latest_telemetry.vibration === 0 ? "#ff9500" : "#f0f6fc";
    }
    if (distVal) {
      distVal.innerText = `${data.latest_telemetry.distance_cm || 0} cm`;
    }
  }

  // Dynamic Situation-Specific Menu Buttons
  renderActionButtons(data.options || []);
}

function renderActionButtons(options) {
  const grid = document.getElementById("actionButtonsGrid");
  const menuTag = document.getElementById("menuTag");
  if (!grid) return;

  if (!options || options.length === 0) {
    grid.innerHTML = `<button class="btn btn-secondary" onclick="sendAction('Reset')">System Standard (No Active Alert)</button>`;
    if (menuTag) menuTag.innerText = "Standard Menu";
    return;
  }

  if (menuTag) menuTag.innerText = "Patent Situation Menu";

  let html = "";
  options.forEach(opt => {
    let btnClass = "btn-secondary";
    if (opt.includes("Dispatch") || opt.includes("Suppressor")) {
      btnClass = "btn-primary";
    } else if (opt.includes("Investigate") || opt.includes("Beacon") || opt.includes("Warning")) {
      btnClass = "btn-warning";
    }
    html += `<button class="btn ${btnClass}" onclick="sendAction('${opt}')">${opt}</button>`;
  });

  grid.innerHTML = html;
}

async function sendAction(actionName) {
  logEvent(`Operator clicked: '${actionName}'`);
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/dashboard/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionName })
    });
    const result = await res.json();
    logEvent(`Server action response: ${result.new_state} (Timer: ${result.timer_seconds}s)`);
    fetchStatus();
  } catch (err) {
    logEvent(`Failed to send action '${actionName}': ${err}`);
  }
}

async function triggerScenario(scenarioName) {
  logEvent(`Triggering Simulation Scenario: '${scenarioName.toUpperCase()}'`);
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/scenario`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenarioName })
    });
    const result = await res.json();
    logEvent(`Scenario applied: state=${result.state}, severity=${result.severity}`);
    fetchStatus();
  } catch (err) {
    logEvent(`Scenario trigger error: ${err}`);
  }
}

function logEvent(msg) {
  const logList = document.getElementById("logList");
  if (!logList) return;
  const timeStr = new Date().toLocaleTimeString();
  const li = document.createElement("li");
  li.innerHTML = `<span class="log-time">[${timeStr}]</span> ${msg}`;
  logList.prepend(li);
}

function exportLogs() {
  const logList = document.getElementById("logList");
  if (!logList) return;
  const text = logList.innerText;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `robo_raksha_audit_log_${Date.now()}.txt`;
  a.click();
}
