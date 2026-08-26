"""
Robo Raksha — Mock Comms Module Listener (Person 4 Simulator Tool)
Runs a simple HTTP server on port 5001 to simulate Person 4's GSM module.
Allows Person 1 to test and verify Server -> Comms dispatch payloads without Person 4.
"""

from flask import Flask, request, jsonify
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MOCK-COMMS] %(message)s")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def comms_index():
    return jsonify({
        "service": "Robo Raksha Mock Comms Listener (Person 4)",
        "status": "online",
        "dispatch_endpoint": "POST /api/comms/dispatch"
    })

@app.route("/api/comms/dispatch", methods=["POST"])
def receive_dispatch():
    data = request.get_json(force=True, silent=True) or {}
    service = data.get("service", "unknown")
    lat = data.get("lat")
    lng = data.get("lng")
    message = data.get("message", "")

    print("\n" + "=" * 60)
    print("📲 [MOCK COMMS MODULE] INCOMING DISPATCH SIGNAL RECEIVED!")
    print(f"   Emergency Service Type : {service.upper()}")
    print(f"   GPS Location          : Latitude {lat}, Longitude {lng}")
    print(f"   SMS Message Body      :\n   \"{message}\"")
    print("=" * 60 + "\n")

    return jsonify({
        "status": "SMS_QUEUED",
        "mock_gsm_signal": "STRONG",
        "sim800l_status": "READY_TEST_MODE"
    }), 200

if __name__ == "__main__":
    print("📡 MOCK COMMS LISTENER (Simulating Person 4) Running on http://localhost:5001 ...")
    app.run(host="0.0.0.0", port=5001, debug=False)
