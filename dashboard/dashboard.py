"""
PHANTOM Module 6 — Live SOC Dashboard
========================================
Streamlit-based Security Operations Center dashboard.
Real-time alerts, kill chain timelines, SHAP explanations,
LLM playbooks, and Red Agent adversarial scoreboard.

Features:
- Pretrained model loading (no training during demo)
- Identity-based tracking (user_id + session, not just IP)
- Multi-network zone awareness
"""

import os
import sys
import time
import json
import random
import pickle
import threading
from collections import deque, defaultdict
from datetime import datetime, timezone

import numpy as np
import streamlit as st

# ─── Path setup ─────────────────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from data.generate_synthetic import (
    generate_network_event,
    generate_application_event,
    generate_endpoint_event,
    flatten_event_to_vector,
    inject_attack,
    NETWORK_ZONES,
)
from models.autoencoder import SpecialistAutoencoder
from pipeline.ingestor import Normalizer
from pipeline.detector import AnomalyDetector
from pipeline.fusion import ContrastiveFusionEngine
from pipeline.kill_chain import KillChainTracker, KillChainStage
from pipeline.explainer import PhantomExplainer
from red_agent.red_agent import RedAgent
from dashboard.components import (
    render_alert_card,
    render_timeline,
    render_shap_bars,
    render_playbook,
    render_scoreboard,
    render_attack_log,
)

# ─── Page Config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PHANTOM — SOC Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap');

    /* Dark theme override */
    .stApp {
        background: #0a0e17;
        color: #e0e0e0;
    }

    /* Header styling */
    .phantom-header {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a0a2e 100%);
        border: 1px solid #30363d;
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }

    .phantom-title {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        font-size: 2em;
        background: linear-gradient(135deg, #ff1744, #ff6d00, #ff1744);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 3px;
    }

    .phantom-subtitle {
        font-family: 'Inter', sans-serif;
        color: #8b949e;
        font-size: 0.85em;
        margin-top: 4px;
    }

    .status-badge {
        background: #0d2818;
        border: 1px solid #00e676;
        color: #00e676;
        padding: 6px 16px;
        border-radius: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85em;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Section headers */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.1em;
        color: #e0e0e0;
        padding: 8px 0;
        border-bottom: 1px solid #21262d;
        margin-bottom: 12px;
    }

    /* Card styling */
    .metric-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }

    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2em;
        font-weight: 700;
        color: #00e5ff;
    }

    .metric-label {
        font-family: 'Inter', sans-serif;
        color: #8b949e;
        font-size: 0.8em;
        margin-top: 4px;
    }

    /* Scrollable containers */
    .scrollable {
        max-height: 500px;
        overflow-y: auto;
        padding-right: 8px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 8px;
        padding: 8px 16px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1a0a2e;
        color: #ff1744;
    }
</style>
""", unsafe_allow_html=True)


# ─── Initialize Session State ────────────────────────────────────────────────────
def init_state():
    """Initialize all session state variables once."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.running = False
        st.session_state.alerts = deque(maxlen=100)
        st.session_state.incidents = deque(maxlen=50)
        st.session_state.all_events_count = 0
        st.session_state.anomalies_count = 0
        st.session_state.selected_incident = None
        st.session_state.playbook_cache = {}
        st.session_state.zone_stats = defaultdict(lambda: {"event_count": 0, "alert_count": 0})

        # Load pretrained models
        st.session_state.normalizer = Normalizer(
            os.path.join(ROOT_DIR, "models", "scaler.pkl")
        )
        st.session_state.detector = AnomalyDetector(
            os.path.join(ROOT_DIR, "models")
        )
        st.session_state.fusion = ContrastiveFusionEngine(
            window_seconds=60, similarity_threshold=0.6
        )
        st.session_state.kill_chain = KillChainTracker()

        # Explainer with pretrained models
        models_dict = st.session_state.detector.models
        # Load background benign data for SHAP
        bg_path = os.path.join(ROOT_DIR, "data", "benign_network.csv")
        bg_data = None
        if os.path.exists(bg_path):
            try:
                import pandas as pd
                df = pd.read_csv(bg_path)
                from sklearn.preprocessing import MinMaxScaler
                scaler = st.session_state.normalizer.scaler
                bg_raw = df.values[:200].astype(np.float32)
                bg_clipped = np.clip(bg_raw, scaler.data_min_, scaler.data_max_)
                bg_data = scaler.transform(bg_clipped)
            except Exception:
                bg_data = None

        st.session_state.explainer = PhantomExplainer(
            models=models_dict,
            background_data=bg_data,
        )

        # Red Agent
        st.session_state.red_agent = RedAgent()

