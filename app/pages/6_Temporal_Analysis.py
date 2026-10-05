import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="Temporal Analysis", layout="wide")

df = load_full_data()

st.title("Temporal Analysis — Recent Orbital Change")
st.markdown("> The temporal part looks at how the satellite's orbital parameters changed across the recent observation history.")

st.markdown("---")
st.markdown("### Selected Satellite")
sat_options = df['OBJECT_NAME'] + " (" + df['NORAD_CAT_ID'].astype(str) + ")"
selected = st.selectbox("Select satellite:", sat_options)
norad = int(selected.split("(")[-1].replace(")", ""))
sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("Change in Semi-Major Axis (Δa)", f"{sat['latest_delta_a']:.4f} km" if pd.notnull(sat['latest_delta_a']) else "N/A")
c2.metric("Change in Eccentricity (Δe)", f"{sat['latest_delta_e']:.6f}" if pd.notnull(sat['latest_delta_e']) else "N/A")
c3.metric("Change in Inclination (Δi)", f"{sat['latest_delta_i']:.4f}°" if pd.notnull(sat['latest_delta_i']) else "N/A")

st.markdown(f"**Temporal Flag:** {'Flagged' if sat['temporal_flag'] else 'Not flagged'}")

st.markdown("> A temporal flag means the recent orbital change is unusual according to the method. It does not prove that a thruster maneuver occurred.")
