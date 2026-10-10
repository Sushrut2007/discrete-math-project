import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout

st.set_page_config(
    page_title="Orbital Spacing & Graph Analysis",
    page_icon="🕸️",
    layout="wide"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Catalog data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Orbital Neighborhood & Spacing (DM Graph)</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Directed 5-nearest-neighbor graph analysis detecting isolated satellites and sparse orbital corridors in LEO.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_dm_flagged = int(df['dm_flag'].sum())
n_zero_indegree = int((df['incoming_neighbor_count'] == 0).sum())
global_mean_dist = float(df['global_mean_dist'].iloc[0])
total_edges = n_total * 5

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("LEO Satellites", f"{n_total:,}", "Graph Nodes", "#60a5fa")
with k2:
    render_metric_card("Directed Spacing Links", f"{total_edges:,}", "5 Nearest Neighbors per Node", "#818cf8")
with k3:
    render_metric_card("Unreciprocated Nodes", f"{n_zero_indegree:,}", "In-degree = 0", "#fbbf24")
with k4:
    render_metric_card("Isolated Satellites", f"{n_dm_flagged}", "Structurally Isolated in LEO", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Mathematical Rule Box
st.markdown("""
<div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-left: 3px solid #6366f1; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
    <div style="font-size: 0.85rem; font-weight: 700; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
        Graph Isolation Rule
    </div>
    <div style="font-size: 1.05rem; color: #f8fafc; font-family: 'JetBrains Mono', monospace; margin-bottom: 10px;">
        Flag = (In-Degree == 0) AND (Neighbor Distance > Global Average)
    </div>
    <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">
        <b>Operational Meaning:</b>
        <ul style="margin-top: 6px; margin-bottom: 0px;">
            <li><b>In-Degree == 0:</b> No other active LEO satellite has this satellite among its 5 closest neighbors.</li>
            <li><b>Above-Average Neighbor Distance:</b> Its own nearest neighbors are farther away than normal for the LEO catalog, confirming that it occupies an unusually empty orbital corridor.</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# Plots
col_g1, col_g2 = st.columns([1, 1.2])

with col_g1:
    st.markdown("#### Incoming Neighbors Distribution")
    in_deg_counts = df['incoming_neighbor_count'].value_counts().sort_index().reset_index()
    in_deg_counts.columns = ['In-Degree', 'Count']
    plot_deg = in_deg_counts[in_deg_counts['In-Degree'] <= 15].copy()
    plot_deg['Color'] = ['#f59e0b' if deg == 0 else '#3b82f6' for deg in plot_deg['In-Degree']]
    
    fig_deg = px.bar(
        plot_deg,
        x='In-Degree',
        y='Count',
        color='In-Degree',
        color_discrete_sequence=plot_deg['Color'].tolist()
    )
    fig_deg.update_traces(marker_line_width=0, hovertemplate="In-Degree: %{x}<br>Count: %{y:,}<extra></extra>")
    layout_deg = get_plotly_layout(height=320)
    layout_deg['showlegend'] = False
    layout_deg['xaxis']['title'] = "Number of Incoming Neighbors (In-Degree)"
    layout_deg['yaxis']['title'] = "Number of Satellites"
    fig_deg.update_layout(layout_deg)
    st.plotly_chart(fig_deg, use_container_width=True)

with col_g2:
    st.markdown("#### Spacing vs. Neighbor Count")
    sample_dm = df.sample(n=min(3000, len(df)), random_state=42).copy()
    flagged_dm = df[df['dm_flag'] == 1]
    plot_scatter = pd.concat([sample_dm, flagged_dm]).drop_duplicates(subset=['NORAD_CAT_ID'])
    plot_scatter['DM_Status'] = plot_scatter['dm_flag'].map({1: 'Isolated (Flagged)', 0: 'Standard LEO Node'})
    
    fig_iso = px.scatter(
        plot_scatter,
        x='incoming_neighbor_count',
        y='mean_neighbor_distance',
        color='DM_Status',
        color_discrete_map={'Standard LEO Node': '#38bdf8', 'Isolated (Flagged)': '#ef4444'},
        hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height'],
        labels={'incoming_neighbor_count': 'In-Degree', 'mean_neighbor_distance': 'Neighbor Distance'}
    )
    fig_iso.update_traces(marker=dict(size=5, opacity=0.75))
    layout_iso = get_plotly_layout(height=320)
    layout_iso['shapes'] = [
        dict(type="line", x0=-0.5, x1=15, y0=global_mean_dist, y1=global_mean_dist, line=dict(color="#f59e0b", dash="dash", width=1.5)),
        dict(type="line", x0=0.5, x1=0.5, y0=0, y1=plot_scatter['mean_neighbor_distance'].max(), line=dict(color="#f59e0b", dash="dash", width=1.5))
    ]
    layout_iso['legend'] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig_iso.update_layout(layout_iso)
    st.plotly_chart(fig_iso, use_container_width=True)
    st.caption("Top-left quadrant (In-Degree = 0 and Distance > Threshold) marks isolated satellites operating outside standard LEO constellation shells.")

st.markdown("<br>", unsafe_allow_html=True)

# Table of DM Flagged Satellites
st.markdown("#### Isolated LEO Satellites (Flagged by Graph Spacing)")
dm_table = df[df['dm_flag'] == 1][[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height', 
    'INCLINATION', 'ECCENTRICITY', 'incoming_neighbor_count', 'anomaly_score'
]].sort_values(by='orbit_height', ascending=False)

dm_table.columns = [
    'NORAD ID', 'Name', 'Altitude (km)', 'Inclination (°)', 
    'Eccentricity', 'Incoming Neighbors', 'Final Score'
]

st.dataframe(
    dm_table.style.format({
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}',
        'Eccentricity': '{:.4f}',
        'Incoming Neighbors': '{:d}'
    }),
    use_container_width=True,
    hide_index=True
)
