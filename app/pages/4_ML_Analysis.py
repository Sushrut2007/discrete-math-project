import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data

st.set_page_config(page_title="ML Analysis", layout="wide")

df = load_full_data()

st.title("Machine Learning — Current Orbital State")
st.markdown("> The ML part looks at the current orbital features and identifies satellites that are unusual compared with satellites in similar groups.")

n_flagged = df['ml_flag'].sum()
n_clusters = df['cluster_id'].nunique()

c1, c2, c3 = st.columns(3)
c1.metric("Orbital Groups (K-Means)", n_clusters)
c2.metric("ML-Flagged Satellites", f"{n_flagged:,}")
c3.metric("Normal Satellites", f"{len(df) - n_flagged:,}")

st.markdown("### ML Anomaly Score Distribution")
fig = px.histogram(df, x='ml_anomaly_score', nbins=50, title="Distribution of Isolation Forest Scores")
st.plotly_chart(fig, use_container_width=True)

with st.expander("How it works"):
    st.markdown("""
    1. Satellites are grouped into orbital families using K-Means clustering.
    2. An Isolation Forest algorithm evaluates satellites within their specific cluster.
    3. Satellites that are statistically easy to isolate receive a negative anomaly score and are flagged.
    """)
    
st.markdown("---")
st.markdown("### Selected Satellite")
sat_options = df['OBJECT_NAME'] + " (" + df['NORAD_CAT_ID'].astype(str) + ")"
selected = st.selectbox("Select satellite:", sat_options)
norad = int(selected.split("(")[-1].replace(")", ""))
sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]

st.markdown(f"**Cluster ID:** {sat['cluster_id']}")
st.markdown(f"**Anomaly Label:** {'-1 (Unusual)' if sat['ml_flag'] else '1 (Normal)'}")
st.markdown(f"**Anomaly Score:** {sat['ml_anomaly_score']:.4f}")

if sat['ml_flag']:
    st.markdown("**Flagged**")
    st.markdown("> The ML model considers the satellite unusual compared with the other satellites it was evaluated against.")
else:
    st.markdown("**Not flagged**")
    st.markdown("> The ML model did not find it unusual.")
