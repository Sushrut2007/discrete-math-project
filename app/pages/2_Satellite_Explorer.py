import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, get_plotly_layout

st.set_page_config(
    page_title="Satellite Deep-Dive Explorer",
    page_icon="🔍",
    layout="wide"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Catalog data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Satellite Deep-Dive Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Interactive inspection tool comparing Machine Learning and Discrete Math structural evidence side-by-side.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Filter Controls
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    filter_score = st.selectbox(
        "Filter by Evidence Level:",
        ["Score 2 · High Priority (Both Flagged)", "Score 1 · Single Model Flag", "Score 0 · Nominal", "All Spacecraft"],
        index=0
    )
with col_f2:
    search_query = st.text_input("Search by NORAD ID or Name:", placeholder="e.g. 28885, STARLINK, COSMOS...")

# Filter dataset
filtered_df = df.copy()
if "Score 2" in filter_score:
    filtered_df = filtered_df[filtered_df['anomaly_score'] == 2]
elif "Score 1" in filter_score:
    filtered_df = filtered_df[filtered_df['anomaly_score'] == 1]
elif "Score 0" in filter_score:
    filtered_df = filtered_df[filtered_df['anomaly_score'] == 0]

if search_query.strip():
    q = search_query.strip().lower()
    filtered_df = filtered_df[
        filtered_df['OBJECT_NAME'].str.lower().str.contains(q, na=False) |
        filtered_df['NORAD_CAT_ID'].astype(str).str.contains(q, na=False)
    ]

if len(filtered_df) == 0:
    st.warning("No satellites match the selected filter or search query.")
    st.stop()

# Satellite selection
st.caption(f"Showing {len(filtered_df):,} matching satellites:")
options = [
    f"[Score {row['anomaly_score']}] NORAD {row['NORAD_CAT_ID']} · {row['OBJECT_NAME']}"
    for _, row in filtered_df.iterrows()
]
selected_option = st.selectbox("Select Spacecraft to Inspect:", options, label_visibility="collapsed")
selected_norad = int(selected_option.split("NORAD ")[1].split(" ·")[0])
sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]

# Compute score info
score = int(sat['anomaly_score'])
score_color = "#ef4444" if score == 2 else ("#f59e0b" if score == 1 else "#10b981")
score_label = "HIGH PRIORITY DUAL FLAG" if score == 2 else ("MODERATE REVIEW" if score == 1 else "NOMINAL ORBIT")

# Satellite Profile Card
epoch_str = str(sat.get('EPOCH', 'N/A'))[:19].replace('T', ' ')
cluster_id = sat.get('cluster_id', 'N/A')

