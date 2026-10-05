import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="Temporal Analysis", layout="wide")
df = load_full_data()

st.title("Temporal Analysis")
st.markdown("### Recent Orbital Change Evaluation")
st.markdown("The temporal part looks at how the satellite's orbital parameters changed across the recent observation history.")

st.markdown("---")
st.markdown("### Object Inspection")
sat_options = df['NORAD_CAT_ID'].astype(str) + " - " + df['OBJECT_NAME'] 
selected = st.selectbox("Select Target:", sat_options, key="temp_sel")
norad = int(selected.split(" - ")[0])
sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    c1.metric("Δ Semi-Major Axis (a)", f"{sat['latest_delta_a']:.4f} km" if pd.notnull(sat['latest_delta_a']) else "N/A")
    c2.metric("Δ Eccentricity (e)", f"{sat['latest_delta_e']:.6f}" if pd.notnull(sat['latest_delta_e']) else "N/A")
    c3.metric("Δ Inclination (i)", f"{sat['latest_delta_i']:.4f}°" if pd.notnull(sat['latest_delta_i']) else "N/A")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if sat['temporal_flag']:
        st.error("**Status: Flagged**")
    else:
        st.success("**Status: Nominal**")
        
    st.caption("A temporal flag means the recent orbital change is unusual according to the method. It does not prove that a thruster maneuver occurred.")
