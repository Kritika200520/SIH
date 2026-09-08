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
        print("[OK] Test 1 Passed: /api/dashboard/status returned full telemetry & routing")

    def test_02_scenario_switching(self):
        scenarios = ["chamoli_fissure", "darjeeling_fissure", "shimla_subsidence", "false_alarm_normal"]
        for sc in scenarios:
            res = self.app.post("/api/scenario/trigger", 
                                data=json.dumps({"scenario_id": sc}),
                                content_type="application/json")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
        print("[OK] Test 2 Passed: All 4 disaster & calibration scenarios verified")

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
        print("[OK] Test 3 Passed: Dynamic Pathfinding & Hazard Cost Surface Algorithm verified")

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
        print("[OK] Test 4 Passed: Multi-dialect voice broadcast synthesis verified")

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
        print("[OK] Test 5 Passed: Crowdsourced multimodal citizen ingestion & VLM verified")

    def test_06_ai_spam_and_authenticity_protocol(self):
        # 1. Test Authentic field capture passes with >= 85% score
        res_auth = self.app.post("/api/spam-filter/verify",
                                 data=json.dumps({"preset_key": "live_authentic_field"}),
                                 content_type="application/json")
        self.assertEqual(res_auth.status_code, 200)
        auth_data = res_auth.get_json()["verification"]
        self.assertEqual(auth_data["verification_status"], "VERIFIED_AUTHENTIC")
        self.assertGreaterEqual(auth_data["composite_trust_score"], 85.0)

        # 2. Test Recycled stock photo duplicate is blocked
        res_stock = self.app.post("/api/spam-filter/verify",
                                  data=json.dumps({"preset_key": "recycled_stock_spam"}),
                                  content_type="application/json")
        self.assertEqual(res_stock.status_code, 200)
        stock_data = res_stock.get_json()["verification"]
        self.assertEqual(stock_data["verification_status"], "REJECTED_SPAM")
        self.assertTrue(stock_data["authenticity_check"]["duplicate_detected"])

        # 3. Test Off-site GPS spoof hoax is blocked
        res_spoof = self.app.post("/api/spam-filter/verify",
                                  data=json.dumps({"preset_key": "gps_spoof_hoax"}),
                                  content_type="application/json")
        self.assertEqual(res_spoof.status_code, 200)
        spoof_data = res_spoof.get_json()["verification"]
        self.assertEqual(spoof_data["verification_status"], "REJECTED_SPAM")

        # 4. Test Digital Manipulation / Photoshop signature is blocked
        res_fake = self.app.post("/api/spam-filter/verify",
                                 data=json.dumps({"preset_key": "manipulated_photoshop_fake"}),
                                 content_type="application/json")
        self.assertEqual(res_fake.status_code, 200)
        fake_data = res_fake.get_json()["verification"]
        self.assertEqual(fake_data["verification_status"], "REJECTED_SPAM")
        print("[OK] Test 6 Passed: AI Hallucination & Anti-Spam Protocol verified (EXIF, dHash, ELA, Cell Tower)")

if __name__ == "__main__":
    unittest.main()