init_state()


# ─── PHANTOM Processing Pipeline ─────────────────────────────────────────────────
def process_event(event: dict) -> dict:
    """Process a single event through the full PHANTOM pipeline."""
    st.session_state.all_events_count += 1

    # Track zone stats
    zone = event.get("network_zone", {}).get("zone", "unknown")
    st.session_state.zone_stats[zone]["event_count"] += 1

    # Module 1: Normalize
    event = st.session_state.normalizer.normalize(event)

    # Module 2: Detect
    detection = st.session_state.detector.detect(event)

    if not detection["is_anomalous"]:
        return None

    st.session_state.anomalies_count += 1
    st.session_state.zone_stats[zone]["alert_count"] += 1

    # Module 3: Fusion
    fusion_result = st.session_state.fusion.ingest_alert(
        event=event,
        layer=event["layer"],
        latent_vec=detection["latent_vector"],
        anomaly_score=detection["anomaly_score"],
    )

    # Module 4: Kill Chain
    kc_result = st.session_state.kill_chain.update(event, fusion_result)

    # Module 5: Explainability
    shap_top3 = st.session_state.explainer.explain_alert(event, detection)

    # Combine results
    incident = {
        "event_id": event.get("event_id"),
        "timestamp": event.get("timestamp"),
        "ip": event.get("source_ip"),
        "user_id": event.get("identity", {}).get("user_id", "—"),
        "session_id": event.get("identity", {}).get("session_id", "—"),
        "role": event.get("identity", {}).get("role", "—"),
        "layer": event["layer"],
        "layers": fusion_result.get("layers", [event["layer"]]),
        "zone": zone,
        "zone_trust": event.get("network_zone", {}).get("trust", "—"),
        "severity": kc_result["severity"] if kc_result["stage_num"] > 0 else fusion_result["severity"],
        "confirmed": fusion_result.get("confirmed", False),
        "suppressed": fusion_result.get("suppressed", False),
        "similarity": fusion_result.get("similarity", 0),
        "anomaly_score": detection["anomaly_score"],
        "recon_error": detection["recon_error"],
        "current_stage": kc_result["current_stage"],
        "stage_num": kc_result["stage_num"],
        "mitre_id": kc_result["mitre_id"],
        "mitre_name": kc_result["mitre_name"],
        "history": kc_result["history"],
        "shap_top3": shap_top3,
        "zones_traversed": kc_result.get("zones_traversed", []),
    }

    # Override severity for suppressed false positives
    if incident["suppressed"] and not incident["confirmed"]:
        incident["severity"] = "SUPPRESSED"

    return incident


def generate_events_batch(attack_schedule: dict, batch_size: int = 20) -> list:
    """Generate a batch of events (mix of benign + attacks)."""
    events = []
    generators = [generate_network_event, generate_application_event, generate_endpoint_event]

    for _ in range(batch_size):
        gen_fn = random.choice(generators)
        event = gen_fn()
        events.append(event)

    # Inject scheduled attacks — ALL layers for cross-layer fusion to work
    for ip, atk_type in attack_schedule.items():
        for gen_fn in generators:
            # Always inject across all 3 layers for proper cross-layer confirmation
            event = gen_fn(src_ip=ip)
            event = inject_attack(event, atk_type, ip)
            events.append(event)

    return events


# ─── Dashboard Layout ────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="phantom-header">
    <div>
        <div class="phantom-title">🔴 PHANTOM</div>
        <div class="phantom-subtitle">Proactive Hybrid Anomaly & Threat Management Operations Network</div>
    </div>
    <div>
        <span class="status-badge">◉ LIVE MONITORING</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Control Bar ────────────────────────────────────────────────────────────────
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5 = st.columns([2, 2, 2, 2, 2])

with ctrl_col1:
    if st.button("▶️ Start Simulation" if not st.session_state.running else "⏹️ Stop", 
                  type="primary", use_container_width=True):
        st.session_state.running = not st.session_state.running
        st.rerun()

with ctrl_col2:
    if st.button("⚔️ Red Agent Attack", use_container_width=True, disabled=not st.session_state.running):
        # Launch a random attack
        events = st.session_state.red_agent.launch_attack()
        caught = False
        for event in events:
            result = process_event(event)
            if result:
                st.session_state.alerts.append(result)
                if result.get("severity") in ["HIGH", "CRITICAL", "MEDIUM"]:
                    st.session_state.incidents.append(result)
                if result.get("confirmed") or result.get("severity") in ["HIGH", "CRITICAL"]:
                    caught = True
                if result.get("stage_num", 0) >= 2:
                    caught = True
        st.session_state.red_agent.report_outcome(
            st.session_state.red_agent.stats.launched - 1, caught
        )
        st.rerun()

