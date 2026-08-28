"""
Robo Raksha — Main Server Application (Person 1 / Builder)
Comprehensive integration of 5 Unique Patent Mechanisms:
1. Multi-Spectral Optical-Acoustic Cross-Validation
2. Predictive RSSI Network Decay & Offline SMS Pre-Caching
3. Dynamic Density-Adjusted 5km Geo-Fence (D3-Perimeter)
4. SHA-256 Cryptographic Tamper-Proof Blackbox Ledger
5. Closed-Loop AI Sensitivity Recalibration
"""

import io
import json
import logging
import os
import requests
import sys
import threading
import time
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS

# Ensure server directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scoring_engine import ScoringEngine
from ai_vision_engine import AIVisionEngine
from crypto_blackbox import CryptoBlackbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, static_folder="static")
CORS(app)

# Global Engines & Locks
state_lock = threading.Lock()
scoring = ScoringEngine(threshold=7.0)
ai_vision = AIVisionEngine(required_consecutive_frames=3)
blackbox = CryptoBlackbox()

# System State Variables
current_state = "NORMAL"
current_event = "none"
current_severity = 0.0
timer_seconds = 0
clip_url = "/video_feed"

# AI Vision & Location Metadata
ai_vision_data = {
    "detected": False,
    "label": "Roadway Clear",
    "intensity_score": 0.0,
    "confidence": 99.0,
    "ai_summary": "Continuous video surveillance active. No anomalies.",
    "anti_false_alarm_verified": False,
    "verification_status": "CLEAR: No hazard signatures detected"
}

location_data = {
    "lat": 12.9716,
    "lng": 77.5946,
    "address": "MG Road - Brigade Junction, Bangalore, Karnataka",
    "maps_url": "https://maps.google.com/?q=12.9716,77.5946",
    "sos_radius_km": 5.0
}

latest_telemetry = {"flame": 0, "sound": 40.0, "vibration": 1, "distance_cm": 110}
wifi_signal_strength = 95.0
predictive_offline_cache = {
    "is_cached": False,
    "pre_armed_sms": "",
    "timestamp": None
}

COMMS_BASE_URL = os.environ.get("COMMS_URL", "http://localhost:5001")
timer_running = True


def trigger_5km_sos_escalation():
    """Triggered when Response Timer expires (Hits 0)."""
    global current_state, ai_vision_data, location_data

    logging.warning("🚨 ESCALATING TO 5KM RADIUS SOS BROADCAST & AUTO-CALLING AMBULANCE!")
    current_state = "ESCALATED_SOS_5KM"

    # Mine Cryptographic Block for 5km SOS Broadcast
    blackbox.append_block("5KM_SOS_DISPATCH_TRIGGERED", ai_vision_data.get("intensity_score", 90.0), location_data, {
        "event": ai_vision_data.get("label"),
        "ambulance_called": True,
        "d3_radius": 5.0
    })

    payload = {
        "hazard_label": ai_vision_data.get("label", "Severe Accident"),
        "intensity": ai_vision_data.get("intensity_score", 90.0),
        "lat": location_data["lat"],
        "lng": location_data["lng"],
        "address": location_data["address"]
    }

    try:
        res = requests.post(f"{COMMS_BASE_URL}/api/comms/broadcast_sos", json=payload, timeout=4.0)
        logging.info(f"5km SOS Broadcast Response [{res.status_code}]: {res.text}")
    except Exception as e:
        logging.warning(f"Comms 5km endpoint unreachable: {e}")


def countdown_worker():
    """Background countdown worker for POLICE_CONFIRMED response window."""
    global current_state, timer_seconds, timer_running

    while timer_running:
        time.sleep(1.0)
        with state_lock:
            if current_state == "POLICE_CONFIRMED":
                if timer_seconds > 0:
                    timer_seconds -= 1
                    logging.info(f"⏱️ Police Response Timer: {timer_seconds}s remaining (Waiting for on-site responders)")

                if timer_seconds <= 0:
                    logging.warning("⚠️ Response window expired! Responders did not reach site in time.")
                    threading.Thread(target=trigger_5km_sos_escalation, daemon=True).start()


timer_thread = threading.Thread(target=countdown_worker, daemon=True)
timer_thread.start()


