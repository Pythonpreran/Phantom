"""
PHANTOM  --  Red Agent Attack Pattern Library
============================================
Individual attack generators for adversarial simulation.
Each function generates events matching specific attack signatures.
"""

import random
from uuid import uuid4
from datetime import datetime, timezone
from faker import Faker

from data.generate_synthetic import (
    generate_network_event,
    generate_application_event,
    generate_endpoint_event,
    inject_attack,
    get_zone_ip,
    get_or_create_session,
)

fake = Faker()


def brute_force_burst(ip: str, count: int = 50) -> list:
    """Generate burst brute force attack events  --  easy to catch."""
    events = []
    for i in range(count):
        event = generate_application_event(src_ip=ip)
        event["raw_features"]["status_code"] = 401 if i < count - 2 else 200
        event["raw_features"]["payload_size"] = random.randint(50, 200)
        event["raw_features"]["req_per_min"] = random.randint(300, 600)
        event["raw_features"]["endpoint"] = "/api/login"
        event["raw_features"]["method"] = "POST"
        events.append(event)

        # Also generate network events for cross-layer detection
        net_event = generate_network_event(src_ip=ip)
        net_event["raw_features"]["conn_count"] = random.randint(50, 200)
        net_event["raw_features"]["bytes_out"] = random.randint(50, 200)
        net_event["raw_features"]["duration"] = random.uniform(0.01, 0.05)
        events.append(net_event)
    return events


def c2_beacon(ip: str, count: int = 30) -> list:
    """Generate C2 beaconing pattern  --  ultra-regular intervals to fixed IP."""
    events = []
    c2_server = "185.220.101.45"
    for _ in range(count):
        event = generate_network_event(src_ip=ip)
        event["raw_features"]["duration"] = 30.0 + random.uniform(-0.05, 0.05)
        event["raw_features"]["dst_ip"] = c2_server
        event["raw_features"]["dst_port"] = 443
        event["raw_features"]["bytes_out"] = random.randint(100, 350)
        event["raw_features"]["bytes_in"] = random.randint(100, 350)
        event["raw_features"]["protocol"] = "TCP"
        events.append(event)

        # Endpoint evidence
        ep_event = generate_endpoint_event(src_ip=ip)
        ep_event["raw_features"]["process_name"] = random.choice(["svchost.exe", "rundll32.exe"])
        ep_event["raw_features"]["net_connections"] = random.randint(50, 100)
        ep_event["raw_features"]["cpu_pct"] = random.uniform(0.1, 2.0)
        events.append(ep_event)
    return events


def data_exfil_burst(ip: str, count: int = 10) -> list:
    """Generate data exfiltration burst  --  massive outbound transfer."""
    events = []
    for _ in range(count):
        event = generate_network_event(src_ip=ip)
        event["raw_features"]["bytes_out"] = random.randint(50_000_000, 200_000_000)
        event["raw_features"]["dst_ip"] = fake.ipv4_public()
        event["raw_features"]["duration"] = random.uniform(10, 60)
        events.append(event)

        app_event = generate_application_event(src_ip=ip)
        app_event["raw_features"]["geo_country"] = random.choice(["CN", "RU"])
        app_event["raw_features"]["payload_size"] = random.randint(1_000_000, 10_000_000)
        app_event["raw_features"]["endpoint"] = "/api/export"
        events.append(app_event)
    return events


def slow_drip_exfil(ip: str, count: int = 20) -> list:
    """
    EVASION: Small data transfers spread over time  --  tries to stay below threshold.
    Kill Chain tracker accumulates evidence across many events.
    """
    events = []
    for _ in range(count):
        event = generate_network_event(src_ip=ip)
        event["raw_features"]["bytes_out"] = random.randint(500_000, 2_000_000)
        event["raw_features"]["dst_ip"] = fake.ipv4_public()
        event["raw_features"]["duration"] = random.uniform(1, 5)
        events.append(event)
    return events


def traffic_mimicry(ip: str, count: int = 30) -> list:
    """
    EVASION: Copies approximate statistical distribution of benign traffic.
    Latent vectors diverge subtly from benign norm  --  caught ~60% of time.
    """
    events = []
    for _ in range(count):
        event = generate_network_event(src_ip=ip)
        # Try to look normal but inject subtle anomalies
        event["raw_features"]["bytes_out"] = int(random.gauss(300, 100))
        event["raw_features"]["bytes_in"] = int(random.gauss(1000, 400))
        event["raw_features"]["duration"] = random.gauss(1.0, 0.3)
        # But destination is suspicious
        event["raw_features"]["dst_ip"] = "185.220.101.45"
        event["raw_features"]["dst_port"] = random.choice([443, 8443])
        events.append(event)
    return events


def distributed_brute_force(target_count: int = 30) -> list:
    """
    EVASION: Many IPs, few attempts each  --  no single IP crosses threshold.
    This is PHANTOM's honest blind spot (per-identity tracking).
    """
    events = []
    ips = [f"10.0.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(target_count)]
    for ip in ips:
        for _ in range(random.randint(3, 8)):  # few attempts per IP
            event = generate_application_event(src_ip=ip)
            event["raw_features"]["status_code"] = 401
            event["raw_features"]["endpoint"] = "/api/login"
            event["raw_features"]["payload_size"] = random.randint(50, 200)
            events.append(event)
    return events


def lateral_movement_sweep(ip: str, count: int = 20) -> list:
    """Generate lateral movement events across multiple network zones."""
    events = []
    target_zones = ["internal", "servers", "dmz"]
    for _ in range(count):
        zone = random.choice(target_zones)
        event = generate_network_event(src_ip=ip)
        event["raw_features"]["dst_ip"] = get_zone_ip(zone)
        event["raw_features"]["dst_port"] = random.choice([445, 3389, 22, 5985])
        event["raw_features"]["bytes_out"] = random.randint(50, 300)
        events.append(event)

        ep_event = generate_endpoint_event(src_ip=ip)
        ep_event["raw_features"]["process_name"] = random.choice(["psexec.exe", "wmic.exe", "powershell.exe"])
        ep_event["raw_features"]["child_proc_count"] = random.randint(5, 20)
        events.append(ep_event)
    return events


# Attack catalog for the Red Agent
ATTACK_CATALOG = {
    "brute_force": {
        "fn": brute_force_burst,
        "needs_ip": True,
        "description": "Burst brute force  --  1000 logins/60s",
        "expected_catch": True,
    },
    "c2_beacon": {
        "fn": c2_beacon,
        "needs_ip": True,
        "description": "C2 beaconing  --  ultra-regular intervals to fixed IP",
        "expected_catch": True,
    },
    "data_exfil": {
        "fn": data_exfil_burst,
        "needs_ip": True,
        "description": "Data exfiltration burst  --  100MB+ outbound",
        "expected_catch": True,
    },
    "slow_drip_exfil": {
        "fn": slow_drip_exfil,
        "needs_ip": True,
        "description": "Slow drip exfil  --  1MB every 30s",
        "expected_catch": True,
    },
    "traffic_mimicry": {
        "fn": traffic_mimicry,
        "needs_ip": True,
        "description": "Traffic mimicry  --  copies benign distribution",
        "expected_catch": False,  # partial
    },
    "distributed_brute_force": {
        "fn": distributed_brute_force,
        "needs_ip": False,
        "description": "Distributed brute force  --  50 IPs × 5 attempts",
        "expected_catch": False,
    },
    "lateral_movement": {
        "fn": lateral_movement_sweep,
        "needs_ip": True,
        "description": "Cross-zone lateral movement  --  probing internal targets",
        "expected_catch": True,
    },
}
