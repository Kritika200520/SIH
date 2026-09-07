# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: Central Flask Server & SIH API Controller
Disaster Management: Landslide & Flash-Flood Early Warning System
"""
import os, time, json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Load .env file for API credentials
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass  # dotenv optional; credentials can be set as system env vars

from geo_rag import geo_rag_engine
from vlm_engine import vlm_engine
from broadcast_agent import broadcast_agent
from scoring_engine import scoring_engine
from routing_engine import routing_engine
from spam_filter import spam_filter_engine
from whatsapp_service import whatsapp_service
import weather_service
from predictive_engine import predictive_engine

app = Flask(__name__, static_folder="../dashboard", static_url_path="")
CORS(app)

# Ensure audio directory exists
os.makedirs("server/static/audio", exist_ok=True)

# Active State Data
CURRENT_STATE = {
    "active_scenario_id": "chamoli_fissure",
    "region_id": "chamoli_joshimath",
    "selected_dialect": "Garhwali",
    "operator_status": "MONITORING",
    "sim_reports": [],
    "last_broadcast": None,
    "last_spam_check": None,
    "latest_whatsapp_alert": None
}

def init_default_scenario(scenario_key="chamoli_fissure"):
    vlm_data = vlm_engine.analyze_image(preset_key=scenario_key)
    sector_profile = geo_rag_engine.profiles.get(vlm_data.get("sector_id", "chamoli_joshimath"))
    
    # InSAR and Rainfall for Scenario
    if scenario_key == "chamoli_fissure":
        insar_disp = 14.8
        slope_angle = 38.0
        cluster_n = 4
    elif scenario_key == "wayanad_flood":
        insar_disp = 18.6
        slope_angle = 34.5
        cluster_n = 7
    elif scenario_key == "shimla_subsidence":
        insar_disp = 11.5
        slope_angle = 42.0
        cluster_n = 3
    else: # False alarm
        insar_disp = 0.5
        slope_angle = 18.0
        cluster_n = 1

    # Fetch live weather data (Rainfall)
    lat = sector_profile["coordinates"]["lat"]
    lng = sector_profile["coordinates"]["lng"]
    live_rainfall = weather_service.get_current_rainfall(lat, lng)
    
    if live_rainfall is not None:
        rainfall_24h = live_rainfall
    else:
        # Fallback to mock values if API fails
        fallback_rain = {
            "chamoli_fissure": 78.5,
            "wayanad_flood": 145.0,
            "shimla_subsidence": 92.0
        }
        rainfall_24h = fallback_rain.get(scenario_key, 12.0)

    fs_data = geo_rag_engine.calculate_safety_factor(sector_profile, slope_deg=slope_angle, insar_disp_mm=insar_disp)
    risk_data = scoring_engine.compute_composite_risk(vlm_data, insar_disp, fs_data, rainfall_24h, cluster_n)
    
    # Broadcast notice in primary dialect
    dialect_to_use = vlm_data.get("dialect", sector_profile.get("primary_dialect", "Garhwali"))
    broadcast_data = broadcast_agent.generate_alert(dialect_key=dialect_to_use, sector_name=sector_profile["region_name"])
    
    # Dynamic Hazard Routing Calculation
    nav_routes = routing_engine.compute_evacuation_routes(
        sector_id=sector_profile["id"],
        vlm_depth_cm=vlm_data.get("fissure_depth_cm", 8.4),
        turbidity_pct=vlm_data.get("turbidity_index_pct", 45.0)
    )

    # AI Predictive Analytics Engine (using Live Weather, Geotech, and VLM)
    ai_prediction = predictive_engine.predict_risk_and_timeline(
        rainfall_mm=rainfall_24h,
        insar_mm=insar_disp,
        slope_deg=slope_angle,
        fissure_cm=vlm_data.get("fissure_depth_cm", 8.4)
    )

    # AI Hallucination & Spam Filter Verification
    spam_verif = spam_filter_engine.verify_report(
        test_case_key="live_authentic_field",
        sector_id=sector_profile["id"]
    )
    CURRENT_STATE["last_spam_check"] = spam_verif

    CURRENT_STATE["active_scenario_id"] = scenario_key
    CURRENT_STATE["region_id"] = sector_profile["id"]
    CURRENT_STATE["selected_dialect"] = dialect_to_use
    CURRENT_STATE["last_broadcast"] = broadcast_data
    
    scoring_engine.severity_score = int(risk_data["composite_risk_score"])
    scoring_engine.alert_level = risk_data["status"]
    scoring_engine.state = "ALERT" if scoring_engine.severity_score >= 65 else "NORMAL"
    
    scoring_engine.latest_telemetry = {
        "vlm": vlm_data,
        "geotechnical_fs": fs_data,
        "risk_fusion": risk_data,
        "sar_insar_displacement_mm": insar_disp,
        "sar_timeseries": geo_rag_engine.get_sar_data(sector_profile["id"]),
        "rainfall_24h_mm": rainfall_24h,
        "slope_angle_deg": slope_angle,
        "cluster_report_count": cluster_n,
        "sector_profile": sector_profile,
        "broadcast": broadcast_data,
        "dynamic_routing": nav_routes,
        "ai_prediction": ai_prediction,
        "spam_filter": spam_verif
    }
    
    scoring_engine.add_log(f"Scenario Activated: {vlm_data['title']} (Risk: {scoring_engine.severity_score}%)", "ALERT" if scoring_engine.severity_score >= 65 else "INFO")

# Initialize default state on startup
init_default_scenario("chamoli_fissure")

@app.route("/")
def serve_dashboard():
    return send_from_directory("../dashboard", "index.html")

@app.route("/citizen")
def serve_citizen_portal():
    return send_from_directory("../dashboard", "citizen.html")

@app.route("/api/citizen/sos", methods=["POST"])
def handle_citizen_sos():
    data = request.get_json() or {}
    sender_phone = str(data.get("sender_phone") or data.get("phone") or "919995622878")
    sender_name = str(data.get("sender_name") or data.get("name") or "Citizen")
    text_body = str(data.get("message") or data.get("text") or "Emergency Landslide SOS")
    msg_type = data.get("msg_type", "text")
    
    clean_sender = sender_phone.replace("+", "").replace(" ", "").replace("-", "")
    current_time_str = time.strftime("%H:%M:%S")
    
    CURRENT_STATE["latest_whatsapp_alert"] = {
        "sender": clean_sender,
        "contact_name": sender_name,
        "text": text_body,
        "timestamp": current_time_str,
        "msg_type": msg_type,
        "id": f"{clean_sender}_{time.time()}"
    }
    
    scoring_engine.add_log(f"Incoming WhatsApp SOS from +{clean_sender} ({sender_name}): '{text_body[:40]}...'", "CRITICAL")
    
    bc = CURRENT_STATE.get("last_broadcast") or {}
    reply_text = bc.get("speech_script", "Bhoomi-Raksha Alert: Your report is logged. Evacuate to high ridge immediately.")
    safe_route = bc.get("evacuation_route", "Move uphill via B-4 bypass.")
    
    # Attempt WhatsApp API notification if token configured
    whatsapp_service.send_evacuation_alert(clean_sender, reply_text, safe_route)
    
    return jsonify({
        "success": True,
        "alert": CURRENT_STATE["latest_whatsapp_alert"],
        "reply": reply_text,
        "safe_route": safe_route,
        "timestamp": current_time_str
    })

@app.route("/static/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory("static/audio", filename)

@app.route("/api/dashboard/status", methods=["GET"])
def get_dashboard_status():
    return jsonify({
        "success": True,
        "state": scoring_engine.state,
        "severity_score": scoring_engine.severity_score,
        "alert_level": scoring_engine.alert_level,
        "timer_seconds": scoring_engine.timer_seconds,
        "active_scenario_id": CURRENT_STATE["active_scenario_id"],
        "region_id": CURRENT_STATE["region_id"],
        "selected_dialect": CURRENT_STATE["selected_dialect"],
        "telemetry": scoring_engine.latest_telemetry,
        "event_log": scoring_engine.event_log,
        "dialects": broadcast_agent.list_dialects(),
        "available_scenarios": vlm_engine.get_presets(),
        "spam_filter_presets": spam_filter_engine.get_test_presets(),
        "latest_whatsapp_alert": CURRENT_STATE.get("latest_whatsapp_alert"),
        "latest_broadcast_event": CURRENT_STATE.get("latest_broadcast_event")
    })

@app.route("/api/scenario/trigger", methods=["POST"])
def trigger_scenario():
    data = request.get_json() or {}
    scenario_id = data.get("scenario_id", "chamoli_fissure")
    init_default_scenario(scenario_id)
    return jsonify({
        "success": True,
        "message": f"Scenario {scenario_id} triggered successfully",
        "telemetry": scoring_engine.latest_telemetry
    })

@app.route("/api/routing/navigate", methods=["POST"])
def get_navigation_routes():
    data = request.get_json() or {}
    sector_id = data.get("sector_id", CURRENT_STATE["region_id"])
    vlm_depth = float(data.get("vlm_depth_cm", 8.4))
    turbidity = float(data.get("turbidity_pct", 45.0))
    mode = data.get("mode", "vehicle")
    
    routes = routing_engine.compute_evacuation_routes(
        sector_id=sector_id,
        vlm_depth_cm=vlm_depth,
        turbidity_pct=turbidity,
        mode=mode
    )
    return jsonify({
        "success": True,
        "routing": routes
    })

@app.route("/api/spam-filter/verify", methods=["POST"])
def verify_spam_protocol():
    data = request.get_json() or {}
    preset_key = data.get("preset_key", "live_authentic_field")
    sector_id = data.get("sector_id", CURRENT_STATE["region_id"])
    telemetry = data.get("telemetry")
    
    result = spam_filter_engine.verify_report(
        telemetry=telemetry,
        sector_id=sector_id,
        test_case_key=preset_key
    )
    CURRENT_STATE["last_spam_check"] = result
    scoring_engine.latest_telemetry["spam_filter"] = result
    
    if result["verification_status"] == "REJECTED_SPAM":
        scoring_engine.add_log(f"AI Anti-Spam BLOCKED: {result['decision_reason']}", "CRITICAL")
    elif result["verification_status"] == "SUSPICIOUS_FLAGGED":
        scoring_engine.add_log(f"AI Anti-Spam FLAGGED: {result['decision_reason']}", "WARNING")
    else:
        scoring_engine.add_log(f"AI Anti-Spam PASSED: Trust Score {result['composite_trust_score']}%", "INFO")
        
    return jsonify({
        "success": True,
        "verification": result
    })

@app.route("/api/citizen/report", methods=["POST"])
def submit_citizen_report():
    data = request.get_json() or {}
    image_base64 = data.get("image_base64")
    voice_text = data.get("voice_memo", "Heavy soil fissures and rock displacement on upper cliff path.")
    location = data.get("location", "Chamoli Village Sector 3")
    reporter = data.get("reporter_name", "Local Villager (WhatsApp Ingestion)")
    preset_key = data.get("test_case_key", "live_authentic_field")
    sector_id = data.get("sector_id", CURRENT_STATE["region_id"])
    
    # Run Anti-Spam & Authenticity Protocol FIRST
    verif = spam_filter_engine.verify_report(
        image_data=image_base64,
        telemetry=data.get("telemetry"),
        sector_id=sector_id,
        test_case_key=preset_key
    )
    CURRENT_STATE["last_spam_check"] = verif
    scoring_engine.latest_telemetry["spam_filter"] = verif
    
    if verif["verification_status"] == "REJECTED_SPAM":
        scoring_engine.add_log(f"Spam Protocol Blocked Report: {verif['decision_reason']}", "CRITICAL")
        return jsonify({
            "success": False,
            "spam_blocked": True,
            "message": "Report blocked by AI Anti-Spam & Authenticity Protocol.",
            "verification": verif
        }), 400
        
    vlm_result = vlm_engine.analyze_image(image_data=image_base64, voice_text=voice_text, location=location)
    vlm_result["reporter_info"] = reporter
    vlm_result["timestamp"] = time.strftime("%H:%M:%S")
    vlm_result["spam_verification"] = verif
    
    CURRENT_STATE["sim_reports"].insert(0, vlm_result)
    scoring_engine.add_log(f"Citizen Ingestion Verified: {vlm_result['hazard_classification']} from {location} (Trust: {verif['composite_trust_score']}%)", "WARNING")
    
    return jsonify({
        "success": True,
        "message": "Citizen report passed Anti-Spam Protocol and analyzed by VLM Engine.",
        "vlm_result": vlm_result,
        "verification": verif
    })

@app.route("/api/reports", methods=["GET"])
def list_reports():
    return jsonify({
        "success": True,
        "reports": CURRENT_STATE["sim_reports"],
        "presets": vlm_engine.get_presets()
    })

@app.route("/api/broadcast/generate", methods=["POST"])
def generate_broadcast():
    data = request.get_json() or {}
    dialect = data.get("dialect", CURRENT_STATE["selected_dialect"])
    sector_id = CURRENT_STATE["region_id"]
    sector_profile = geo_rag_engine.profiles.get(sector_id, geo_rag_engine.profiles["chamoli_joshimath"])
    
    broadcast_data = broadcast_agent.generate_alert(dialect_key=dialect, sector_name=sector_profile["region_name"])
    CURRENT_STATE["selected_dialect"] = dialect
    CURRENT_STATE["last_broadcast"] = broadcast_data
    scoring_engine.latest_telemetry["broadcast"] = broadcast_data
    
    scoring_engine.add_log(f"Broadcasting Agent Dispatched Voice Note: {dialect} ({broadcast_data['dialect_name']})", "ALERT")
    
    return jsonify({
        "success": True,
        "broadcast": broadcast_data
    })

@app.route("/api/rag/query", methods=["POST"])
def query_geotechnical_rag():
    data = request.get_json() or {}
    query = data.get("query", "slope failure threshold")
    sector_id = data.get("sector_id", CURRENT_STATE["region_id"])
    rag_result = geo_rag_engine.query_rag_context(query, sector_id=sector_id)
    return jsonify({
        "success": True,
        "rag": rag_result
    })

@app.route("/api/action/operator", methods=["POST"])
def operator_action():
    data = request.get_json() or {}
    action = data.get("action", "CONFIRM_DISPATCH")
    
    if action == "CONFIRM_DISPATCH":
        scoring_engine.state = "DISPATCHED"
        scoring_engine.add_log("OPERATOR CONFIRMED: Evacuation Siren & Dialect Voice Blast Dispatched to Village", "CRITICAL")
        
        # Pull live dialect broadcast alert text and safe corridor route
        bc = CURRENT_STATE.get("last_broadcast") or {}
        alert_text = bc.get("speech_script") or bc.get("broadcast_text") or "CRITICAL EMERGENCY WARNING: Severe landslide and debris torrent risk verified. Evacuate immediately to designated high ridge shelters."
        safe_route = bc.get("evacuation_route") or "Avoid river ravines and culverts. Follow high-ridge bypass corridors until official clearance."
        dialect = bc.get("dialect_name") or CURRENT_STATE.get("selected_dialect") or "National Broadcast"
        
        # Identify recipient phone numbers
        recipients = ["919995622878", "919773834230"]
        latest_sos = CURRENT_STATE.get("latest_whatsapp_alert")
        if latest_sos and latest_sos.get("sender"):
            clean_s = str(latest_sos["sender"]).replace("+", "").replace(" ", "").replace("-", "")
            if clean_s and clean_s not in recipients:
                recipients.append(clean_s)

        # Store in state so /citizen and polling dashboards can render live broadcast SOS
        broadcast_record = {
            "title": f"🚨 EMERGENCY EVACUATION BROADCAST ({dialect})",
            "alert": alert_text,
            "route": safe_route,
            "dialect": dialect,
            "audio_url": bc.get("audio_url", "/static/audio/alert_english.mp3"),
            "timestamp": time.strftime("%H:%M:%S"),
            "recipients": recipients
        }
        CURRENT_STATE["latest_broadcast_event"] = broadcast_record
        
        # Send live text evacuation via WhatsApp Cloud API
        dispatch_results = []
        for phone in recipients:
            res = whatsapp_service.send_evacuation_alert(phone, alert_text, safe_route)
            dispatch_results.append({"phone": phone, "result": res})
            scoring_engine.add_log(f"WhatsApp Dialect SOS Dispatched to +{phone}: '{alert_text[:40]}...'", "CRITICAL")
            
        return jsonify({
            "success": True,
            "state": scoring_engine.state,
            "broadcast": broadcast_record,
            "dispatch_results": dispatch_results,
            "message": f"Broadcast dispatched to {len(recipients)} WhatsApp recipients."
        })
        
    elif action == "FALSE_ALARM":
        scoring_engine.state = "NORMAL"
        scoring_engine.severity_score = 0
        scoring_engine.alert_level = "SAFE"
        scoring_engine.add_log("OPERATOR ACTION: Marked as False Alarm - System Calibrated", "INFO")
    
    return jsonify({
        "success": True,
        "state": scoring_engine.state,
        "message": f"Action {action} recorded."
    })

@app.route("/api/whatsapp/send", methods=["POST"])
def send_whatsapp_alert():
    data = request.get_json() or {}
    recipient = data.get("phone", "")
    sector_id = CURRENT_STATE.get("region_id", "chamoli_joshimath")
    bc = CURRENT_STATE.get("last_broadcast") or {}

    alert_text = bc.get("speech_script", "CRITICAL EMERGENCY: Severe landslide risk verified. Evacuate immediately!")
    safe_route = bc.get("evacuation_route", "Evacuate to designated high-ridge shelter immediately.")

    if not recipient:
        return jsonify({"success": False, "message": "Phone number required. E.g. +919876543210"}), 400

    result = whatsapp_service.send_evacuation_alert(
        recipient_phone=recipient,
        alert_message=alert_text,
        safe_route=safe_route
    )
    if result.get("success"):
        scoring_engine.add_log(f"WhatsApp SOS Dispatched to {recipient} via Meta Cloud API", "CRITICAL")
    return jsonify(result)

# =====================================================================
# META WHATSAPP WEBHOOK HANDLERS (GET Verification & POST Incoming SOS)
# =====================================================================
WEBHOOK_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "bhoomi_raksha_verify_token")

@app.route("/webhook", methods=["GET"])
def verify_whatsapp_webhook():
    """
    Meta Developer Portal Webhook Verification Endpoint.
    Meta sends a challenge query param when you click 'Verify and Save'.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
            print(f"[WhatsApp Webhook] Verification successful with token: {token}")
            return challenge, 200
        else:
            print(f"[WhatsApp Webhook] Verification failed. Token mismatch: {token}")
            return "Verification token mismatch", 403
    return "Missing parameters", 400