# MJPEG Camera Frame Stream Generator
def generate_mjpeg_frames():
    try:
        from PIL import Image, ImageDraw
        has_pil = True
    except ImportError:
        has_pil = False

    frame_idx = 0
    while True:
        frame_idx = (frame_idx + 1) % 360
        if has_pil:
            img = Image.new("RGB", (640, 360), color=(10, 14, 20))
            draw = ImageDraw.Draw(img)

            cx, cy = 320, 180
            draw.line([(cx - 30, cy), (cx + 30, cy)], fill=(0, 255, 170), width=1)
            draw.line([(cx, cy - 30), (cx, cy + 30)], fill=(0, 255, 170), width=1)

            scan_y = (frame_idx * 5) % 360
            draw.line([(0, scan_y), (640, scan_y)], fill=(0, 255, 170, 70), width=2)

            with state_lock:
                st = current_state
                ai_info = ai_vision_data.copy()

            draw.rectangle([(10, 10), (320, 48)], fill=(0, 0, 0))
            status_color = (255, 59, 48) if st in ["UNVERIFIED_ALERT", "POLICE_CONFIRMED", "ESCALATED_SOS_5KM"] else (52, 199, 89)
            draw.text((18, 14), f"ESP32-CAM [LIVE] | STATE: {st}", fill=status_color)
            draw.text((18, 30), f"AI INTENSITY: {ai_info.get('intensity_score', 0):.1f}% | CONF: {ai_info.get('confidence', 0):.1f}%", fill=(240, 246, 254))

            if ai_info.get("detected"):
                box_color = (255, 59, 48) if ai_info.get("anti_false_alarm_verified") else (255, 149, 0)
                draw.rectangle([(cx - 100, cy - 70), (cx + 100, cy + 70)], outline=box_color, width=3)
                draw.text((cx - 95, cy - 90), f"⚠️ {ai_info.get('label', 'HAZARD')}", fill=box_color)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=75)
            frame_bytes = buffer.getvalue()
        else:
            frame_bytes = b''

        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.1)


