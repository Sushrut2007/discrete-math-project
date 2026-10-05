import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="DM Graph Analysis", layout="wide")

df = load_full_data()

st.title("Discrete Mathematics — Orbital Similarity Graph")
st.markdown("> Each satellite is a node. A satellite is connected to its 5 nearest satellites in the standardized orbital feature space.")
st.info("**This is orbital similarity, NOT physical distance between satellites.**")

st.markdown("### DM Rule")
st.markdown("> A satellite receives a DM flag when:")
st.code("incoming_neighbor_count == 0")
st.markdown("> **and**")
st.code("mean_neighbor_distance > global_mean_distance")

st.markdown("> Zero incoming neighbours alone can happen for satellites sitting at the edge of a dense group. Requiring large neighbour distance also makes sure the satellite is far from its nearest graph neighbours.")

st.markdown("---")
st.markdown("### Selected Satellite")
sat_options = df['OBJECT_NAME'] + " (" + df['NORAD_CAT_ID'].astype(str) + ")"
selected = st.selectbox("Select satellite:", sat_options)
norad = int(selected.split("(")[-1].replace(")", ""))
sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("In-Degree", sat['incoming_neighbor_count'])
c2.metric("Mean Neighbor Dist", f"{sat['mean_neighbor_distance']:.4f}")
c3.metric("Global Mean Dist", f"{sat['global_mean_dist']:.4f}")
c4.metric("DM Flagged", "Flagged" if sat['dm_flag'] else "Not flagged")

if sat['dm_flag']:
    st.error("This satellite is structurally isolated in the orbital-similarity graph.")
else:
    st.success("This satellite is connected within the orbital-similarity graph.")
