import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data

st.set_page_config(page_title="Anomaly Analysis", layout="wide")

df = load_full_data()

st.title("Anomaly Analysis")
st.markdown("### Integrated Anomaly Result")
st.markdown("> The final score is the number of methods that detected unusual behaviour or structure.")

counts = df['anomaly_score'].value_counts()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("#### Score 0")
    st.markdown("No method flagged the satellite.")
    st.markdown(f"**{counts.get(0, 0):,}** satellites")
with col2:
    st.markdown("#### Score 1")
    st.markdown("One method flagged the satellite.")
    st.markdown(f"**{counts.get(1, 0):,}** satellites")
with col3:
    st.markdown("#### Score 2")
    st.markdown("Two methods flagged the satellite.")
    st.markdown(f"**{counts.get(2, 0):,}** satellites")
with col4:
    st.markdown("#### Score 3")
    st.markdown("All three methods flagged the satellite.")
    st.markdown(f"**{counts.get(3, 0):,}** satellites")
    
st.markdown("---")
st.markdown("### Score Combination Analysis")

anomalous = df[df['anomaly_score'] > 0].copy()
def get_combo(row):
    parts = []
    if row['ml_flag']: parts.append("ML")
    if row['dm_flag']: parts.append("DM")
    if row['temporal_flag']: parts.append("Temporal")
    return " + ".join(parts)
    
anomalous['Combination'] = anomalous.apply(get_combo, axis=1)
combo_counts = anomalous['Combination'].value_counts().reset_index()
combo_counts.columns = ['Combination', 'Count']

c1, c2 = st.columns(2)
with c1:
    st.dataframe(combo_counts, use_container_width=True, hide_index=True)
with c2:
    fig = px.bar(combo_counts, x='Count', y='Combination', orientation='h', title="Methods Flagging Satellites")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