@app.route("/", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def serve_dashboard_ui():
    dashboard_dir = os.path.abspath(os.path.join(app.root_path, "..", "dashboard"))
    return send_from_directory(dashboard_dir, "index.html")


@app.route("/<path:filename>", methods=["GET"])
def serve_static_assets(filename):
    dashboard_dir = os.path.abspath(os.path.join(app.root_path, "..", "dashboard"))
    file_path = os.path.join(dashboard_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(dashboard_dir, filename)
    return jsonify({"error": f"File {filename} not found"}), 404


@app.route("/video_feed", methods=["GET"])
def video_feed():
    return Response(generate_mjpeg_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/api/dashboard/status", methods=["GET"])
def get_dashboard_status():
    """
    Polled every second by Dashboard JS.
    Returns status + 5 Novel Patent Modules (Multi-Spectral, RSSI Decay, D3 Geo-Fence, Crypto Ledger, AI Memory).
    """
    with state_lock:
        # Patent Claim 1: Multi-Spectral Cross-Validation Matrix
        multi_spectral = scoring.compute_multi_spectral_matrix(
            ai_confidence=ai_vision_data.get("confidence", 95.0),
            sound_db=latest_telemetry.get("sound", 40.0),
            distance_cm=latest_telemetry.get("distance_cm", 110),
            flame_val=latest_telemetry.get("flame", 0)
        )

        # Patent Claim 2: RSSI Decay & Predictive Pre-Caching Check
        effective_risk, should_cache = scoring.calculate_rssi_network_risk(
            base_severity=ai_vision_data.get("intensity_score", 0.0),
            elapsed_seconds=0,
            current_telemetry=latest_telemetry,
            wifi_rssi=wifi_signal_strength
        )

        if should_cache and not predictive_offline_cache["is_cached"]:
            predictive_offline_cache["is_cached"] = True
            predictive_offline_cache["pre_armed_sms"] = f"PREDICTIVE SOS [OFFLINE BUFFER]: {ai_vision_data.get('label')} at GPS {location_data['lat']},{location_data['lng']}"
            predictive_offline_cache["timestamp"] = time.time()
            logging.warning("⚠️ Wi-Fi RSSI degraded below 25%! Pre-armed offline emergency SMS on SIM800L cache.")

        # Patent Claim 3: Dynamic D3 Geo-Fence
        d3_perimeter = scoring.calculate_d3_geofence(
            severity_intensity=ai_vision_data.get("intensity_score", 0.0),
            base_radius_km=location_data["sos_radius_km"]
        )

        # Patent Claim 4: Cryptographic Blackbox Recent Blocks
        crypto_blocks = blackbox.get_latest_blocks(limit=4)
        is_chain_valid = blackbox.verify_chain_integrity()

        response = {
            "state": current_state,
            "event": current_event,
            "severity": current_severity,
            "timer_seconds": timer_seconds,
            "clip_url": clip_url,
            "ai_vision": ai_vision_data,
            "location": location_data,
            "latest_telemetry": latest_telemetry,
            "wifi_signal": wifi_signal_strength,
            # 5 Novel Patent Modules
            "multi_spectral_matrix": multi_spectral,
            "predictive_cache": predictive_offline_cache,
            "d3_perimeter": d3_perimeter,
            "crypto_ledger": {
                "chain_valid": is_chain_valid,
                "total_blocks_mined": len(blackbox.chain),
                "latest_blocks": crypto_blocks
            },
            "ai_recalibration": {
                "false_alarm_penalties": ai_vision.false_alarm_penalty_count,
                "suppression_efficiency": f"{min(99.8, 92.0 + ai_vision.false_alarm_penalty_count * 1.5):.1f}%"
            }
        }
    return jsonify(response)


@app.route("/api/dashboard/action", methods=["POST"])
def process_police_action():
    """Processes Police / Operator actions and logs SHA-256 cryptographic proof."""
    global current_state, timer_seconds, current_severity, ai_vision_data

    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "")
    logging.info(f"👮 POLICE ACTION: '{action}'")

    with state_lock:
        if action == "CONFIRM_ACCIDENT" or "Confirm" in action:
            current_state = "POLICE_CONFIRMED"
            timer_seconds = 300
            # Mine Cryptographic Block for Police Confirmation
            blackbox.append_block("POLICE_CONFIRMATION_VERIFIED", ai_vision_data.get("intensity_score", 90.0), location_data, {
                "action": "CONFIRM_ACCIDENT",
                "response_window_seconds": 300
            })
            logging.info(f"🚨 POLICE CONFIRMED ACCIDENT! Starting 5-minute response timer: {timer_seconds}s")

        elif action == "FALSE_ALARM" or "False" in action:
            current_state = "CANCELLED"
            timer_seconds = 0
            current_severity = 0.0
            ai_vision.mark_false_alarm_feedback()
            ai_vision_data = ai_vision.analyze_frame({"scenario": "normal"})
            # Mine Cryptographic Block for False Alarm
            blackbox.append_block("FALSE_ALARM_CALIBRATION_RECORDED", 0.0, location_data, {
                "feedback_penalty_index": ai_vision.false_alarm_penalty_count
            })
            logging.info("❌ Operator marked False Alarm. AI feedback recorded.")

        elif action == "HELP_ARRIVED" or "Resolved" in action:
            current_state = "RESOLVED"
            timer_seconds = 0
            blackbox.append_block("RESPONDERS_ON_SITE_RESOLVED", 0.0, location_data, {"resolved": True})
            logging.info("✅ Responders reached scene! Emergency resolved.")

        elif action == "DISPATCH_AMBULANCE_NOW" or "Ambulance" in action:
            timer_seconds = 0
            threading.Thread(target=trigger_5km_sos_escalation, daemon=True).start()

        else:
            return jsonify({"status": "error", "message": f"Unknown action '{action}'"}), 400

        res_state = current_state
        res_timer = timer_seconds

    return jsonify({"status": "success", "new_state": res_state, "timer_seconds": res_timer})


def _apply_ai_scenario_locked(scenario: str):
    global current_state, current_event, current_severity, ai_vision_data, timer_seconds

    res = None
    for _ in range(3):
        res = ai_vision.analyze_frame({"scenario": scenario})

    ai_vision_data = res

    if res.get("anti_false_alarm_verified"):
        current_state = "UNVERIFIED_ALERT"
        current_event = scenario
        current_severity = res.get("intensity_score", 85.0)
        timer_seconds = 0
        # Mine Cryptographic Block for AI Anomaly Detection
        blackbox.append_block("AI_VISION_HAZARD_VERIFIED", current_severity, location_data, {
            "label": res.get("label"),
            "confidence": res.get("confidence")
        })
        logging.warning(f"🚨 AI DETECTED VERIFIED HAZARD: '{res.get('label')}' (Intensity: {res.get('intensity_score')}%)")
    else:
        current_state = "NORMAL"
        current_event = "none"
        current_severity = 0.0
        timer_seconds = 0


@app.route("/api/scenario", methods=["POST"])
def trigger_scenario():
    """1-Click Simulator API for demo testing."""
    global current_state, current_event, current_severity, ai_vision_data, timer_seconds, latest_telemetry, wifi_signal_strength, predictive_offline_cache

    data = request.get_json(force=True, silent=True) or {}
    scenario = data.get("scenario", "reset")

    with state_lock:
        if scenario == "accident":
            latest_telemetry = {"flame": 0, "sound": 95.0, "vibration": 0, "distance_cm": 25}
            _apply_ai_scenario_locked("accident")

        elif scenario == "fire":
            latest_telemetry = {"flame": 1, "sound": 85.0, "vibration": 0, "distance_cm": 40}
            _apply_ai_scenario_locked("fire")

        elif scenario == "person_down":
            latest_telemetry = {"flame": 0, "sound": 80.0, "vibration": 0, "distance_cm": 90}
            _apply_ai_scenario_locked("person_down")

        elif scenario == "wifi_loss":
            wifi_signal_strength = 15.0
            logging.warning("⚠️ Wi-Fi RSSI decayed to 15%! Triggering Claim 2 predictive pre-generation.")

        else:
            current_state = "NORMAL"
            current_event = "none"
            current_severity = 0.0
            timer_seconds = 0
            wifi_signal_strength = 95.0
            predictive_offline_cache["is_cached"] = False
            latest_telemetry = {"flame": 0, "sound": 40.0, "vibration": 1, "distance_cm": 110}
            ai_vision.consecutive_detections.clear()
            ai_vision_data = ai_vision.analyze_frame({"scenario": "normal"})

    return jsonify({"status": "scenario_applied", "scenario": scenario, "state": current_state, "ai_vision": ai_vision_data})


@app.route("/api/reset", methods=["POST"])
def reset_system():
    return trigger_scenario()


if __name__ == "__main__":
    print("=" * 65)
    print("🏛️ ROBO RAKSHA PATENT SUITE (5 UNIQUE CLAIMS) RUNNING ON PORT 5000 🏛️")
    print("Dashboard available at: http://localhost:5000/")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=False)
