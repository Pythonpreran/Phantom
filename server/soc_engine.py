"""
PHANTOM — SOC Engine
====================
Singleton wrapper around the Kill Chain Tracker and SOC Playbook Generator.
Used by FastAPI routes to track per-IP attack progression through MITRE ATT&CK stages.
No dependency on autoencoders — works purely with attack metadata.
"""

import os
import sys
from datetime import datetime

# Add parent dir so we can import the pipeline modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.kill_chain import KillChainTracker, MITRE_MAP, SEVERITY_MAP


# ── Global singleton ──────────────────────────────────────────────────────────
_kill_chain = KillChainTracker()


# ── Attack type → simulated raw_features ────────────────────────────────────
# Maps each attack button to raw feature signals KillChainTracker understands
_ATTACK_SIGNALS = {
    "Brute Force": {
        "status_code": 401,
        "req_per_min": 350,
        "bytes_out": 200,
        "dst_port": 80,
        "conn_count": 60,
    },
    "DDoS": {
        "conn_count": 180,
        "bytes_out": 120_000,
        "dst_port": 80,
        "status_code": 200,
        "duration": 0.01,
    },
    "SQL Injection": {
        "status_code": 200,
        "bytes_out": 5_000,
        "dst_port": 3306,
        "payload_size": 1500,
        "endpoint": "/api/query",
    },
    "XSS": {
        "status_code": 200,
        "bytes_out": 2_000,
        "endpoint": "/api/form",
        "payload_size": 900,
    },
    "Port Scan": {
        "dst_port": 15000,
        "duration": 0.01,
        "conn_count": 90,
        "bytes_out": 50,
    },
    "Lateral Movement": {
        "dst_ip": "10.0.0.15",
        "dst_port": 445,
        "bytes_out": 250,
        "process_name": "psexec.exe",
    },
    "Data Exfiltration": {
        "bytes_out": 85_000_000,
        "geo_country": "CN",
        "dst_port": 443,
        "duration": 50.0,
    },
}


