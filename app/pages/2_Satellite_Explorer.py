import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, get_plotly_layout
from diagnostics import get_operator_explanation

st.set_page_config(
    page_title="Satellite Mission Inspector",
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
st.markdown('<div class="page-title">Satellite Mission Inspector</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Look up any active LEO satellite to inspect its orbital status, physical parameters, and operational diagnosis.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Filter Controls
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    filter_score = st.selectbox(
        "Filter by alert level:",
        ["Score 2 (Critical Attention)", "Score 1 (Watch List)", "Score 0 (Nominal)", "All Satellites"],
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
st.caption(f"Displaying {len(filtered_df):,} matching satellites:")
options = [
    f"[Score {row['anomaly_score']}] NORAD {row['NORAD_CAT_ID']} · {row['OBJECT_NAME']}"
    for _, row in filtered_df.iterrows()
]
selected_option = st.selectbox("Select satellite to inspect:", options, label_visibility="collapsed")
selected_norad = int(selected_option.split("NORAD ")[1].split(" ·")[0])
sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]

# Compute score info
score = int(sat['anomaly_score'])
score_color = "#ef4444" if score == 2 else ("#f59e0b" if score == 1 else "#10b981")
score_label = "SCORE 2 · CRITICAL ATTENTION" if score == 2 else ("SCORE 1 · WATCH LIST" if score == 1 else "SCORE 0 · NOMINAL ORBIT")

# Satellite Profile Card
epoch_str = str(sat.get('EPOCH', 'N/A'))[:19].replace('T', ' ')
alt_val = float(sat.get('orbit_height', 0.0))
inc_val = float(sat.get('INCLINATION', 0.0))
ecc_val = float(sat.get('ECCENTRICITY', 0.0))
sma_val = float(sat.get('semi_major_axis', 0.0))

# Derive velocity and period if available or from Keplerian physics
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
                <span>Catalog ID: <b style="color: #e2e8f0;">NORAD {sat['NORAD_CAT_ID']}</b></span>
                <span>·</span>
                <span>Orbit Band: <b style="color: #e2e8f0;">Low Earth Orbit ({alt_val:,.0f} km)</b></span>
                <span>·</span>
                <span>Latest Ephemeris Epoch: <b style="color: #e2e8f0;">{epoch_str} UTC</b></span>
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
    st.metric("Period", f"{period_val:.1f} min")

st.markdown("<br>", unsafe_allow_html=True)

# Operator Diagnostic Box
st.markdown("### Operational Diagnostic Assessment")
reasons = get_operator_explanation(sat, df)

box_bg = "rgba(239, 68, 68, 0.08)" if score == 2 else ("rgba(245, 158, 11, 0.08)" if score == 1 else "rgba(16, 185, 129, 0.08)")
box_border = "#ef4444" if score == 2 else ("#f59e0b" if score == 1 else "#10b981")
status_title = "Critical Anomalies Detected" if score == 2 else ("Notice / Deviations Observed" if score == 1 else "Nominal Operating Profile")

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

# Subsystem Checks
st.markdown("### Subsystem Status Checks")
col_s1, col_s2 = st.columns(2)

with col_s1:
    ml_flagged = bool(sat['ml_flag'])
    color_ml = "#ef4444" if ml_flagged else "#10b981"
    tag_ml = "FLAGGED" if ml_flagged else "NOMINAL"
    
    st.markdown(f"""
    <div class="evidence-panel" style="border-top: 3px solid {color_ml};">
        <div class="evidence-header">
            <span style="color: #e2e8f0;">Statistical Orbit Profile Check</span>
            <span style="color: {color_ml}; font-size: 0.8rem; font-weight: 700;">{tag_ml}</span>
        </div>
        <p style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5; margin-bottom: 0px;">
            {
                "This satellite exhibits a statistical outlier profile when compared against active LEO satellites in the same general altitude band." 
                if ml_flagged else 
                "This satellite operates with standard orbital parameters matching common operational LEO constellations."
            }
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_s2:
    dm_flagged = bool(sat['dm_flag'])
    color_dm = "#ef4444" if dm_flagged else "#10b981"
    tag_dm = "ISOLATED" if dm_flagged else "NOMINAL"
    
    st.markdown(f"""
    <div class="evidence-panel" style="border-top: 3px solid {color_dm};">
        <div class="evidence-header">
            <span style="color: #e2e8f0;">Orbital Neighborhood Spacing Check</span>
            <span style="color: {color_dm}; font-size: 0.8rem; font-weight: 700;">{tag_dm}</span>
        </div>
        <p style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5; margin-bottom: 0px;">
            {
                "No other active satellites share this specific orbital plane or spacing. The satellite is structurally isolated in the catalog." 
                if dm_flagged else 
                "The satellite is well-spaced and shares its orbital corridor with normal neighboring satellites."
            }
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Technical Details Expander (Kept light for operators, available for audits)
with st.expander("Technical Subsystem Telemetry (For Engineering Audits)"):
    c_t1, c_t2, c_t3, c_t4 = st.columns(4)
    with c_t1:
        st.metric("K-Means Orbital Cluster", f"Cluster {sat.get('cluster_id', 'N/A')}")
    with c_t2:
        st.metric("Isolation Forest Score", f"{sat.get('ml_anomaly_score', 0):.4f}")
    with c_t3:
        st.metric("Incoming Neighbors (In-Degree)", f"{int(sat.get('incoming_neighbor_count', 0))}")
    with c_t4:
        st.metric("Mean 5-NN Distance", f"{sat.get('mean_neighbor_distance', 0):.4f}")
    st.caption("Standardized feature scores are calculated internally by the pipeline. Operators can use the physical assessment above for routine tracking.")
