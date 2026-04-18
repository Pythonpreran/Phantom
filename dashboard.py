"""
PHANTOM — Model Analysis Dashboard (Streamlit)
LightGBM + Optuna HPO detection engine evaluation & metrics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import sys

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phantom_engine import (
    DataHandler, FeatureEngineer, DetectionEngine,
    CorrelationEngine, DecisionEngine, ResponseEngine,
    Evaluator, SyntheticLogGenerator
)

# ───────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ───────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PHANTOM — Model Analysis",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ───────────────────────────────────────────────────────────────────
#  CUSTOM CSS
# ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Inter:wght@300;400;600;700;900&display=swap');

    :root {
        --bg-primary: #0a0e17;
        --bg-card: #111827;
        --border: #1e293b;
        --accent: #06d6a0;
        --danger: #ef4444;
        --warn: #f59e0b;
        --info: #3b82f6;
        --text: #e2e8f0;
        --muted: #64748b;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0e17 0%, #0f172a 50%, #0a0e17 100%);
    }

    .block-container {
        padding-top: 1.5rem;
        max-width: 100%;
    }

    /* Hide sidebar completely */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, #111827 0%, #1e293b 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent), var(--info));
    }

    .metric-card.danger::before {
        background: linear-gradient(90deg, #ef4444, #dc2626);
    }

    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #06d6a0;
        line-height: 1;
        margin-bottom: 0.4rem;
    }

    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Header */
    .phantom-header {
        text-align: center;
        padding: 0.5rem 0 1.5rem;
    }

    .phantom-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #06d6a0, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 6px;
        margin-bottom: 0.15rem;
    }

    .phantom-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #64748b;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* Section headers */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: #e2e8f0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 1rem;
        letter-spacing: 1px;
    }

    /* Detail box */
    .detail-box {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #94a3b8;
    }

    /* Hide streamlit extras */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────
#  HELPER FUNCTIONS
# ───────────────────────────────────────────────────────────────────

def create_gauge_chart(value, title, color="#06d6a0"):
    """Create a plotly gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        title={'text': title, 'font': {'color': '#94a3b8', 'size': 13, 'family': 'Inter'}},
        number={'suffix': '%', 'font': {'color': color, 'size': 36, 'family': 'JetBrains Mono'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#334155'},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': '#1e293b',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 60], 'color': '#1e293b'},
                {'range': [60, 80], 'color': '#1a2332'},
                {'range': [80, 100], 'color': '#162030'}
            ],
            'threshold': {
                'line': {'color': '#ef4444', 'width': 2},
                'thickness': 0.8,
                'value': 90
            }
        }
    ))
    fig.update_layout(
        height=220,
        margin=dict(t=40, b=0, l=30, r=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#e2e8f0'}
    )
    return fig


def create_confusion_matrix_heatmap(cm):
    """Create a confusion matrix heatmap."""
    labels = ['Normal', 'Attack']
    cm_arr = np.array(cm)

    fig = go.Figure(data=go.Heatmap(
        z=cm_arr,
        x=labels,
        y=labels,
        text=[[f"{v:,}" for v in row] for row in cm_arr],
        texttemplate="%{text}",
        textfont={"size": 18, "family": "JetBrains Mono", "color": "white"},
        colorscale=[[0, '#0f172a'], [0.5, '#1e40af'], [1, '#06d6a0']],
        showscale=False,
        hovertemplate="True: %{y}<br>Predicted: %{x}<br>Count: %{text}<extra></extra>"
    ))

    fig.update_layout(
        xaxis_title="Predicted",
        yaxis_title="Actual",
        height=300,
        margin=dict(t=20, b=60, l=80, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#94a3b8', 'family': 'Inter'},
        xaxis={'side': 'bottom'}
    )
    return fig


def create_confidence_histogram(probabilities, predictions):
    """Create probability distribution histogram."""
    normal_probs = [p for p, pred in zip(probabilities, predictions) if pred == 0]
    attack_probs = [p for p, pred in zip(probabilities, predictions) if pred == 1]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=normal_probs, name='Normal',
        marker_color='#06d6a0', opacity=0.7,
        nbinsx=50
    ))
    fig.add_trace(go.Histogram(
        x=attack_probs, name='Attack',
        marker_color='#ef4444', opacity=0.7,
        nbinsx=50
    ))

    # Threshold line
    fig.add_vline(x=0.85, line_dash="dash", line_color="#f59e0b",
                  annotation_text="Threshold (0.85)", annotation_font_color="#f59e0b")

    fig.update_layout(
        barmode='overlay',
        height=280,
        margin=dict(t=20, b=40, l=50, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis={'title': 'Attack Probability', 'color': '#64748b', 'gridcolor': '#1e293b'},
        yaxis={'title': 'Count', 'color': '#64748b', 'gridcolor': '#1e293b'},
        legend={'font': {'color': '#94a3b8', 'family': 'Inter'}},
        font={'family': 'Inter', 'color': '#e2e8f0'}
    )
    return fig


def create_attack_type_bar(responses):
    """Create attack type distribution bar chart."""
    type_counts = {}
    for r in responses:
        for t in r.get('unique_attack_types', []):
            type_counts[t] = type_counts.get(t, 0) + 1

    if not type_counts:
        return go.Figure()

    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [t[0] for t in sorted_types[:10]]
    values = [t[1] for t in sorted_types[:10]]

    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(
            color=values,
            colorscale=[[0, '#1e3a5f'], [0.5, '#3b82f6'], [1, '#06d6a0']],
        ),
        text=values,
        textposition='outside',
        textfont={'family': 'JetBrains Mono', 'size': 11, 'color': '#94a3b8'}
    )])

    fig.update_layout(
        height=300,
        margin=dict(t=10, b=30, l=120, r=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis={'showgrid': True, 'gridcolor': '#1e293b', 'color': '#64748b'},
        yaxis={'color': '#94a3b8'},
        font={'family': 'Inter', 'color': '#e2e8f0'}
    )
    return fig


def create_group_size_chart(responses):
    """Create group size distribution."""
    sizes = [r['size'] for r in responses]
    severities = [r['severity'] for r in responses]
    confs = [r['avg_confidence'] for r in responses]

    color_map = {'CRITICAL': '#ef4444', 'HIGH': '#f59e0b', 'MEDIUM': '#3b82f6'}

    fig = go.Figure(data=[go.Scatter(
        x=list(range(1, len(sizes) + 1)),
        y=sizes,
        mode='markers',
        marker=dict(
            size=[c * 30 + 5 for c in confs],
            color=[color_map.get(s, '#64748b') for s in severities],
            line=dict(width=1, color='#1e293b'),
            opacity=0.85
        ),
        text=[f"Group {i+1}<br>Size: {s}<br>Severity: {sev}<br>Confidence: {c:.2%}"
              for i, (s, sev, c) in enumerate(zip(sizes, severities, confs))],
        hoverinfo='text'
    )])

    fig.update_layout(
        height=280,
        margin=dict(t=20, b=40, l=60, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis={'title': 'Attack Group #', 'color': '#64748b', 'gridcolor': '#1e293b'},
        yaxis={'title': 'Group Size', 'color': '#64748b', 'gridcolor': '#1e293b'},
        font={'family': 'Inter', 'color': '#e2e8f0'}
    )
    return fig


# ───────────────────────────────────────────────────────────────────
#  RUN PIPELINE (CACHED)
# ───────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def run_pipeline():
    """Run the full PHANTOM pipeline and cache results."""
    base = os.path.dirname(os.path.abspath(__file__))
    train_path = os.path.join(base, 'train.csv')
    test_path = os.path.join(base, 'test.csv')

    # Step 1
    train_df = DataHandler.load_and_clean(train_path)
    test_df = DataHandler.load_and_clean(test_path)
    X_train, y_train, _ = DataHandler.separate_features_labels(train_df)
    X_test, y_test, attack_cats = DataHandler.separate_features_labels(test_df)

    # Step 2
    X_train = FeatureEngineer.add_behavioral_features(X_train)
    X_test = FeatureEngineer.add_behavioral_features(X_test)
    X_train, X_test = FeatureEngineer.encode_and_align(X_train, X_test)
    X_train_s, X_test_s, scaler = FeatureEngineer.scale_features(X_train, X_test)

    # Step 3
    engine = DetectionEngine()
    if not engine.load():
        engine.train(X_train_s, y_train)
    preds, probas = engine.predict(X_test_s, threshold=0.7)

    # Step 4
    groups = CorrelationEngine.correlate(preds, probas, attack_cats)

    # Step 5
    decisions = DecisionEngine.assess(groups)

    # Step 6
    responses = ResponseEngine.respond(decisions)

    # Step 7
    metrics = Evaluator.evaluate(y_test, preds)

    return {
        'metrics': metrics,
        'responses': responses,
        'predictions': preds.tolist(),
        'probabilities': probas.tolist(),
        'y_test': y_test.tolist(),
        'attack_cats': attack_cats.tolist() if attack_cats is not None else []
    }


# ───────────────────────────────────────────────────────────────────
#  MAIN CONTENT
# ───────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="phantom-header">
    <div class="phantom-title">P H A N T O M</div>
    <div class="phantom-subtitle">Model Analysis Dashboard</div>
</div>
""", unsafe_allow_html=True)

# Load data
with st.spinner("Loading pipeline results..."):
    results = run_pipeline()

metrics = results['metrics']
responses = results['responses']
predictions = results['predictions']
probabilities = results['probabilities']


# ─── TOP METRICS ───

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{metrics['accuracy']*100:.1f}%</div>
        <div class="metric-label">Accuracy</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    report = metrics['report']
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #3b82f6;">{report['weighted avg']['precision']*100:.1f}%</div>
        <div class="metric-label">Precision (W)</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #8b5cf6;">{report['weighted avg']['recall']*100:.1f}%</div>
        <div class="metric-label">Recall (W)</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #f59e0b;">{report['weighted avg']['f1-score']*100:.1f}%</div>
        <div class="metric-label">F1-Score (W)</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #94a3b8;">{metrics['total_samples']:,}</div>
        <div class="metric-label">Test Samples</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── CLASSIFICATION REPORT ───

st.markdown('<div class="section-header">CLASSIFICATION REPORT</div>', unsafe_allow_html=True)

report_df = pd.DataFrame({
    'Class': ['Normal', 'Attack', 'Macro Avg', 'Weighted Avg'],
    'Precision': [report['Normal']['precision'], report['Attack']['precision'],
                  report['macro avg']['precision'], report['weighted avg']['precision']],
    'Recall': [report['Normal']['recall'], report['Attack']['recall'],
               report['macro avg']['recall'], report['weighted avg']['recall']],
    'F1-Score': [report['Normal']['f1-score'], report['Attack']['f1-score'],
                 report['macro avg']['f1-score'], report['weighted avg']['f1-score']],
    'Support': [int(report['Normal']['support']), int(report['Attack']['support']),
                int(report['macro avg']['support']), int(report['weighted avg']['support'])]
})
st.dataframe(report_df, use_container_width=True, hide_index=True)


# ─── CHARTS ROW 1 ───

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-header">CONFUSION MATRIX</div>', unsafe_allow_html=True)
    fig = create_confusion_matrix_heatmap(metrics['confusion_matrix'])
    st.plotly_chart(fig, use_container_width=True)

    cm = np.array(metrics['confusion_matrix'])
    tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
    st.markdown(f"""
    <div class="detail-box">
        True Negatives: <span style="color: #06d6a0;">{tn:,}</span> &nbsp;|&nbsp;
        False Positives: <span style="color: #ef4444;">{fp:,}</span><br>
        False Negatives: <span style="color: #f59e0b;">{fn:,}</span> &nbsp;|&nbsp;
        True Positives: <span style="color: #06d6a0;">{tp:,}</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-header">PROBABILITY DISTRIBUTION</div>', unsafe_allow_html=True)
    fig = create_confidence_histogram(probabilities, predictions)
    st.plotly_chart(fig, use_container_width=True)


# ─── CHARTS ROW 2 ───

st.markdown('<div class="section-header">ATTACK GROUP ANALYSIS</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    fig = create_group_size_chart(responses)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = create_attack_type_bar(responses)
    st.plotly_chart(fig, use_container_width=True)


# ─── RESPONSE LOG ───

st.markdown('<div class="section-header">RESPONSE ACTION LOG</div>', unsafe_allow_html=True)
if responses:
    log_data = []
    for r in responses[:30]:
        log_data.append({
            'Group': f"#{r['group_id']}",
            'Size': r['size'],
            'Severity': r['severity'],
            'Confidence': f"{r['avg_confidence']:.2%}",
            'Type': r['interpretation'][:40],
            'Action': r['action_code']
        })
    st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
