import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="Satellite Explorer", layout="wide")

df = load_full_data()

st.title("Satellite Explorer")

st.sidebar.markdown("### Filters")
search_q = st.sidebar.text_input("Search Name or NORAD ID")
score_filter = st.sidebar.selectbox("Final Anomaly Score", ["All", 0, 1, 2, 3])
ml_filter = st.sidebar.selectbox("ML Flagged", ["All", "Yes", "No"])
dm_filter = st.sidebar.selectbox("DM Flagged", ["All", "Yes", "No"])
temp_filter = st.sidebar.selectbox("Temporal Flagged", ["All", "Yes", "No"])

filtered = df.copy()
if search_q:
    q = search_q.lower()
    filtered = filtered[
        filtered['OBJECT_NAME'].str.lower().str.contains(q, na=False) |
        filtered['NORAD_CAT_ID'].astype(str).str.contains(q, na=False)
    ]
if score_filter != "All":
    filtered = filtered[filtered['anomaly_score'] == score_filter]
if ml_filter != "All":
    filtered = filtered[filtered['ml_flag'] == (1 if ml_filter == "Yes" else 0)]
if dm_filter != "All":
    filtered = filtered[filtered['dm_flag'] == (1 if dm_filter == "Yes" else 0)]
if temp_filter != "All":
    filtered = filtered[filtered['temporal_flag'] == (1 if temp_filter == "Yes" else 0)]

st.markdown(f"**Showing {len(filtered):,} satellites**")

display_cols = ['OBJECT_NAME', 'NORAD_CAT_ID', 'anomaly_score', 'ml_flag', 'dm_flag', 'temporal_flag']
st.dataframe(filtered[display_cols].rename(columns={
    'OBJECT_NAME': 'Satellite Name', 'NORAD_CAT_ID': 'NORAD ID', 'anomaly_score': 'Final Score',
    'ml_flag': 'ML Status', 'dm_flag': 'DM Status', 'temporal_flag': 'Temporal Status'
}), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### Satellite Selection")

sat_options = filtered['OBJECT_NAME'] + " (" + filtered['NORAD_CAT_ID'].astype(str) + ")"
if len(sat_options) > 0:
    selected_label = st.selectbox("Select a satellite to view details:", sat_options)
    selected_norad = int(selected_label.split("(")[-1].replace(")", ""))
    sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]
    
    st.markdown(f"#### **{sat['OBJECT_NAME']}**")
    st.markdown(f"**NORAD ID:** {sat['NORAD_CAT_ID']}")
    st.markdown(f"**Final anomaly score: {sat['anomaly_score']} / 3**")
    
    def df_flag(v): return "Flagged" if v == 1 else "Not flagged"
    
    st.markdown(f"""
    | Check | Result |
    |---|---|
    | ML | {df_flag(sat['ml_flag'])} |
    | DM | {df_flag(sat['dm_flag'])} |
    | Temporal | {df_flag(sat['temporal_flag'])} |
    """)
    
    flagged_by = []
    if sat['ml_flag']: flagged_by.append("ML")
    if sat['dm_flag']: flagged_by.append("DM graph")
    if sat['temporal_flag']: flagged_by.append("Temporal")
    
    not_flagged = [m for m in ["ML", "DM graph", "Temporal"] if m not in flagged_by]
    
    if sat['anomaly_score'] == 0:
        explanation = "This satellite received a score of 0 because no method flagged it."
    elif sat['anomaly_score'] == 3:
        explanation = "This satellite received a score of 3 because all three methods flagged it."
    else:
        flagged_str = " and ".join(flagged_by)
        if len(not_flagged) == 1:
            explanation = f"This satellite received a score of {sat['anomaly_score']} because {flagged_str} flagged it, while the {not_flagged[0]} did not."
        else:
            not_flagged_str = " and ".join(not_flagged)
            explanation = f"This satellite received a score of {sat['anomaly_score']} because {flagged_str} flagged it, while {not_flagged_str} did not."
            
    st.markdown(f"> {explanation}")
