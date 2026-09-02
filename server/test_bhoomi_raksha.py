# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha Integration Test Suite
Verifies VLM Ingestion, InSAR + GSI Fusion, Dialect Voice Generation, and API responses.
"""
import sys, os
sys.path.insert(0, os.path.abspath("server"))

import unittest
import json
from app import app, init_default_scenario

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
        print("? Test 1 Passed: /api/dashboard/status returned full telemetry")

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

    def test_03_dialect_broadcast(self):
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
        print("? Test 3 Passed: Multi-dialect voice broadcast synthesis verified")

    def test_04_citizen_report_submission(self):
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
        print("? Test 4 Passed: Crowdsourced multimodal citizen ingestion & VLM verified")

    def test_05_operator_actions(self):
        res = self.app.post("/api/action/operator",
                            data=json.dumps({"action": "CONFIRM_DISPATCH"}),
                            content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["state"], "DISPATCHED")
        print("? Test 5 Passed: Incident Command Dispatch verified")

if __name__ == "__main__":
    unittest.main()
