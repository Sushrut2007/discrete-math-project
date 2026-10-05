import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="Satellite Explorer", layout="wide")
df = load_full_data()

st.title("Spacecraft Tracking & Diagnostics")

st.sidebar.markdown("### Catalog Search")
search_q = st.sidebar.text_input("Object Name or ID", placeholder="e.g. 25544 or ISS")
status_filter = st.sidebar.selectbox("System Status", ["All", "Nominal", "Warning", "Critical"])

filtered = df.copy()
if search_q:
    q = search_q.lower()
    filtered = filtered[
        filtered['OBJECT_NAME'].str.lower().str.contains(q, na=False) |
        filtered['NORAD_CAT_ID'].astype(str).str.contains(q, na=False)
    ]
if status_filter == "Nominal":
    filtered = filtered[filtered['anomaly_score'] == 0]
elif status_filter == "Warning":
    filtered = filtered[filtered['anomaly_score'].isin([1, 2])]
elif status_filter == "Critical":
    filtered = filtered[filtered['anomaly_score'] == 3]

sat_options = filtered['NORAD_CAT_ID'].astype(str) + " - " + filtered['OBJECT_NAME']
if len(sat_options) > 0:
    selected_label = st.selectbox("Select Spacecraft:", sat_options)
    selected_norad = int(selected_label.split(" - ")[0])
    sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]
    
    st.markdown("---")
    
    # Status Header
    score = sat['anomaly_score']
    if score == 0:
        status_text, color = "NOMINAL", "#4CAF50"
    elif score in [1, 2]:
        status_text, color = "WARNING", "#FFC107"
    else:
        status_text, color = "CRITICAL", "#F44336"
        
    st.markdown(f"""
    <div style='background-color: #1E2127; padding: 20px; border-radius: 10px; border: 1px solid {color};'>
        <h2 style='margin-bottom: 0px;'>{sat['OBJECT_NAME']}</h2>
        <p style='color: #8B949E; margin-top: 5px; font-size: 16px;'>Catalog ID: {sat['NORAD_CAT_ID']} | Observation Epoch: {str(sat['EPOCH'])[:10] if 'EPOCH' in sat else 'N/A'}</p>
        <h3 style='color: {color}; margin-top: 10px;'>SYSTEM STATUS: {status_text}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Physical Telemetry
    st.markdown("### Current Orbital Telemetry")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orbit Altitude", f"{sat['orbit_height']:.2f} km" if 'orbit_height' in sat else "N/A")
    c2.metric("Inclination", f"{sat['INCLINATION']:.2f}°" if 'INCLINATION' in sat else "N/A")
    c3.metric("Eccentricity", f"{sat['ECCENTRICITY']:.5f}" if 'ECCENTRICITY' in sat else "N/A")
    c4.metric("Semi-Major Axis", f"{sat['semi_major_axis']:.2f} km" if 'semi_major_axis' in sat else "N/A")
    
    # Anomaly Diagnostics (Simplified for the operator)
    st.markdown("### Anomaly Diagnostics")
    
    if score == 0:
        st.success("No anomalous behaviour detected in current state, neighborhood topology, or recent maneuvers.")
    else:
        reasons = []
        if sat['ml_flag']: reasons.append("an unusual statistical orbital state")
        if sat['dm_flag']: reasons.append("severe structural isolation from its orbital neighborhood")
        if sat['temporal_flag']: reasons.append("an anomalous recent orbital maneuver or shift")
        
        reason_text = "The system flagged this spacecraft due to "
        if len(reasons) == 1:
            reason_text += reasons[0] + "."
        elif len(reasons) == 2:
            reason_text += reasons[0] + " and " + reasons[1] + "."
        else:
            reason_text += reasons[0] + ", " + reasons[1] + ", and " + reasons[2] + "."
            
        st.warning(reason_text)
        
    # Expandable technical breakdown
    with st.expander("View Backend Algorithm Outputs"):
        st.markdown("This section details the specific triggers from the three independent analysis models.")
        col1, col2, col3 = st.columns(3)
        col1.metric("Statistical Model (ML)", "Flagged" if sat['ml_flag'] else "Nominal", 
                    f"Score: {sat['ml_anomaly_score']:.2f}" if 'ml_anomaly_score' in sat else "")
        col2.metric("Topology Model (DM)", "Flagged" if sat['dm_flag'] else "Nominal", 
                    f"In-Degree: {sat['incoming_neighbor_count']}" if 'incoming_neighbor_count' in sat else "")
        col3.metric("Behavioral Model (Temporal)", "Flagged" if sat['temporal_flag'] else "Nominal", 
                    f"Δa: {sat['latest_delta_a']:.4f}" if pd.notnull(sat['latest_delta_a']) else "")
        
else:
    st.info("No spacecraft found matching the criteria.")
