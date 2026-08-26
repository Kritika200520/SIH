"""
Robo Raksha — Unit Tests for Person 1 (Server Builder)
Tests severity calculation, risk decay, state machine transitions, and API contracts.
"""

import unittest
import json
from scoring_engine import ScoringEngine
from app import app


class TestScoringEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ScoringEngine(threshold=7.0)

    def test_normal_telemetry(self):
        telemetry = {"flame": 0, "sound": 40.0, "vibration": 1, "distance_cm": 100}
        score, event = self.engine.compute_baseline_score(telemetry)
        self.assertEqual(score, 0.0)
        self.assertEqual(event, "none")

    def test_flame_only(self):
        telemetry = {"flame": 1, "sound": 40.0, "vibration": 1, "distance_cm": 100}
        score, event = self.engine.compute_baseline_score(telemetry)
        self.assertEqual(score, 5.0)
        self.assertEqual(event, "fire")

    def test_fire_sound_no_movement(self):
        telemetry = {"flame": 1, "sound": 87.0, "vibration": 0, "distance_cm": 45}
        score, event = self.engine.compute_baseline_score(telemetry)
        self.assertEqual(score, 12.0)  # 5 + 3 + 4
        self.assertEqual(event, "fire")

    def test_sound_and_no_movement(self):
        telemetry = {"flame": 0, "sound": 85.0, "vibration": 0, "distance_cm": 80}
        score, event = self.engine.compute_baseline_score(telemetry)
        self.assertEqual(score, 7.0)  # 3 + 4
        self.assertEqual(event, "person_down_or_distress")

    def test_risk_decay(self):
        telemetry = {"flame": 0, "sound": 40.0, "vibration": 1, "distance_cm": 100}
        decayed = self.engine.calculate_risk_decay(initial_severity=10.0, elapsed_seconds=10.0, current_telemetry=telemetry)
        self.assertLess(decayed, 10.0)


class TestServerEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.post("/api/reset")

    def test_dashboard_status_contract(self):
        res = self.client.get("/api/dashboard/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("state", data)
        self.assertIn("event", data)
        self.assertIn("severity", data)
        self.assertIn("clip_url", data)
        self.assertIn("timer_seconds", data)
        self.assertIn("options", data)

    def test_telemetry_triggers_alert(self):
        # Send normal
        self.client.post("/api/telemetry", json={"flame": 0, "sound": 30, "vibration": 1, "distance_cm": 100})
        status_res = self.client.get("/api/dashboard/status").get_json()
        self.assertEqual(status_res["state"], "NORMAL")

        # Send emergency payload (flame=1, sound=85, vibration=0 -> score 12)
        res = self.client.post("/api/telemetry", json={"flame": 1, "sound": 85, "vibration": 0, "distance_cm": 45})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["state"], "ALERT")
        self.assertGreaterEqual(data["severity"], 7.0)

        # Check status endpoint
        status_res = self.client.get("/api/dashboard/status").get_json()
        self.assertEqual(status_res["state"], "ALERT")
        self.assertGreater(status_res["timer_seconds"], 0)

    def test_operator_false_alarm_action(self):
        # Trigger emergency
        self.client.post("/api/telemetry", json={"flame": 1, "sound": 85, "vibration": 0, "distance_cm": 45})
        
        # Click False Alarm
        action_res = self.client.post("/api/dashboard/action", json={"action": "False alarm"})
        self.assertEqual(action_res.status_code, 200)
        self.assertEqual(action_res.get_json()["new_state"], "CANCELLED")

        # Verify status endpoint returns CANCELLED
        status = self.client.get("/api/dashboard/status").get_json()
        self.assertEqual(status["state"], "CANCELLED")


if __name__ == "__main__":
    unittest.main()