st.markdown(f"""
<div style="background: linear-gradient(145deg, #131b2e 0%, #0d1322 100%); border: 1px solid rgba(255,255,255,0.08); border-left: 4px solid {score_color}; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 1.6rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em;">
                {sat['OBJECT_NAME']}
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; display: flex; gap: 12px; flex-wrap: wrap;">
                <span>NORAD ID: <b style="color: #e2e8f0;">{sat['NORAD_CAT_ID']}</b></span>
                <span>·</span>
                <span>Orbital Regime: <b style="color: #e2e8f0;">Cluster {cluster_id}</b></span>
                <span>·</span>
                <span>Epoch: <b style="color: #e2e8f0;">{epoch_str} UTC</b></span>
            </div>
        </div>
        <div>
            <span style="display: inline-block; background: {score_color}22; color: {score_color}; border: 1px solid {score_color}55; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.05em;">
                SCORE {score} · {score_label}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Orbital Elements Grid
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Altitude (Perigee/Apogee)", f"{sat['orbit_height']:.1f} km")
with k2:
    st.metric("Inclination", f"{sat['INCLINATION']:.2f}°")
with k3:
    st.metric("Eccentricity", f"{sat['ECCENTRICITY']:.5f}")
with k4:
    st.metric("Semi-Major Axis", f"{sat['semi_major_axis']:.1f} km")
with k5:
    st.metric("K-Means Cluster", f"Cluster {cluster_id}")

st.markdown("<br>", unsafe_allow_html=True)

# Side-by-side Model Evidence
st.markdown("### Model Evidence Comparison")
col_ml, col_dm = st.columns(2)

with col_ml:
    ml_flagged = bool(sat['ml_flag'])
    ml_status_color = "#ef4444" if ml_flagged else "#10b981"
    ml_status_text = "FLAGGED (ANOMALOUS)" if ml_flagged else "NORMAL (WITHIN BOUNDS)"
    
    st.markdown(f"""
    <div class="evidence-panel" style="border-top: 3px solid {ml_status_color};">
        <div class="evidence-header">
            <span style="color: #e2e8f0;">Machine Learning Component</span>
            <span style="color: {ml_status_color}; font-size: 0.8rem; font-weight: 700;">{ml_status_text}</span>
        </div>
        <div style="margin-bottom: 12px;">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Methodology</div>
            <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 2px;">
                Intra-Cluster Isolation Forest trained on K-Means orbital family (Cluster {cluster_id}).
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
            <div style="background: rgba(0,0,0,0.25); padding: 10px; border-radius: 6px;">
                <div style="font-size: 0.75rem; color: #94a3b8;">Isolation Forest Score</div>
                <div style="font-size: 1.15rem; font-weight: 600; color: #f8fafc;">{sat['ml_anomaly_score']:.4f}</div>
                <div style="font-size: 0.7rem; color: #64748b;">(Negative = Outlier)</div>
            </div>
            <div style="background: rgba(0,0,0,0.25); padding: 10px; border-radius: 6px;">
                <div style="font-size: 0.75rem; color: #94a3b8;">Cluster Assignment</div>
                <div style="font-size: 1.15rem; font-weight: 600; color: #f8fafc;">Cluster {cluster_id}</div>
                <div style="font-size: 0.7rem; color: #64748b;">Orbital Family Context</div>
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
            <b>Diagnostic Assessment:</b><br>
            {
                "The spacecraft's orbital parameters isolate quickly during recursive tree partitioning, placing it in the extreme tail of its orbital family distribution." 
                if ml_flagged else 
                "The spacecraft's telemetry falls well within the high-density region of its assigned orbital family."
            }
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_dm:
    dm_flagged = bool(sat['dm_flag'])
    dm_status_color = "#ef4444" if dm_flagged else "#10b981"
    dm_status_text = "FLAGGED (TOPOLOGICALLY ISOLATED)" if dm_flagged else "NORMAL (WELL CONNECTED)"
    in_deg = int(sat['incoming_neighbor_count'])
    mean_dist = float(sat['mean_neighbor_distance'])
    global_mean = float(sat['global_mean_dist'])
    
    st.markdown(f"""
    <div class="evidence-panel" style="border-top: 3px solid {dm_status_color};">
        <div class="evidence-header">
            <span style="color: #e2e8f0;">Discrete Mathematics Component</span>
            <span style="color: {dm_status_color}; font-size: 0.8rem; font-weight: 700;">{dm_status_text}</span>
        </div>
        <div style="margin-bottom: 12px;">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Methodology</div>
            <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 2px;">
                Directed 5-Nearest Neighbour Graph in standardized 6D orbital parameter space.
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
            <div style="background: rgba(0,0,0,0.25); padding: 10px; border-radius: 6px;">
                <div style="font-size: 0.75rem; color: #94a3b8;">In-Degree d⁻(v)</div>
                <div style="font-size: 1.15rem; font-weight: 600; color: #f8fafc;">{in_deg} incoming edges</div>
                <div style="font-size: 0.7rem; color: #64748b;">(Must equal 0 for flag)</div>
            </div>
            <div style="background: rgba(0,0,0,0.25); padding: 10px; border-radius: 6px;">
                <div style="font-size: 0.75rem; color: #94a3b8;">Mean 5-NN Distance</div>
                <div style="font-size: 1.15rem; font-weight: 600; color: #f8fafc;">{mean_dist:.4f}</div>
                <div style="font-size: 0.7rem; color: #64748b;">Global Mean: {global_mean:.4f}</div>
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
            <b>Diagnostic Assessment:</b><br>
            {
                f"Structurally isolated: No other satellite selects this node among its 5 nearest neighbours (in-degree = 0) and its own mean neighbor distance ({mean_dist:.4f}) exceeds the catalog average ({global_mean:.4f})."
                if dm_flagged else
                f"Connected graph node: Selected by {in_deg} satellite(s) as a nearest neighbour with acceptable local density."
            }
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Contextual Deviation Radar
st.markdown("#### Parameter Deviation from Catalog Median")
features_compare = ['orbit_height', 'INCLINATION', 'ECCENTRICITY', 'semi_major_axis']
labels_compare = ['Altitude (km)', 'Inclination (°)', 'Eccentricity', 'Semi-Major Axis (km)']

medians = df[features_compare].median()
stds = df[features_compare].std()
z_scores = [(sat[f] - medians[f]) / (stds[f] if stds[f] > 0 else 1.0) for f in features_compare]

fig_bar = go.Figure()
bar_colors = ['#ef4444' if abs(z) > 2.0 else '#60a5fa' for z in z_scores]

fig_bar.add_trace(go.Bar(
    x=labels_compare,
    y=z_scores,
    marker_color=bar_colors,
    text=[f"{z:+.2f} σ" for z in z_scores],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Z-Score: %{y:.2f} σ<extra></extra>"
))

layout_bar = get_plotly_layout(height=260)
layout_bar['yaxis']['title'] = "Standard Deviations from Median (σ)"
layout_bar['xaxis']['title'] = ""
layout_bar['shapes'] = [
    dict(type="line", y0=2, y1=2, x0=-0.5, x1=3.5, line=dict(color="#ef4444", dash="dash", width=1)),
    dict(type="line", y0=-2, y1=-2, x0=-0.5, x1=3.5, line=dict(color="#ef4444", dash="dash", width=1))
]
fig_bar.update_layout(layout_bar)
st.plotly_chart(fig_bar, use_container_width=True)
st.caption("Dashed lines represent ±2.0 standard deviations from the catalog median. Parameters exceeding this threshold indicate the primary drivers of anomalous classification.")
