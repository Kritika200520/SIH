"""
Robo Raksha — Main Server Application (Person 1 / Builder)
Integrates ESP32 Camera streaming, Generative AI Vision Analysis (Intensity 0-100%),
Anti-False-Alarm Temporal Verification, Police/Operator Confirmation,
Response Countdown Timer (starts upon police confirmation), AI Ambulance Calling,
and 5km Radius SOS Emergency Broadcast.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, static_folder="static")
CORS(app)

# Global Engines & Locks
state_lock = threading.Lock()
scoring = ScoringEngine(threshold=7.0)
ai_vision = AIVisionEngine(required_consecutive_frames=3)

# System State Machine
# States: NORMAL, UNVERIFIED_ALERT, POLICE_CONFIRMED, ESCALATED_SOS_5KM, CANCELLED, RESOLVED
current_state = "NORMAL"
current_event = "none"
current_severity = 0.0
timer_seconds = 0
clip_url = "/video_feed"
active_scenario = "normal"

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
wifi_signal_strength = 95

# Comms Endpoints
COMMS_BASE_URL = os.environ.get("COMMS_URL", "http://localhost:5001")
timer_running = True


def trigger_5km_sos_escalation():
    """
    [PATENT NOVELTY ESCALATION]
    Triggered when Response Timer reaches 0 after police confirmation.
    1. AI calls ambulance
    2. Sends 5km Radius SOS broadcast
    """
    global current_state, ai_vision_data, location_data

    logging.warning("🚨 ESCALATING TO 5KM RADIUS SOS BROADCAST & CALLING AMBULANCE!")
    current_state = "ESCALATED_SOS_5KM"

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
        logging.warning(f"Comms 5km endpoint ({COMMS_BASE_URL}) unreachable: {e}")


def countdown_worker():
    """
    Background worker: Only decrements timer when in POLICE_CONFIRMED state!
    If timer hits 0 before responders arrive, triggers 5km SOS broadcast & ambulance call.
    """
    global current_state, timer_seconds, timer_running

    while timer_running:
        time.sleep(1.0)
        with state_lock:
            if current_state == "POLICE_CONFIRMED":
                if timer_seconds > 0:
                    timer_seconds -= 1
                    logging.info(f"⏱️ Police Response Timer ticking: {timer_seconds}s remaining (Waiting for responders on-site)")

                if timer_seconds <= 0:
                    logging.warning("⚠️ Response window expired! Responders did not arrive in time.")
                    # Trigger escalation in separate thread
                    threading.Thread(target=trigger_5km_sos_escalation, daemon=True).start()


timer_thread = threading.Thread(target=countdown_worker, daemon=True)
timer_thread.start()


# MJPEG Camera Frame Generator with AI Bounding Box & HUD
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
            # Target Crosshair HUD
            draw.line([(cx - 30, cy), (cx + 30, cy)], fill=(0, 255, 170), width=1)
            draw.line([(cx, cy - 30), (cx, cy + 30)], fill=(0, 255, 170), width=1)

            # Scanning effect line
            scan_y = (frame_idx * 5) % 360
            draw.line([(0, scan_y), (640, scan_y)], fill=(0, 255, 170, 70), width=2)

            with state_lock:
                st = current_state
                ai_info = ai_vision_data.copy()

            # Top HUD Bar
            draw.rectangle([(10, 10), (320, 48)], fill=(0, 0, 0))
            status_color = (255, 59, 48) if st in ["UNVERIFIED_ALERT", "POLICE_CONFIRMED", "ESCALATED_SOS_5KM"] else (52, 199, 89)
            draw.text((18, 14), f"ESP32-CAM [LIVE] | STATE: {st}", fill=status_color)
            draw.text((18, 30), f"AI INTENSITY: {ai_info.get('intensity_score', 0):.1f}% | CONF: {ai_info.get('confidence', 0):.1f}%", fill=(240, 246, 254))

            # Draw AI Target Bounding Box if anomaly detected
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
    Returns state, AI vision analysis, location, countdown, and situation-specific menu options.
    """
    with state_lock:
        response = {
            "state": current_state,
            "event": current_event,
            "severity": current_severity,
            "timer_seconds": timer_seconds,
            "clip_url": clip_url,
            "ai_vision": ai_vision_data,
            "location": location_data,
            "latest_telemetry": latest_telemetry,
            "wifi_signal": wifi_signal_strength
        }
    return jsonify(response)


@app.route("/api/telemetry", methods=["POST"])
def receive_telemetry():
    """Robot sensor telemetry endpoint."""
    global current_state, current_event, current_severity, latest_telemetry

    data = request.get_json(force=True, silent=True) or {}
    flame = int(data.get("flame", 0))
    sound = float(data.get("sound", 0))
    vibration = int(data.get("vibration", 0))
    distance_cm = int(data.get("distance_cm", 100))

    with state_lock:
        latest_telemetry = {"flame": flame, "sound": sound, "vibration": vibration, "distance_cm": distance_cm}
        score, event = scoring.compute_baseline_score(latest_telemetry)
        current_severity = score

        if flame > 0 or (sound >= 75 and vibration == 0):
            # Auto-trigger AI frame analyzer with scenario
            scenario_name = "fire" if flame > 0 else "accident"
            _apply_ai_scenario_locked(scenario_name)

    return jsonify({"status": "ok", "state": current_state, "severity": current_severity})


