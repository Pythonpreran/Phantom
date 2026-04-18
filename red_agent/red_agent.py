"""
PHANTOM Module 7  --  Red Agent Adversarial Simulation
=====================================================
Live adversarial coroutine that launches attacks against the PHANTOM pipeline.
Tracks success/failure rate and feeds the SOC dashboard scoreboard.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Optional

from red_agent.attack_patterns import ATTACK_CATALOG


@dataclass
class RedAgentStats:
    """Tracks Red Agent performance."""
    launched: int = 0
    caught: int = 0
    missed: int = 0
    delta_caught: int = 0
    delta_missed: int = 0
    attack_log: list = field(default_factory=list)

    @property
    def detection_rate(self) -> float:
        if self.launched == 0:
            return 0.0
        return self.caught / self.launched

    @property
    def evasion_rate(self) -> float:
        return 1.0 - self.detection_rate


class RedAgent:
    """
    Adversarial simulation engine.
    Launches diverse attack patterns and tracks PHANTOM's detection rate.
    """

    def __init__(self):
        self.stats = RedAgentStats()
        self.attack_types = list(ATTACK_CATALOG.keys())

    def launch_attack(self, attack_type: str = None) -> list:
        """
        Launch an attack and return the generated events.
        The dashboard pipeline will process these events through PHANTOM.
        """
        if attack_type is None:
            attack_type = random.choice(self.attack_types)

        attack_info = ATTACK_CATALOG.get(attack_type)
        if not attack_info:
            return []

        self.stats.launched += 1
        attacker_ip = f"10.0.0.{random.randint(100, 254)}"

        # Generate attack events
        if attack_info["needs_ip"]:
            events = attack_info["fn"](ip=attacker_ip)
        else:
            events = attack_info["fn"]()

        # Log the attack
        self.stats.attack_log.append({
            "attack_num": self.stats.launched,
            "type": attack_type,
            "description": attack_info["description"],
            "ip": attacker_ip if attack_info["needs_ip"] else "distributed",
            "event_count": len(events),
            "timestamp": time.strftime("%H:%M:%S"),
            "expected_catch": attack_info["expected_catch"],
            "result": "pending",
        })

        return events

    def report_outcome(self, attack_index: int, was_caught: bool):
        """Called by PHANTOM's detection pipeline after each verdict."""
        if was_caught:
            self.stats.caught += 1
            self.stats.delta_caught = 1
            self.stats.delta_missed = 0
        else:
            self.stats.missed += 1
            self.stats.delta_caught = 0
            self.stats.delta_missed = 1

        # Update attack log
        if 0 <= attack_index < len(self.stats.attack_log):
            self.stats.attack_log[attack_index]["result"] = "CAUGHT" if was_caught else "EVADED"

    def get_recent_attacks(self, n: int = 10) -> list:
        """Return last N attacks for display."""
        return self.stats.attack_log[-n:]

    def get_stats_dict(self) -> dict:
        return {
            "launched": self.stats.launched,
            "caught": self.stats.caught,
            "missed": self.stats.missed,
            "detection_rate": self.stats.detection_rate,
            "evasion_rate": self.stats.evasion_rate,
            "delta_caught": self.stats.delta_caught,
        }
