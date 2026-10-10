import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
st.markdown('<div class="page-title">Machine Learning Component</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Two-stage unsupervised architecture: Global K-Means clustering + Intra-cluster Isolation Forests.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_flagged = int(df['ml_flag'].sum())
n_nominal = n_total - n_flagged
n_clusters = int(df['cluster_id'].nunique())
flag_pct = (n_flagged / n_total) * 100

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Orbital Clusters", f"{n_clusters}", "K-Means Partitions", "#818cf8")
with k2:
    render_metric_card("ML Flagged", f"{n_flagged:,}", f"{flag_pct:.2f}% anomaly rate", "#f87171", "#ef4444")
with k3:
    render_metric_card("Nominal Satellites", f"{n_nominal:,}", f"{100 - flag_pct:.2f}% conforming", "#34d399", "#10b981")
with k4:
    render_metric_card("Model Type", "Isolation Forest", "Intra-Cluster Trees", "#38bdf8")

st.markdown("<br>", unsafe_allow_html=True)

# Methodology Explanation Card
with st.expander("Methodology: Why Two-Stage Machine Learning?", expanded=False):
    st.markdown("""
    1. **Why not a single global Isolation Forest?** Satellites naturally belong to distinct orbital regimes (e.g. LEO constellations vs geostationary communication belts). A single global model would misclassify all GEO satellites as anomalies simply because they are far from the dense LEO cluster.
    2. **Stage 1 (K-Means Clustering):** Partitions the catalog into homogenous orbital families based on normalized semi-major axis, eccentricity, inclination, and motion.
    3. **Stage 2 (Intra-Cluster Isolation Forest):** An ensemble of isolation trees is evaluated specifically *within* each cluster. Spacecraft that isolate at shallow tree depths within their own family receive a negative score and are flagged.
    """)

# Plots Row
col_plot1, col_plot2 = st.columns([1.4, 1])

with col_plot1:
    st.markdown("#### Orbital Family Map (Sampled Spacecraft)")
    sample_df = df.sample(n=min(3000, len(df)), random_state=42).copy()
    sample_df['Status'] = sample_df['ml_flag'].map({1: 'ML Anomaly', 0: 'Nominal'})
    sample_df['Cluster_Label'] = "Cluster " + sample_df['cluster_id'].astype(str)
    
    fig_clusters = px.scatter(
        sample_df,
        x='semi_major_axis',
        y='INCLINATION',
        color='Cluster_Label',
        symbol='Status',
        symbol_map={'Nominal': 'circle', 'ML Anomaly': 'x'},
        hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'ml_anomaly_score'],
        labels={'semi_major_axis': 'Semi-Major Axis (km)', 'INCLINATION': 'Inclination (deg)'}
    )
    fig_clusters.update_traces(marker=dict(size=5, opacity=0.7))
    layout_c = get_plotly_layout(height=360)
    layout_c['legend'] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig_clusters.update_layout(layout_c)
    st.plotly_chart(fig_clusters, use_container_width=True)

with col_plot2:
    st.markdown("#### Isolation Forest Score Distribution")
    fig_hist = px.histogram(
        df,
        x='ml_anomaly_score',
        nbins=45,
        color='ml_flag',
        color_discrete_map={0: '#38bdf8', 1: '#ef4444'},
        labels={'ml_anomaly_score': 'Decision Function Score', 'count': 'Spacecraft'}
    )
    fig_hist.update_traces(marker_line_width=0)
    layout_h = get_plotly_layout(height=360)
    layout_h['showlegend'] = False
    layout_h['xaxis']['title'] = "Isolation Score (Negative = Outlier)"
    layout_h['yaxis']['title'] = "Count"
    layout_h['shapes'] = [
        dict(type="line", x0=0, x1=0, y0=0, y1=1, yref="paper", line=dict(color="#f87171", dash="dash", width=1.5))
    ]
    fig_hist.update_layout(layout_h)
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Cluster Breakdown Table
st.markdown("#### Orbital Family Diagnostic Summary")
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
    'Cluster ID', 'Total Objects', 'Flagged Anomalies', 'Avg Altitude (km)', 
    'Avg Inclination (°)', 'Avg Eccentricity', 'Anomaly Rate (%)'
]

st.dataframe(
    cluster_summary.style.format({
        'Total Objects': '{:,}',
        'Flagged Anomalies': '{:,}',
        'Avg Altitude (km)': '{:,.1f}',
        'Avg Inclination (°)': '{:.2f}',
        'Avg Eccentricity': '{:.4f}',
        'Anomaly Rate (%)': '{:.2f}%'
    }),
    use_container_width=True,
    hide_index=True
)