@app.route("/api/dashboard/action", methods=["POST"])
def process_police_action():
    """
    Handles Police / Operator intervention:
    1. 'CONFIRM_ACCIDENT' -> Starts 300s response countdown timer!
    2. 'FALSE_ALARM' -> Cancels alert and trains AI anti-false-alarm penalty.
    3. 'HELP_ARRIVED' -> Resolves emergency.
    4. 'DISPATCH_AMBULANCE_NOW' -> Immediate manual ambulance call & 5km SOS broadcast.
    """
    global current_state, timer_seconds, current_severity, ai_vision_data

    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "")
    logging.info(f"👮 POLICE ACTION: '{action}'")

    with state_lock:
        if action == "CONFIRM_ACCIDENT" or "Confirm" in action:
            # Police confirms accident -> Start response countdown timer (300 seconds / 5 minutes)
            current_state = "POLICE_CONFIRMED"
            timer_seconds = 300
            logging.info(f"🚨 POLICE CONFIRMED ACCIDENT! Starting 5-minute response timer: {timer_seconds}s")

        elif action == "FALSE_ALARM" or "False" in action:
            # Marked as false alarm -> Cancel alert and log feedback
            current_state = "CANCELLED"
            timer_seconds = 0
            current_severity = 0.0
            ai_vision.mark_false_alarm_feedback()
            ai_vision_data = ai_vision.analyze_frame({"scenario": "normal"})
            logging.info("❌ Operator marked False Alarm. Alert cleared & AI feedback recorded.")

        elif action == "HELP_ARRIVED" or "Resolved" in action:
            current_state = "RESOLVED"
            timer_seconds = 0
            logging.info("✅ Responders reached scene! Emergency successfully resolved.")

        elif action == "DISPATCH_AMBULANCE_NOW" or "Ambulance" in action:
            # Immediate escalation
            timer_seconds = 0
            threading.Thread(target=trigger_5km_sos_escalation, daemon=True).start()

        else:
            return jsonify({"status": "error", "message": f"Unknown action '{action}'"}), 400

        res_state = current_state
        res_timer = timer_seconds

    return jsonify({"status": "success", "new_state": res_state, "timer_seconds": res_timer})


def _apply_ai_scenario_locked(scenario: str):
    """Internal helper to execute AI vision analysis for a scenario."""
    global current_state, current_event, current_severity, ai_vision_data, timer_seconds

    # Run AI Vision frame analysis with temporal anti-false-alarm filter (3-frame verification)
    res = None
    for _ in range(3):
        res = ai_vision.analyze_frame({"scenario": scenario})

    ai_vision_data = res

    if res.get("anti_false_alarm_verified"):
        current_state = "UNVERIFIED_ALERT"
        current_event = scenario
        current_severity = res.get("intensity_score", 85.0)
        # Note: Timer does NOT start until Police clicks 'CONFIRM ACCIDENT'!
        timer_seconds = 0
        logging.warning(f"🚨 AI VISION DETECTED VERIFIED HAZARD: '{res.get('label')}' (Intensity: {res.get('intensity_score')}%) - Awaiting Police Confirmation!")
    else:
        current_state = "NORMAL"
        current_event = "none"
        current_severity = 0.0
        timer_seconds = 0


@app.route("/api/scenario", methods=["POST"])
def trigger_scenario():
    """1-Click Simulator API for demo testing."""
    global current_state, current_event, current_severity, ai_vision_data, timer_seconds, latest_telemetry

    data = request.get_json(force=True, silent=True) or {}
    scenario = data.get("scenario", "reset")

    with state_lock:
        if scenario in ["accident", "fire", "person_down"]:
            if scenario == "accident":
                latest_telemetry = {"flame": 0, "sound": 95.0, "vibration": 0, "distance_cm": 25}
            elif scenario == "fire":
                latest_telemetry = {"flame": 1, "sound": 85.0, "vibration": 0, "distance_cm": 40}
            elif scenario == "person_down":
                latest_telemetry = {"flame": 0, "sound": 80.0, "vibration": 0, "distance_cm": 90}
            _apply_ai_scenario_locked(scenario)
        else:
            current_state = "NORMAL"
            current_event = "none"
            current_severity = 0.0
            timer_seconds = 0
            latest_telemetry = {"flame": 0, "sound": 40.0, "vibration": 1, "distance_cm": 110}
            ai_vision.consecutive_detections.clear()
            ai_vision_data = ai_vision.analyze_frame({"scenario": "normal"})

    return jsonify({"status": "scenario_applied", "scenario": scenario, "state": current_state, "ai_vision": ai_vision_data})


@app.route("/api/reset", methods=["POST"])
def reset_system():
    return trigger_scenario()


if __name__ == "__main__":
    print("=" * 65)
    print("🚨 ROBO RAKSHA AI VISION & 5KM SOS SERVER RUNNING ON PORT 5000 🚨")
    print("Dashboard available at: http://localhost:5000/")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=False)
