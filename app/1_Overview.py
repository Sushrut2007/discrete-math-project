import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from data_loader import load_full_data

st.set_page_config(page_title="Orbital Anomaly Overview", layout="wide", initial_sidebar_state="expanded")
df = load_full_data()
if df.empty:
    st.error("SYSTEM ERROR: Processed data files are missing. Cannot load catalog.")
    st.stop()

# --- Custom Styling (SpaceDebrisRadar.AI Aesthetic) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    
    .glass-card {
        background: linear-gradient(145deg, rgba(30, 35, 45, 0.7), rgba(20, 25, 30, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    .premium-metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 8px;
        color: #e0e0e8;
    }
    
    .premium-metric-label {
        font-size: 0.85rem;
        color: #8B949E;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }
    
    .sub-glow {
        height: 2px;
        width: 60px;
        background: linear-gradient(90deg, #00d4ff, transparent);
        margin-bottom: 20px;
    }
    
    .status-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #10b981;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 1);
        animation: pulse-green 2s infinite;
    }
    
    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    /* Header Gradient */
    .title-grad {
        background: -webkit-linear-gradient(0deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title-grad'>ORBITAL ANOMALY RADAR</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8B949E; font-size: 1.1rem; margin-bottom: 30px;'>Low Earth Orbit & Deep Space Traffic Monitoring System.</p>", unsafe_allow_html=True)

counts = df['anomaly_score'].value_counts()

# --- Operational Snapshot ---
st.markdown("### Operational Snapshot")
st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value">{len(df):,}</div>
        <div class="premium-metric-label">Tracked Objects</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value" style="background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); -webkit-background-clip: text; color: transparent;">{counts.get(0, 0):,}</div>
        <div class="premium-metric-label">Nominal Status</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="glass-card">
        <div class="premium-metric-value" style="background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); -webkit-background-clip: text; color: transparent;">{counts.get(1, 0):,}</div>
        <div class="premium-metric-label">Active Warnings</div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown(f"""
    <div class="glass-card" style="border-left: 2px solid #ef4444;">
        <div class="premium-metric-value" style="background: linear-gradient(135deg, #f87171 0%, #ef4444 100%); -webkit-background-clip: text; color: transparent;">{counts.get(2, 0):,}</div>
        <div class="premium-metric-label">Critical Alerts</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Core Content ---
left_col, right_col = st.columns([1.5, 1])

with left_col:
    st.markdown("#### Catalog Anomaly Distribution")
    st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)
    
    with st.container():
        score_df = pd.DataFrame({'Alert Level': ['Nominal', 'Warning', 'Critical'], 'Count': [counts.get(i, 0) for i in range(3)]})
        fig = px.bar(score_df, x='Alert Level', y='Count', text='Count',
                     color='Alert Level', color_discrete_sequence=['#22c55e', '#fbbf24', '#ef4444'])
        fig.update_traces(textposition='outside', marker_line_width=0)
        fig.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="", yaxis_title="Number of Spacecraft", showlegend=False,
            height=300, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.markdown("#### System Status")
    st.markdown('<div class="sub-glow"></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="glass-card" style="padding: 15px;">
        <div style="display: flex; align-items: center;">
            <div class="status-pulse"></div>
            <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">System Operational</div>
        </div>
        <div style="font-size: 0.75rem; color: #64748b; margin-top: 8px; margin-left: 18px;">
            Last sync epoch: {str(df['EPOCH'].iloc[0])[:10] if 'EPOCH' in df.columns else 'N/A'} UTC<br>
            Pipeline Status: Nominal
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="glass-card" style="margin-top: 10px;">
        <p style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0px;">
            The system evaluates spacecraft telemetry using two independent models: Statistical state distribution and orbital topology (neighborhood). An object receives a <b>Critical alert</b> when both systems independently detect anomalous behaviour.
        </p>
    </div>
    """, unsafe_allow_html=True)
