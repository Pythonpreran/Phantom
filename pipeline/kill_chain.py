"""
PHANTOM Module 4  --  Kill Chain State Machine
=============================================
Tracks per-identity attack progression through the cyber kill chain.
Maps each stage to MITRE ATT&CK techniques.

Enhancements:
- Identity-based tracking (IP + user_id composite key)
- Multi-network lateral movement detection across zones/VLANs
"""

from enum import IntEnum
from datetime import datetime, timezone


class KillChainStage(IntEnum):
    CLEAN            = 0
    RECON            = 1
    INITIAL_ACCESS   = 2
    EXECUTION        = 3
    LATERAL_MOVEMENT = 4
    EXFILTRATION     = 5


MITRE_MAP = {
    0: {"id": " -- ",     "name": "Clean / No Threat"},
    1: {"id": "T1595", "name": "Active Scanning (Reconnaissance)"},
    2: {"id": "T1110", "name": "Brute Force (Initial Access)"},
    3: {"id": "T1059", "name": "Command & Scripting Interpreter (Execution)"},
    4: {"id": "T1021", "name": "Remote Services (Lateral Movement)"},
    5: {"id": "T1041", "name": "Exfiltration Over C2 Channel"},
}

SEVERITY_MAP = {
    0: "NONE",
    1: "LOW",
    2: "LOW",
    3: "MEDIUM",
    4: "HIGH",
    5: "CRITICAL",
}

# Internal subnets for cross-network lateral movement detection
INTERNAL_SUBNETS = ["10.0.0", "10.0.1", "172.16.0", "192.168.1", "192.168.2"]


class KillChainTracker:
    """
    Maintains per-identity state machines tracking kill chain progression.
    Identity key: IP::user_id (not just IP).
    """

    def __init__(self):
        # identity_key → state record
        self.identity_state: dict = {}
        self.total_escalations = 0

    def _identity_key(self, event: dict) -> str:
        ip = event.get("source_ip", "unknown")
        identity = event.get("identity", {})
        user_id = identity.get("user_id", "unknown")
        return f"{ip}::{user_id}"

    def update(self, event: dict, fusion_result: dict = None) -> dict:
        """
        Analyze event, infer kill chain stage, update state machine.
        Returns full state for this identity including MITRE mapping + history.
        """
        identity_key = self._identity_key(event)
        detected_stage = self.infer_stage_from_event(event)

        if identity_key not in self.identity_state:
            self.identity_state[identity_key] = {
                "stage": KillChainStage.CLEAN,
                "history": [],
                "first_seen": event.get("timestamp", ""),
                "last_seen": event.get("timestamp", ""),
                "source_ip": event.get("source_ip", ""),
                "identity": event.get("identity", {}),
                "zones_seen": set(),
            }

        record = self.identity_state[identity_key]
        record["last_seen"] = event.get("timestamp", "")

        # Track multi-network movement
        zone = event.get("network_zone", {}).get("zone", "unknown")
        if isinstance(record["zones_seen"], set):
            record["zones_seen"].add(zone)
        else:
            record["zones_seen"] = {zone}

        # Detect cross-zone lateral movement
        if len(record["zones_seen"]) >= 2 and detected_stage < KillChainStage.LATERAL_MOVEMENT:
            # Entity appeared in multiple network zones  --  upgrade to lateral movement
            detected_stage = KillChainStage.LATERAL_MOVEMENT

        # Kill chain only moves forward, never backward
        if detected_stage > record["stage"]:
            self.total_escalations += 1
            record["stage"] = detected_stage
            mitre = MITRE_MAP[detected_stage.value]

            record["history"].append({
                "stage": detected_stage.name,
                "stage_num": detected_stage.value,
                "timestamp": event.get("timestamp", ""),
                "mitre_id": mitre["id"],
                "mitre_name": mitre["name"],
                "source_ip": event.get("source_ip", ""),
                "layer": event.get("layer", ""),
                "zones": list(record["zones_seen"]) if isinstance(record["zones_seen"], set) else [],
            })

        severity = SEVERITY_MAP[record["stage"].value]

        return {
            "identity_key": identity_key,
            "ip": event.get("source_ip", ""),
            "user_id": event.get("identity", {}).get("user_id", "unknown"),
            "current_stage": record["stage"].name,
            "stage_num": record["stage"].value,
            "severity": severity,
            "mitre_id": MITRE_MAP[record["stage"].value]["id"],
            "mitre_name": MITRE_MAP[record["stage"].value]["name"],
            "history": record["history"],
            "first_seen": record["first_seen"],
            "last_seen": record["last_seen"],
            "zones_traversed": list(record["zones_seen"]) if isinstance(record["zones_seen"], set) else [],
        }

    def infer_stage_from_event(self, event: dict) -> KillChainStage:
        """Heuristic classifier: maps event signals to a kill chain stage."""
        raw = event.get("raw_features", {})

        # Exfiltration: massive outbound to foreign destination
        bytes_out = raw.get("bytes_out", 0)
        geo = raw.get("geo_country", "IN")
        if bytes_out > 10_000_000 and geo not in ["IN", "US", "GB", "DE", "JP"]:
            return KillChainStage.EXFILTRATION

        # Large bytes_out to external (even domestic) is suspicious above 50MB
        if bytes_out > 50_000_000:
            return KillChainStage.EXFILTRATION

        # Lateral movement: hitting internal IPs on admin ports
        dst_ip = raw.get("dst_ip", "")
        dst_port = raw.get("dst_port", 80)
        is_internal_dst = any(dst_ip.startswith(s) for s in INTERNAL_SUBNETS)
        if is_internal_dst and dst_port in [445, 3389, 22, 5985, 5986]:
            return KillChainStage.LATERAL_MOVEMENT

        # Cross-zone movement detection
        process = raw.get("process_name", "")
        if process in ["psexec.exe", "wmic.exe"]:
            return KillChainStage.LATERAL_MOVEMENT

        # Execution: suspicious process spawning
        if process in ["cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe",
                        "rundll32.exe", "mshta.exe", "regsvr32.exe"]:
            return KillChainStage.EXECUTION

        # Initial Access: brute force pattern
        status = raw.get("status_code", 200)
        if status == 401:
            return KillChainStage.INITIAL_ACCESS

        # Recon: wide port scanning
        if dst_port > 10000 and raw.get("duration", 1) < 0.05:
            return KillChainStage.RECON

        # High connection rate to diverse IPs  
        conn_count = raw.get("conn_count", 0)
        if conn_count > 50:
            return KillChainStage.RECON

        return KillChainStage.CLEAN

    def get_active_threats(self, min_stage: int = 1) -> list:
        """Return all identities at or above a given kill chain stage."""
        threats = []
        for key, record in self.identity_state.items():
            if record["stage"].value >= min_stage:
                mitre = MITRE_MAP[record["stage"].value]
                threats.append({
                    "identity_key": key,
                    "ip": record.get("source_ip", ""),
                    "stage": record["stage"].name,
                    "stage_num": record["stage"].value,
                    "severity": SEVERITY_MAP[record["stage"].value],
                    "mitre_id": mitre["id"],
                    "history": record["history"],
                    "zones": list(record["zones_seen"]) if isinstance(record["zones_seen"], set) else [],
                })
        return sorted(threats, key=lambda x: x["stage_num"], reverse=True)

    def get_stats(self) -> dict:
        stages = {}
        for record in self.identity_state.values():
            name = record["stage"].name
            stages[name] = stages.get(name, 0) + 1
        return {
            "total_identities_tracked": len(self.identity_state),
            "total_escalations": self.total_escalations,
            "stage_distribution": stages,
        }
