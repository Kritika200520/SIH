"""
Robo Raksha — Main Server Application (Person 1 / Builder)
Python Flask server running on laptop. Handles robot telemetry ingestion,
severity scoring, background emergency countdown, dashboard API feeds, operator actions,
and automated comms dispatch.
"""

import json
import logging
import os
import requests
import sys
import threading
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Ensure server directory is on sys.path for scoring_engine import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scoring_engine import ScoringEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, static_folder="static")
CORS(app)  # Enable CORS for Person 2/3 Dashboard cross-origin polling

# Global Lock & System State
state_lock = threading.Lock()
scoring = ScoringEngine(threshold=7.0)

# System State Variables
current_state = "NORMAL"  # NORMAL, ALERT, INVESTIGATING, DISPATCHED, CANCELLED
current_event = "none"
current_severity = 0.0
timer_seconds = 0
clip_url = "http://localhost:5000/static/sample_stream.jpg"
default_options = ["Dispatch fire", "Investigate", "False alarm"]
current_options = default_options.copy()
latest_telemetry = {"flame": 0, "sound": 0, "vibration": 1, "distance_cm": 100}

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
    global current_state, current_severity, current_event, latest_telemetry
    
    msg = (
        f"ROBO RAKSHA EMERGENCY ALERT ({reason.upper()})! "
        f"Event: {current_event.upper()}, Severity Score: {current_severity}. "
        f"Flame: {latest_telemetry.get('flame')}, Sound: {latest_telemetry.get('sound')}dB, "
        f"Vibration: {latest_telemetry.get('vibration')}. Location: https://maps.google.com/?q={GPS_LAT},{GPS_LNG}"
    )

    payload = {
        "service": current_event if current_event != "none" else "emergency",
        "lat": GPS_LAT,
        "lng": GPS_LNG,
        "message": msg
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
    Triggers dispatch if timer reaches zero unanswered.
    """
    global current_state, timer_seconds, timer_running

    while timer_running:
        time.sleep(1.0)
        with state_lock:
            if current_state in ["ALERT", "INVESTIGATING"]:
                if timer_seconds > 0:
                    timer_seconds -= 1
                    logging.info(f"⏳ Countdown ticking: {timer_seconds}s remaining (State: {current_state})")
                
                if timer_seconds <= 0:
                    logging.warning("⚠️ Countdown reached 0 unanswered! Auto-dispatching emergency services...")
                    current_state = "DISPATCHED"
                    timer_seconds = 0
                    current_options = []
                    # Trigger dispatch in separate thread to avoid holding lock
                    threading.Thread(target=trigger_comms_dispatch, args=("timer_expired_unanswered",), daemon=True).start()


# Start countdown background thread
timer_thread = threading.Thread(target=countdown_worker, daemon=True)
timer_thread.start()


@app.route("/", methods=["GET"])
def root_dashboard():
    """Serves Person 2/3 Control Room UI directly at main site root!"""
    dashboard_dir = os.path.abspath(os.path.join(app.root_path, "..", "dashboard"))
    return send_from_directory(dashboard_dir, "index.html")


@app.route("/dashboard", methods=["GET"])
def serve_dashboard_ui():
    """Serves Person 2/3 Control Room UI."""
    dashboard_dir = os.path.abspath(os.path.join(app.root_path, "..", "dashboard"))
    return send_from_directory(dashboard_dir, "index.html")


@app.route("/dashboard/<path:filename>", methods=["GET"])
def serve_dashboard_assets(filename):
    dashboard_dir = os.path.abspath(os.path.join(app.root_path, "..", "dashboard"))
    return send_from_directory(dashboard_dir, filename)


@app.route("/api", methods=["GET"])
def index():
    host_url = request.host_url.rstrip("/")
    return jsonify({
        "service": "Robo Raksha Server (Person 1 - Builder)",
        "status": "online",
        "dashboard_ui": f"{host_url}/",
        "endpoints": [
            "POST /api/telemetry",
            "GET /api/dashboard/status",
            "POST /api/dashboard/action",
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
    global current_state, current_event, current_severity, timer_seconds, latest_telemetry

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
            # Base timer 45s, adjusted if severity is extra high
            timer_seconds = scoring.calculate_timer_adjustment(score, baseline_timer_seconds=45)
            logging.warning(f"🚨 EMERGENCY THRESHOLD CROSSED! Score={score} >= {scoring.threshold}. State=ALERT, Timer={timer_seconds}s")
        
        elif current_state in ["ALERT", "INVESTIGATING"]:
            # Live re-scoring adjustment (Patent mechanism)
            if score >= 12 and timer_seconds > 20:
                logging.info(f"🔥 Severity spiked to {score}! Shortening remaining timer to 20s.")
                timer_seconds = 20

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
            "latest_telemetry": latest_telemetry
        }
    return jsonify(response)


@app.route("/api/dashboard/action", methods=["POST"])
def process_dashboard_action():
    """
    Dashboard -> Server Endpoint (Sent by Person 3 on button click).
    Processes human intervention: "Dispatch fire", "Investigate", "False alarm".
    """
    global current_state, timer_seconds, current_severity

    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action")

    logging.info(f"🕹️ OPERATOR ACTION RECEIVED: '{action}'")

    with state_lock:
        if action == "Dispatch fire":
            current_state = "DISPATCHED"
            timer_seconds = 0
            threading.Thread(target=trigger_comms_dispatch, args=("operator_manual_dispatch",), daemon=True).start()

        elif action == "Investigate":
            current_state = "INVESTIGATING"
            timer_seconds += 30  # Extend countdown by 30 seconds
            logging.info(f"Operator investigating. Countdown extended to {timer_seconds}s.")

        elif action == "False alarm":
            current_state = "CANCELLED"
            timer_seconds = 0
            current_severity = 0.0
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


@app.route("/api/reset", methods=["POST"])
def reset_system():
    """
    Utility endpoint to reset state back to NORMAL for testing.
    """
    global current_state, current_event, current_severity, timer_seconds
    with state_lock:
        current_state = "NORMAL"
        current_event = "none"
        current_severity = 0.0
        timer_seconds = 0
    return jsonify({"status": "reset", "state": "NORMAL"})


@app.route("/static/<path:filename>")
def serve_static(filename):
    static_dir = os.path.join(app.root_path, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    return send_from_directory(static_dir, filename)


if __name__ == "__main__":
    # Create static placeholder image if missing
    os.makedirs(os.path.join(app.root_path, "static"), exist_ok=True)
    
    print("=" * 65)
    print("🔥 ROBO RAKSHA SERVER (Person 1 - Builder) RUNNING ON PORT 5000 🔥")
    print("Contract Endpoints Available:")
    print("  • Robot -> Server:      POST http://localhost:5000/api/telemetry")
    print("  • Server -> Dashboard:  GET  http://localhost:5000/api/dashboard/status")
    print("  • Dashboard -> Server:  POST http://localhost:5000/api/dashboard/action")
    print("  • Server -> Comms Target:    " + COMMS_DISPATCH_URL)
    print("=" * 65)
    
    app.run(host="0.0.0.0", port=5000, debug=False)
