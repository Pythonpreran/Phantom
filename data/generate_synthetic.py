"""
PHANTOM Module 1  --  Synthetic Data Generator
=============================================
Faker-based async generators for Network, Application, and Endpoint logs.
Supports attack injection modes and CSV export for pretraining.

Enhancements:
- Identity-based tracking: user_id + session_id per event (not just IP)
- Multi-network awareness: events across multiple subnets/VLANs
"""

import asyncio
import random
import csv
import os
from uuid import uuid4
from datetime import datetime, timezone
from faker import Faker

fake = Faker()

# ─── Multi-Network Zones ───────────────────────────────────────────────────────
NETWORK_ZONES = {
    "dmz":       {"subnet": "172.16.0", "vlan": 10,  "trust": "low"},
    "internal":  {"subnet": "10.0.0",   "vlan": 20,  "trust": "high"},
    "servers":   {"subnet": "10.0.1",   "vlan": 30,  "trust": "critical"},
    "iot":       {"subnet": "192.168.1","vlan": 40,  "trust": "untrusted"},
    "guest":     {"subnet": "192.168.2","vlan": 50,  "trust": "untrusted"},
}

# ─── Identity Registry (persistent user/session tracking) ──────────────────────
KNOWN_USERS = [
    {"user_id": f"user_{i:03d}", "role": r, "department": d}
    for i, (r, d) in enumerate([
        ("admin",    "IT"),      ("analyst",  "SOC"),
        ("engineer", "DevOps"),  ("manager",  "Finance"),
        ("intern",   "HR"),      ("svc_acct", "System"),
        ("admin",    "NetOps"),  ("analyst",  "Security"),
        ("engineer", "Backend"), ("manager",  "Legal"),
    ])
]

ACTIVE_SESSIONS = {}  # ip → {user_id, session_id, start_time}


def get_zone_ip(zone_name: str = None) -> str:
    """Generate an IP from a specific network zone."""
    if zone_name is None:
        zone_name = random.choice(list(NETWORK_ZONES.keys()))
    zone = NETWORK_ZONES[zone_name]
    return f"{zone['subnet']}.{random.randint(1, 254)}"


def get_or_create_session(ip: str) -> dict:
    """Identity-based tracking: maintain persistent sessions per IP."""
    if ip not in ACTIVE_SESSIONS or random.random() < 0.05:  # 5% new session
        user = random.choice(KNOWN_USERS)
        ACTIVE_SESSIONS[ip] = {
            "user_id": user["user_id"],
            "session_id": str(uuid4())[:8],
            "role": user["role"],
            "department": user["department"],
            "start_time": datetime.now(timezone.utc).isoformat(),
        }
    return ACTIVE_SESSIONS[ip]


def classify_network_zone(ip: str) -> dict:
    """Multi-network awareness: classify IP into zone with trust level."""
    for zone_name, zone_info in NETWORK_ZONES.items():
        if ip.startswith(zone_info["subnet"]):
            return {"zone": zone_name, "vlan": zone_info["vlan"], "trust": zone_info["trust"]}
    return {"zone": "external", "vlan": 0, "trust": "untrusted"}


# ─── Benign Event Generators ───────────────────────────────────────────────────

def generate_network_event(src_ip: str = None, **overrides) -> dict:
    """Generate a single network-layer event."""
    if src_ip is None:
        src_ip = get_zone_ip(random.choice(["internal", "servers", "dmz"]))
    session = get_or_create_session(src_ip)
    zone_info = classify_network_zone(src_ip)

    raw = {
        "src_ip": src_ip,
        "dst_ip": fake.ipv4_public(),
        "src_port": random.randint(1024, 65535),
        "dst_port": random.choice([80, 443, 22, 3389, 8080, 8443, 53]),
        "protocol": random.choice(["TCP", "UDP", "ICMP"]),
        "bytes_in": random.randint(200, 2000),
        "bytes_out": random.randint(100, 500),
        "duration": random.uniform(0.1, 2.0),
        "tcp_flags": random.choice(["SYN", "ACK", "SYN-ACK", "FIN", "RST", "PSH"]),
        "packet_rate": random.uniform(10, 200),
        "conn_count": random.randint(1, 10),
    }
    raw.update(overrides)

    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": src_ip,
        "layer": "network",
        "identity": {
            "user_id": session["user_id"],
            "session_id": session["session_id"],
            "role": session["role"],
            "department": session["department"],
        },
        "network_zone": zone_info,
        "raw_features": raw,
        "normalized_vector": None,
        "label": None,
    }
    return event


