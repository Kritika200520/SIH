# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: Risk Fusion & Threat Verification Scoring Engine
Combines VLM Vision Depth, InSAR Satellite Radar Shift, GSI Geotechnical Fs, and IMD Rainfall.
"""
import time, math

class RiskScoringEngine:
    def __init__(self):
        self.state = "NORMAL"
        self.severity_score = 0
        self.alert_level = "SAFE"
        self.timer_seconds = 300
        self.timer_active = False
        self.last_update = time.time()
        self.latest_telemetry = {}
        self.event_log = [
            {"time": "00:00:01", "event": "BHOOMI-RAKSHA GEOTECHNICAL MONITORING ONLINE", "type": "INFO"}
        ]

    def compute_composite_risk(self, vlm_data, insar_disp_mm, fs_data, rainfall_24h_mm, cluster_count=1):
        """
        Multi-Factor Threat Index (0 - 100):
        - VLM Crack Depth & Turbidity: 30%
        - InSAR Satellite Displacement: 25%
        - Geotechnical Slope Fs (Inverted): 25%
        - IMD 24h Cumulative Rainfall: 20%
        - Multi-report cluster multiplier
        """
        # 1. VLM Component (0 - 100)
        crack_depth = vlm_data.get("fissure_depth_cm", 0.0)
        turbidity = vlm_data.get("turbidity_index_pct", 0.0)
        tilt = vlm_data.get("vegetation_tilt_deg", 0.0)
        
        vlm_score = min(100.0, (crack_depth / 10.0) * 50.0 + (turbidity / 100.0) * 30.0 + (tilt / 25.0) * 20.0)
        
        # 2. InSAR Component (0 - 100)
        insar_score = min(100.0, (insar_disp_mm / 20.0) * 100.0)
        
        # 3. Geotechnical Slope Fs Component
        # Fs = 1.0 is critical (100 risk), Fs >= 2.0 is safe (0 risk)
        fs = fs_data.get("safety_factor_fs", 1.8)
        if fs <= 0.8:
            fs_score = 100.0
        elif fs <= 1.0:
            fs_score = 90.0
        elif fs <= 1.3:
            fs_score = 65.0
        elif fs <= 1.6:
            fs_score = 30.0
        else:
            fs_score = 10.0
            
        # 4. Rainfall Component (0 - 100)
        rainfall_score = min(100.0, (rainfall_24h_mm / 100.0) * 100.0)
        
        # Weighted Fusion
        composite = (0.30 * vlm_score) + (0.25 * insar_score) + (0.25 * fs_score) + (0.20 * rainfall_score)
        
        # Cluster Multiplier (Corroborating Crowdsourced Reports within 500m)
        if cluster_count >= 3:
            composite = min(100.0, composite * 1.15)
        elif cluster_count == 2:
            composite = min(100.0, composite * 1.08)
            
        final_score = round(composite, 1)
        
        # Determine Threat Classification
        if final_score >= 70.0:
            status = "CRITICAL_EMERGENCY"
            verification = "VERIFIED_MULTI_FACTOR_IMMINENT"
        elif final_score >= 45.0:
            status = "ELEVATED_WATCH"
            verification = "CORROBORATING_ANOMALIES_DETECTED"
        else:
            status = "NORMAL_SAFE"
            verification = "WITHIN_NOMINAL_BASELINES"
            
        return {
            "composite_risk_score": final_score,
            "status": status,
            "verification_status": verification,
            "breakdown": {
                "vlm_vision_score": round(vlm_score, 1),
                "insar_radar_score": round(insar_score, 1),
                "geotechnical_fs_score": round(fs_score, 1),
                "imd_rainfall_score": round(rainfall_score, 1),
                "spatial_cluster_reports": cluster_count
            }
        }

    def add_log(self, event_text, event_type="INFO"):
        curr_time = time.strftime("%H:%M:%S")
        self.event_log.insert(0, {
            "time": curr_time,
            "event": event_text,
            "type": event_type
        })
        if len(self.event_log) > 25:
            self.event_log.pop()

scoring_engine = RiskScoringEngine()
