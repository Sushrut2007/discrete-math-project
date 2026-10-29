import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.neighbors import NearestNeighbors
from data_loader import load_full_data
from theme import apply_theme, render_metric_card, render_sidebar, get_plotly_layout, PLOTLY_CONFIG
from diagnostics import get_dm_reasons

st.set_page_config(
    page_title="DM Graph Analysis",
    layout="wide"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Satellite data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Discrete Math Graph Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">How a directed 5-nearest-neighbour graph detects isolated satellites flying without close neighbors.</div>', unsafe_allow_html=True)

# Top KPIs
n_total = len(df)
n_dm_flagged = int(df['dm_flag'].sum())
n_dm_normal = n_total - n_dm_flagged
pct_flagged = (n_dm_flagged / n_total) * 100
global_mean_dist = float(df['global_mean_dist'].iloc[0])

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Satellites", f"{n_total:,}", "Graph nodes |V|", "#f8fafc")
with k2:
    render_metric_card("Flagged by DM", f"{n_dm_flagged}", f"{pct_flagged:.2f}% of all satellites", "#f87171", "#ef4444")
with k3:
    render_metric_card("Connected Peers", f"{n_dm_normal:,}", f"{100 - pct_flagged:.2f}% normal spacing", "#34d399", "#10b981")
with k4:
    render_metric_card("Overall Avg Spacing", f"{global_mean_dist:.4f}", "Isolation threshold", "#818cf8")

st.markdown("<br>", unsafe_allow_html=True)

# Important Note on Physical Distance vs Feature Similarity
st.markdown("""
<div class="info-box">
    <b>Important Distinction:</b> Graph neighbour connections represent similarity across orbital features (altitude, tilt, shape, speed, and period), <b>not physical distance between satellites in space</b>.
</div>
""", unsafe_allow_html=True)

# Cached NearestNeighbors model
@st.cache_resource
def get_graph_indexer(feature_data):
    nn_model = NearestNeighbors(n_neighbors=6, algorithm="kd_tree")
    nn_model.fit(feature_data)
    dists, indices = nn_model.kneighbors(feature_data)
    return nn_model, indices, dists

feats = ['std_semi_major_axis', 'std_eccentricity', 'std_inclination']
X = df[feats].to_numpy()
nn_model, nn_indices, nn_dists = get_graph_indexer(X)

# --- Interactive Neighbor Network Section ---
st.markdown("### Satellite Neighbor Network")
st.caption("Select any satellite to see its 5 closest neighbors and whether those neighbors connect back.")

c_ctrl1, c_ctrl2 = st.columns([1, 1.8])

with c_ctrl1:
    filter_mode = st.radio(
        "Choose category:",
        ["Flagged Isolated Satellites (64)", "Normal Satellites (with close neighbors)", "Search by Name or ID"],
        horizontal=False
    )

selected_norad = None

if filter_mode == "Flagged Isolated Satellites (64)":
    flagged_sats = df[df['dm_flag'] == 1].sort_values(by='orbit_height', ascending=False)
    sat_options = {
        f"{row['OBJECT_NAME']} (NORAD {row['NORAD_CAT_ID']}, {row['orbit_height']:.0f} km)": row['NORAD_CAT_ID']
        for _, row in flagged_sats.iterrows()
    }
    with c_ctrl2:
        choice = st.selectbox("Select isolated satellite:", list(sat_options.keys()))
        selected_norad = sat_options.get(choice)

elif filter_mode == "Normal Satellites (with close neighbors)":
    normal_sats = df[(df['dm_flag'] == 0) & (df['incoming_neighbor_count'] >= 4)].sort_values(by='incoming_neighbor_count', ascending=False).head(100)
    sat_options = {
        f"{row['OBJECT_NAME']} (NORAD {row['NORAD_CAT_ID']}, {row['orbit_height']:.0f} km)": row['NORAD_CAT_ID']
        for _, row in normal_sats.iterrows()
    }
    with c_ctrl2:
        choice = st.selectbox("Select normal satellite:", list(sat_options.keys()))
        selected_norad = sat_options.get(choice)

else:
    with c_ctrl2:
        search_query = st.text_input("Enter satellite name or NORAD ID:", placeholder="e.g. ISS, STARLINK, 25544...")
        if search_query.strip():
            sq = search_query.strip().lower()
            matched = df[
                df['OBJECT_NAME'].str.lower().str.contains(sq, na=False) |
                df['NORAD_CAT_ID'].astype(str).str.contains(sq, na=False)
            ].head(50)
            if not matched.empty:
                sat_options = {
                    f"{row['OBJECT_NAME']} (NORAD {row['NORAD_CAT_ID']})": row['NORAD_CAT_ID']
                    for _, row in matched.iterrows()
                }
                choice = st.selectbox("Matching satellites:", list(sat_options.keys()))
                selected_norad = sat_options.get(choice)
            else:
                st.warning("No satellites found matching that search.")
        else:
            st.info("Type a name or ID to search.")

# If a satellite is selected, render network graph & operator details
if selected_norad is not None:
    target_matches = df.index[df['NORAD_CAT_ID'] == selected_norad].tolist()
    if target_matches:
        target_idx = target_matches[0]
        target_row = df.iloc[target_idx]
        
        nbr_indices = nn_indices[target_idx, 1:]
        nbr_distances = nn_dists[target_idx, 1:]
        
        # Coordinates in 2D circular layout
        angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, 5, endpoint=False)
        radius = 2.0
        
        x_nodes = [0.0]
        y_nodes = [0.0]
        node_names = [target_row['OBJECT_NAME']]
        node_norads = [target_row['NORAD_CAT_ID']]
        node_alts = [target_row['orbit_height']]
        node_incs = [target_row['INCLINATION']]
        
        for k in range(5):
            nbr_idx = nbr_indices[k]
            nbr_row = df.iloc[nbr_idx]
            x_nodes.append(radius * np.cos(angles[k]))
            y_nodes.append(radius * np.sin(angles[k]))
            node_names.append(nbr_row['OBJECT_NAME'])
            node_norads.append(nbr_row['NORAD_CAT_ID'])
            node_alts.append(nbr_row['orbit_height'])
            node_incs.append(nbr_row['INCLINATION'])
            
        fig_net = go.Figure()
        
        # Inter-neighbor links (links between the 5 neighbors)
        inter_x, inter_y = [], []
        for i in range(5):
            for j in range(i + 1, 5):
                idx_i = nbr_indices[i]
                idx_j = nbr_indices[j]
                if idx_j in nn_indices[idx_i, 1:] or idx_i in nn_indices[idx_j, 1:]:
                    inter_x.extend([x_nodes[i + 1], x_nodes[j + 1], None])
                    inter_y.extend([y_nodes[i + 1], y_nodes[j + 1], None])
                    
        if inter_x:
            fig_net.add_trace(go.Scatter(
                x=inter_x, y=inter_y,
                mode='lines',
                line=dict(color='rgba(148, 163, 184, 0.25)', width=1.5, dash='dot'),
                hoverinfo='none',
                showlegend=False
            ))
            
        # Links between target and neighbors
        reciprocal_count = 0
        for k in range(5):
            nbr_idx = nbr_indices[k]
            points_back = target_idx in nn_indices[nbr_idx, 1:]
            if points_back:
                reciprocal_count += 1
                line_color = '#10b981' # Green/Emerald
                line_dash = 'solid'
                line_width = 2.5
            else:
                line_color = '#ef4444' # Red/Coral
                line_dash = 'dash'
                line_width = 1.8
                
            fig_net.add_trace(go.Scatter(
                x=[0, x_nodes[k + 1]],
                y=[0, y_nodes[k + 1]],
                mode='lines',
                line=dict(color=line_color, width=line_width, dash=line_dash),
                hoverinfo='none',
                showlegend=False
            ))
            
            # Arrow from center to neighbor
            fig_net.add_annotation(
                x=x_nodes[k + 1] * 0.65,
                y=y_nodes[k + 1] * 0.65,
                ax=0,
                ay=0,
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor=line_color
            )
            
            # If neighbor points back, add reverse arrow
            if points_back:
                fig_net.add_annotation(
                    x=x_nodes[k + 1] * 0.35,
                    y=y_nodes[k + 1] * 0.35,
                    ax=x_nodes[k + 1] * 0.7,
                    ay=y_nodes[k + 1] * 0.7,
                    xref='x', yref='y', axref='x', ayref='y',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=2,
                    arrowcolor=line_color
                )
                
        # Outer Neighbor Nodes
        fig_net.add_trace(go.Scatter(
            x=x_nodes[1:],
            y=y_nodes[1:],
            mode='markers+text',
            marker=dict(size=18, color='#38bdf8', line=dict(color='#0284c7', width=2)),
            text=[f"<b>{name[:13]}</b>" for name in node_names[1:]],
            textposition="top center",
            textfont=dict(color='#cbd5e1', size=11),
            hovertext=[
                f"<b>{name}</b><br>NORAD: {norad}<br>Altitude: {alt:,.1f} km<br>Tilt: {inc:.2f}°"
                for name, norad, alt, inc in zip(node_names[1:], node_norads[1:], node_alts[1:], node_incs[1:])
            ],
            hoverinfo='text',
            showlegend=False
        ))
        
        # Center Target Node
        is_dm_flagged = bool(target_row.get('dm_flag', 0)) or (int(target_row.get('incoming_neighbor_count', 0)) == 0)
        target_color = '#ef4444' if is_dm_flagged else '#10b981'
        target_border = '#b91c1c' if is_dm_flagged else '#059669'
        
        fig_net.add_trace(go.Scatter(
            x=[0],
            y=[0],
            mode='markers+text',
            marker=dict(size=26, color=target_color, line=dict(color=target_border, width=3)),
            text=[f"<b>{node_names[0][:15]}</b><br>(Selected)"],
            textposition="bottom center",
            textfont=dict(color='#f8fafc', size=12),
            hovertext=[
                f"<b>{node_names[0]} (Selected)</b><br>NORAD: {node_norads[0]}<br>Altitude: {node_alts[0]:,.1f} km<br>Tilt: {node_incs[0]:.2f}°<br>Incoming Connections: {target_row.get('incoming_neighbor_count', 0)}"
            ],
            hoverinfo='text',
            showlegend=False
        ))
        
        fig_net.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15, 23, 42, 0.4)',
            showlegend=False,
            margin=dict(l=15, r=15, t=25, b=25),
            height=370,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2.8, 2.8]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2.8, 2.8])
        )
        
        # Render side-by-side: graph on left, status card on right
        col_g_plot, col_g_status = st.columns([1.3, 1])
        with col_g_plot:
            st.plotly_chart(fig_net, use_container_width=True, config=PLOTLY_CONFIG)
            st.caption("Green solid arrows: mutual neighbors. Red dashed arrows: one-way only (neighbor points elsewhere). Dotted gray lines: connections among the neighbors themselves.")
            
        with col_g_status:
            in_count = int(target_row.get('incoming_neighbor_count', 0))
            avg_d = float(target_row.get('mean_neighbor_distance', 0.0))
            alt_val = float(target_row.get('orbit_height', 0.0))
            tilt_val = float(target_row.get('INCLINATION', 0.0))
            
            if is_dm_flagged:
                status_title = "⚠️ Isolated Orbit"
                status_color = "#ef4444"
                status_desc = f"This satellite points to its 5 closest neighbors, but <b>0 satellites point back</b> to it. Its neighbors belong to other satellite groups and point to each other instead. It flies alone in space without close neighbors."
            else:
                status_title = "✅ Connected Orbit"
                status_color = "#10b981"
                status_desc = f"This satellite has <b>{reciprocal_count} mutual neighbors</b> (and {in_count} other satellites total have it as a close neighbor). It flies in a group with other satellites."
                
            st.markdown(f"""
            <div style="background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid {status_color}; border-radius: 6px; padding: 18px 20px; margin-top: 10px;">
                <div style="font-weight: 700; color: {status_color}; font-size: 1.05rem; margin-bottom: 8px;">{status_title}</div>
                <div style="font-size: 0.88rem; color: #f8fafc; font-weight: 600; margin-bottom: 12px;">{target_row['OBJECT_NAME']} (NORAD {target_row['NORAD_CAT_ID']})</div>
                <p style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 14px;">
                    {status_desc}
                </p>
                <div style="font-size: 0.82rem; color: #94a3b8; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 10px;">
                    <div>• <b>Altitude:</b> {alt_val:,.1f} km</div>
                    <div style="margin-top: 4px;">• <b>Orbital Tilt:</b> {tilt_val:.2f}°</div>
                    <div style="margin-top: 4px;">• <b>Incoming Connections:</b> {in_count} satellites</div>
                    <div style="margin-top: 4px;">• <b>Average Neighbor Spacing:</b> {avg_d:.4f} (overall average: {global_mean_dist:.4f})</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

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

st.caption("Red bar: exactly 64 satellites have 0 incoming neighbors (unreciprocated in the 5-NN graph) and an average neighbor distance exceeding the overall average.")

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
