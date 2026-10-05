import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data

st.set_page_config(page_title="ML Analysis", layout="wide")
df = load_full_data()

st.title("Machine Learning Analysis")
st.markdown("### Current Orbital State Evaluation")
st.markdown("The ML part looks at the current orbital features and identifies satellites that are unusual compared with satellites in similar groups.")

n_flagged = df['ml_flag'].sum()
n_clusters = df['cluster_id'].nunique()

c1, c2, c3 = st.columns(3)
c1.metric("Orbital Groups (K-Means)", n_clusters)
c2.metric("ML-Flagged Satellites", f"{n_flagged:,}")
c3.metric("Nominal Satellites", f"{len(df) - n_flagged:,}")

col_chart, col_exp = st.columns([2, 1])
with col_chart:
    fig = px.histogram(df, x='ml_anomaly_score', nbins=50, 
                       color_discrete_sequence=['#0078D7'])
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Isolation Forest Score (Negative = Outlier)", yaxis_title="Count",
        title="Distribution of ML Scores"
    )
    st.plotly_chart(fig, use_container_width=True)

with col_exp:
    with st.container(border=True):
        st.markdown("#### How it works")
        st.markdown("1. Satellites are grouped into orbital families using K-Means clustering.")
        st.markdown("2. An Isolation Forest algorithm evaluates satellites within their specific cluster.")
        st.markdown("3. Satellites that are statistically easy to isolate receive a negative anomaly score and are flagged.")

st.markdown("---")
st.markdown("### Object Inspection")
sat_options = df['NORAD_CAT_ID'].astype(str) + " - " + df['OBJECT_NAME'] 
selected = st.selectbox("Select Target:", sat_options, key="ml_sel")
norad = int(selected.split(" - ")[0])
sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Orbital Group ID:** {sat['cluster_id']}")
        st.markdown(f"**Anomaly Score:** {sat['ml_anomaly_score']:.4f}")
    with col2:
        if sat['ml_flag']:
            st.error("**Status: Flagged**")
            st.markdown("The ML model considers the satellite unusual compared with the other satellites it was evaluated against.")
        else:
            st.success("**Status: Not flagged**")
            st.markdown("The ML model did not find it unusual.")
