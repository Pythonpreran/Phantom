"""
PHANTOM  --  Dashboard UI Components
====================================
Reusable Streamlit widgets for the SOC Dashboard.
"""

import streamlit as st


def render_alert_card(alert: dict):
    """Render a single alert card with severity coloring."""
    severity = alert.get("severity", "LOW")
    color_map = {
        "CRITICAL": ("🔴", "#ff1744", "#2d0a0a"),
        "HIGH":     ("🟠", "#ff9100", "#2d1a0a"),
        "MEDIUM":   ("🟡", "#ffea00", "#2d2a0a"),
        "LOW":      ("🟢", "#00e676", "#0a2d12"),
        "SUPPRESSED": ("⚪", "#90a4ae", "#1a1a1a"),
    }
    icon, color, bg = color_map.get(severity, ("⚪", "#90a4ae", "#1a1a1a"))

    stage_num = alert.get("stage_num", 0)
    stage_bar = "█" * stage_num + "░" * (5 - stage_num)

    ip = alert.get("ip", "unknown")
    user_id = alert.get("user_id", " -- ")
    mitre_id = alert.get("mitre_id", " -- ")
    stage_name = alert.get("current_stage", alert.get("stage", ""))
    layers = ", ".join(alert.get("layers", []))
    zone = alert.get("zone", " -- ")

    st.markdown(f"""
    <div style="
        background: {bg};
        border-left: 4px solid {color};
        padding: 12px 16px;
        margin: 6px 0;
        border-radius: 8px;
        font-family: 'Cascadia Code', 'Fira Code', monospace;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1.1em; font-weight:700; color:{color};">
                {icon} {severity}
            </span>
            <span style="color:#888; font-size:0.8em;">{mitre_id}</span>
        </div>
        <div style="color:#e0e0e0; margin-top:4px;">
            <b>IP:</b> <code>{ip}</code> &nbsp;|&nbsp; <b>User:</b> <code>{user_id}</code>
        </div>
        <div style="color:#aaa; margin-top:2px; font-size:0.9em;">
            {stage_name} &nbsp; <span style="letter-spacing:2px;">{stage_bar}</span> &nbsp; {stage_num}/5
        </div>
        <div style="color:#777; margin-top:2px; font-size:0.8em;">
            Layers: {layers} &nbsp;|&nbsp; Zone: {zone}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_timeline(history: list):
    """Render kill chain timeline for an incident."""
    if not history:
        st.markdown("*No progression data yet*")
        return

    for entry in history:
        stage_num = entry.get("stage_num", 0)
        stage_colors = {1: "🔵", 2: "🟡", 3: "🟠", 4: "🔴", 5: "💀"}
        icon = stage_colors.get(stage_num, "⚪")

        ts = entry.get("timestamp", "")
        if "T" in ts:
            ts = ts.split("T")[1][:8]

        zones_str = ""
        zones = entry.get("zones", [])
        if zones:
            zones_str = f" [{', '.join(zones)}]"

        st.markdown(f"""
        <div style="
            display: flex; align-items: center; gap: 12px;
            padding: 6px 0;
            border-left: 2px solid #444;
            padding-left: 16px;
            margin-left: 8px;
        ">
            <span style="font-size:1.2em;">{icon}</span>
            <div>
                <span style="color:#aaa; font-size:0.85em;">{ts}</span>
                <br/>
                <span style="color:#e0e0e0; font-weight:600;">{entry.get('stage', '')}</span>
                <span style="color:#888; font-size:0.85em;">  --  {entry.get('mitre_id', '')} {entry.get('mitre_name', '')}</span>
                <span style="color:#666; font-size:0.75em;">{zones_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_shap_bars(shap_top3: list):
    """Render SHAP feature contribution bars."""
    if not shap_top3:
        st.markdown("*No SHAP data*")
        return

    for feat, pct in shap_top3:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(min(pct, 1.0), text=f"**{feat}**")
        with col2:
            st.markdown(f"<span style='color:#00e5ff; font-weight:700;'>{pct:.0%}</span>",
                       unsafe_allow_html=True)


def render_playbook(playbook_text: str):
    """Render LLM-generated playbook in a styled card."""
    if not playbook_text:
        st.markdown("*Generating playbook...*")
        return

    st.markdown(f"""
    <div style="
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 0.9em;
        line-height: 1.6;
        color: #c9d1d9;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    ">
{playbook_text}
    </div>
    """, unsafe_allow_html=True)


def render_scoreboard(stats: dict):
    """Render Red Agent scoreboard."""
    launched = stats.get("launched", 0)
    caught = stats.get("caught", 0)
    missed = stats.get("missed", 0)
    rate = stats.get("detection_rate", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("⚔️ Attacks Launched", launched)
    with col2:
        delta = f"+{stats.get('delta_caught', 0)}"
        st.metric("🛡️ Caught", f"{caught} ({rate:.0%})", delta=delta)
    with col3:
        st.metric("💨 Evaded", missed)
    with col4:
        # Detection rate bar
        if launched > 0:
            st.progress(min(rate, 1.0), text=f"Detection Rate: {rate:.0%}")
        else:
            st.progress(0.0, text="No attacks yet")


def render_attack_log(attacks: list):
    """Render recent Red Agent attack log."""
    if not attacks:
        st.markdown("*No attacks launched yet*")
        return

    for atk in reversed(attacks[-8:]):
        result = atk.get("result", "pending")
        result_color = {"CAUGHT": "🟢", "EVADED": "🔴", "pending": "⏳"}.get(result, "⚪")

        st.markdown(f"""
        <div style="
            display: flex; justify-content: space-between; align-items: center;
            padding: 6px 12px; margin: 3px 0;
            background: #161b22; border-radius: 6px;
            font-size: 0.85em;
        ">
            <span style="color:#8b949e;">#{atk.get('attack_num', '?')}</span>
            <span style="color:#e0e0e0;">{atk.get('type', '')}</span>
            <span style="color:#8b949e;">{atk.get('ip', '')}</span>
            <span>{result_color} {result}</span>
        </div>
        """, unsafe_allow_html=True)


def render_network_zones(zone_stats: dict):
    """Render multi-network zone overview."""
    for zone, info in zone_stats.items():
        trust_colors = {
            "critical": "#ff1744",
            "high": "#00e676",
            "low": "#ffea00",
            "untrusted": "#ff9100",
        }
        color = trust_colors.get(info.get("trust", ""), "#888")
        count = info.get("event_count", 0)
        alerts = info.get("alert_count", 0)

        st.markdown(f"""
        <div style="
            display: flex; justify-content: space-between;
            padding: 4px 8px; margin: 2px 0;
            background: #161b22; border-radius: 4px;
            border-left: 3px solid {color};
        ">
            <span style="color:#e0e0e0; font-weight:600;">{zone.upper()}</span>
            <span style="color:#888;">Events: {count} | Alerts: {alerts}</span>
        </div>
        """, unsafe_allow_html=True)
