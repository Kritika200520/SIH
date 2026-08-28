"""
Robo Raksha — Main Server Application (Person 1 / Builder)
Python Flask server running on laptop. Handles robot telemetry ingestion,
severity scoring, background emergency countdown, dashboard API feeds, operator actions,
MJPEG camera stream, simulation scenarios, and automated comms dispatch.
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

# Ensure server directory is on sys.path for scoring_engine import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scoring_engine import ScoringEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, static_folder="static")
CORS(app)  # Enable CORS for cross-origin polling

# Global Lock & System State
state_lock = threading.Lock()
scoring = ScoringEngine(threshold=7.0)

# System State Variables
current_state = "NORMAL"  # NORMAL, ALERT, INVESTIGATING, DISPATCHED, CANCELLED
current_event = "none"
current_severity = 0.0
initial_severity = 0.0
alert_start_time = 0.0
timer_seconds = 0
clip_url = "/video_feed"
current_options = ["Dispatch Emergency Services", "Investigate (+30s)", "False Alarm"]
latest_telemetry = {"flame": 0, "sound": 42.0, "vibration": 1, "distance_cm": 100}
wifi_signal_strength = 95  # Percentage (Patent feature: Wi-Fi degradation trigger)

# Comms Module Endpoint (Person 4's listener or local mock on port 5001)
COMMS_DISPATCH_URL = os.environ.get("COMMS_URL", "http://localhost:5001/api/comms/dispatch")
GPS_LAT = 12.9716
GPS_LNG = 77.5946

# Flag to control background timer thread
timer_running = True


def trigger_comms_dispatch(reason: str):
    """
    Sends emergency payload to Person 4 (Comms module) via HTTP POST.
    Contract: Server -> Comms
    """
    global current_state, current_severity, current_event, latest_telemetry, wifi_signal_strength

    msg = (
        f"ROBO RAKSHA EMERGENCY DISPATCH ({reason.upper()})! "
        f"Event: {current_event.upper()}, Severity Score: {current_severity}. "
        f"Flame: {latest_telemetry.get('flame')}, Sound: {latest_telemetry.get('sound')}dB, "
        f"Vibration: {latest_telemetry.get('vibration')}. Wi-Fi Signal: {wifi_signal_strength}%. "
        f"GPS: https://maps.google.com/?q={GPS_LAT},{GPS_LNG}"
    )

    payload = {
        "service": current_event if current_event != "none" else "emergency",
        "lat": GPS_LAT,
        "lng": GPS_LNG,
        "message": msg,
        "wifi_signal": wifi_signal_strength
    }

    logging.info(f"🚨 TRIGGERING COMMS DISPATCH: {payload}")
    try:
        res = requests.post(COMMS_DISPATCH_URL, json=payload, timeout=3.0)
        logging.info(f"Comms Dispatch Response [{res.status_code}]: {res.text}")
    except Exception as e:
        logging.warning(f"Failed to reach Comms endpoint ({COMMS_DISPATCH_URL}): {e}. Dispatch payload logged locally.")


def countdown_worker():
    """
    Background worker that decrements timer_seconds every second
    when system is in ALERT or INVESTIGATING state.
    Calculates dynamic risk decay and auto-dispatches at 0 seconds.
    """
    global current_state, timer_seconds, timer_running, current_severity, alert_start_time, initial_severity, latest_telemetry

    while timer_running:
        time.sleep(1.0)
        with state_lock:
            if current_state in ["ALERT", "INVESTIGATING"]:
                elapsed = time.time() - alert_start_time if alert_start_time > 0 else 0
                # Patent Risk Decay calculation
                current_severity = scoring.calculate_risk_decay(initial_severity, elapsed, latest_telemetry)

                if timer_seconds > 0:
                    timer_seconds -= 1
                    logging.info(f"⏳ Countdown ticking: {timer_seconds}s remaining (Score={current_severity}, State={current_state})")

                if timer_seconds <= 0:
                    logging.warning("⚠️ Countdown reached 0 unanswered! Auto-dispatching emergency services...")
                    current_state = "DISPATCHED"
                    timer_seconds = 0
                    threading.Thread(target=trigger_comms_dispatch, args=("timer_expired_unanswered",), daemon=True).start()


# Start background countdown thread
timer_thread = threading.Thread(target=countdown_worker, daemon=True)
timer_thread.start()


# Simulated Robot MJPEG Video Stream Generator
def generate_mjpeg_frames():
    """Generates an animated tactical camera stream with crosshairs & telemetry overlay."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        has_pil = True
    except ImportError:
        has_pil = False

    frame_idx = 0
    while True:
        frame_idx = (frame_idx + 1) % 360
        if has_pil:
            img = Image.new("RGB", (640, 360), color=(15, 20, 28))
            draw = ImageDraw.Draw(img)

            # Draw tactical HUD grid & crosshair
            cx, cy = 320, 180
            draw.line([(cx - 40, cy), (cx + 40, cy)], fill=(0, 255, 170), width=1)
            draw.line([(cx, cy - 40), (cx, cy + 40)], fill=(0, 255, 170), width=1)
            draw.ellipse([(cx - 60, cy - 60), (cx + 60, cy + 60)], outline=(0, 255, 170), width=1)

            # Draw scanning line
            scan_y = (frame_idx * 4) % 360
            draw.line([(0, scan_y), (640, scan_y)], fill=(0, 255, 170, 80), width=2)

            # Draw status overlay
            with state_lock:
                st = current_state
                fl = latest_telemetry.get("flame", 0)
                dist = latest_telemetry.get("distance_cm", 100)

            status_color = (255, 59, 48) if st == "ALERT" else (52, 199, 89)
            draw.rectangle([(10, 10), (220, 45)], fill=(0, 0, 0))
            draw.text((20, 15), f"CAM-01 [LIVE] - {st}", fill=status_color)
            draw.text((20, 30), f"DISTANCE: {dist}cm | FLAME: {fl}", fill=(240, 246, 254))

            if fl > 0 or st == "ALERT":
                # Simulated hazard bounding box
                draw.rectangle([(cx - 80, cy - 80), (cx + 80, cy + 80)], outline=(255, 59, 48), width=3)
                draw.text((cx - 75, cy - 100), "⚠️ HAZARD TARGET DETECTED", fill=(255, 59, 48))

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=75)
            frame_bytes = buffer.getvalue()
        else:
            # Fallback static pixel buffer
            frame_bytes = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.1)