with ctrl_col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{st.session_state.all_events_count:,}</div>
        <div class="metric-label">Events Processed</div>
    </div>
    """, unsafe_allow_html=True)

with ctrl_col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{st.session_state.anomalies_count}</div>
        <div class="metric-label">Anomalies Detected</div>
    </div>
    """, unsafe_allow_html=True)

with ctrl_col5:
    active_threats = st.session_state.kill_chain.get_active_threats(min_stage=2)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#ff1744;">{len(active_threats)}</div>
        <div class="metric-label">Active Threats</div>
    </div>
    """, unsafe_allow_html=True)


# ─── Process Events if Running ──────────────────────────────────────────────────
if st.session_state.running:
    # Demo attack schedule — two simultaneous attacks
    attack_schedule = {
        "10.0.0.47": "brute_force",
        "10.0.0.91": "c2_beacon",
        "10.0.0.5": "false_positive_admin",
    }

    events = generate_events_batch(attack_schedule, batch_size=30)
    for event in events:
        result = process_event(event)
        if result:
            st.session_state.alerts.append(result)
            if result.get("severity") in ["HIGH", "CRITICAL", "MEDIUM"]:
                st.session_state.incidents.append(result)

st.divider()

# ─── Main Content: Two Columns ──────────────────────────────────────────────────
col_left, col_right = st.columns([2, 3])

# ═══ LEFT COLUMN: Live Alert Feed ═══════════════════════════════════════════════
with col_left:
    st.markdown('<div class="section-header">📡 Live Alert Feed</div>', unsafe_allow_html=True)

    alerts = list(st.session_state.alerts)
    if alerts:
        # Filter tabs
        tab_all, tab_critical, tab_suppressed = st.tabs(["All", "🔴 Critical/High", "⚪ Suppressed"])

        with tab_all:
            for alert in reversed(alerts[-15:]):
                render_alert_card(alert)

        with tab_critical:
            critical = [a for a in alerts if a["severity"] in ["CRITICAL", "HIGH"]]
            if critical:
                for alert in reversed(critical[-10:]):
                    render_alert_card(alert)
            else:
                st.info("No critical alerts yet")

        with tab_suppressed:
            suppressed = [a for a in alerts if a["severity"] == "SUPPRESSED"]
            if suppressed:
                for alert in reversed(suppressed[-10:]):
                    render_alert_card(alert)
                st.success(f"✅ {len(suppressed)} false positives successfully suppressed")
            else:
                st.info("No suppressed events yet")
    else:
        st.info("🔄 Waiting for events... Click **Start Simulation** to begin.")

    # Multi-Network Zone Overview
    st.markdown('<div class="section-header">🌐 Multi-Network Zones</div>', unsafe_allow_html=True)
    for zone_name, zone_info in NETWORK_ZONES.items():
        zs = st.session_state.zone_stats[zone_name]
        trust = zone_info["trust"]
        trust_colors = {"critical": "🔴", "high": "🟢", "low": "🟡", "untrusted": "🟠"}
        icon = trust_colors.get(trust, "⚪")
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; padding:4px 8px; margin:2px 0;
            background:#161b22; border-radius:4px;">
            <span>{icon} <b>{zone_name.upper()}</b> <span style="color:#666;">({zone_info['subnet']}.x)</span></span>
            <span style="color:#888;">VLAN {zone_info['vlan']} | {zs['event_count']} events | {zs['alert_count']} alerts</span>
        </div>
        """, unsafe_allow_html=True)


