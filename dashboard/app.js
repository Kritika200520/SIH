/**
 * Robo Raksha — Dashboard Logic (Person 3)
 * Polling engine, UI state rendering, and action dispatch handler.
 */

const SERVER_STATUS_URL = "http://localhost:5000/api/dashboard/status";
const SERVER_ACTION_URL = "http://localhost:5000/api/dashboard/action";
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
  const url = mode === "live" ? SERVER_STATUS_URL : MOCK_FILE_URL;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.warn(`Dashboard fetch error from ${url}:`, err);
    document.getElementById("statusBadge").className = "badge badge-normal";
    document.getElementById("statusBadge").innerText = "SERVER OFFLINE";
  }
}

function renderDashboard(data) {
  // Update Status Badge & State Theme
  const badge = document.getElementById("statusBadge");
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
  document.getElementById("severityScore").innerText = (data.severity || 0.0).toFixed(1);

  // Update Countdown Number
  const cdNum = document.getElementById("countdownNumber");
  if (state === "ALERT" || state === "INVESTIGATING") {
    const secs = data.timer_seconds !== undefined ? data.timer_seconds : 45;
    cdNum.innerText = secs < 10 ? `00:0${secs}` : `00:${secs}`;
  } else if (state === "DISPATCHED") {
    cdNum.innerText = "00:00";
  } else {
    cdNum.innerText = "--";
  }

  // Update Telemetry Bar
  if (data.latest_telemetry) {
    document.getElementById("telemetryFlame").innerText = data.latest_telemetry.flame > 0 ? "🔥 FLAME DETECTED" : "NONE";
    document.getElementById("telemetrySound").innerText = `${data.latest_telemetry.sound || 0} dB`;
    document.getElementById("telemetryVibration").innerText = data.latest_telemetry.vibration === 0 ? "⚠️ STATIONARY" : "MOVING";
    document.getElementById("telemetryDistance").innerText = `${data.latest_telemetry.distance_cm || 0} cm`;
  }
}

async function sendAction(actionName) {
  logEvent(`Operator clicked: '${actionName}'`);
  if (mode === "mock") {
    alert(`[MOCK MODE] Action '${actionName}' logged locally to console.`);
    return;
  }

  try {
    const res = await fetch(SERVER_ACTION_URL, {
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
