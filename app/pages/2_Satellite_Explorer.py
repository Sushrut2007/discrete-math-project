import streamlit as st
import pandas as pd
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, get_badge_html

st.set_page_config(
    page_title="Satellite Explorer",
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
st.markdown('<div class="page-subtitle">Search and inspect individual satellites to see detector results, reasons, and orbital features.</div>', unsafe_allow_html=True)

# Controls
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    filter_score = st.selectbox(
        "Filter by score:",
        ["Score 2 — Both flagged", "Score 1 — One flag", "Score 0 — No flags", "All satellites"],
        index=0
    )
with col_f2:
    search_query = st.text_input("Search by name or NORAD ID:", placeholder="e.g. EXPRESS, 38745, STARLINK, ISS...")

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

# Satellite selection dropdown
options = [
    f"[Score {row['anomaly_score']}] NORAD {row['NORAD_CAT_ID']} · {row['OBJECT_NAME']}"
    for _, row in filtered_df.iterrows()
]
selected_option = st.selectbox("Select satellite:", options)
selected_norad = int(selected_option.split("NORAD ")[1].split(" ·")[0])
sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]

score = int(sat['anomaly_score'])
epoch_str = str(sat.get('EPOCH', 'N/A'))[:19].replace('T', ' ')
alt_val = float(sat.get('orbit_height', 0.0))
inc_val = float(sat.get('INCLINATION', 0.0))
ecc_val = float(sat.get('ECCENTRICITY', 0.0))
sma_val = float(sat.get('semi_major_axis', 0.0))

mu = 398600.4418
speed_val = (mu / sma_val) ** 0.5 if sma_val > 0 else 7.5
period_val = (2 * 3.14159265 * (sma_val ** 1.5)) / (mu ** 0.5) / 60 if sma_val > 0 else 95.0

# Satellite Identity Card
score_badge = get_badge_html(score)
st.markdown(f"""
<div style="background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 18px 22px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em;">
                {sat['OBJECT_NAME']}
            </div>
            <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 4px; display: flex; gap: 12px; flex-wrap: wrap;">
                <span>NORAD ID: <b style="color: #e2e8f0;">{sat['NORAD_CAT_ID']}</b></span>
                <span>·</span>
                <span>Altitude: <b style="color: #e2e8f0;">{alt_val:,.1f} km</b></span>
                <span>·</span>
                <span>Epoch: <b style="color: #e2e8f0;">{epoch_str} UTC</b></span>
            </div>
        </div>
        <div>
            {score_badge}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Orbital Elements Metrics
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Altitude", f"{alt_val:,.1f} km")
with k2:
    st.metric("Semi-Major Axis", f"{sma_val:,.1f} km")
with k3:
    st.metric("Inclination", f"{inc_val:.2f}°")
with k4:
    st.metric("Eccentricity", f"{ecc_val:.5f}")
with k5:
    st.metric("Orbital Speed", f"{speed_val:.2f} km/s")
with k6:
    st.metric("Orbital Period", f"{period_val:.1f} min")

st.markdown("<br>", unsafe_allow_html=True)

# Detector Results Section
st.markdown("### Detector Results")

col_ml, col_dm = st.columns(2)

with col_ml:
    ml_flagged = bool(sat['ml_flag'])
    tag_ml = "FLAGGED" if ml_flagged else "NOT FLAGGED"
    tag_color = "#f87171" if ml_flagged else "#34d399"
    border_color = "#dc2626" if ml_flagged else "rgba(255,255,255,0.08)"
    
    st.markdown(f"""
    <div style="background: #1e293b; border: 1px solid {border_color}; border-radius: 6px; padding: 16px 20px; height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-weight: 600; color: #f8fafc; font-size: 0.95rem;">Machine Learning Result</span>
            <span style="color: {tag_color}; font-weight: 700; font-size: 0.8rem; letter-spacing: 0.05em;">{tag_ml}</span>
        </div>
        <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0px;">
            {"ML flagged this satellite because its orbital features are unusual compared with other satellites in its group." if ml_flagged else "ML did not flag this satellite. Its orbital features are consistent with other satellites in its group."}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_dm:
    dm_flagged = bool(sat['dm_flag'])
    tag_dm = "FLAGGED" if dm_flagged else "NOT FLAGGED"
    tag_color_dm = "#f87171" if dm_flagged else "#34d399"
    border_color_dm = "#dc2626" if dm_flagged else "rgba(255,255,255,0.08)"
    
    st.markdown(f"""
    <div style="background: #1e293b; border: 1px solid {border_color_dm}; border-radius: 6px; padding: 16px 20px; height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-weight: 600; color: #f8fafc; font-size: 0.95rem;">Discrete Math (Graph) Result</span>
            <span style="color: {tag_color_dm}; font-weight: 700; font-size: 0.8rem; letter-spacing: 0.05em;">{tag_dm}</span>
        </div>
        <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0px;">
            {"DM flagged this satellite because no other satellite selected it among its five nearest orbital-feature neighbours, and its average distance to those neighbours is above the dataset average." if dm_flagged else "DM did not flag this satellite. It has nearby peers in orbital-feature space and is connected to other satellites in the graph."}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Final Assessment Summary
if score == 2:
    st.markdown("""
    <div style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; border-radius: 4px; padding: 12px 16px; font-size: 0.88rem; color: #f8fafc;">
        <b>Both methods flagged this satellite.</b> Review this satellite first.
    </div>
    """, unsafe_allow_html=True)
elif score == 1:
    st.markdown("""
    <div style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; border-radius: 4px; padding: 12px 16px; font-size: 0.88rem; color: #f8fafc;">
        <b>One method flagged this satellite.</b> See individual detector results above.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: rgba(16, 185, 129, 0.08); border-left: 3px solid #10b981; border-radius: 4px; padding: 12px 16px; font-size: 0.88rem; color: #f8fafc;">
        <b>Neither method flagged this satellite.</b> It operates within standard orbital ranges.
    </div>
    """, unsafe_allow_html=True)

# Technical Details Expander
with st.expander("Technical details"):
    c_t1, c_t2, c_t3, c_t4, c_t5 = st.columns(5)
    with c_t1:
        st.metric("Assigned Orbital Group", f"Group {sat.get('cluster_id', 'N/A')}")
    with c_t2:
        st.metric("ML Decision Score", f"{sat.get('ml_anomaly_score', 0):.4f}")
    with c_t3:
        st.metric("Incoming Neighbours", f"{int(sat.get('incoming_neighbor_count', 0))}")
    with c_t4:
        st.metric("Avg Neighbour Distance", f"{sat.get('mean_neighbor_distance', 0):.4f}")
    with c_t5:
        st.metric("Dataset Avg Distance", f"{sat.get('global_mean_dist', 0):.4f}")
    
    st.caption("Note: Neighbour relationships are calculated in normalized orbital-feature space, not physical distance in space.")
