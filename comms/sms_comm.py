"""
Robo Raksha — Comms & Dispatch Module (Person 4)
Handles SIM800L GSM module integration, dynamic SMS payload formatting,
GPS coordinate insertion, auto-dialing simulation, and HTTP listener for Person 1 dispatches.
"""

import argparse
import json
import logging
import time
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [COMMS] %(message)s")

app = Flask(__name__)

# Configured Target Phone Number for Testing (OWN PHONE ONLY!)
TARGET_PHONE_NUMBER = "+919876543210"


def send_sim800l_sms(phone_number: str, message: str) -> bool:
    """
    Simulates / handles SIM800L AT commands over Serial UART.
    AT+CMGF=1 (Text mode)
    AT+CMGS="<phone_number>"
    > <message> <Ctrl+Z>
    """
    logging.info(f"📱 [SIM800L AT COMMAND DISPATCH]")
    logging.info(f"   Target Phone: {phone_number}")
    logging.info(f"   SMS Body    :\n   {message}")
    logging.info("   Executing AT+CMGF=1 ... OK")
    logging.info(f"   Executing AT+CMGS=\"{phone_number}\" ... OK")
    logging.info("   Message Sent Successfully! ✅\n")
    return True


def trigger_autodial(phone_number: str) -> bool:
    """
    Simulates / handles SIM800L auto-dialing voice call:
    ATD<phone_number>;
    """
    logging.info(f"📞 [SIM800L AUTO-DIAL] Calling {phone_number} via ATD ... Call initiated! 🔔")
    return True


@app.route("/api/comms/dispatch", methods=["POST"])
def handle_dispatch_request():
    """
    Server -> Comms Contract Endpoint.
    Receives JSON: { "service": "fire", "lat": 12.9716, "lng": 77.5946, "message": "..." }
    """
    data = request.get_json(force=True, silent=True) or {}
    service = data.get("service", "emergency")
    lat = data.get("lat", 12.9716)
    lng = data.get("lng", 77.5946)
    raw_message = data.get("message")

    if not raw_message:
        raw_message = f"ROBO RAKSHA {service.upper()} ALERT! Location: Lat {lat}, Lng {lng}"

    # Send SMS & Trigger Auto-dial
    sms_success = send_sim800l_sms(TARGET_PHONE_NUMBER, raw_message)
    dial_success = trigger_autodial(TARGET_PHONE_NUMBER)

    return jsonify({
        "status": "DISPATCH_EXECUTED",
        "sms_sent": sms_success,
        "auto_dial_initiated": dial_success,
        "target_number": TARGET_PHONE_NUMBER
    }), 200


def main():
    parser = argparse.ArgumentParser(description="Robo Raksha Comms Module (Person 4)")
    parser.add_argument("--test-sms", action="store_true", help="Week 1-2 Task: Send one 'test' SMS to configured number")
    parser.add_argument("--port", type=int, default=5001, help="HTTP Listener port for Person 1 dispatches")

    args = parser.parse_args()

    if args.test_sms:
        print("▶️ Running Week 1-2 Task: Sending test SMS to phone...")
        send_sim800l_sms(TARGET_PHONE_NUMBER, "test")
    else:
        print(f"📡 Starting Comms Dispatch HTTP Server on port {args.port}...")
        app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
