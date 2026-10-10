import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout

st.set_page_config(
    page_title="Machine Learning Analysis",
    page_icon="🤖",
    layout="wide"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Catalog data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Statistical Orbit Classification (ML)</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Groups satellites into orbital families with K-Means, then flags outliers within each family using Isolation Forest.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_flagged = int(df['ml_flag'].sum())
n_nominal = n_total - n_flagged
n_clusters = int(df['cluster_id'].nunique())
flag_pct = (n_flagged / n_total) * 100

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Orbital Families", f"{n_clusters}", "Identified by K-Means", "#818cf8")
with k2:
    render_metric_card("Outliers Flagged", f"{n_flagged:,}", f"{flag_pct:.2f}% of LEO catalog", "#f87171", "#ef4444")
with k3:
    render_metric_card("Conforming Orbits", f"{n_nominal:,}", f"{100 - flag_pct:.2f}% standard orbits", "#34d399", "#10b981")
with k4:
    render_metric_card("Detection Method", "Isolation Forest", "Evaluated per orbital shell", "#38bdf8")

st.markdown("<br>", unsafe_allow_html=True)

# Methodology Explanation Card
with st.expander("Why evaluate satellites within orbital families?", expanded=False):
    st.markdown("""
    Even within Low Earth Orbit, satellites operate in distinct functional shells:
    - **Mega-Constellations:** High-density circular shells around 550 km at 53° inclination (e.g. Starlink).
    - **Sun-Synchronous Orbits:** Polar observations at 700–800 km at 97° inclination.
    - **Space Stations:** Lower LEO at 400 km at 51.6° inclination (ISS, Tiangong).
    
    If we evaluated all LEO satellites together, satellites in less crowded but normal shells would be falsely flagged as anomalies. **K-Means clustering** first groups satellites by orbital family, so that **Isolation Forest** checks each satellite against its actual peers.
    """)

# Plots Row
col_plot1, col_plot2 = st.columns([1.4, 1])

with col_plot1:
    st.markdown("#### LEO Orbital Families (3,000 Sampled Satellites)")
    sample_df = df.sample(n=min(3000, len(df)), random_state=42).copy()
    sample_df['Status'] = sample_df['ml_flag'].map({1: 'Flagged Outlier', 0: 'Conforming'})
    sample_df['Cluster_Label'] = "Family " + sample_df['cluster_id'].astype(str)
    
    fig_clusters = px.scatter(
        sample_df,
        x='semi_major_axis',
        y='INCLINATION',
        color='Cluster_Label',
        symbol='Status',
        symbol_map={'Conforming': 'circle', 'Flagged Outlier': 'x'},
        hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height'],
        labels={'semi_major_axis': 'Semi-Major Axis (km)', 'INCLINATION': 'Inclination (degrees)'}
    )
    fig_clusters.update_traces(marker=dict(size=5, opacity=0.7))
    layout_c = get_plotly_layout(height=360)
    layout_c['legend'] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig_clusters.update_layout(layout_c)
    st.plotly_chart(fig_clusters, use_container_width=True)

with col_plot2:
    st.markdown("#### Outlier Score Distribution")
    fig_hist = px.histogram(
        df,
        x='ml_anomaly_score',
        nbins=45,
        color='ml_flag',
        color_discrete_map={0: '#38bdf8', 1: '#ef4444'},
        labels={'ml_anomaly_score': 'Decision Score', 'count': 'Satellites'}
    )
    fig_hist.update_traces(marker_line_width=0)
    layout_h = get_plotly_layout(height=360)
    layout_h['showlegend'] = False
    layout_h['xaxis']['title'] = "Isolation Score (Negative = Outlier)"
    layout_h['yaxis']['title'] = "Number of Satellites"
    layout_h['shapes'] = [
        dict(type="line", x0=0, x1=0, y0=0, y1=1, yref="paper", line=dict(color="#f87171", dash="dash", width=1.5))
    ]
    fig_hist.update_layout(layout_h)
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Cluster Breakdown Table
st.markdown("#### Orbital Family Characteristics")
cluster_summary = df.groupby('cluster_id').agg(
    Total_Satellites=('NORAD_CAT_ID', 'count'),
    ML_Anomalies=('ml_flag', 'sum'),
    Mean_Altitude=('orbit_height', 'mean'),
    Mean_Inclination=('INCLINATION', 'mean'),
    Mean_Eccentricity=('ECCENTRICITY', 'mean')
).reset_index()

cluster_summary['Anomaly_Rate'] = (cluster_summary['ML_Anomalies'] / cluster_summary['Total_Satellites']) * 100
cluster_summary['Mean_Altitude'] = cluster_summary['Mean_Altitude'].round(1)
cluster_summary['Mean_Inclination'] = cluster_summary['Mean_Inclination'].round(2)
cluster_summary['Mean_Eccentricity'] = cluster_summary['Mean_Eccentricity'].round(4)
cluster_summary['Anomaly_Rate'] = cluster_summary['Anomaly_Rate'].round(2)

cluster_summary.columns = [
    'Family ID', 'Total Satellites', 'Flagged Outliers', 'Avg Altitude (km)', 
    'Avg Inclination (°)', 'Avg Eccentricity', 'Flag Rate (%)'
]

st.dataframe(
    cluster_summary.style.format({
        'Total Satellites': '{:,}',
        'Flagged Outliers': '{:,}',
        'Avg Altitude (km)': '{:,.1f}',
        'Avg Inclination (°)': '{:.2f}',
        'Avg Eccentricity': '{:.4f}',
        'Flag Rate (%)': '{:.2f}%'
    }),
    use_container_width=True,
    hide_index=True
)
