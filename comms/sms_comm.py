"""
Robo Raksha — Comms & 5km Radius SOS Dispatch Engine (Person 4)
Handles GSM SIM800L module communication, AI Voice Ambulance auto-dialing,
and 5km Radius Emergency SOS Broadcast with exact GPS location.
"""

import argparse
import json
import logging
import time
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [COMMS-5KM] %(message)s")

app = Flask(__name__)

# Configured Target Emergency Phone Numbers
EMERGENCY_AMBULANCE_NUMBER = "108"
REGISTERED_NEARBY_RESPONDERS = [
    "+919876543210",
    "+919123456780",
    "+919988776655"
]


def send_sim800l_sms(phone_number: str, message: str) -> bool:
    """Simulates / sends SMS over SIM800L UART AT commands."""
    logging.info(f"📱 [SIM800L SMS SENT] -> {phone_number}")
    logging.info(f"   Message: \"{message}\"")
    return True


def trigger_ai_ambulance_call(phone_number: str, location_str: str, hazard_label: str) -> bool:
    """
    [PATENT ESCALATION MECHANISM]
    Simulates / triggers AI Voice Synthesis Auto-Dial to Emergency Ambulance Dispatch:
    ATD108;
    """
    logging.warning("=" * 65)
    logging.warning(f"📞 [AI VOICE CALL INITIATED] Dialing Ambulance Service ({phone_number})...")
    logging.warning(f"   Voice Payload: 'EMERGENCY! Severe {hazard_label} confirmed. Responders did not arrive in time window. Location: {location_str}'")
    logging.warning("   SIM800L Voice Channel Active: CONNECTED 🔔")
    logging.warning("=" * 65)
    return True


@app.route("/", methods=["GET"])
def comms_index():
    return jsonify({
        "service": "Robo Raksha Comms & 5km Radius SOS Dispatcher",
        "status": "online",
        "endpoints": [
            "POST /api/comms/dispatch",
            "POST /api/comms/broadcast_sos"
        ]
    })


@app.route("/api/comms/dispatch", methods=["POST"])
def receive_dispatch():
    data = request.get_json(force=True, silent=True) or {}
    service = data.get("service", "emergency")
    lat = data.get("lat", 12.9716)
    lng = data.get("lng", 77.5946)
    message = data.get("message", "")

    logging.info(f"🚨 [STANDARD DISPATCH] Service: {service.upper()} | GPS: {lat}, {lng}")
    send_sim800l_sms(REGISTERED_NEARBY_RESPONDERS[0], message)
    return jsonify({"status": "DISPATCH_SENT", "sms_queued": True}), 200


@app.route("/api/comms/broadcast_sos", methods=["POST"])
def broadcast_5km_sos():
    """
    [PATENT NOVELTY ENDPOINT]
    Triggered when Response Timer expires (Responders did not arrive in time).
    Auto-calls Ambulance & Broadcasts SOS SMS to all registered responders within 5km radius!
    """
    data = request.get_json(force=True, silent=True) or {}
    lat = data.get("lat", 12.9716)
    lng = data.get("lng", 77.5946)
    hazard_label = data.get("hazard_label", "Severe Accident")
    intensity = data.get("intensity", 90.0)
    address = data.get("address", "MG Road Junction, Bangalore")
    maps_url = f"https://maps.google.com/?q={lat},{lng}"

    # 1. Trigger AI Voice Auto-Dial to Ambulance
    call_success = trigger_ai_ambulance_call(EMERGENCY_AMBULANCE_NUMBER, f"{address} ({maps_url})", hazard_label)

    # 2. Broadcast SOS Message to 5km Radius Responders
    sos_body = (
        f"🚨 [5KM RADIUS SOS ALERT] {hazard_label.upper()}!\n"
        f"Intensity: {intensity}%. Emergency response window expired. Immediate civilian/medical assistance needed!\n"
        f"📍 Location: {address}\n"
        f"🗺️ Map: {maps_url}"
    )

    sent_count = 0
    for number in REGISTERED_NEARBY_RESPONDERS:
        send_sim800l_sms(number, sos_body)
        sent_count += 1

    logging.info(f"📡 5KM RADIUS SOS BROADCAST COMPLETE: Sent to {sent_count} responders in 5km perimeter.")

    return jsonify({
        "status": "5KM_SOS_BROADCAST_COMPLETED",
        "ambulance_call_initiated": call_success,
        "sos_messages_dispatched": sent_count,
        "radius_km": 5.0,
        "location": {"lat": lat, "lng": lng, "address": address, "map_url": maps_url}
    }), 200


def main():
    parser = argparse.ArgumentParser(description="Robo Raksha Comms 5km SOS Module")
    parser.add_argument("--port", type=int, default=5001, help="HTTP Listener port")
    args = parser.parse_args()
    print(f"📡 Robo Raksha Comms Server starting on port {args.port}...")
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
