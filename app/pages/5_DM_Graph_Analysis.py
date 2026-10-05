import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="DM Graph Analysis", layout="wide")
df = load_full_data()

st.title("Discrete Mathematics Analysis")
st.markdown("### Orbital Similarity Graph")
st.markdown("Each satellite is a node. A satellite is connected to its 5 nearest satellites in the standardized orbital feature space.")
st.info("⚠️ **Note:** This represents orbital similarity, NOT physical distance between satellites.")

with st.container(border=True):
    st.markdown("#### DM Structural Rule")
    st.markdown("A satellite receives a DM flag when:")
    st.code("incoming_neighbor_count == 0  AND  mean_neighbor_distance > global_mean_distance", language="python")
    st.markdown("Zero incoming neighbours alone can happen for satellites sitting at the edge of a dense group. Requiring large neighbour distance also makes sure the satellite is far from its nearest graph neighbours.")

st.markdown("---")
st.markdown("### Object Inspection")
sat_options = df['NORAD_CAT_ID'].astype(str) + " - " + df['OBJECT_NAME'] 
selected = st.selectbox("Select Target:", sat_options, key="dm_sel")
norad = int(selected.split(" - ")[0])
sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("In-Degree", sat['incoming_neighbor_count'])
    c2.metric("Mean Neighbor Dist", f"{sat['mean_neighbor_distance']:.4f}")
    c3.metric("Global Mean Dist", f"{sat['global_mean_dist']:.4f}")
    
    if sat['dm_flag']:
        c4.error("Status: Flagged")
        st.error("This satellite is structurally isolated in the orbital-similarity graph.")
    else:
        c4.success("Status: Nominal")
        st.success("This satellite is well-connected within the orbital-similarity graph.")