def generate_application_event(src_ip: str = None, **overrides) -> dict:
    """Generate a single application-layer event."""
    if src_ip is None:
        src_ip = get_zone_ip("internal")
    session = get_or_create_session(src_ip)
    zone_info = classify_network_zone(src_ip)

    raw = {
        "user_id": session["user_id"],
        "session_id": session["session_id"],
        "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
        "endpoint": random.choice([
            "/api/login", "/api/data", "/api/upload", "/api/users",
            "/api/reports", "/api/config", "/api/health", "/api/export",
        ]),
        "status_code": random.choices([200, 201, 301, 401, 403, 500],
                                       weights=[70, 10, 5, 8, 4, 3])[0],
        "payload_size": random.randint(100, 5000),
        "user_agent": fake.user_agent(),
        "geo_country": random.choices(
            ["IN", "US", "GB", "DE", "JP", "CN", "RU"],
            weights=[50, 20, 10, 5, 5, 5, 5]
        )[0],
        "req_per_min": random.randint(5, 60),
        "auth_age": random.randint(60, 86400),  # seconds since last auth
    }
    raw.update(overrides)

    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": src_ip,
        "layer": "application",
        "identity": {
            "user_id": session["user_id"],
            "session_id": session["session_id"],
            "role": session["role"],
            "department": session["department"],
        },
        "network_zone": zone_info,
        "raw_features": raw,
        "normalized_vector": None,
        "label": None,
    }
    return event


def generate_endpoint_event(src_ip: str = None, **overrides) -> dict:
    """Generate a single endpoint-layer event."""
    if src_ip is None:
        src_ip = get_zone_ip("internal")
    session = get_or_create_session(src_ip)
    zone_info = classify_network_zone(src_ip)

    raw = {
        "process_name": random.choice([
            "chrome.exe", "svchost.exe", "python.exe", "explorer.exe",
            "notepad.exe", "outlook.exe", "teams.exe", "code.exe",
        ]),
        "parent_pid": random.randint(1, 9999),
        "user": session["user_id"],
        "file_path": fake.file_path(depth=3),
        "registry_key": r"HKLM\SOFTWARE\\" + fake.word(),
        "cpu_pct": random.uniform(0.5, 30.0),
        "mem_mb": random.uniform(50, 500),
        "child_proc_count": random.randint(0, 5),
        "net_connections": random.randint(0, 20),
        "file_writes": random.randint(0, 50),
    }
    raw.update(overrides)

    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": src_ip,
        "layer": "endpoint",
        "identity": {
            "user_id": session["user_id"],
            "session_id": session["session_id"],
            "role": session["role"],
            "department": session["department"],
        },
        "network_zone": zone_info,
        "raw_features": raw,
        "normalized_vector": None,
        "label": None,
    }
    return event


# ─── Attack Injection ───────────────────────────────────────────────────────────

