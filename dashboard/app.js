/**
 * Robo Raksha — Dashboard Logic (Person 3)
 * Polling engine, UI state rendering, and action dispatch handler.
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

document.addEventListener("DOMContentLoaded", () => {
  const modeSelect = document.getElementById("mockModeToggle");
  if (modeSelect) {
    modeSelect.addEventListener("change", (e) => {
      mode = e.target.value;
      logEvent(`Switched mode to: ${mode.toUpperCase()}`);
    });
  }

  // Start polling every 1000ms
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
      badge.className = "badge badge-normal";
      badge.innerText = "SERVER CONNECTING...";
    }
  }
}

function renderDashboard(data) {
  // Update Status Badge & State Theme
  const badge = document.getElementById("statusBadge");
  if (!badge) return;
  const state = data.state || "NORMAL";
  badge.className = "badge";

  if (state === "ALERT") {
    badge.classList.add("badge-alert");
    badge.innerText = `EMERGENCY ALERT: ${(data.event || "FIRE").toUpperCase()}`;
  } else if (state === "DISPATCHED") {
    badge.classList.add("badge-dispatched");
    badge.innerText = "DISPATCHING EMERGENCY SERVICES";
  } else {
    badge.classList.add("badge-normal");
    badge.innerText = "SYSTEM NORMAL";
  }

  // Update Severity Score
  const scoreElem = document.getElementById("severityScore");
  if (scoreElem) scoreElem.innerText = (data.severity || 0.0).toFixed(1);

  // Update Countdown Number
  const cdNum = document.getElementById("countdownNumber");
  if (cdNum) {
    if (state === "ALERT" || state === "INVESTIGATING") {
      const secs = data.timer_seconds !== undefined ? data.timer_seconds : 45;
      cdNum.innerText = secs < 10 ? `00:0${secs}` : `00:${secs}`;
    } else if (state === "DISPATCHED") {
      cdNum.innerText = "00:00";
    } else {
      cdNum.innerText = "--";
    }
  }

  // Update Telemetry Bar
  if (data.latest_telemetry) {
    const flameEl = document.getElementById("telemetryFlame");
    const soundEl = document.getElementById("telemetrySound");
    const vibEl = document.getElementById("telemetryVibration");
    const distEl = document.getElementById("telemetryDistance");

    if (flameEl) flameEl.innerText = data.latest_telemetry.flame > 0 ? "🔥 FLAME DETECTED" : "NONE";
    if (soundEl) soundEl.innerText = `${data.latest_telemetry.sound || 0} dB`;
    if (vibEl) vibEl.innerText = data.latest_telemetry.vibration === 0 ? "⚠️ STATIONARY" : "MOVING";
    if (distEl) distEl.innerText = `${data.latest_telemetry.distance_cm || 0} cm`;
  }
}

async function sendAction(actionName) {
  logEvent(`Operator clicked: '${actionName}'`);
  if (mode === "mock") {
    alert(`[MOCK MODE] Action '${actionName}' logged locally to console.`);
    return;
  }

  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/dashboard/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionName })
    });
    const result = await res.json();
    logEvent(`Server response: ${result.new_state} (Timer: ${result.timer_seconds}s)`);
    fetchStatus();
  } catch (err) {
    logEvent(`Failed to post action '${actionName}': ${err}`);
  }
}

function logEvent(msg) {
  const logList = document.getElementById("eventLog");
  if (!logList) return;
  const timeStr = new Date().toLocaleTimeString();
  const li = document.createElement("li");
  li.innerHTML = `<span class="time">[${timeStr}]</span> ${msg}`;
  logList.prepend(li);
}
