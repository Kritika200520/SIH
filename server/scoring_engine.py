"""
Robo Raksha — Enhanced Severity Scoring & Patent Risk-Decay Engine
Module owned by Person 1 (The Builder).
"""

import math
import time
from typing import Dict, Any, Tuple, List


class ScoringEngine:
    """
    Computes real-time severity scores from raw sensor telemetry,
    evaluates emergency thresholds, calculates patent risk-decay & live re-scoring values,
    and generates situation-specific action menus.
    """

    # Scoring Weights (Agreed Contract Rules)
    FLAME_POINTS = 5
    SOUND_POINTS = 3
    NO_MOVEMENT_POINTS = 4

    # Thresholds
    SOUND_DB_THRESHOLD = 70.0
    EMERGENCY_SCORE_THRESHOLD = 7.0

    def __init__(self, threshold: float = 7.0, decay_lambda: float = 0.05):
        self.threshold = threshold
        self.decay_lambda = decay_lambda

    def compute_baseline_score(self, telemetry: Dict[str, Any]) -> Tuple[float, str]:
        """
        Calculates baseline severity score:
        - Flame: +5 pts
        - Loud sound (>=70dB): +3 pts
        - No movement/vibration (vibration == 0): +4 pts
        Returns: (score, primary_event_type)
        """
        flame = int(telemetry.get("flame", 0))
        sound = float(telemetry.get("sound", 0))
        vibration = int(telemetry.get("vibration", 0))

        score = 0.0
        events = []

        if flame > 0:
            score += self.FLAME_POINTS
            events.append("fire")

        if sound >= self.SOUND_DB_THRESHOLD:
            score += self.SOUND_POINTS
            events.append("loud_sound")

        if vibration == 0:
            score += self.NO_MOVEMENT_POINTS
            events.append("no_movement")

        primary_event = "none"
        if "fire" in events:
            primary_event = "fire"
        elif "loud_sound" in events and "no_movement" in events:
            primary_event = "person_down_or_distress"
        elif "loud_sound" in events:
            primary_event = "acoustic_anomaly"
        elif "no_movement" in events and len(events) > 1:
            primary_event = "stationary_hazard"

        return score, primary_event

    def calculate_risk_decay(self, initial_severity: float, elapsed_seconds: float, current_telemetry: Dict[str, Any]) -> float:
        """
        [PATENT NOVELTY MECHANISM]
        Risk Decay & Live Re-scoring Formula:
        R(t) = S0 * e^(-lambda * t) + Delta_S_live
        """
        live_score, _ = self.compute_baseline_score(current_telemetry)
        decayed_initial = initial_severity * math.exp(-self.decay_lambda * elapsed_seconds)
        adjusted_risk = max(live_score, round(decayed_initial, 2))
        return float(adjusted_risk)

    def calculate_timer_adjustment(self, current_severity: float, baseline_timer_seconds: int = 45) -> int:
        """
        [PATENT NOVELTY MECHANISM]
        Shortens timer if severity spikes.
        """
        if current_severity >= 12:
            return 20
        elif current_severity >= 9:
            return 30
        return baseline_timer_seconds

    def get_situation_specific_menu(self, event_type: str) -> List[str]:
        """
        [PATENT NOVELTY MECHANISM]
        Generates situation-specific intervention menu options tailored to hazard type.
        """
        if event_type == "fire":
            return [
                "Dispatch Fire Dept",
                "Activate Suppressor",
                "Investigate (+30s)",
                "False Alarm"
            ]
        elif event_type == "person_down_or_distress":
            return [
                "Dispatch Paramedics",
                "Activate Voice Beacon",
                "Investigate (+30s)",
                "False Alarm"
            ]
        elif event_type == "acoustic_anomaly":
            return [
                "Dispatch Security",
                "Play Audio Warning",
                "Investigate (+30s)",
                "False Alarm"
            ]
        return [
            "Dispatch Emergency Services",
            "Investigate (+30s)",
            "False Alarm"
        ]