def inject_attack(event: dict, attack_type: str, ip: str) -> dict:
    """Modifies a benign event to exhibit attack patterns."""
    event["source_ip"] = ip
    session = get_or_create_session(ip)
    event["identity"] = {
        "user_id": session["user_id"],
        "session_id": session["session_id"],
        "role": session["role"],
        "department": session["department"],
    }

    raw = event["raw_features"]
    layer = event["layer"]

    if attack_type == "brute_force":
        if layer == "application":
            raw["status_code"] = 401
            raw["payload_size"] = random.randint(50, 200)
            raw["req_per_min"] = random.randint(200, 500)
            raw["endpoint"] = "/api/login"
            raw["method"] = "POST"
        elif layer == "network":
            raw["bytes_out"] = random.randint(50, 150)
            raw["conn_count"] = random.randint(50, 200)
            raw["duration"] = random.uniform(0.01, 0.05)

    elif attack_type == "c2_beacon":
        if layer == "network":
            raw["duration"] = 30.0 + random.uniform(-0.05, 0.05)
            raw["dst_ip"] = "185.220.101.45"
            raw["dst_port"] = 443
            raw["bytes_out"] = random.randint(100, 300)
            raw["bytes_in"] = random.randint(100, 300)
        elif layer == "endpoint":
            raw["process_name"] = random.choice(["svchost.exe", "rundll32.exe"])
            raw["net_connections"] = random.randint(50, 100)
            raw["cpu_pct"] = random.uniform(0.1, 2.0)

    elif attack_type == "data_exfil":
        if layer == "network":
            raw["bytes_out"] = random.randint(50_000_000, 200_000_000)
            raw["dst_ip"] = fake.ipv4_public()
            raw["duration"] = random.uniform(10, 60)
        elif layer == "application":
            raw["geo_country"] = random.choice(["CN", "RU"])
            raw["payload_size"] = random.randint(500_000, 5_000_000)
            raw["endpoint"] = "/api/export"
            raw["method"] = "POST"

    elif attack_type == "lateral_movement":
        if layer == "network":
            raw["dst_ip"] = get_zone_ip(random.choice(["servers", "internal"]))
            raw["dst_port"] = random.choice([445, 3389, 22, 5985])
            raw["bytes_out"] = random.randint(50, 200)
        elif layer == "endpoint":
            raw["process_name"] = random.choice(["psexec.exe", "wmic.exe", "powershell.exe"])
            raw["child_proc_count"] = random.randint(5, 20)

    elif attack_type == "false_positive_admin":
        if layer == "application":
            raw["payload_size"] = 80_000_000
            raw["user_agent"] = "InternalBackupTool/2.1"
            raw["geo_country"] = "IN"
            raw["status_code"] = 200
            raw["endpoint"] = "/api/export"
        elif layer == "network":
            raw["bytes_out"] = 80_000_000
            raw["dst_ip"] = get_zone_ip("servers")
            raw["protocol"] = "TCP"
            raw["tcp_flags"] = "ACK"

    return event


# ─── Async Generators for Live Pipeline ─────────────────────────────────────────

async def network_generator(queue: asyncio.Queue, attack_schedule: dict = None):
    """Generates ~500 network events/sec in normal mode."""
    while True:
        event = generate_network_event()

        # Apply attack if scheduled for this IP
        if attack_schedule:
            for ip, atk_type in list(attack_schedule.items()):
                if random.random() < 0.3:  # 30% of events from attacker IP
                    event = generate_network_event(src_ip=ip)
                    event = inject_attack(event, atk_type, ip)

        await queue.put(("network", event))
        await asyncio.sleep(0.002)


async def application_generator(queue: asyncio.Queue, attack_schedule: dict = None):
    """Generates ~300 application events/sec."""
    while True:
        event = generate_application_event()

        if attack_schedule:
            for ip, atk_type in list(attack_schedule.items()):
                if random.random() < 0.3:
                    event = generate_application_event(src_ip=ip)
                    event = inject_attack(event, atk_type, ip)

        await queue.put(("application", event))
        await asyncio.sleep(0.003)


