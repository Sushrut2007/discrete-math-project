import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout, PLOTLY_CONFIG

st.set_page_config(
    page_title="DM Graph Analysis",
    layout="wide"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Catalog data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Discrete Math Graph Detector Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Results from the directed 5-nearest-neighbour graph based on orbital-feature similarity.</div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_dm_flagged = int(df['dm_flag'].sum())
n_dm_normal = n_total - n_dm_flagged
pct_flagged = (n_dm_flagged / n_total) * 100
global_mean_dist = float(df['global_mean_dist'].iloc[0])

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Satellites", f"{n_total:,}", "Graph nodes", "#f8fafc")
with k2:
    render_metric_card("Flagged by DM", f"{n_dm_flagged}", f"{pct_flagged:.2f}% of catalog", "#f87171", "#ef4444")
with k3:
    render_metric_card("Not Flagged", f"{n_dm_normal:,}", f"{100 - pct_flagged:.2f}% connected peers", "#34d399", "#10b981")
with k4:
    render_metric_card("Dataset Avg Spacing", f"{global_mean_dist:.4f}", "Feature distance threshold", "#818cf8")

st.markdown("<br>", unsafe_allow_html=True)

# Clarification Box on Physical Distance vs Feature Similarity
st.markdown("""
<div class="info-box">
    <b>Note on Graph Construction:</b> Neighbour connections represent similarity in orbital features (altitude, inclination, eccentricity, speed, and period), <b>not physical distance between satellites in space</b>.
</div>
""", unsafe_allow_html=True)

# Simple Chart
st.markdown("#### Detector Results Breakdown")
chart_df = pd.DataFrame({
    'Status': ['Flagged by DM', 'Not Flagged'],
    'Count': [n_dm_flagged, n_dm_normal],
    'Display': [f"{n_dm_flagged} ({pct_flagged:.2f}%)", f"{n_dm_normal:,} ({100 - pct_flagged:.2f}%)"]
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
        'Flagged by DM': '#ef4444'
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

dm_flagged_df = df[df['dm_flag'] == 1].sort_values(by='orbit_height', ascending=False)
dm_options = [
    f"NORAD {row['NORAD_CAT_ID']} · {row['OBJECT_NAME']}"
    for _, row in dm_flagged_df.iterrows()
]

selected_sat_str = st.selectbox("Select DM-flagged satellite to inspect:", dm_options)
selected_norad = int(selected_sat_str.split("NORAD ")[1].split(" ·")[0])
selected_sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]

c_d1, c_d2, c_d3, c_d4 = st.columns(4)
with c_d1:
    st.metric("Satellite Name", selected_sat['OBJECT_NAME'])
with c_d2:
    st.metric("NORAD ID", f"{selected_sat['NORAD_CAT_ID']}")
with c_d3:
    st.metric("Incoming Neighbours", f"{int(selected_sat['incoming_neighbor_count'])}")
with c_d4:
    st.metric("Avg Neighbour Distance", f"{selected_sat['mean_neighbor_distance']:.4f}")

st.markdown(f"""
<div class="info-box" style="margin-top: 10px; border-left: 3px solid #ef4444;">
    <b>Detector Explanation:</b><br>
    Other satellites did not select this satellite among their five nearest orbital-feature neighbours, and its own nearest neighbours are farther away than the dataset average ({global_mean_dist:.4f}).
    <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 6px;">
        DM Flag: <b>1 (Flagged)</b> · Final Anomaly Score: <b>{int(selected_sat['anomaly_score'])}</b>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Table of Flagged Satellites
st.markdown("### All Satellites Flagged by Discrete Math Graph")

search_term = st.text_input("Filter table by name or NORAD ID:", placeholder="e.g. EXPRESS, 38745...")
display_df = dm_flagged_df.copy()

if search_term.strip():
    t = search_term.strip().lower()
    display_df = display_df[
        display_df['OBJECT_NAME'].str.lower().str.contains(t, na=False) |
        display_df['NORAD_CAT_ID'].astype(str).str.contains(t, na=False)
    ]

table_cols = display_df[[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height', 'INCLINATION',
    'ECCENTRICITY', 'incoming_neighbor_count', 'mean_neighbor_distance', 'anomaly_score'
]]
table_cols.columns = [
    'NORAD ID', 'Satellite Name', 'Altitude (km)', 'Inclination (°)',
    'Eccentricity', 'Incoming Neighbours', 'Avg Neighbour Distance', 'Final Score'
]

st.dataframe(
    table_cols.style.format({
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}',
        'Eccentricity': '{:.4f}',
        'Avg Neighbour Distance': '{:.4f}',
        'Incoming Neighbours': '{:d}',
        'Final Score': '{:d}'
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(f"Showing all {len(table_cols)} satellites flagged by the DM graph detector.")
