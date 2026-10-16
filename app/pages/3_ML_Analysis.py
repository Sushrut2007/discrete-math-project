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
    st.error("Catalog data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Machine Learning Detector Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">How K-Means groups orbital shells and how Isolation Forest detects outliers within each group.</div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_ml_flagged = int(df['ml_flag'].sum())
n_ml_normal = n_total - n_ml_flagged
pct_flagged = (n_ml_flagged / n_total) * 100
n_clusters = int(df['cluster_id'].nunique())

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Analysed", f"{n_total:,}", "Active LEO catalog", "#f8fafc")
with k2:
    render_metric_card("Flagged by ML", f"{n_ml_flagged:,}", f"{pct_flagged:.2f}% of catalog", "#f87171", "#ef4444")
with k3:
    render_metric_card("Conforming Orbits", f"{n_ml_normal:,}", f"{100 - pct_flagged:.2f}% standard paths", "#34d399", "#10b981")
with k4:
    render_metric_card("Orbital Groups", f"{n_clusters}", "K-Means clusters (k=5)", "#818cf8")

st.markdown("<br>", unsafe_allow_html=True)

# Why ML Flags Satellites (Intuitive & Technical)
st.markdown("### How the ML Detector Works")

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.markdown("""
    <div style="background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #3b82f6; border-radius: 6px; padding: 16px 20px; height: 100%;">
        <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem; margin-bottom: 8px;">Intuitive Explanation</div>
        <p style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 8px;">
            Low Earth Orbit has different functional regions: high-density circular shells around 550 km (like Starlink) versus polar observation paths at 800 km.
        </p>
        <p style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0px;">
            If we checked all satellites together, normal polar satellites would be falsely flagged just because they look different from Starlinks. <b>Grouping satellites by altitude and tilt first ensures each satellite is only compared against its actual peers.</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_exp2:
    st.markdown("""
    <div style="background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #8b5cf6; border-radius: 6px; padding: 16px 20px; height: 100%;">
        <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem; margin-bottom: 8px;">Technical ML Formulation</div>
        <ul style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0px; padding-left: 18px;">
            <li style="margin-bottom: 6px;"><b>Step 1 (Clustering):</b> K-Means (k=5) partitions the 3D standardized orbital feature space (semi-major axis, eccentricity, inclination).</li>
            <li style="margin-bottom: 6px;"><b>Step 2 (Outlier Scoring):</b> Inside each cluster, an Isolation Forest builds an ensemble of random decision trees.</li>
            <li><b>Step 3 (Flagging):</b> Satellites isolated in fewer tree splits receive a negative decision score (&lt; 0) and are flagged as outliers (5% expected contamination rate).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

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
    2: "Mid-Tilt Constellations (Starlink / OneWeb / ISS)",
    0: "Sun-Synchronous Polar (Earth Observation)",
    1: "Upper LEO Polar (Communication & Navigation)",
    4: "Intermediate Altitude Shell",
    3: "Elliptical Transfer Shell"
}

cluster_reasons = {
    2: "Oval orbits or altitude offsets outside the 550 km plane",
    0: "Non-polar inclinations or high eccentricities",
    1: "Unusual tilts or altitudes far above 1,200 km",
    4: "Uncommon inclination (76.7°) outside dense orbits",
    3: "High orbital eccentricity (> 0.04)"
}

cluster_summary['Group_Name'] = cluster_summary['cluster_id'].map(cluster_names)
cluster_summary['Outlier_Profile'] = cluster_summary['cluster_id'].map(cluster_reasons)

cluster_display = cluster_summary[[
    'cluster_id', 'Group_Name', 'Total_Satellites', 'ML_Anomalies', 
    'Mean_Altitude', 'Mean_Inclination', 'Mean_Eccentricity', 'Outlier_Profile'
]].sort_values(by='Total_Satellites', ascending=False)

cluster_display.columns = [
    'Group ID', 'Orbital Family Name', 'Total Satellites', 'Flagged Outliers',
    'Avg Altitude (km)', 'Avg Tilt (°)', 'Avg Eccentricity', 'Common Outlier Characteristics'
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

st.caption("Because contamination is set to 5%, Isolation Forest flags the ~5% most distant satellites within each specific group.")

st.markdown("<br>", unsafe_allow_html=True)

# Table of Flagged Satellites with Reasons
st.markdown("### All Satellites Flagged by Machine Learning")

ml_flagged_df = df[df['ml_flag'] == 1].copy()

# Compute reasons for all flagged satellites
ml_flagged_df['Reason'] = ml_flagged_df.apply(lambda r: get_ml_reasons(r)[0], axis=1)

search_term = st.text_input("Filter table by satellite name or NORAD ID:", placeholder="e.g. EXPRESS, 38745, STARLINK...")
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
    'Tilt (°)', 'Eccentricity', 'Decision Score', 'Why Flagged by ML'
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

st.caption(f"Showing {len(display_table):,} satellites flagged by ML. To inspect all parameters for any individual satellite, use the Satellite Explorer page.")