async def endpoint_generator(queue: asyncio.Queue, attack_schedule: dict = None):
    """Generates ~200 endpoint events/sec."""
    while True:
        event = generate_endpoint_event()

        if attack_schedule:
            for ip, atk_type in list(attack_schedule.items()):
                if random.random() < 0.3:
                    event = generate_endpoint_event(src_ip=ip)
                    event = inject_attack(event, atk_type, ip)

        await queue.put(("endpoint", event))
        await asyncio.sleep(0.005)


# ─── CSV Export for Pretraining ─────────────────────────────────────────────────

FEATURE_COLUMNS = [
    # Network (0-10)
    "bytes_out", "bytes_in", "duration", "dst_port", "src_port",
    "tcp_flags_enc", "protocol_enc", "packet_rate", "conn_count",
    "dst_ip_hash", "src_ip_hash",
    # Application (11-20)
    "status_code_enc", "payload_size", "method_enc", "geo_country_enc",
    "endpoint_hash", "user_agent_hash", "req_per_min", "auth_age",
    "session_hash", "role_enc",
    # Endpoint (21-30)
    "cpu_pct", "mem_mb", "process_hash", "parent_pid_enc", "file_path_hash",
    "registry_hash", "child_proc_count", "net_connections", "file_writes",
    "user_hash",
    # Derived (31)
    "zone_trust_enc", "vlan_enc",
]

# Encoding maps
PROTOCOL_MAP = {"TCP": 0.0, "UDP": 0.5, "ICMP": 1.0}
TCP_FLAGS_MAP = {"SYN": 0.0, "ACK": 0.2, "SYN-ACK": 0.4, "FIN": 0.6, "RST": 0.8, "PSH": 1.0}
METHOD_MAP = {"GET": 0.0, "POST": 0.33, "PUT": 0.66, "DELETE": 1.0}
GEO_MAP = {"IN": 0.0, "US": 0.14, "GB": 0.28, "DE": 0.42, "JP": 0.57, "CN": 0.71, "RU": 0.85}
TRUST_MAP = {"critical": 0.0, "high": 0.25, "low": 0.5, "untrusted": 0.75}
ROLE_MAP = {"admin": 0.0, "analyst": 0.2, "engineer": 0.4, "manager": 0.6, "intern": 0.8, "svc_acct": 1.0}


def _safe_hash(val, mod=1000) -> float:
    """Hash a string to a float [0,1]."""
    if val is None:
        return 0.0
    return (hash(str(val)) % mod) / mod


def flatten_event_to_vector(event: dict) -> list:
    """
    Convert a raw event dict into a 32-dim float vector.
    Each layer fills its section; missing sections get zeros.
    """
    raw = event.get("raw_features", {})
    identity = event.get("identity", {})
    zone = event.get("network_zone", {})
    vec = [0.0] * 32

    # Network features (0-10)
    vec[0] = float(raw.get("bytes_out", 0))
    vec[1] = float(raw.get("bytes_in", 0))
    vec[2] = float(raw.get("duration", 0))
    vec[3] = float(raw.get("dst_port", 0))
    vec[4] = float(raw.get("src_port", 0))
    vec[5] = TCP_FLAGS_MAP.get(raw.get("tcp_flags", ""), 0.5)
    vec[6] = PROTOCOL_MAP.get(raw.get("protocol", ""), 0.5)
    vec[7] = float(raw.get("packet_rate", 0))
    vec[8] = float(raw.get("conn_count", 0))
    vec[9] = _safe_hash(raw.get("dst_ip"))
    vec[10] = _safe_hash(raw.get("src_ip"))

    # Application features (11-20)
    vec[11] = float(raw.get("status_code", 200)) / 600.0
    vec[12] = float(raw.get("payload_size", 0))
    vec[13] = METHOD_MAP.get(raw.get("method", ""), 0.5)
    vec[14] = GEO_MAP.get(raw.get("geo_country", ""), 0.5)
    vec[15] = _safe_hash(raw.get("endpoint"))
    vec[16] = _safe_hash(raw.get("user_agent"))
    vec[17] = float(raw.get("req_per_min", 0))
    vec[18] = float(raw.get("auth_age", 0))
    vec[19] = _safe_hash(identity.get("session_id"))
    vec[20] = ROLE_MAP.get(identity.get("role", ""), 0.5)

    # Endpoint features (21-30)
    vec[21] = float(raw.get("cpu_pct", 0))
    vec[22] = float(raw.get("mem_mb", 0))
    vec[23] = _safe_hash(raw.get("process_name"))
    vec[24] = float(raw.get("parent_pid", 0))
    vec[25] = _safe_hash(raw.get("file_path"))
    vec[26] = _safe_hash(raw.get("registry_key"))
    vec[27] = float(raw.get("child_proc_count", 0))
    vec[28] = float(raw.get("net_connections", 0))
    vec[29] = float(raw.get("file_writes", 0))
    vec[30] = _safe_hash(raw.get("user", identity.get("user_id")))

    # Derived (31)
    vec[31] = TRUST_MAP.get(zone.get("trust", ""), 0.5)

    return vec


