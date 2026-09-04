# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha Integration Test Suite
Verifies VLM Ingestion, InSAR + GSI Fusion, Dynamic Routing Engine, Dialect Voice Generation, and API responses.
"""
import sys, os
sys.path.insert(0, os.path.abspath("server"))

import unittest
import json
from app import app, init_default_scenario
from routing_engine import routing_engine

class TestBhoomiRakshaSystem(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_dashboard_status(self):
        res = self.app.get("/api/dashboard/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("telemetry", data)
        self.assertIn("vlm", data["telemetry"])
        self.assertIn("geotechnical_fs", data["telemetry"])
        self.assertIn("dynamic_routing", data["telemetry"])
        print("? Test 1 Passed: /api/dashboard/status returned full telemetry & routing")

    def test_02_scenario_switching(self):
        scenarios = ["chamoli_fissure", "wayanad_flood", "shimla_subsidence", "false_alarm_normal"]
        for sc in scenarios:
            res = self.app.post("/api/scenario/trigger", 
                                data=json.dumps({"scenario_id": sc}),
                                content_type="application/json")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
        print("? Test 2 Passed: All 4 disaster & calibration scenarios verified")

    def test_03_dynamic_hazard_routing_engine(self):
        # Chamoli with 8.4cm fissure
        routes = routing_engine.compute_evacuation_routes(sector_id="chamoli_joshimath", vlm_depth_cm=8.4, turbidity_pct=45.0)
        self.assertIn("google_maps_naive", routes)
        self.assertIn("bhoomi_raksha_safe", routes)
        
        # Verify Google Maps Naive hits hazard
        self.assertEqual(routes["google_maps_naive"]["hazard_exposure_pct"], 95.0)
        # Verify Bhoomi-Raksha Safe Route has 0% hazard
        self.assertEqual(routes["bhoomi_raksha_safe"]["hazard_exposure_pct"], 0.0)
        self.assertTrue(len(routes["bhoomi_raksha_safe"]["waypoints"]) > 1)
        print("? Test 3 Passed: Dynamic Pathfinding & Hazard Cost Surface Algorithm verified")

    def test_04_dialect_broadcast(self):
        dialects = ["Garhwali", "Malayalam", "Pahari", "Nepali", "Hindi", "English"]
        for d in dialects:
            res = self.app.post("/api/broadcast/generate",
                                data=json.dumps({"dialect": d}),
                                content_type="application/json")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertIn("speech_script", data["broadcast"])
            self.assertIn("evacuation_route", data["broadcast"])
        print("? Test 4 Passed: Multi-dialect voice broadcast synthesis verified")

    def test_05_citizen_report_submission(self):
        report_payload = {
            "location": "Joshimath Upper Ward 4",
            "voice_memo": "Road cracks are widening rapidly after heavy rain.",
            "reporter_name": "Gram Pradhan",
            "image_base64": "fake_base64_data"
        }
        res = self.app.post("/api/citizen/report",
                            data=json.dumps(report_payload),
                            content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("vlm_result", data)
        self.assertEqual(data["vlm_result"]["hazard_classification"], "CRITICAL_TENSION_SCARP")
        print("? Test 5 Passed: Crowdsourced multimodal citizen ingestion & VLM verified")

if __name__ == "__main__":
    unittest.main()
