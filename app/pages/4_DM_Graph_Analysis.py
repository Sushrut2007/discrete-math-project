import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout, PLOTLY_CONFIG
from diagnostics import get_dm_reasons

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
st.markdown('<div class="page-subtitle">How a directed 5-nearest-neighbour graph detects isolated satellites and sparse orbital corridors.</div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_dm_flagged = int(df['dm_flag'].sum())
n_dm_normal = n_total - n_dm_flagged
pct_flagged = (n_dm_flagged / n_total) * 100
global_mean_dist = float(df['global_mean_dist'].iloc[0])

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Satellites", f"{n_total:,}", "Graph nodes |V|", "#f8fafc")
with k2:
    render_metric_card("Flagged by DM", f"{n_dm_flagged}", f"{pct_flagged:.2f}% of catalog", "#f87171", "#ef4444")
with k3:
    render_metric_card("Connected Peers", f"{n_dm_normal:,}", f"{100 - pct_flagged:.2f}% normal spacing", "#34d399", "#10b981")
with k4:
    render_metric_card("Catalog Avg Spacing", f"{global_mean_dist:.4f}", "Isolation threshold", "#818cf8")

st.markdown("<br>", unsafe_allow_html=True)

# Why the Graph Flags Satellites (Intuitive & Technical)
st.markdown("### How the Graph Detector Works")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("""
    <div style="background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #3b82f6; border-radius: 6px; padding: 16px 20px; height: 100%;">
        <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem; margin-bottom: 8px;">Intuitive Explanation</div>
        <p style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 8px;">
            In a crowded region like Low Earth Orbit, most satellites share very similar orbits with dozens of other satellites.
        </p>
        <p style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0px;">
            A satellite is considered <b>isolated</b> if no other satellite in the catalog considers it a close peer, and its own closest peers are unusually far away. It flies in an empty or sparsely occupied orbital corridor.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_g2:
    st.markdown(f"""
    <div style="background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #8b5cf6; border-radius: 6px; padding: 16px 20px; height: 100%;">
        <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem; margin-bottom: 8px;">Technical Discrete Math Formulation</div>
        <ul style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0px; padding-left: 18px;">
            <li style="margin-bottom: 6px;"><b>Graph Construction:</b> Directed 5-NN graph G = (V, E) where |V| = {n_total:,} satellites. Each node points to its 5 closest peers in standardized orbital feature space.</li>
            <li style="margin-bottom: 6px;"><b>Asymmetric Relation:</b> The relation is directed and asymmetric: if satellite u has v in its top-5, v does not necessarily have u in its top-5.</li>
            <li><b>Isolation Rule:</b> Node v is flagged iff: <b>in-degree(v) == 0</b> (unreciprocated node) AND <b>mean_5nn_dist(v) &gt; {global_mean_dist:.4f}</b> (catalog average distance).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Important Note on Physical Distance vs Feature Similarity
st.markdown("""
<div class="info-box">
    <b>Important Distinction:</b> Graph neighbour connections represent similarity across orbital features (altitude, inclination, eccentricity, speed, and period), <b>not physical distance between satellites in space</b>.
</div>
""", unsafe_allow_html=True)

# In-Degree Distribution Chart
st.markdown("### Incoming Neighbor Distribution (In-Degree)")

in_deg_counts = df['incoming_neighbor_count'].value_counts().sort_index().reset_index()
in_deg_counts.columns = ['In_Degree', 'Count']
plot_deg = in_deg_counts[in_deg_counts['In_Degree'] <= 12].copy()

# Highlight bar 0 in red
bar_colors = ['#ef4444' if deg == 0 else '#38bdf8' for deg in plot_deg['In_Degree']]

fig_deg = px.bar(
    plot_deg,
    x='In_Degree',
    y='Count'
)
fig_deg.update_traces(
    marker_color=bar_colors,
    marker_line_width=0,
    hovertemplate="Incoming Neighbors: %{x}<br>Satellites: %{y:,}<extra></extra>"
)
layout_deg = get_plotly_layout(height=230)
layout_deg['showlegend'] = False
layout_deg['xaxis']['title'] = "Number of Other Satellites Having This as a Top-5 Neighbor (In-Degree)"
layout_deg['yaxis']['title'] = "Number of Satellites"
layout_deg['yaxis']['rangemode'] = 'tozero'
layout_deg['margin'] = dict(l=45, r=20, t=10, b=40)
fig_deg.update_layout(layout_deg)
st.plotly_chart(fig_deg, use_container_width=True, config=PLOTLY_CONFIG)

st.caption("Red bar: exactly 64 satellites have 0 incoming neighbors (unreciprocated in the 5-NN graph) and an average neighbor distance exceeding the catalog mean.")

st.markdown("<br>", unsafe_allow_html=True)

# Table of Flagged Satellites with Reasons
st.markdown("### All Satellites Flagged by Discrete Math Graph")

dm_flagged_df = df[df['dm_flag'] == 1].copy()

# Compute reasons for all flagged satellites
dm_flagged_df['Reason'] = dm_flagged_df.apply(lambda r: get_dm_reasons(r, global_mean_dist)[0], axis=1)

search_term = st.text_input("Filter table by satellite name or NORAD ID:", placeholder="e.g. EXPRESS, 38745...")
if search_term.strip():
    t = search_term.strip().lower()
    dm_flagged_df = dm_flagged_df[
        dm_flagged_df['OBJECT_NAME'].str.lower().str.contains(t, na=False) |
        dm_flagged_df['NORAD_CAT_ID'].astype(str).str.contains(t, na=False)
    ]

display_table = dm_flagged_df[[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height', 'INCLINATION',
    'ECCENTRICITY', 'incoming_neighbor_count', 'mean_neighbor_distance', 'Reason'
]].sort_values(by='orbit_height', ascending=False)

display_table.columns = [
    'NORAD ID', 'Satellite Name', 'Altitude (km)', 'Tilt (°)',
    'Eccentricity', 'Incoming Peers', 'Avg 5-NN Distance', 'Why Isolated in Graph'
]

st.dataframe(
    display_table.style.format({
        'Altitude (km)': '{:,.1f}',
        'Tilt (°)': '{:.2f}',
        'Eccentricity': '{:.4f}',
        'Incoming Peers': '{:d}',
        'Avg 5-NN Distance': '{:.4f}'
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(f"Showing all {len(display_table)} satellites flagged by the DM graph. To inspect all orbital parameters for any satellite, use the Satellite Explorer page.")
