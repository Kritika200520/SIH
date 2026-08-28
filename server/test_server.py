"""
Robo Raksha — Integrated Multi-Role Unit Tests (Persons 1, 2, 3, 4)
Tests severity calculation, patent risk-decay, dynamic situation menus, scenario triggers, and API contracts.
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

    def test_fire_event_scoring(self):
        telemetry = {"flame": 1, "sound": 87.0, "vibration": 0, "distance_cm": 45}
        score, event = self.engine.compute_baseline_score(telemetry)
        self.assertEqual(score, 12.0)
        self.assertEqual(event, "fire")

    def test_person_down_scoring(self):
        telemetry = {"flame": 0, "sound": 95.0, "vibration": 0, "distance_cm": 90}
        score, event = self.engine.compute_baseline_score(telemetry)
        self.assertEqual(score, 7.0)
        self.assertEqual(event, "person_down_or_distress")

    def test_situation_specific_menu_generation(self):
        fire_menu = self.engine.get_situation_specific_menu("fire")
        self.assertIn("Dispatch Fire Dept", fire_menu)
        self.assertIn("Activate Suppressor", fire_menu)

        person_menu = self.engine.get_situation_specific_menu("person_down_or_distress")
        self.assertIn("Dispatch Paramedics", person_menu)
        self.assertIn("Activate Voice Beacon", person_menu)


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
        self.assertIn("options", data)
        self.assertIn("wifi_signal", data)

    def test_scenario_trigger_fire(self):
        res = self.client.post("/api/scenario", json={"scenario": "fire"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["state"], "ALERT")
        self.assertEqual(data["severity"], 12.0)

        # Verify status endpoint reflects fire scenario and patent menu options
        status = self.client.get("/api/dashboard/status").get_json()
        self.assertEqual(status["event"], "fire")
        self.assertIn("Dispatch Fire Dept", status["options"])

    def test_scenario_trigger_wifi_loss(self):
        res = self.client.post("/api/scenario", json={"scenario": "wifi_loss"})
        self.assertEqual(res.status_code, 200)
        status = self.client.get("/api/dashboard/status").get_json()
        self.assertLess(status["wifi_signal"], 30)

    def test_operator_dispatch_action(self):
        self.client.post("/api/scenario", json={"scenario": "fire"})
        action_res = self.client.post("/api/dashboard/action", json={"action": "Dispatch Fire Dept"})
        self.assertEqual(action_res.status_code, 200)
        self.assertEqual(action_res.get_json()["new_state"], "DISPATCHED")


if __name__ == "__main__":
    unittest.main()