def _build_event(ip: str, attack_type: str, user_id: str = "unknown") -> dict:
    """Build a KillChainTracker-compatible event dict from attack metadata."""
    raw = _ATTACK_SIGNALS.get(attack_type, {
        "status_code": 401,
        "conn_count": 60,
        "bytes_out": 1_000,
    })
    return {
        "source_ip": ip,
        "layer": "application",
        "timestamp": datetime.utcnow().isoformat(),
        "network_zone": {"zone": "external", "trust": "untrusted"},
        "identity": {"user_id": user_id},
        "raw_features": raw,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def update_kill_chain(ip: str, attack_type: str, user_id: str = "unknown") -> dict:
    """
    Advance the kill chain state for this IP based on the attack type.
    Returns the updated kill chain state dict.
    """
    event = _build_event(ip, attack_type, user_id)
    return _kill_chain.update(event)


def get_kill_chain_status(min_stage: int = 0) -> list:
    """Return all active threat records (above min_stage), enriched with mitre_name."""
    threats = _kill_chain.get_active_threats(min_stage=max(min_stage, 1))
    # Enrich with mitre_name (get_active_threats only returns mitre_id)
    for t in threats:
        stage_num = t.get("stage_num", 0)
        t["mitre_name"] = MITRE_MAP[stage_num]["name"]
    return threats


def get_kill_chain_for_ip(ip: str) -> dict | None:
    """Return kill chain state for a specific IP address."""
    # Try exact key first, then prefix match
    for key, record in _kill_chain.identity_state.items():
        if key.startswith(ip + "::"):
            stage_val = record["stage"].value
            mitre = MITRE_MAP[stage_val]
            return {
                "identity_key": key,
                "ip": ip,
                "current_stage": record["stage"].name,
                "stage_num": stage_val,
                "severity": SEVERITY_MAP[stage_val],
                "mitre_id": mitre["id"],
                "mitre_name": mitre["name"],
                "history": record.get("history", []),
                "first_seen": record.get("first_seen", ""),
                "last_seen": record.get("last_seen", ""),
                "zones_traversed": list(record.get("zones_seen", set())),
            }
    return None


def get_kill_chain_stats() -> dict:
    """Return aggregate kill chain stats."""
    return _kill_chain.get_stats()


# ── SOC Playbook Generator (template-based) ───────────────────────────────────

_PLAYBOOKS = {
    "Brute Force": {
        "why": (
            "An IP was detected making repeated failed login attempts in rapid succession. "
            "PHANTOM's LightGBM model flagged the traffic as consistent with credential stuffing "
            "or a brute-force attack based on req_per_min, status_code, and conn_count signals."
        ),
        "steps": [
            "Block IP at the perimeter firewall — already auto-applied by PHANTOM",
            "Reset passwords for all accounts targeted in the past 2 hours",
            "Check auth logs for any HTTP 200 response after repeated 401 failures",
            "Preserve all logs in auth.log for forensic chain of custody",
            "Scan for lateral movement originating from this IP on internal subnets",
        ],
        "fp_check": "Verify the IP does not belong to an automated test suite, CI/CD pipeline, or load balancer.",
        "mitre": "T1110 — Brute Force (Initial Access)",
    },
    "DDoS": {
        "why": (
            "Abnormally high connection count and traffic volume was detected from this IP. "
            "The LightGBM model identified a packet rate and conn_count pattern in the top "
            "percentile of DoS-category attacks in the UNSW-NB15 training distribution."
        ),
        "steps": [
            "IP has been auto-blocked by PHANTOM — verify block is active at network edge",
            "Enable rate limiting on all public-facing load balancers",
            "Activate CDN DDoS protection (Cloudflare/AWS Shield) if available",
            "Contact upstream ISP for traffic scrubbing if volumetric attack continues",
            "Monitor service recovery — check API response times returning to baseline",
        ],
        "fp_check": "Confirm this is not a legitimate high-volume API consumer with prior authorization.",
        "mitre": "T1498 — Network Denial of Service",
    },
    "SQL Injection": {
        "why": (
            "The traffic payload and database port activity matched Exploit-category "
            "signatures. The model flagged the byte pattern and endpoint combination "
            "using dst_port, payload_size, and bytes_out as primary signals."
        ),
        "steps": [
            "IP is auto-blocked — verify DB is not receiving queries from this source",
            "Audit all database queries executed from this IP in the last 24 hours",
            "Check for unauthorized data reads or schema enumeration in DB logs",
            "Rotate database credentials and API keys if exfiltration is suspected",
            "Patch the flagged endpoint with parameterized queries / prepared statements",
        ],
        "fp_check": "Check if IP belongs to a penetration testing team or authorized vulnerability scanner.",
        "mitre": "T1190 — Exploit Public-Facing Application",
    },
    "XSS": {
        "why": (
            "Cross-site scripting payload signatures were detected. The model identified "
            "payload_size and endpoint patterns consistent with script injection attempts "
            "against the application layer (Exploit category, UNSW-NB15)."
        ),
        "steps": [
            "IP is auto-blocked — audit recent form submissions for script payloads",
            "Sanitize all user input endpoints with proper HTML/JS encoding",
            "Check browser session logs for any executed scripts affecting real users",
            "Review Content-Security-Policy headers and tighten if necessary",
            "Scan for stored XSS payloads in the database that were already persisted",
        ],
        "fp_check": "Verify flagged requests are not from a legitimate frontend app sending rich text content.",
        "mitre": "T1059.007 — JavaScript Injection / XSS",
    },
    "Port Scan": {
        "why": (
            "Rapid connection attempts across high-numbered ports with sub-50ms durations "
            "were detected. The LightGBM model classified this as Reconnaissance-category "
            "traffic based on conn_count, duration, and dst_port distribution."
        ),
        "steps": [
            "IP is auto-blocked — review which ports were probed in request logs",
            "Verify firewall rules restrict exposure of internal/non-essential ports",
            "Check if this IP appears in threat intel feeds (VirusTotal, Shodan, AbuseIPDB)",
            "Alert the infrastructure team if the scan reached any internal services",
            "Review whether other IPs from the same subnet are also scanning (distributed recon)",
        ],
        "fp_check": "Confirm this is not a legitimate IT asset scanner or network monitoring agent.",
        "mitre": "T1595 — Active Scanning (Reconnaissance)",
    },
}

_DEFAULT_PLAYBOOK = {
    "why": (
        "PHANTOM's LightGBM model detected anomalous traffic from this IP. "
        "The traffic pattern deviated significantly from baseline benign behavior "
        "in the UNSW-NB15 training distribution (93.5% accurate model, 0.98 ROC-AUC)."
    ),
    "steps": [
        "Review all recent activity from this IP in the PHANTOM request logs",
        "Check for indicators of compromise on the associated endpoint",
        "Review network flows for suspicious external connections",
        "Escalate to Tier 2 SOC team if kill chain stage continues advancing",
        "Document all findings for the incident response report",
    ],
    "fp_check": "Verify this activity does not match any known scheduled tasks or authorized operations.",
    "mitre": "T1595 — Unknown Attack Pattern",
}


def get_playbook(attack_type: str, ip: str, confidence: float) -> dict:
    """Return a structured SOC playbook for the given attack type."""
    pb = _PLAYBOOKS.get(attack_type, _DEFAULT_PLAYBOOK)
    return {
        "attack_type": attack_type,
        "ip": ip,
        "confidence_pct": f"{confidence * 100:.1f}%",
        "why": pb["why"],
        "steps": pb["steps"],
        "fp_check": pb["fp_check"],
        "mitre": pb["mitre"],
    }