@app.route("/", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def serve_dashboard_ui():
    """Serves Person 2/3 Control Room UI directly at site root!"""
    dashboard_dir = os.path.abspath(os.path.join(app.root_path, "..", "dashboard"))
    return send_from_directory(dashboard_dir, "index.html")


@app.route("/dashboard/<path:filename>", methods=["GET"])
def serve_dashboard_assets(filename):
    dashboard_dir = os.path.abspath(os.path.join(app.root_path, "..", "dashboard"))
    return send_from_directory(dashboard_dir, filename)


@app.route("/video_feed", methods=["GET"])
def video_feed():
    """Live MJPEG video stream endpoint for dashboard camera panel."""
    return Response(generate_mjpeg_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/api", methods=["GET"])
def index():
    host_url = request.host_url.rstrip("/")
    return jsonify({
        "service": "Robo Raksha Server (Person 1 - Builder)",
        "status": "online",
        "dashboard_ui": f"{host_url}/",
        "video_feed": f"{host_url}/video_feed",
        "endpoints": [
            "POST /api/telemetry",
            "GET /api/dashboard/status",
            "POST /api/dashboard/action",
            "POST /api/scenario",
            "POST /api/reset"
        ]
    })


@app.route("/api/telemetry", methods=["POST"])
def receive_telemetry():
    """
    Robot -> Server Endpoint.
    Receives JSON telemetry: { "flame": 1, "sound": 87, "vibration": 0, "distance_cm": 45 }
    Computes severity score and updates state.
    """
    global current_state, current_event, current_severity, initial_severity, alert_start_time, timer_seconds, latest_telemetry, current_options

    data = request.get_json(force=True, silent=True) or {}
    flame = int(data.get("flame", 0))
    sound = float(data.get("sound", 0))
    vibration = int(data.get("vibration", 0))
    distance_cm = int(data.get("distance_cm", 100))

    with state_lock:
        latest_telemetry = {
            "flame": flame,
            "sound": sound,
            "vibration": vibration,
            "distance_cm": distance_cm
        }

        score, event = scoring.compute_baseline_score(latest_telemetry)
        current_severity = score

        logging.info(f"Received Telemetry -> Score: {score}, Event: {event}, Raw: {latest_telemetry}")

        # Transition logic
        if score >= scoring.threshold and current_state == "NORMAL":
            current_state = "ALERT"
            current_event = event
            initial_severity = score
            alert_start_time = time.time()
            timer_seconds = scoring.calculate_timer_adjustment(score, baseline_timer_seconds=45)
            current_options = scoring.get_situation_specific_menu(event)
            logging.warning(f"🚨 EMERGENCY THRESHOLD CROSSED! Score={score} >= {scoring.threshold}. State=ALERT, Event={event}, Timer={timer_seconds}s")

        elif current_state in ["ALERT", "INVESTIGATING"]:
            # Patent Live re-scoring adjustment
            if score >= 12 and timer_seconds > 20:
                logging.info(f"🔥 Severity spiked to {score}! Shortening remaining timer to 20s.")
                timer_seconds = 20
                current_options = scoring.get_situation_specific_menu(event)

    return jsonify({
        "status": "ok",
        "severity": current_severity,
        "event": current_event,
        "state": current_state,
        "timer_seconds": timer_seconds
    })


@app.route("/api/dashboard/status", methods=["GET"])
def get_dashboard_status():
    """
    Server -> Dashboard Endpoint (Polled every second by Person 3).
    Returns exact JSON contract structure agreed for Dashboard.
    """
    with state_lock:
        response = {
            "state": current_state,
            "event": current_event,
            "severity": current_severity,
            "clip_url": clip_url,
            "timer_seconds": timer_seconds,
            "options": current_options if current_state in ["ALERT", "INVESTIGATING"] else [],
            "latest_telemetry": latest_telemetry,
            "wifi_signal": wifi_signal_strength
        }
    return jsonify(response)


@app.route("/api/dashboard/action", methods=["POST"])
def process_dashboard_action():
    """
    Dashboard -> Server Endpoint (Sent by Person 3 on button click).
    Processes human intervention: "Dispatch Fire Dept", "Investigate (+30s)", "False Alarm", etc.
    """
    global current_state, timer_seconds, current_severity, current_options

    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "")

    logging.info(f"🕹️ OPERATOR ACTION RECEIVED: '{action}'")

    with state_lock:
        if "Dispatch" in action or action == "Dispatch fire":
            current_state = "DISPATCHED"
            timer_seconds = 0
            current_options = []
            threading.Thread(target=trigger_comms_dispatch, args=(f"operator_manual_{action}",), daemon=True).start()

        elif "Investigate" in action:
            current_state = "INVESTIGATING"
            timer_seconds += 30  # Extend countdown by 30 seconds
            logging.info(f"Operator investigating. Countdown extended to {timer_seconds}s.")

        elif "False" in action or action == "False alarm":
            current_state = "CANCELLED"
            timer_seconds = 0
            current_severity = 0.0
            current_options = []
            logging.info("Operator marked event as False Alarm. Emergency cancelled.")

        else:
            return jsonify({"status": "error", "message": f"Unknown action '{action}'"}), 400

        res_state = current_state
        res_timer = timer_seconds

    return jsonify({
        "status": "success",
        "action_received": action,
        "new_state": res_state,
        "timer_seconds": res_timer
    })


@app.route("/api/scenario", methods=["POST"])
def trigger_scenario():
    """
    Simulation Helper API to trigger 1-click test scenarios directly from the dashboard UI!
    """
    global current_state, current_event, current_severity, initial_severity, alert_start_time, timer_seconds, latest_telemetry, current_options, wifi_signal_strength

    data = request.get_json(force=True, silent=True) or {}
    scenario = data.get("scenario", "reset")

    with state_lock:
        if scenario == "fire":
            latest_telemetry = {"flame": 1, "sound": 88.0, "vibration": 0, "distance_cm": 35}
            current_state = "ALERT"
            current_event = "fire"
            current_severity = 12.0
            initial_severity = 12.0
            alert_start_time = time.time()
            timer_seconds = 20
            current_options = scoring.get_situation_specific_menu("fire")

        elif scenario == "person_down":
            latest_telemetry = {"flame": 0, "sound": 92.0, "vibration": 0, "distance_cm": 85}
            current_state = "ALERT"
            current_event = "person_down_or_distress"
            current_severity = 7.0
            initial_severity = 7.0
            alert_start_time = time.time()
            timer_seconds = 45
            current_options = scoring.get_situation_specific_menu("person_down_or_distress")

        elif scenario == "wifi_loss":
            wifi_signal_strength = 15  # Signal drops below 20%
            logging.warning("⚠️ Wi-Fi signal weakened! Pre-generating predictive emergency SMS...")
            threading.Thread(target=trigger_comms_dispatch, args=("predictive_wifi_loss_cache",), daemon=True).start()

        else:
            current_state = "NORMAL"
            current_event = "none"
            current_severity = 0.0
            timer_seconds = 0
            wifi_signal_strength = 95
            latest_telemetry = {"flame": 0, "sound": 40.0, "vibration": 1, "distance_cm": 110}
            current_options = []

    return jsonify({"status": "scenario_applied", "scenario": scenario, "state": current_state, "severity": current_severity})


@app.route("/api/reset", methods=["POST"])
def reset_system():
    return trigger_scenario()


if __name__ == "__main__":
    print("=" * 65)
    print("🔥 ROBO RAKSHA INTEGRATED SERVER RUNNING ON PORT 5000 🔥")
    print("Dashboard UI Available at: http://localhost:5000/")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=False)
