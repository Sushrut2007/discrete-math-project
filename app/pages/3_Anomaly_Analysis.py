import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data

st.set_page_config(page_title="Anomaly Analysis", layout="wide")
df = load_full_data()

st.title("System-Wide Anomaly Analysis")
st.markdown("Detailed breakdown of the integrated results across the catalog.")

counts = df['anomaly_score'].value_counts()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Score 0 (Nominal)", f"{counts.get(0, 0):,}")
c2.metric("Score 1 (Low Warning)", f"{counts.get(1, 0):,}")
c3.metric("Score 2 (High Warning)", f"{counts.get(2, 0):,}")
c4.metric("Score 3 (Critical)", f"{counts.get(3, 0):,}")

st.markdown("---")
st.markdown("### Score Combination Analysis")
st.markdown("The final score is the number of methods that detected unusual behaviour or structure. Understanding which combinations triggered the score is critical for operational awareness.")

anomalous = df[df['anomaly_score'] > 0].copy()
def get_combo(row):
    parts = []
    if row['ml_flag']: parts.append("ML")
    if row['dm_flag']: parts.append("DM")
    if row['temporal_flag']: parts.append("Temporal")
    return " + ".join(parts)
    
anomalous['Combination'] = anomalous.apply(get_combo, axis=1)
combo_counts = anomalous['Combination'].value_counts().reset_index()
combo_counts.columns = ['Trigger Combination', 'Number of Satellites']

c_table, c_chart = st.columns([1, 1.5])
with c_table:
    st.dataframe(combo_counts, use_container_width=True, hide_index=True)
    
with c_chart:
    fig = px.bar(combo_counts, x='Number of Satellites', y='Trigger Combination', orientation='h', 
                 color='Number of Satellites', color_continuous_scale='Reds')
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis={'categoryorder':'total ascending'}, showlegend=False, coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
