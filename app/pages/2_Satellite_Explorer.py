import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="Anomaly Inspector", layout="wide")
df = load_full_data()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    
    .anomaly-card {
        background: linear-gradient(145deg, rgba(35, 40, 50, 0.9), rgba(25, 30, 35, 0.95));
        border-radius: 0 12px 12px 0;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .satellite-name { font-size: 1.4rem; font-weight: 600; color: #e0e0e8; margin-bottom: 4px; display: block; }
    .anomaly-reason { color: #94a3b8; font-size: 0.9rem; line-height: 1.5; margin-top: 12px; }
    
    .meta-tag {
        display: inline-block;
        background: rgba(100, 100, 150, 0.15);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #94a3b8;
        margin-right: 8px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .severity-critical { border-left: 4px solid #ef4444; }
    .severity-high { border-left: 4px solid #f97316; }
    .severity-moderate { border-left: 4px solid #fbbf24; }
    .severity-low { border-left: 4px solid #22c55e; }
    
    .sub-glow {
        height: 2px;
        width: 60px;
        background: linear-gradient(90deg, #00d4ff, transparent);
        margin-bottom: 20px;
    }
    
    .metric-box {
        background: rgba(10, 10, 15, 0.3);
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.02);
    }
    .metric-box-title { color: #8B949E; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .metric-box-val { color: #e0e0e8; font-size: 1.2rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="padding: 10px 0 20px 0;">
    <h1 style="font-size: 2rem; font-weight: 700; color: #e0e0e8; margin-bottom: 4px;">
        ⚠️ Anomaly Inspector
    </h1>
    <p style="color: #8888aa; font-size: 1rem;">
        Detailed review of spacecraft telemetry and risk assessment.
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### Catalog Filters")
search_q = st.sidebar.text_input("Search ID / Name")
status_filter = st.sidebar.selectbox("Risk Level", ["All Levels", "Nominal (Score 0)", "Warning (Score 1-2)", "Critical (Score 3)"])

filtered = df.copy()
if search_q:
    q = search_q.lower()
    filtered = filtered[
        filtered['OBJECT_NAME'].str.lower().str.contains(q, na=False) |
        filtered['NORAD_CAT_ID'].astype(str).str.contains(q, na=False)
    ]
if status_filter == "Nominal (Score 0)": filtered = filtered[filtered['anomaly_score'] == 0]
elif status_filter == "Warning (Score 1-2)": filtered = filtered[filtered['anomaly_score'].isin([1, 2])]
elif status_filter == "Critical (Score 3)": filtered = filtered[filtered['anomaly_score'] == 3]

sat_options = filtered['NORAD_CAT_ID'].astype(str) + " - " + filtered['OBJECT_NAME']
if len(sat_options) > 0:
    selected_label = st.selectbox("Select Target Spacecraft:", sat_options)
    selected_norad = int(selected_label.split(" - ")[0])
    sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]
    
    score = sat['anomaly_score']
    if score == 0: sev_class, sev_label, sev_color = "severity-low", "NOMINAL", "#22c55e"
    elif score in [1, 2]: sev_class, sev_label, sev_color = "severity-moderate" if score==1 else "severity-high", f"WARNING L{score}", "#f97316"
    else: sev_class, sev_label, sev_color = "severity-critical", "CRITICAL", "#ef4444"
    
    # --- Spacecraft Card ---
    st.markdown(f"""
    <div class="anomaly-card {sev_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span class="satellite-name">{sat['OBJECT_NAME']}</span>
                <span class="meta-tag">🆔 ID: {sat['NORAD_CAT_ID']}</span>
                <span class="meta-tag">🌐 Regime: Group {sat.get('cluster_id', 'N/A')}</span>
                <span class="meta-tag">⏱️ Epoch: {str(sat.get('EPOCH', 'N/A'))[:10]}</span>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba({int(sev_color[1:3],16)},{int(sev_color[3:5],16)},{int(sev_color[5:7],16)}, 0.15); color: {sev_color}; padding: 6px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; border: 1px solid {sev_color};">
                    {sev_label}
                </span>
            </div>
        </div>
        
        <div style="margin-top: 24px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
            <div class="metric-box"><div class="metric-box-title">Altitude</div><div class="metric-box-val">{sat.get('orbit_height', 0):.1f} km</div></div>
            <div class="metric-box"><div class="metric-box-title">Inclination</div><div class="metric-box-val">{sat.get('INCLINATION', 0):.2f}°</div></div>
            <div class="metric-box"><div class="metric-box-title">Eccentricity</div><div class="metric-box-val">{sat.get('ECCENTRICITY', 0):.4f}</div></div>
            <div class="metric-box"><div class="metric-box-title">Semi-Major Axis</div><div class="metric-box-val">{sat.get('semi_major_axis', 0):.1f} km</div></div>
        </div>
        
        <div class="anomaly-reason">
    """, unsafe_allow_html=True)
    
    if score == 0:
        st.success("Target is operating within nominal orbital parameters. No anomalous behaviour detected across statistical, structural, or temporal models.")
    else:
        reasons = []
        if sat['ml_flag']: reasons.append("statistical deviation from its nominal orbital regime")
        if sat['dm_flag']: reasons.append("severe topological isolation from its structural neighborhood")
        if sat['temporal_flag']: reasons.append("an anomalous recent orbital maneuver or shift")
        
        reason_text = "The system flagged this spacecraft due to "
        if len(reasons) == 1: reason_text += reasons[0] + "."
        elif len(reasons) == 2: reason_text += reasons[0] + " and " + reasons[1] + "."
        else: reason_text += reasons[0] + ", " + reasons[1] + ", and " + reasons[2] + "."
            
        st.warning(f"**Diagnostic Report:** {reason_text}")
        
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # --- Backend Technical Details Dropdown ---
    with st.expander("View Subsystem Telemetry (Technical)"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Statistical Subsystem (ML)", "Flagged" if sat['ml_flag'] else "Nominal", f"Score: {sat['ml_anomaly_score']:.3f}" if 'ml_anomaly_score' in sat else "")
        c2.metric("Topology Subsystem (DM)", "Flagged" if sat['dm_flag'] else "Nominal", f"In-Degree: {sat['incoming_neighbor_count']}" if 'incoming_neighbor_count' in sat else "")
        c3.metric("Behavioral Subsystem (Temp)", "Flagged" if sat['temporal_flag'] else "Nominal", f"Δa: {sat['latest_delta_a']:.4f} km" if pd.notnull(sat['latest_delta_a']) else "")
        
else:
    st.info("No spacecraft found matching the criteria.")
