import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, get_plotly_layout
from diagnostics import get_operator_explanation

st.set_page_config(
    page_title="Satellite Explorer",
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
st.markdown('<div class="page-title">Satellite Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Search for any active LEO satellite to inspect its orbital values and see why it got flagged.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Filter Controls
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    filter_score = st.selectbox(
        "Filter by score:",
        ["Score 2 (Flagged by both)", "Score 1 (Flagged by one)", "Score 0 (Normal)", "All Satellites"],
        index=0
    )
with col_f2:
    search_query = st.text_input("Search by NORAD ID or name:", placeholder="e.g. 38745, EXPRESS, STARLINK, ISS...")

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
selected_option = st.selectbox("Select satellite:", options, label_visibility="collapsed")
selected_norad = int(selected_option.split("NORAD ")[1].split(" ·")[0])
sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]

# Compute score info
score = int(sat['anomaly_score'])
score_color = "#ef4444" if score == 2 else ("#f59e0b" if score == 1 else "#10b981")
score_label = "SCORE 2 · BOTH FLAGGED" if score == 2 else ("SCORE 1 · ONE FLAGGED" if score == 1 else "SCORE 0 · NORMAL")

# Satellite Profile Card
epoch_str = str(sat.get('EPOCH', 'N/A'))[:19].replace('T', ' ')
alt_val = float(sat.get('orbit_height', 0.0))
inc_val = float(sat.get('INCLINATION', 0.0))
ecc_val = float(sat.get('ECCENTRICITY', 0.0))
sma_val = float(sat.get('semi_major_axis', 0.0))

# Speed and period
mu = 398600.4418
speed_val = (mu / sma_val) ** 0.5 if sma_val > 0 else 7.5
period_val = (2 * 3.14159265 * (sma_val ** 1.5)) / (mu ** 0.5) / 60 if sma_val > 0 else 95.0

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
                <span>Altitude: <b style="color: #e2e8f0;">{alt_val:,.0f} km</b></span>
                <span>·</span>
                <span>Data Date: <b style="color: #e2e8f0;">{epoch_str} UTC</b></span>
            </div>
        </div>
        <div>
            <span style="display: inline-block; background: {score_color}22; color: {score_color}; border: 1px solid {score_color}55; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.05em;">
                {score_label}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Orbital Elements Grid (Physical Units)
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Altitude", f"{alt_val:,.1f} km")
with k2:
    st.metric("Inclination", f"{inc_val:.2f}°")
with k3:
    st.metric("Eccentricity", f"{ecc_val:.5f}")
with k4:
    st.metric("Orbital Speed", f"{speed_val:.2f} km/s")
with k5:
    st.metric("Orbital Period", f"{period_val:.1f} min")

st.markdown("<br>", unsafe_allow_html=True)

# Visual Comparison: Map & Benchmark Table
col_v1, col_v2 = st.columns([1.2, 1])

with col_v1:
    st.markdown("#### Position in Low Earth Orbit")
    bg_df = df.sample(n=min(2000, len(df)), random_state=42)
    fig_loc = go.Figure()
    
    # Background satellites
    fig_loc.add_trace(go.Scatter(
        x=bg_df['orbit_height'],
        y=bg_df['INCLINATION'],
        mode='markers',
        marker=dict(size=4, color='#334155', opacity=0.4),
        name='LEO Catalog',
        hoverinfo='skip'
    ))
    
    # Selected satellite
    fig_loc.add_trace(go.Scatter(
        x=[alt_val],
        y=[inc_val],
        mode='markers+text',
        marker=dict(size=14, color=score_color, symbol='diamond', line=dict(width=2, color='#ffffff')),
        text=[sat['OBJECT_NAME']],
        textposition="top center",
        textfont=dict(size=11, color='#f8fafc'),
        name=sat['OBJECT_NAME'],
        hovertemplate=f"<b>{sat['OBJECT_NAME']}</b><br>Altitude: {alt_val:,.1f} km<br>Inclination: {inc_val:.2f}°<extra></extra>"
    ))
    
    loc_layout = get_plotly_layout(height=280)
    loc_layout['xaxis']['title'] = "Altitude (km)"
    loc_layout['yaxis']['title'] = "Inclination (°)"
    loc_layout['xaxis']['range'] = [100, 2000]
    loc_layout['yaxis']['range'] = [0, 115]
    loc_layout['showlegend'] = False
    fig_loc.update_layout(loc_layout)
    st.plotly_chart(fig_loc, use_container_width=True)
    st.caption("Gray dots represent active LEO satellites. Diamond marks this satellite's orbit.")

with col_v2:
    st.markdown("#### Comparison with LEO Norms")
    
    if alt_val > 1000:
        alt_status = "Upper LEO Corridor (Rare)"
    elif alt_val < 350:
        alt_status = "Very Low Orbit (Decay Zone)"
    else:
        alt_status = "Standard Shell (Common)"
        
    if ecc_val > 0.05:
        ecc_status = "Highly Elliptical (Rare in LEO)"
    elif ecc_val > 0.01:
        ecc_status = "Slightly Oval"
    else:
        ecc_status = "Near Circular (Standard)"
        
    if 95 <= inc_val <= 105:
        inc_status = "Sun-Synchronous Polar Shell"
    elif abs(inc_val - 53.0) < 5:
        inc_status = "Standard Constellation Tilt (53°)"
    else:
        inc_status = f"Uncommon Tilt ({inc_val:.1f}°)"
        
    in_deg = int(sat.get('incoming_neighbor_count', 0))
    if in_deg == 0:
        nbr_status = "Isolated (0 close peers)"
    elif in_deg >= 5:
        nbr_status = "Well Connected (Standard)"
    else:
        nbr_status = "Sparse Neighborhood"

    comp_df = pd.DataFrame([
        {"Parameter": "Altitude", "This Satellite": f"{alt_val:,.1f} km", "Typical LEO": "480–550 km", "Assessment": alt_status},
        {"Parameter": "Orbit Shape (Ecc.)", "This Satellite": f"{ecc_val:.5f}", "Typical LEO": "< 0.001", "Assessment": ecc_status},
        {"Parameter": "Inclination (Tilt)", "This Satellite": f"{inc_val:.2f}°", "Typical LEO": "53° or 98°", "Assessment": inc_status},
        {"Parameter": "Close Neighbors", "This Satellite": f"{in_deg}", "Typical LEO": "5", "Assessment": nbr_status},
    ])
    
    st.dataframe(comp_df, hide_index=True, use_container_width=True)
    st.caption("Benchmarked against the active LEO population median.")

st.markdown("<br>", unsafe_allow_html=True)

# Why Flagged Box
st.markdown("### Why was this satellite flagged?")
reasons = get_operator_explanation(sat, df)

box_bg = "rgba(239, 68, 68, 0.08)" if score == 2 else ("rgba(245, 158, 11, 0.08)" if score == 1 else "rgba(16, 185, 129, 0.08)")
box_border = "#ef4444" if score == 2 else ("#f59e0b" if score == 1 else "#10b981")
status_title = "Flagged by Both Methods" if score == 2 else ("Flagged by One Method" if score == 1 else "Normal Orbit")

reasons_html = "".join([f"<li style='margin-bottom: 6px;'>{r}</li>" for r in reasons])

st.markdown(f"""
<div style="background: {box_bg}; border: 1px solid {box_border}55; border-left: 4px solid {box_border}; border-radius: 8px; padding: 16px 20px; margin-bottom: 24px;">
    <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">
        {status_title}
    </div>
    <ul style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin: 0; padding-left: 18px;">
        {reasons_html}
    </ul>
</div>
""", unsafe_allow_html=True)

# Method Checks
st.markdown("### Method Checks")
col_s1, col_s2 = st.columns(2)

with col_s1:
    ml_flagged = bool(sat['ml_flag'])
    color_ml = "#ef4444" if ml_flagged else "#10b981"
    tag_ml = "FLAGGED" if ml_flagged else "NORMAL"
    
    st.markdown(f"""
    <div class="evidence-panel" style="border-top: 3px solid {color_ml};">
        <div class="evidence-header">
            <span style="color: #e2e8f0;">Machine Learning Check</span>
            <span style="color: {color_ml}; font-size: 0.8rem; font-weight: 700;">{tag_ml}</span>
        </div>
        <p style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5; margin-bottom: 0px;">
            {
                "This satellite sits far from other satellites in its cluster, so the Isolation Forest algorithm marks it as an outlier." 
                if ml_flagged else 
                "This satellite's orbit fits right in with other satellites in its cluster."
            }
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_s2:
    dm_flagged = bool(sat['dm_flag'])
    color_dm = "#ef4444" if dm_flagged else "#10b981"
    tag_dm = "FLAGGED" if dm_flagged else "NORMAL"
    
    st.markdown(f"""
    <div class="evidence-panel" style="border-top: 3px solid {color_dm};">
        <div class="evidence-header">
            <span style="color: #e2e8f0;">Discrete Math (Graph) Check</span>
            <span style="color: {color_dm}; font-size: 0.8rem; font-weight: 700;">{tag_dm}</span>
        </div>
        <p style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5; margin-bottom: 0px;">
            {
                "No other satellite has this satellite in its 5 nearest neighbors (in-degree is 0), and its own neighbors are unusually far away." 
                if dm_flagged else 
                "This satellite has neighboring satellites in similar orbits and is well-connected in the graph."
            }
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Technical Details Expander
with st.expander("Technical Model Details"):
    c_t1, c_t2, c_t3, c_t4 = st.columns(4)
    with c_t1:
        st.metric("K-Means Cluster", f"Cluster {sat.get('cluster_id', 'N/A')}")
    with c_t2:
        st.metric("Isolation Forest Score", f"{sat.get('ml_anomaly_score', 0):.4f}")
    with c_t3:
        st.metric("Incoming Neighbors (In-Degree)", f"{int(sat.get('incoming_neighbor_count', 0))}")
    with c_t4:
        st.metric("Mean 5-NN Distance", f"{sat.get('mean_neighbor_distance', 0):.4f}")
