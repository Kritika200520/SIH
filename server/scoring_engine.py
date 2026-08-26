"""
Robo Raksha — Severity Scoring & Patent Risk-Decay Engine
Module owned by Person 1 (The Builder).
"""

import math
import time
from typing import Dict, Any, Tuple


class ScoringEngine:
    """
    Computes real-time severity scores from raw sensor telemetry,
    evaluates emergency thresholds, and calculates patent risk-decay & re-scoring values.
    """

    # Scoring Weights (Weeks 1-2 Specification)
    FLAME_POINTS = 5
    SOUND_POINTS = 3
    NO_MOVEMENT_POINTS = 4

    # Thresholds
    SOUND_DB_THRESHOLD = 70.0
    EMERGENCY_SCORE_THRESHOLD = 7

    def __init__(self, threshold: float = 7.0, decay_lambda: float = 0.05):
        self.threshold = threshold
        self.decay_lambda = decay_lambda  # Risk decay rate parameter

    def compute_baseline_score(self, telemetry: Dict[str, Any]) -> Tuple[float, str]:
        """
        Calculates baseline severity score according to agreed rules:
        - Flame: +5 pts
        - Loud sound (>=70): +3 pts
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

        primary_event = events[0] if events else "none"
        if "fire" in events:
            primary_event = "fire"
        elif "loud_sound" in events and "no_movement" in events:
            primary_event = "person_down_or_distress"

        return score, primary_event

    def calculate_risk_decay(self, initial_severity: float, elapsed_seconds: float, current_telemetry: Dict[str, Any]) -> float:
        """
        [PATENT CORE NOVELTY MECHANISM - Week 6]
        Risk Decay & Live Re-scoring Formula:
        R(t) = S0 * e^(-lambda * t) + Delta_S_live

        If fire/sound persists or grows, Delta_S_live increases, counteracting decay or shortening timer.
        """
        live_score, _ = self.compute_baseline_score(current_telemetry)
        decayed_initial = initial_severity * math.exp(-self.decay_lambda * elapsed_seconds)
        adjusted_risk = max(live_score, decayed_initial)
        return round(adjusted_risk, 2)

    def calculate_timer_adjustment(self, current_severity: float, baseline_timer_seconds: int = 45) -> int:
        """
        [PATENT CORE NOVELTY MECHANISM]
        Shortens timer if severity spikes (e.g. score >= 12 -> 20 seconds remaining).
        """
        if current_severity >= 12:
            return 20
        elif current_severity >= 9:
            return 30
        return baseline_timer_seconds