# ═══ RIGHT COLUMN: Incident Details ═════════════════════════════════════════════
with col_right:
    incidents = list(st.session_state.incidents)

    if incidents:
        # Pick most critical incident for detailed view
        critical_incidents = sorted(incidents, key=lambda x: x.get("stage_num", 0), reverse=True)
        selected = critical_incidents[0]

        # ─── Incident Header ────────────────────────────────────
        sev = selected["severity"]
        sev_colors = {"CRITICAL": "#ff1744", "HIGH": "#ff9100", "MEDIUM": "#ffea00", "LOW": "#00e676"}
        sev_color = sev_colors.get(sev, "#888")

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #161b22, #1a0a2e);
            border: 1px solid {sev_color};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:1.4em; font-weight:900; color:{sev_color};">
                        INCIDENT — {selected['ip']}
                    </span>
                    <br/>
                    <span style="color:#8b949e;">
                        User: <b>{selected['user_id']}</b> | 
                        Role: <b>{selected['role']}</b> | 
                        Session: <code>{selected['session_id']}</code>
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="color:{sev_color}; font-size:1.2em; font-weight:700;">{sev}</span>
                    <br/>
                    <span style="color:#888;">Score: {selected['anomaly_score']:.1f}x</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ─── Sub-columns: Timeline + SHAP ────────────────────────
        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.markdown('<div class="section-header">🔗 Kill Chain Timeline</div>',
                       unsafe_allow_html=True)
            render_timeline(selected.get("history", []))

            if selected.get("zones_traversed"):
                st.markdown(f"""
                <div style="margin-top:12px; padding:8px; background:#161b22; border-radius:8px;">
                    <span style="color:#ff9100;">🌐 Zones Traversed:</span>
                    <span style="color:#e0e0e0;"> {' → '.join(selected['zones_traversed'])}</span>
                </div>
                """, unsafe_allow_html=True)

        with detail_col2:
            st.markdown('<div class="section-header">📊 SHAP Feature Attribution</div>',
                       unsafe_allow_html=True)
            render_shap_bars(selected.get("shap_top3", []))

            st.markdown(f"""
            <div style="margin-top:12px; padding:8px; background:#161b22; border-radius:8px; font-size:0.85em;">
                <b>MITRE:</b> {selected.get('mitre_id', '')} — {selected.get('mitre_name', '')}
                <br/><b>Layers:</b> {', '.join(selected.get('layers', []))}
                <br/><b>Cosine Similarity:</b> {selected.get('similarity', 0):.3f}
                <br/><b>Recon Error:</b> {selected.get('recon_error', 0):.4f}
            </div>
            """, unsafe_allow_html=True)

        # ─── Playbook ────────────────────────────────────────────
        st.markdown('<div class="section-header">📋 AI-Generated Playbook (Phi-3)</div>',
                   unsafe_allow_html=True)

        ip = selected["ip"]
        if ip not in st.session_state.playbook_cache:
            playbook_ctx = {
                "ip": selected["ip"],
                "user_id": selected["user_id"],
                "mitre_id": selected.get("mitre_id", ""),
                "mitre_name": selected.get("mitre_name", ""),
                "stage": selected.get("current_stage", ""),
                "stage_num": selected.get("stage_num", 0),
                "layers_triggered": selected.get("layers", []),
                "shap_top3": selected.get("shap_top3", []),
                "anomaly_score": selected.get("anomaly_score", 0),
                "severity": selected.get("severity", ""),
                "zone": selected.get("zone", ""),
                "zone_trust": selected.get("zone_trust", ""),
            }
            playbook = st.session_state.explainer.generate_playbook(playbook_ctx)
            st.session_state.playbook_cache[ip] = playbook

        render_playbook(st.session_state.playbook_cache.get(ip, ""))

    else:
        st.markdown("""
        <div style="
            text-align:center; padding:60px;
            background: #161b22; border-radius:16px;
            border: 1px dashed #30363d;
        ">
            <div style="font-size:3em;">🛡️</div>
            <div style="font-size:1.2em; color:#8b949e; margin-top:16px;">
                No incidents detected yet
            </div>
            <div style="color:#666; margin-top:8px;">
                Start the simulation to watch PHANTOM detect threats in real time
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─── Red Agent Scoreboard ────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">🤖 Red Agent — Adversarial Scoreboard</div>',
           unsafe_allow_html=True)

score_col1, score_col2 = st.columns([3, 2])

with score_col1:
    render_scoreboard(st.session_state.red_agent.get_stats_dict())

with score_col2:
    render_attack_log(st.session_state.red_agent.get_recent_attacks())


# ─── Footer ──────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; padding:16px; color:#666; font-size:0.8em;">
    <b>PHANTOM v1.0</b> — Proactive Hybrid Anomaly & Threat Management Operations Network
    <br/>Hack Malenadu '26 | Pre-trained Models • Identity-Based Tracking • Multi-Network Awareness
    <br/>Built with PyTorch • SHAP • Phi-3 (Ollama) • Streamlit
</div>
""", unsafe_allow_html=True)


# ─── Auto-Refresh ────────────────────────────────────────────────────────────────
if st.session_state.running:
    time.sleep(0.8)
    st.rerun()
