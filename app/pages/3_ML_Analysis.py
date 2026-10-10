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

CLUSTER_NAMES = {
    2: "Constellations (500 km, 51°)",
    0: "Polar / SSO (510 km, 97°)",
    1: "Upper LEO (1,150 km, 81°)",
    4: "Intermediate (720 km)",
    3: "Elliptical Orbits (950 km)"
}

with col_plot1:
    st.markdown("#### LEO Orbital Families (Altitude vs. Tilt)")
    sample_df = df.sample(n=min(3000, len(df)), random_state=42).copy()
    
    # Ensure all ML outliers in sample are visible
    ml_outliers = df[df['ml_flag'] == 1]
    sample_df = pd.concat([sample_df, ml_outliers]).drop_duplicates(subset=['NORAD_CAT_ID'])
    
    # Map friendly group names
    sample_df['Display_Group'] = sample_df.apply(
        lambda r: '🚨 Flagged Outlier' if r['ml_flag'] == 1 else CLUSTER_NAMES.get(r['cluster_id'], f"Cluster {r['cluster_id']}"),
        axis=1
    )
    
    # Sort so Flagged Outliers are plotted last (on top)
    sample_df['Sort_Key'] = sample_df['ml_flag']
    sample_df = sample_df.sort_values(by='Sort_Key')
    
    color_map = {
        'Constellations (500 km, 51°)': '#60a5fa',
        'Polar / SSO (510 km, 97°)': '#a78bfa',
        'Upper LEO (1,150 km, 81°)': '#34d399',
        'Intermediate (720 km)': '#94a3b8',
        'Elliptical Orbits (950 km)': '#fb923c',
        '🚨 Flagged Outlier': '#ef4444'
    }
    
    fig_clusters = px.scatter(
        sample_df,
        x='orbit_height',
        y='INCLINATION',
        color='Display_Group',
        color_discrete_map=color_map,
        range_x=[100, 2000],
        range_y=[0, 115],
        hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'Display_Group'],
        labels={'orbit_height': 'Altitude (km)', 'INCLINATION': 'Inclination (°)', 'Display_Group': 'Group'}
    )
    
    # Set sizes
    fig_clusters.update_traces(
        marker=dict(size=4, opacity=0.55),
        hovertemplate="<b>%{customdata[1]}</b> (NORAD %{customdata[0]})<br>Altitude: %{x:,.0f} km<br>Inclination: %{y:.1f}°<br>Group: %{customdata[2]}<extra></extra>"
    )
    fig_clusters.update_traces(
        selector=dict(name='🚨 Flagged Outlier'),
        marker=dict(size=8, opacity=1.0, line=dict(width=1, color='#ffffff'))
    )
    
    layout_c = get_plotly_layout(height=360)
    layout_c['legend'] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig_clusters.update_layout(layout_c)
    st.plotly_chart(fig_clusters, use_container_width=True)
    st.caption("Satellites are grouped into orbital families by altitude and tilt. Red dots are the outliers flagged within each group.")

with col_plot2:
    st.markdown("#### Outlier Score Distribution")
    plot_hist_df = df.copy()
    plot_hist_df['Score_Status'] = plot_hist_df['ml_flag'].map({
        1: 'Flagged Outlier (Score < 0)',
        0: 'Conforming Orbit (Score ≥ 0)'
    })
    
    fig_hist = px.histogram(
        plot_hist_df,
        x='ml_anomaly_score',
        nbins=40,
        color='Score_Status',
        color_discrete_map={
            'Conforming Orbit (Score ≥ 0)': '#38bdf8',
            'Flagged Outlier (Score < 0)': '#ef4444'
        },
        labels={'ml_anomaly_score': 'Isolation Score', 'count': 'Satellites'}
    )
    fig_hist.update_traces(marker_line_width=0)
    layout_h = get_plotly_layout(height=360)
    layout_h['showlegend'] = False
    layout_h['xaxis']['title'] = "Isolation Score (Left of 0 = Outlier)"
    layout_h['yaxis']['title'] = "Number of Satellites"
    layout_h['shapes'] = [
        dict(type="line", x0=0, x1=0, y0=0, y1=1, yref="paper", line=dict(color="#f87171", dash="dash", width=2))
    ]
    layout_h['annotations'] = [
        dict(x=-0.08, y=0.92, xref="x", yref="paper", text="← 792 Outliers", showarrow=False, font=dict(color="#f87171", size=11, weight="bold")),
        dict(x=0.08, y=0.92, xref="x", yref="paper", text="15,007 Conforming →", showarrow=False, font=dict(color="#38bdf8", size=11, weight="bold")),
        dict(x=0, y=1.05, xref="x", yref="paper", text="Threshold (0.0)", showarrow=False, font=dict(color="#94a3b8", size=10))
    ]
    fig_hist.update_layout(layout_h)
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption("Negative scores indicate satellites located unusually far from their orbital peers.")

st.markdown("<br>", unsafe_allow_html=True)

# Cluster Breakdown Table
st.markdown("#### Orbital Family Summary")
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

cluster_summary['Orbital Family'] = cluster_summary['cluster_id'].map({
    2: "Constellations (Starlink / OneWeb / ISS)",
    0: "Sun-Synchronous Polar (Earth Observation)",
    1: "Upper LEO Polar (Communication)",
    4: "Intermediate Altitude Shell",
    3: "Elliptical Shell"
})

cluster_display = cluster_summary[[
    'Orbital Family', 'Total_Satellites', 'ML_Anomalies', 
    'Mean_Altitude', 'Mean_Inclination', 'Mean_Eccentricity', 'Anomaly_Rate'
]].sort_values(by='Total_Satellites', ascending=False)

cluster_display.columns = [
    'Orbital Family', 'Total Satellites', 'Flagged Outliers', 'Avg Altitude (km)', 
    'Avg Inclination (°)', 'Avg Eccentricity', 'Flag Rate (%)'
]

st.dataframe(
    cluster_display.style.format({
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
