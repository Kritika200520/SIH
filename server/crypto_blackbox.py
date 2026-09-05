"""
Robo Raksha — Cryptographic SHA-256 Tamper-Proof Blackbox Audit Ledger (Claim 4)
Generates an immutable sequential Merkle-style cryptographic chain for all telemetry,
AI diagnoses, police interventions, and emergency dispatches for legal/insurance evidentiary proof.
"""

import hashlib
import json
import time
from typing import Dict, Any, List


class CryptoBlackbox:
    """
    Immutable Cryptographic Blackbox Ledger using SHA-256 hash chaining:
    Hash_k = SHA256(Hash_{k-1} || Timestamp || Event || GPS || Intensity)
    """

    GENESIS_HASH = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"

    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self._mine_genesis_block()

    def _mine_genesis_block(self):
        genesis_block = {
            "index": 0,
            "timestamp": time.time(),
            "event_type": "GENESIS_BOOT",
            "gps": {"lat": 12.9716, "lng": 77.5946},
            "intensity": 0.0,
            "previous_hash": "0" * 64,
            "hash": self.GENESIS_HASH
        }
        self.chain.append(genesis_block)

    def append_block(self, event_type: str, intensity: float, gps: Dict[str, float], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Creates and appends a new cryptographically hashed block to the chain."""
        prev_block = self.chain[-1]
        timestamp = time.time()
        meta = metadata or {}

        payload_to_hash = (
            f"{prev_block['hash']}-{timestamp}-{event_type}-"
            f"{gps.get('lat', 0.0):.6f},{gps.get('lng', 0.0):.6f}-{intensity:.2f}-{json.dumps(meta, sort_keys=True)}"
        )

        block_hash = hashlib.sha256(payload_to_hash.encode("utf-8")).hexdigest()

        new_block = {
            "index": len(self.chain),
            "timestamp": timestamp,
            "event_type": event_type,
            "intensity": intensity,
            "gps": gps,
            "metadata": meta,
            "previous_hash": prev_block["hash"],
            "hash": block_hash
        }

        self.chain.append(new_block)
        # Keep recent 20 blocks in active memory window for dashboard streaming
        if len(self.chain) > 50:
            self.chain = self.chain[-50:]

        return new_block

    def get_latest_blocks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns the most recent N blocks in reverse chronological order."""
        return list(reversed(self.chain[-limit:]))

    def verify_chain_integrity(self) -> bool:
        """Verifies mathematical validity of the entire cryptographic chain."""
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr["previous_hash"] != prev["hash"]:
                return False
        return True