@app.route("/webhook", methods=["POST"])
def handle_incoming_whatsapp():
    """
    Receives incoming WhatsApp messages from citizens via Meta Cloud API webhook.
    Extracts text/image, runs anti-spam filter, and auto-replies with evacuation guidance.
    """
    data = request.get_json() or {}
    print(f"[WhatsApp Webhook Event]: {json.dumps(data, indent=2)}")

    try:
        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])
                
                # Extract contact name if available
                contact_name = "Citizen"
                if contacts:
                    contact_name = contacts[0].get("profile", {}).get("name", "Citizen")

                for msg in messages:
                    sender = msg.get("from", "Unknown")  # Citizen phone number
                    msg_type = msg.get("type", "text")
                    text_body = ""

                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "")
                    elif msg_type == "image":
                        text_body = msg.get("image", {}).get("caption") or "Citizen uploaded landslide damage photo"
                    elif msg_type == "audio" or msg_type == "voice":
                        text_body = "Citizen sent voice SOS note"
                    elif msg_type == "location":
                        loc = msg.get("location", {})
                        text_body = f"Location SOS shared: Lat {loc.get('latitude')}, Lng {loc.get('longitude')}"
                    elif msg_type == "button":
                        text_body = msg.get("button", {}).get("text", "Button clicked")
                    elif msg_type == "interactive":
                        inter = msg.get("interactive", {})
                        text_body = inter.get("button_reply", {}).get("title") or inter.get("list_reply", {}).get("title") or "Interactive reply"
                    else:
                        text_body = f"Citizen sent {msg_type} message"

                    # Fallback if empty
                    if not text_body or not text_body.strip():
                        text_body = "Emergency SOS: Landslide alert reported by citizen!"

                    current_time_str = time.strftime("%H:%M:%S")
                    
                    scoring_engine.add_log(f"Incoming WhatsApp SOS from +{sender} ({contact_name}): '{text_body[:40]}...'", "CRITICAL")
                    
                    # Store latest emergency alert for Web Dashboard Live Popup
                    CURRENT_STATE["latest_whatsapp_alert"] = {
                        "sender": sender,
                        "contact_name": contact_name,
                        "text": text_body,
                        "timestamp": current_time_str,
                        "msg_type": msg_type,
                        "id": f"{sender}_{time.time()}"
                    }

                    # Auto reply to citizen with current evacuation status
                    bc = CURRENT_STATE.get("last_broadcast") or {}
                    reply_text = bc.get("speech_script", "Bhoomi-Raksha Alert: Your report is logged. Evacuate to high ridge immediately.")
                    safe_route = bc.get("evacuation_route", "Move uphill via B-4 bypass.")
                    whatsapp_service.send_evacuation_alert(sender, reply_text, safe_route)
    except Exception as e:
        print(f"[Webhook Handler Error]: {e}")

    # Meta requires a 200 OK fast response to acknowledge receipt
    return jsonify({"status": "EVENT_RECEIVED"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Bhoomi-Raksha Server running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
