import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data

st.set_page_config(page_title="Orbital Anomaly Overview", layout="wide")

df = load_full_data()
if df.empty:
    st.error("SYSTEM ERROR: Processed data files are missing. Cannot load catalog.")
    st.stop()

# Custom CSS for a cleaner, dashboard-like feel
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
    .header-style { font-size: 24px; font-weight: bold; border-bottom: 1px solid #30363D; padding-bottom: 10px; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

st.title("Catalog Anomaly Overview")
st.markdown("Monitor satellite orbital data using machine learning, similarity graphs, and recent orbital transitions.")
st.markdown("---")

counts = df['anomaly_score'].value_counts()

# Top Metrics Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Tracked Catalog</div><div class="metric-val">{len(df):,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Nominal (Score 0)</div><div class="metric-val" style="color: #4CAF50;">{counts.get(0, 0):,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Warnings (Score 1-2)</div><div class="metric-val" style="color: #FFC107;">{counts.get(1, 0) + counts.get(2, 0):,}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card" style="border-left: 5px solid #F44336;"><div class="metric-title">Critical (Score 3)</div><div class="metric-val" style="color: #F44336;">{counts.get(3, 0):,}</div></div>', unsafe_allow_html=True)

st.markdown("<div class='header-style'>System Anomaly Distribution</div>", unsafe_allow_html=True)

col_chart, col_exp = st.columns([2, 1])

with col_chart:
    score_df = pd.DataFrame({'Score': ['Score 0', 'Score 1', 'Score 2', 'Score 3'], 'Count': [counts.get(i, 0) for i in range(4)]})
    fig = px.bar(score_df, x='Score', y='Count', text='Count',
                 color='Score', color_discrete_sequence=['#4CAF50', '#FFC107', '#FF9800', '#F44336'])
    fig.update_traces(textposition='outside')
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="", yaxis_title="Number of Satellites", showlegend=False,
        height=350, margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_exp:
    st.markdown("### Interpretation")
    st.markdown("- **Score 0:** Nominal state. No detectors triggered.")
    st.markdown("- **Score 1:** Low confidence. One detector triggered.")
    st.markdown("- **Score 2:** High confidence. Two detectors triggered.")
    st.markdown("- **Score 3:** Critical consensus. All three detectors triggered.")
    st.info("Score 3 means that all three methods found unusual behaviour or structure. These satellites should receive the highest attention for further investigation.")

st.markdown("<br><div class='header-style'>Detection Architectures</div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.markdown("#### 1. Machine Learning")
        st.markdown("Checks whether the current orbital state is unusual compared with other satellites in the same orbital regime.")
with c2:
    with st.container(border=True):
        st.markdown("#### 2. DM Graph")
        st.markdown("Checks whether the satellite is strongly isolated structurally in the orbital-similarity graph.")
with c3:
    with st.container(border=True):
        st.markdown("#### 3. Temporal")
        st.markdown("Checks whether the satellite's recent orbital change is unusual compared with its own recent history.")
