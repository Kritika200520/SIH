"""
Robo Raksha — Unit Tests for 5 Unique Patent Mechanisms
"""

import unittest
import json
from crypto_blackbox import CryptoBlackbox
from scoring_engine import ScoringEngine
from ai_vision_engine import AIVisionEngine
from app import app


class TestPatentMechanisms(unittest.TestCase):

    def setUp(self):
        self.blackbox = CryptoBlackbox()
        self.engine = ScoringEngine()
        self.ai = AIVisionEngine()

    def test_cryptographic_blackbox_merkle_chain(self):
        # Genesis block check
        self.assertTrue(self.blackbox.verify_chain_integrity())
        self.assertEqual(len(self.blackbox.chain), 1)

        # Append new event blocks
        b1 = self.blackbox.append_block("ACCIDENT_DETECTED", 92.5, {"lat": 12.9716, "lng": 77.5946})
        self.assertEqual(len(b1["hash"]), 64)  # Valid SHA-256 hex string
        self.assertEqual(b1["previous_hash"], self.blackbox.GENESIS_HASH)

        b2 = self.blackbox.append_block("POLICE_CONFIRMED", 92.5, {"lat": 12.9716, "lng": 77.5946})
        self.assertEqual(b2["previous_hash"], b1["hash"])

        # Entire chain must be mathematically valid
        self.assertTrue(self.blackbox.verify_chain_integrity())

    def test_multi_spectral_matrix_claim1(self):
        matrix = self.engine.compute_multi_spectral_matrix(
            ai_confidence=95.0,
            sound_db=92.0,
            distance_cm=30,
            flame_val=1
        )
        self.assertIn("fused_corroboration_index", matrix)
        self.assertGreater(matrix["fused_corroboration_index"], 65.0)
        self.assertTrue(matrix["is_corroborated"])

    def test_predictive_rssi_network_decay_claim2(self):
        # Test low RSSI triggers pre-caching
        effective_risk, should_cache = self.engine.calculate_rssi_network_risk(
            base_severity=90.0,
            elapsed_seconds=10,
            current_telemetry={"flame": 1, "sound": 85.0, "vibration": 0},
            wifi_rssi=15.0  # Degraded Wi-Fi
        )
        self.assertTrue(should_cache)
        self.assertGreater(effective_risk, 0.0)

    def test_dynamic_d3_geofence_claim3(self):
        d3 = self.engine.calculate_d3_geofence(severity_intensity=95.0, base_radius_km=5.0)
        self.assertGreaterEqual(d3["active_radius_km"], 5.0)
        self.assertIn("responders_in_range", d3)


class TestFullSystemEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.post("/api/reset")

    def test_patent_status_endpoint(self):
        res = self.client.get("/api/dashboard/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("multi_spectral_matrix", data)
        self.assertIn("crypto_ledger", data)
        self.assertIn("d3_perimeter", data)
        self.assertTrue(data["crypto_ledger"]["chain_valid"])

    def test_police_confirmation_mines_block(self):
        # 1. Trigger accident
        self.client.post("/api/scenario", json={"scenario": "accident"})
        
        # 2. Police confirms accident
        res = self.client.post("/api/dashboard/action", json={"action": "CONFIRM_ACCIDENT"})
        self.assertEqual(res.status_code, 200)
        
        # 3. Check that SHA-256 block was mined for confirmation
        status = self.client.get("/api/dashboard/status").get_json()
        self.assertEqual(status["state"], "POLICE_CONFIRMED")
        self.assertGreaterEqual(status["crypto_ledger"]["total_blocks_mined"], 2)


if __name__ == "__main__":
    unittest.main()
