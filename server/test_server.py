"""
Robo Raksha — Unit Tests for AI Vision, Anti-False Alarm Filter & 5km SOS Escalation
"""

import unittest
import json
from ai_vision_engine import AIVisionEngine
from scoring_engine import ScoringEngine
from app import app


class TestAIVisionEngine(unittest.TestCase):

    def setUp(self):
        self.ai = AIVisionEngine(required_consecutive_frames=3)

    def test_normal_scene(self):
        res = self.ai.analyze_frame({"scenario": "normal"})
        self.assertFalse(res["detected"])
        self.assertFalse(res["anti_false_alarm_verified"])
        self.assertLess(res["intensity_score"], 10.0)

    def test_anti_false_alarm_temporal_buffer(self):
        # Frame 1: Detected but NOT yet verified
        f1 = self.ai.analyze_frame({"scenario": "accident"})
        self.assertTrue(f1["detected"])
        self.assertFalse(f1["anti_false_alarm_verified"])

        # Frame 2: Still validating
        f2 = self.ai.analyze_frame({"scenario": "accident"})
        self.assertTrue(f2["detected"])
        self.assertFalse(f2["anti_false_alarm_verified"])

        # Frame 3: 3rd consecutive frame -> VERIFIED!
        f3 = self.ai.analyze_frame({"scenario": "accident"})
        self.assertTrue(f3["detected"])
        self.assertTrue(f3["anti_false_alarm_verified"])
        self.assertGreater(f3["intensity_score"], 80.0)


class TestPoliceWorkflowAndEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.post("/api/reset")

    def test_dashboard_status_contract(self):
        res = self.client.get("/api/dashboard/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("ai_vision", data)
        self.assertIn("location", data)
        self.assertEqual(data["location"]["sos_radius_km"], 5.0)

    def test_police_confirmation_workflow(self):
        # 1. Trigger accident scenario -> AI detects and sets UNVERIFIED_ALERT
        self.client.post("/api/scenario", json={"scenario": "accident"})
        status = self.client.get("/api/dashboard/status").get_json()
        self.assertEqual(status["state"], "UNVERIFIED_ALERT")
        self.assertEqual(status["timer_seconds"], 0)  # Timer not started yet!

        # 2. Police clicks CONFIRM_ACCIDENT -> Starts 300s response countdown timer!
        confirm_res = self.client.post("/api/dashboard/action", json={"action": "CONFIRM_ACCIDENT"})
        self.assertEqual(confirm_res.status_code, 200)
        data = confirm_res.get_json()
        self.assertEqual(data["new_state"], "POLICE_CONFIRMED")
        self.assertEqual(data["timer_seconds"], 300)

        # Verify status endpoint reflects timer
        status = self.client.get("/api/dashboard/status").get_json()
        self.assertEqual(status["state"], "POLICE_CONFIRMED")
        self.assertEqual(status["timer_seconds"], 300)

    def test_police_mark_false_alarm(self):
        self.client.post("/api/scenario", json={"scenario": "accident"})
        action_res = self.client.post("/api/dashboard/action", json={"action": "FALSE_ALARM"})
        self.assertEqual(action_res.status_code, 200)
        self.assertEqual(action_res.get_json()["new_state"], "CANCELLED")


if __name__ == "__main__":
    unittest.main()
