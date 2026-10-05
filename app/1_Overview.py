import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data

st.set_page_config(page_title="Orbital Anomaly Overview", layout="wide")
df = load_full_data()
if df.empty:
    st.error("SYSTEM ERROR: Processed data files are missing. Cannot load catalog.")
    st.stop()

st.markdown("""
<style>
    .metric-card {
        background-color: #1E2127;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #0078D7;
        margin-bottom: 20px;
    }
    .metric-title { color: #8B949E; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;}
    .metric-val { color: #E0E0E0; font-size: 28px; font-weight: bold; }
    .header-style { font-size: 20px; font-weight: bold; border-bottom: 1px solid #30363D; padding-bottom: 10px; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

st.title("Spacecraft Catalog Health")
st.markdown("Real-time monitoring of orbital anomalies across the active tracking catalog.")

counts = df['anomaly_score'].value_counts()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Tracked Objects</div><div class="metric-val">{len(df):,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card" style="border-left: 5px solid #4CAF50;"><div class="metric-title">Nominal Status</div><div class="metric-val" style="color: #4CAF50;">{counts.get(0, 0):,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card" style="border-left: 5px solid #FFC107;"><div class="metric-title">Active Warnings</div><div class="metric-val" style="color: #FFC107;">{counts.get(1, 0) + counts.get(2, 0):,}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card" style="border-left: 5px solid #F44336;"><div class="metric-title">Critical Alerts</div><div class="metric-val" style="color: #F44336;">{counts.get(3, 0):,}</div></div>', unsafe_allow_html=True)

st.markdown("<div class='header-style'>Catalog Anomaly Distribution</div>", unsafe_allow_html=True)

score_df = pd.DataFrame({'Alert Level': ['Nominal', 'Low Warning', 'High Warning', 'Critical'], 'Count': [counts.get(i, 0) for i in range(4)]})
fig = px.bar(score_df, x='Alert Level', y='Count', text='Count',
             color='Alert Level', color_discrete_sequence=['#4CAF50', '#FFC107', '#FF9800', '#F44336'])
fig.update_traces(textposition='outside')
fig.update_layout(
    template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    xaxis_title="", yaxis_title="Number of Spacecraft", showlegend=False,
    height=300, margin=dict(l=0, r=0, t=10, b=0)
)
st.plotly_chart(fig, use_container_width=True)

st.info("System evaluates spacecraft using three independent models: Statistical state, orbital topology (neighborhood), and recent maneuver history. An object receives a Critical alert only when all three systems independently detect anomalous behaviour.")
