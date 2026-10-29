import streamlit as st
import pandas as pd
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card
from diagnostics import get_ml_reasons

st.set_page_config(
    page_title="ML Detector Analysis",
    layout="wide"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Satellite data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Machine Learning Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">K-Means groups satellites by orbital features, and Isolation Forest identifies outliers within each group.</div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_ml_flagged = int(df['ml_flag'].sum())
n_ml_normal = n_total - n_ml_flagged
pct_flagged = (n_ml_flagged / n_total) * 100
n_clusters = int(df['cluster_id'].nunique())

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Analysed", f"{n_total:,}", "Satellites in the dataset", "#f8fafc")
with k2:
    render_metric_card("Flagged by ML", f"{n_ml_flagged:,}", f"{pct_flagged:.2f}% of all satellites", "#f87171", "#ef4444")
with k3:
    render_metric_card("Not Flagged by ML", f"{n_ml_normal:,}", f"{100 - pct_flagged:.2f}% of all satellites", "#34d399", "#10b981")
with k4:
    render_metric_card("Orbital Groups", f"{n_clusters}", "K-Means clusters (k=5)", "#818cf8")

st.markdown("<br>", unsafe_allow_html=True)

# Orbital Groups Summary Table
st.markdown("### The 5 Orbital Groups")

cluster_summary = df.groupby('cluster_id').agg(
    Total_Satellites=('NORAD_CAT_ID', 'count'),
    ML_Anomalies=('ml_flag', 'sum'),
    Mean_Altitude=('orbit_height', 'mean'),
    Mean_Inclination=('INCLINATION', 'mean'),
    Mean_Eccentricity=('ECCENTRICITY', 'mean')
).reset_index()

cluster_summary['Anomaly_Rate'] = (cluster_summary['ML_Anomalies'] / cluster_summary['Total_Satellites']) * 100

cluster_names = {
    2: "Mid-Inclination Group",
    0: "Sun-Synchronous and Near-Polar Group",
    1: "Higher-Altitude Polar Group",
    4: "Intermediate-Altitude Group",
    3: "Higher-Eccentricity Group"
}

cluster_reasons = {
    2: "Unusual eccentricity or altitude compared with other records in this group.",
    0: "Unusual inclination or eccentricity compared with other records in this group.",
    1: "Unusual inclination or altitude compared with other records in this group.",
    4: "Inclination values that differ from others in this group.",
    3: "Higher eccentricity compared with other records in this group."
}

cluster_summary['Group_Name'] = cluster_summary['cluster_id'].map(cluster_names)
cluster_summary['Outlier_Profile'] = cluster_summary['cluster_id'].map(cluster_reasons)

cluster_display = cluster_summary[[
    'cluster_id', 'Group_Name', 'Total_Satellites', 'ML_Anomalies', 
    'Mean_Altitude', 'Mean_Inclination', 'Mean_Eccentricity', 'Outlier_Profile'
]].sort_values(by='Total_Satellites', ascending=False)

cluster_display.columns = [
    'Group ID', 'Orbital Group', 'Total Satellites', 'Flagged Outliers',
    'Mean Altitude (km)', 'Mean Inclination (°)', 'Mean Eccentricity', 'Common Outlier Features'
]

st.dataframe(
    cluster_display.style.format({
        'Group ID': '{:d}',
        'Total Satellites': '{:,}',
        'Flagged Outliers': '{:,}',
        'Avg Altitude (km)': '{:,.1f}',
        'Avg Tilt (°)': '{:.2f}',
        'Avg Eccentricity': '{:.4f}'
    }),
    use_container_width=True,
    hide_index=True
)

st.caption("Isolation Forest uses a contamination setting of 5%, which influences the expected proportion of records labelled as outliers. It does not simply select the satellites with the greatest distance from the group.")

st.markdown("<br>", unsafe_allow_html=True)

# Table of Flagged Satellites with Reasons
st.markdown("### Satellites Flagged by Machine Learning")

ml_flagged_df = df[df['ml_flag'] == 1].copy()

# Compute reasons for all flagged satellites
ml_flagged_df['Reason'] = ml_flagged_df.apply(lambda r: get_ml_reasons(r)[0], axis=1)

search_term = st.text_input("Filter by satellite name or NORAD ID:", placeholder="e.g. EXPRESS, 38745, STARLINK...")
if search_term.strip():
    t = search_term.strip().lower()
    ml_flagged_df = ml_flagged_df[
        ml_flagged_df['OBJECT_NAME'].str.lower().str.contains(t, na=False) |
        ml_flagged_df['NORAD_CAT_ID'].astype(str).str.contains(t, na=False)
    ]

display_table = ml_flagged_df[[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'cluster_id', 'orbit_height',
    'INCLINATION', 'ECCENTRICITY', 'ml_anomaly_score', 'Reason'
]].sort_values(by='orbit_height', ascending=False)

display_table.columns = [
    'NORAD ID', 'Satellite Name', 'Group', 'Altitude (km)',
    'Inclination (°)', 'Eccentricity', 'Decision Score', 'Why Flagged by ML'
]

st.dataframe(
    display_table.style.format({
        'Altitude (km)': '{:,.1f}',
        'Tilt (°)': '{:.2f}',
        'Eccentricity': '{:.4f}',
        'Group': '{:d}',
        'Decision Score': '{:.4f}'
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(f"Showing {len(display_table):,} satellites flagged by ML. Use Satellite Explorer to view an individual satellite's orbital features and results.")
