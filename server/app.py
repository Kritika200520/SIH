# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: Central Flask Server & SIH API Controller
Disaster Management: Landslide & Flash-Flood Early Warning System
"""
import os, time, json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from geo_rag import geo_rag_engine
from vlm_engine import vlm_engine
from broadcast_agent import broadcast_agent
from scoring_engine import scoring_engine
from routing_engine import routing_engine
from spam_filter import spam_filter_engine

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
    "last_spam_check": None
}

def init_default_scenario(scenario_key="chamoli_fissure"):
    vlm_data = vlm_engine.analyze_image(preset_key=scenario_key)
    sector_profile = geo_rag_engine.profiles.get(vlm_data.get("sector_id", "chamoli_joshimath"))
    
    # InSAR and Rainfall for Scenario
    if scenario_key == "chamoli_fissure":
        insar_disp = 14.8
        rainfall_24h = 78.5
        slope_angle = 38.0
        cluster_n = 4
    elif scenario_key == "wayanad_flood":
        insar_disp = 18.6
        rainfall_24h = 145.0
        slope_angle = 34.5
        cluster_n = 7
    elif scenario_key == "shimla_subsidence":
        insar_disp = 11.5
        rainfall_24h = 92.0
        slope_angle = 42.0
        cluster_n = 3
    else: # False alarm
        insar_disp = 0.5
        rainfall_24h = 12.0
        slope_angle = 18.0
        cluster_n = 1

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
        "spam_filter": spam_verif
    }
    
    scoring_engine.add_log(f"Scenario Activated: {vlm_data['title']} (Risk: {scoring_engine.severity_score}%)", "ALERT" if scoring_engine.severity_score >= 65 else "INFO")

# Initialize default state on startup
init_default_scenario("chamoli_fissure")

@app.route("/")
def serve_dashboard():
    return send_from_directory("../dashboard", "index.html")

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
        "spam_filter_presets": spam_filter_engine.get_test_presets()
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Bhoomi-Raksha Server running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
