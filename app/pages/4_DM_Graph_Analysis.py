import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout

st.set_page_config(
    page_title="Discrete Mathematics Graph Analysis",
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
st.markdown('<div class="page-title">Discrete Mathematics Component</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Builds a 5-nearest-neighbor directed graph of satellites to spot structurally isolated nodes.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# KPIs
n_total = len(df)
n_dm_flagged = int(df['dm_flag'].sum())
n_zero_indegree = int((df['incoming_neighbor_count'] == 0).sum())
global_mean_dist = float(df['global_mean_dist'].iloc[0])
total_edges = n_total * 5

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Graph Nodes", f"{n_total:,}", "1 node per satellite", "#60a5fa")
with k2:
    render_metric_card("Directed Edges", f"{total_edges:,}", "5 outgoing arrows per node", "#818cf8")
with k3:
    render_metric_card("Zero In-Degree Nodes", f"{n_zero_indegree:,}", "No arrows pointing in", "#fbbf24")
with k4:
    render_metric_card("DM Flagged Nodes", f"{n_dm_flagged}", "Pass both DM tests", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Mathematical Rule Box
st.markdown("""
<div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-left: 3px solid #6366f1; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
    <div style="font-size: 0.85rem; font-weight: 700; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
        Discrete Math Flagging Rule
    </div>
    <div style="font-size: 1.05rem; color: #f8fafc; font-family: 'JetBrains Mono', monospace; margin-bottom: 10px;">
        Flag = (in_degree == 0) AND (mean_neighbor_dist > global_mean_dist)
    </div>
    <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">
        <b>Why we check both conditions:</b>
        <ul style="margin-top: 6px; margin-bottom: 0px;">
            <li><b>Zero incoming arrows (in_degree == 0):</b> No other satellite considers this satellite one of its 5 closest neighbors.</li>
            <li><b>Large neighbor distance (mean_dist > {:.4f}):</b> Its own 5 closest neighbors are farther away than the catalog average. This prevents flagging normal satellites that just happen to sit at the edge of a dense constellation.</li>
        </ul>
    </div>
</div>
""".format(global_mean_dist), unsafe_allow_html=True)

# Plots
col_g1, col_g2 = st.columns([1, 1.2])

with col_g1:
    st.markdown("#### Incoming Connections Distribution (In-Degree)")
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
    layout_deg['xaxis']['title'] = "Number of Incoming Neighbors"
    layout_deg['yaxis']['title'] = "Number of Satellites"
    fig_deg.update_layout(layout_deg)
    st.plotly_chart(fig_deg, use_container_width=True)
    st.caption("The yellow bar shows satellites with 0 incoming connections. Only the ones that also have high neighbor distance get flagged.")

with col_g2:
    st.markdown("#### Neighbor Distance vs. Incoming Connections")
    sample_dm = df.sample(n=min(3000, len(df)), random_state=42).copy()
    flagged_dm = df[df['dm_flag'] == 1]
    plot_scatter = pd.concat([sample_dm, flagged_dm]).drop_duplicates(subset=['NORAD_CAT_ID'])
    plot_scatter['DM_Status'] = plot_scatter['dm_flag'].map({1: 'Flagged by DM', 0: 'Normal Node'})
    
    fig_iso = px.scatter(
        plot_scatter,
        x='incoming_neighbor_count',
        y='mean_neighbor_distance',
        color='DM_Status',
        color_discrete_map={'Normal Node': '#38bdf8', 'Flagged by DM': '#ef4444'},
        hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'incoming_neighbor_count', 'mean_neighbor_distance'],
        labels={'incoming_neighbor_count': 'In-Degree', 'mean_neighbor_distance': 'Mean 5-NN Distance'}
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
    st.caption("Dashed lines show the decision rule: Top-left corner (In-Degree = 0 and Distance > Threshold) contains the flagged satellites.")

st.markdown("<br>", unsafe_allow_html=True)

# Table of DM Flagged Satellites
st.markdown("#### Satellites Flagged by Graph Analysis")
dm_table = df[df['dm_flag'] == 1][[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'incoming_neighbor_count', 
    'mean_neighbor_distance', 'global_mean_dist', 'orbit_height', 'INCLINATION', 'anomaly_score'
]].sort_values(by='mean_neighbor_distance', ascending=False)

dm_table.columns = [
    'NORAD ID', 'Name', 'In-Degree', 'Mean 5-NN Dist', 
    'Catalog Mean', 'Altitude (km)', 'Inclination (°)', 'Final Score'
]

st.dataframe(
    dm_table.style.format({
        'Mean 5-NN Dist': '{:.4f}',
        'Catalog Mean': '{:.4f}',
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}'
    }),
    use_container_width=True,
    hide_index=True
)