def generate_training_data(output_dir: str = "data"):
    """Generate CSV files for pretraining the autoencoders."""
    os.makedirs(output_dir, exist_ok=True)

    print("[PHANTOM] Generating synthetic training data...")

    all_benign = {"network": [], "application": [], "endpoint": []}
    all_attacks = {"network": [], "application": [], "endpoint": []}

    # ─── Generate Benign Data ────────────────────────────────────────────────
    for layer, gen_fn, count in [
        ("network", generate_network_event, 4000),
        ("application", generate_application_event, 3500),
        ("endpoint", generate_endpoint_event, 2500),
    ]:
        for _ in range(count):
            event = gen_fn()
            vec = flatten_event_to_vector(event)
            all_benign[layer].append(vec)

    # ─── Generate Attack Data ────────────────────────────────────────────────
    attack_configs = [
        ("brute_force",     "10.0.0.47", 150),
        ("c2_beacon",       "10.0.0.91", 100),
        ("data_exfil",      "10.0.0.88", 100),
        ("lateral_movement","10.0.0.77", 100),
    ]

    for atk_type, ip, count in attack_configs:
        for layer, gen_fn in [
            ("network", generate_network_event),
            ("application", generate_application_event),
            ("endpoint", generate_endpoint_event),
        ]:
            for _ in range(count // 3):
                event = gen_fn(src_ip=ip)
                event = inject_attack(event, atk_type, ip)
                vec = flatten_event_to_vector(event)
                all_attacks[layer].append(vec)

    # ─── False Positive Events ───────────────────────────────────────────────
    fp_ip = "10.0.0.5"
    for layer, gen_fn in [
        ("network", generate_network_event),
        ("application", generate_application_event),
        ("endpoint", generate_endpoint_event),
    ]:
        for _ in range(30):
            event = gen_fn(src_ip=fp_ip)
            event = inject_attack(event, "false_positive_admin", fp_ip)
            vec = flatten_event_to_vector(event)
            all_benign[layer].append(vec)  # FPs go into benign set

    # ─── Save CSVs ───────────────────────────────────────────────────────────
    for layer in ["network", "application", "endpoint"]:
        _save_csv(os.path.join(output_dir, f"benign_{layer}.csv"), all_benign[layer])
        _save_csv(os.path.join(output_dir, f"attacks_{layer}.csv"), all_attacks[layer])
        print(f"  [{layer}] Benign: {len(all_benign[layer])}, Attacks: {len(all_attacks[layer])}")

    print("[PHANTOM] Training data generated successfully.")
    return all_benign, all_attacks


def _save_csv(filepath: str, data: list):
    """Save list of vectors to CSV."""
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"f{i}" for i in range(32)])
        writer.writerows(data)


if __name__ == "__main__":
    generate_training_data()
