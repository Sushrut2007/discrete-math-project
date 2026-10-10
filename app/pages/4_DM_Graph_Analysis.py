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
    render_metric_card("LEO Satellites", f"{n_total:,}", "Catalog Objects", "#60a5fa")
with k2:
    render_metric_card("Neighbor Connections", f"{total_edges:,}", "5 closest peers per satellite", "#818cf8")
with k3:
    render_metric_card("Zero Incoming", f"{n_zero_indegree:,}", "No satellite has these in top-5", "#fbbf24")
with k4:
    render_metric_card("Isolated Satellites", f"{n_dm_flagged}", "Empty orbital corridors", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Mathematical Rule Box
st.markdown("""
<div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-left: 3px solid #6366f1; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
    <div style="font-size: 0.85rem; font-weight: 700; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
        Graph Isolation Rule
    </div>
    <div style="font-size: 1.05rem; color: #f8fafc; font-family: 'JetBrains Mono', monospace; margin-bottom: 10px;">
        Flag = (Incoming Neighbors == 0) AND (Neighbor Distance > Catalog Average)
    </div>
    <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">
        <b>What this means:</b>
        <ul style="margin-top: 6px; margin-bottom: 0px;">
            <li><b>Zero Incoming Neighbors:</b> No other satellite has this satellite among its 5 closest peers.</li>
            <li><b>Above-Average Spacing:</b> Its own 5 closest neighbors are unusually far away, confirming an empty orbital region.</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# Plots
col_g1, col_g2 = st.columns([1, 1.2])

with col_g1:
    st.markdown("#### Incoming Neighbors Distribution")
    in_deg_counts = df['incoming_neighbor_count'].value_counts().sort_index().reset_index()
    in_deg_counts.columns = ['In_Degree', 'Count']
    plot_deg = in_deg_counts[in_deg_counts['In_Degree'] <= 15].copy()
    
    fig_deg = px.bar(
        plot_deg,
        x='In_Degree',
        y='Count',
        color='In_Degree',
        color_discrete_map={0: '#ef4444'},
        color_continuous_scale=None
    )
    # Highlight 0 in red and others in slate blue
    bar_colors = ['#ef4444' if deg == 0 else '#38bdf8' for deg in plot_deg['In_Degree']]
    fig_deg.update_traces(
        marker_color=bar_colors,
        marker_line_width=0,
        hovertemplate="Incoming Neighbors: %{x}<br>Satellites: %{y:,}<extra></extra>"
    )
    layout_deg = get_plotly_layout(height=320)
    layout_deg['showlegend'] = False
    layout_deg['xaxis']['title'] = "Number of Other Satellites Having This as Peer"
    layout_deg['yaxis']['title'] = "Number of Satellites"
    layout_deg['annotations'] = [
        dict(x=0, y=plot_deg[plot_deg['In_Degree']==0]['Count'].iloc[0], text="🚨 64 with 0", showarrow=True, arrowhead=2, arrowcolor="#f87171", ax=35, ay=-25, font=dict(color="#f87171", size=10))
    ]
    fig_deg.update_layout(layout_deg)
    st.plotly_chart(fig_deg, use_container_width=True)

with col_g2:
    st.markdown("#### Spacing vs. Neighbor Count")
    sample_dm = df.sample(n=min(3000, len(df)), random_state=42).copy()
    flagged_dm = df[df['dm_flag'] == 1]
    plot_scatter = pd.concat([sample_dm, flagged_dm]).drop_duplicates(subset=['NORAD_CAT_ID'])
    plot_scatter['DM_Status'] = plot_scatter['dm_flag'].map({1: '🚨 Isolated (Flagged)', 0: 'Standard LEO Spacing'})
    
    # Sort so Flagged points plot on top
    plot_scatter = plot_scatter.sort_values(by='dm_flag')
    
    fig_iso = px.scatter(
        plot_scatter,
        x='incoming_neighbor_count',
        y='mean_neighbor_distance',
        color='DM_Status',
        color_discrete_map={'Standard LEO Spacing': '#38bdf8', '🚨 Isolated (Flagged)': '#ef4444'},
        hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height'],
        labels={'incoming_neighbor_count': 'Incoming Neighbors', 'mean_neighbor_distance': 'Relative Spacing'}
    )
    fig_iso.update_traces(
        marker=dict(size=4, opacity=0.55),
        hovertemplate="<b>%{customdata[1]}</b> (NORAD %{customdata[0]})<br>Incoming Neighbors: %{x}<br>Relative Spacing: %{y:.2f}<br>Altitude: %{customdata[2]:,.0f} km<extra></extra>"
    )
    fig_iso.update_traces(
        selector=dict(name='🚨 Isolated (Flagged)'),
        marker=dict(size=8, opacity=1.0, line=dict(width=1, color='#ffffff'))
    )
    
    max_y = float(plot_scatter['mean_neighbor_distance'].max())
    layout_iso = get_plotly_layout(height=320)
    layout_iso['shapes'] = [
        # Shaded top-left isolation zone
        dict(type="rect", x0=-0.5, x1=0.5, y0=global_mean_dist, y1=max_y * 1.05, fillcolor="rgba(239, 68, 68, 0.15)", line=dict(color="#ef4444", width=1.5, dash="dot"), layer="below"),
        dict(type="line", x0=-0.5, x1=15, y0=global_mean_dist, y1=global_mean_dist, line=dict(color="#94a3b8", dash="dash", width=1))
    ]
    layout_iso['annotations'] = [
        dict(x=0.0, y=max_y * 0.95, text="🚨 Isolated Zone", showarrow=False, font=dict(color="#f87171", size=11, weight="bold"), align="left"),
        dict(x=12, y=global_mean_dist + 0.1, text="Catalog Average Spacing", showarrow=False, font=dict(color="#94a3b8", size=9))
    ]
    layout_iso['legend'] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig_iso.update_layout(layout_iso)
    st.plotly_chart(fig_iso, use_container_width=True)
    st.caption("The shaded red zone (0 incoming neighbors and far spacing) highlights satellites operating in empty corridors.")

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
