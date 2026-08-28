/**
 * Robo Raksha — AI Emergency Vision & 5 Patent Claims Dashboard Logic
 * Handles real-time polling, Web Audio sirens, Cryptographic block streaming,
 * Multi-Spectral Matrix updates, D3 Geo-Fence stats, and Police confirmation timers.
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

function playWarningAlarm() {
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
  } catch (e) {
    // Autoplay restrictions
  }
}

document.addEventListener("DOMContentLoaded", () => {
  pollInterval = setInterval(fetchStatus, 1000);
  fetchStatus();
});

async function fetchStatus() {
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/dashboard/status`);
    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.warn("Dashboard fetch error:", err);
    const badge = document.getElementById("statusBadge");
    if (badge) {
      badge.className = "status-badge state-normal";
      badge.innerText = "SERVER CONNECTING...";
    }
  }
}

function renderDashboard(data) {
  const state = data.state || "NORMAL";
  const badge = document.getElementById("statusBadge");
  const hudLabel = document.getElementById("hudHazardLabel");
  const aiInfo = data.ai_vision || {};
  const spectral = data.multi_spectral_matrix || {};
  const d3 = data.d3_perimeter || {};
  const crypto = data.crypto_ledger || {};

  // Status Badge & Alarm
  if (badge) {
    badge.className = "status-badge";
    if (state === "UNVERIFIED_ALERT") {
      badge.classList.add("state-alert");
      badge.innerText = `🚨 AI DETECTED: ${(aiInfo.label || "HAZARD").toUpperCase()} (AWAITING POLICE CONFIRMATION)`;
      if (lastState !== "UNVERIFIED_ALERT") {
        playWarningAlarm();
        logEvent(`🚨 AI DETECTED HAZARD: ${aiInfo.label} (Intensity: ${aiInfo.intensity_score}%). Awaiting Police.`);
      }
    } else if (state === "POLICE_CONFIRMED") {
      badge.classList.add("state-alert");
      badge.innerText = "🚨 POLICE CONFIRMED: RESPONSE WINDOW COUNTDOWN ACTIVE";
      if (lastState !== "POLICE_CONFIRMED") {
        logEvent(`👮 POLICE CONFIRMED EMERGENCY. Response countdown window started.`);
      }
    } else if (state === "ESCALATED_SOS_5KM") {
      badge.classList.add("state-dispatched");
      badge.innerText = "🚨 ESCALATED: AMBULANCE CALLED & 5KM SOS BROADCASTED";
      if (lastState !== "ESCALATED_SOS_5KM") {
        playWarningAlarm();
        logEvent(`🚨 RESPONSE WINDOW EXPIRED! Auto-called Ambulance & Broadcasted 5km SOS.`);
      }
    } else if (state === "RESOLVED") {
      badge.classList.add("state-normal");
      badge.innerText = "✅ EMERGENCY RESOLVED (HELP ARRIVED)";
    } else if (state === "CANCELLED") {
      badge.classList.add("state-normal");
      badge.innerText = "❌ ALERT CANCELLED (MARKED FALSE ALARM)";
    } else {
      badge.classList.add("state-normal");
      badge.innerText = "AI SURVEILLANCE ACTIVE (ROADWAY CLEAR)";
    }
  }

  lastState = state;

  // Video HUD
  if (hudLabel) {
    hudLabel.innerText = aiInfo.detected ? `⚠️ DETECTED: ${aiInfo.label.toUpperCase()}` : "SCENE: ROADWAY CLEAR";
  }
  const confText = document.getElementById("aiConfidenceText");
  if (confText) {
    confText.innerText = `CONFIDENCE: ${(aiInfo.confidence || 99.0).toFixed(1)}%`;
  }

  // Anti-False-Alarm Badge
  const antiFalse = document.getElementById("antiFalseBadge");
  if (antiFalse) {
    if (aiInfo.anti_false_alarm_verified) {
      antiFalse.innerText = "✅ Anti-False-Alarm: VERIFIED (3/3 Frames)";
      antiFalse.style.borderColor = "#34c759";
      antiFalse.style.color = "#34c759";
    } else if (aiInfo.detected) {
      antiFalse.innerText = "⏳ Anti-False-Alarm: VALIDATING...";
      antiFalse.style.borderColor = "#ff9500";
      antiFalse.style.color = "#ff9500";
    } else {
      antiFalse.innerText = "🛡️ Anti-False-Alarm: CLEAR";
      antiFalse.style.borderColor = "#30363d";
      antiFalse.style.color = "#8b949e";
    }
  }

  // Intensity Gauge
  const intensityNum = document.getElementById("intensityNum");
  const intensityFill = document.getElementById("intensityFill");
  const score = aiInfo.intensity_score || 0;
  if (intensityNum) intensityNum.innerText = `${score.toFixed(1)}%`;
  if (intensityFill) intensityFill.style.width = `${Math.min(100, score)}%`;

  // Patent Claim 1: Multi-Spectral Matrix
  const specOpt = document.getElementById("specOptical");
  const specAc = document.getElementById("specAcoustic");
  const specDep = document.getElementById("specDepth");
  if (specOpt) specOpt.innerText = `${spectral.optical_confidence || 95}%`;
  if (specAc) specAc.innerText = `${spectral.acoustic_fft_match || 40}%`;
  if (specDep) specDep.innerText = `${spectral.structural_depth_variance || 27}%`;

  // Patent Claim 3: D3 Geo-Fence
  const d3Rad = document.getElementById("d3Radius");
  const d3Resp = document.getElementById("d3Responders");
  const d3Eta = document.getElementById("d3Eta");
  if (d3Rad) d3Rad.innerText = `${d3.active_radius_km || 5.0} km`;
  if (d3Resp) d3Resp.innerText = `${d3.responders_in_range || 14} Units`;
  if (d3Eta) d3Eta.innerText = d3.estimated_first_responder_eta || "4 mins";

  // Patent Claim 4: Cryptographic Blackbox Block Stream
  const blocksStream = document.getElementById("blocksStream");
  if (blocksStream && crypto.latest_blocks) {
    let html = "";
    crypto.latest_blocks.forEach(blk => {
      const shortHash = blk.hash ? `${blk.hash.substring(0, 16)}...` : "00000000";
      html += `<li><span class="block-idx">[BLK #${blk.index}]</span> ${blk.event_type} | <span class="block-hash">${shortHash}</span></li>`;
    });
    blocksStream.innerHTML = html;
  }

  // Police Panel Buttons State
  const btnConfirm = document.getElementById("btnConfirmAccident");
  const resolveRow = document.getElementById("resolveRow");
  if (btnConfirm) {
    if (state === "POLICE_CONFIRMED") {
      btnConfirm.disabled = true;
      btnConfirm.innerText = "⏳ ACCIDENT CONFIRMED (RESPONSE WINDOW RUNNING)";
      if (resolveRow) resolveRow.style.display = "block";
    } else {
      btnConfirm.disabled = false;
      btnConfirm.innerText = "🚨 CONFIRM ACCIDENT / EMERGENCY";
      if (resolveRow) resolveRow.style.display = "none";
    }
  }

  // 5-Minute Countdown Clock
  const cdClock = document.getElementById("countdownClock");
  if (cdClock) {
    if (state === "POLICE_CONFIRMED") {
      const secs = data.timer_seconds !== undefined ? data.timer_seconds : 300;
      const mins = Math.floor(secs / 60);
      const remSecs = secs % 60;
      const mStr = mins < 10 ? `0${mins}` : `${mins}`;
      const sStr = remSecs < 10 ? `0${remSecs}` : `${remSecs}`;
      cdClock.innerText = `${mStr}:${sStr}`;
    } else if (state === "ESCALATED_SOS_5KM") {
      cdClock.innerText = "00:00 [SOS EXECUTED]";
    } else {
      cdClock.innerText = "--:--";
    }
  }

  // 5km SOS Radar Visualizer Badge
  const sosBadge = document.getElementById("sosBadge");
  const sosText = document.getElementById("sosSummaryText");
  if (sosBadge) {
    if (state === "ESCALATED_SOS_5KM") {
      sosBadge.innerText = "🚨 5KM BROADCAST SENT";
      sosBadge.style.background = "#ff3b30";
      sosBadge.style.color = "#fff";
      if (sosText) sosText.innerText = "Ambulance called via AI Voice. SOS SMS dispatched to all responders in 5km perimeter.";
    } else if (state === "POLICE_CONFIRMED") {
      sosBadge.innerText = "⏳ 5KM BROADCAST PENDING";
      sosBadge.style.background = "#ff9500";
      sosBadge.style.color = "#000";
      if (sosText) sosText.innerText = "Armed: If responders do not arrive before timer reaches 00:00, 5km broadcast will trigger.";
    } else {
      sosBadge.innerText = "STANDBY";
      sosBadge.style.background = "#21262d";
      sosBadge.style.color = "#8b949e";
      if (sosText) sosText.innerText = "5km Perimeter Standby: 3 registered medical responders & emergency ambulance (108) configured.";
    }
  }
}

async function sendPoliceAction(actionName) {
  logEvent(`Police / Operator action: '${actionName}'`);
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/dashboard/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionName })
    });
    const result = await res.json();
    logEvent(`Action executed: ${result.new_state} (Timer: ${result.timer_seconds}s)`);
    fetchStatus();
  } catch (err) {
    logEvent(`Failed to execute action: ${err}`);
  }
}

async function triggerScenario(scenarioName) {
  logEvent(`Applying Demo Scenario: '${scenarioName.toUpperCase()}'`);
  const baseUrl = getBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/scenario`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenarioName })
    });
    const result = await res.json();
    logEvent(`AI Scenario set: ${result.scenario} -> State: ${result.state}`);
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
  a.download = `robo_raksha_crypto_ledger_${Date.now()}.txt`;
  a.click();
}
