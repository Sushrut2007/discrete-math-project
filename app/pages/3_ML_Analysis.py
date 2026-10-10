import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout, PLOTLY_CONFIG

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
st.markdown('<div class="page-subtitle">Results from the ML detector, which checks each satellite against peers in its orbital group.</div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_ml_flagged = int(df['ml_flag'].sum())
n_ml_normal = n_total - n_ml_flagged
pct_flagged = (n_ml_flagged / n_total) * 100
n_clusters = int(df['cluster_id'].nunique())

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Satellites", f"{n_total:,}", "Active LEO catalog", "#f8fafc")
with k2:
    render_metric_card("Flagged by ML", f"{n_ml_flagged:,}", f"{pct_flagged:.2f}% of catalog", "#f87171", "#ef4444")
with k3:
    render_metric_card("Not Flagged", f"{n_ml_normal:,}", f"{100 - pct_flagged:.2f}% conforming", "#34d399", "#10b981")
with k4:
    render_metric_card("Orbital Groups", f"{n_clusters}", "Evaluated per group", "#818cf8")

st.markdown("<br>", unsafe_allow_html=True)

# Simple Chart
st.markdown("#### Detector Results Breakdown")
chart_df = pd.DataFrame({
    'Status': ['Flagged by ML', 'Not Flagged'],
    'Count': [n_ml_flagged, n_ml_normal],
    'Display': [f"{n_ml_flagged:,} ({pct_flagged:.2f}%)", f"{n_ml_normal:,} ({100 - pct_flagged:.2f}%)"]
})

fig = px.bar(
    chart_df,
    y='Status',
    x='Count',
    orientation='h',
    text='Display',
    color='Status',
    color_discrete_map={
        'Not Flagged': '#38bdf8',
        'Flagged by ML': '#ef4444'
    }
)
fig.update_traces(
    textposition='outside',
    marker_line_width=0,
    hovertemplate='<b>%{y}</b><br>Satellites: %{x:,}<extra></extra>'
)
layout = get_plotly_layout(height=180)
layout['showlegend'] = False
layout['xaxis']['title'] = "Number of Satellites"
layout['yaxis']['title'] = ""
layout['margin'] = dict(l=40, r=40, t=10, b=35)
fig.update_layout(layout)
st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

st.markdown("<br>", unsafe_allow_html=True)

# Selected Satellite Inspector
st.markdown("### Inspect a Flagged Satellite")

ml_flagged_df = df[df['ml_flag'] == 1].sort_values(by='orbit_height', ascending=False)
ml_options = [
    f"NORAD {row['NORAD_CAT_ID']} · {row['OBJECT_NAME']}"
    for _, row in ml_flagged_df.iterrows()
]

selected_sat_str = st.selectbox("Select ML-flagged satellite to inspect:", ml_options)
selected_norad = int(selected_sat_str.split("NORAD ")[1].split(" ·")[0])
selected_sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]

c_i1, c_i2, c_i3, c_i4 = st.columns(4)
with c_i1:
    st.metric("Satellite Name", selected_sat['OBJECT_NAME'])
with c_i2:
    st.metric("NORAD ID", f"{selected_sat['NORAD_CAT_ID']}")
with c_i3:
    st.metric("Assigned Orbital Group", f"Group {selected_sat['cluster_id']}")
with c_i4:
    st.metric("ML Decision Score", f"{selected_sat.get('ml_anomaly_score', 0):.4f}")

st.markdown("""
<div class="info-box" style="margin-top: 10px; border-left: 3px solid #ef4444;">
    <b>Detector Explanation:</b><br>
    The ML detector found this satellite unusual compared with other satellites in its orbital group.
    <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 6px;">
        Note: The decision score indicates relative distance from the group center (negative values indicate outliers). It is not a calibrated failure probability.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Table of Flagged Satellites
st.markdown("### All Satellites Flagged by Machine Learning")

search_term = st.text_input("Filter table by name or NORAD ID:", placeholder="e.g. EXPRESS, STARLINK, 38745...")
display_df = ml_flagged_df.copy()

if search_term.strip():
    t = search_term.strip().lower()
    display_df = display_df[
        display_df['OBJECT_NAME'].str.lower().str.contains(t, na=False) |
        display_df['NORAD_CAT_ID'].astype(str).str.contains(t, na=False)
    ]

table_cols = display_df[[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'cluster_id', 'orbit_height',
    'INCLINATION', 'ECCENTRICITY', 'anomaly_score'
]]
table_cols.columns = [
    'NORAD ID', 'Satellite Name', 'Assigned Group', 'Altitude (km)',
    'Inclination (°)', 'Eccentricity', 'Final Score'
]

st.dataframe(
    table_cols.style.format({
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}',
        'Eccentricity': '{:.4f}',
        'Assigned Group': '{:d}',
        'Final Score': '{:d}'
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(f"Showing {len(table_cols):,} satellites flagged by the ML detector.")
