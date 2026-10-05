import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data

st.set_page_config(page_title="Overview", layout="wide")

df = load_full_data()
if df.empty:
    st.error("Processed data files are missing.")
    st.stop()

st.title("ML and Discrete Mathematics Based Satellite Anomaly Detection")
st.markdown("> Analyze satellite orbital data using machine learning, a similarity graph, and recent orbital changes.")
st.markdown("---")

col1, col2, col3, col4, col5, col6 = st.columns(6)
counts = df['anomaly_score'].value_counts()

col1.metric("Total Satellites", f"{len(df):,}")
col2.metric("Latest Observation", str(df['EPOCH'].iloc[0])[:10] if 'EPOCH' in df.columns else "N/A")
col3.metric("Score 0", f"{counts.get(0, 0):,}")
col4.metric("Score 1", f"{counts.get(1, 0):,}")
col5.metric("Score 2", f"{counts.get(2, 0):,}")
col6.metric("Score 3", f"{counts.get(3, 0):,}")

st.markdown("### Anomaly Score Distribution")

score_df = pd.DataFrame({'Score': [0, 1, 2, 3], 'Count': [counts.get(i, 0) for i in range(4)]})
fig = px.bar(score_df, x='Score', y='Count', title="Distribution of Final Scores",
             color='Score', color_continuous_scale=['#4CAF50', '#FFC107', '#FF9800', '#F44336'])
fig.update_layout(xaxis=dict(tickmode='linear', dtick=1), showlegend=False, coloraxis_showscale=False)
st.plotly_chart(fig, use_container_width=True)

st.markdown("""
- **0:** No detector flagged the satellite
- **1:** One detector flagged it
- **2:** Two detectors flagged it
- **3:** All three detectors flagged it

> Score 3 means that all three methods found unusual behaviour or structure. These satellites should receive the highest attention for further investigation.
""")

st.markdown("---")
st.markdown("### Three-Method Overview")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**ML**\n> Checks whether the current orbital state is unusual compared with other satellites.")
with c2:
    st.markdown("**DM Graph**\n> Checks whether the satellite is strongly isolated in the orbital-similarity graph.")
with c3:
    st.markdown("**Temporal**\n> Checks whether the satellite's recent orbital change is unusual compared with its own recent history.")
