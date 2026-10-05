import streamlit as st
import pandas as pd
from data_loader import load_full_data

st.set_page_config(page_title="Satellite Explorer", layout="wide")
df = load_full_data()

st.title("Satellite Explorer")
st.markdown("Search and filter the catalog to inspect specific anomaly assessments.")

st.sidebar.markdown("### Catalog Filters")
search_q = st.sidebar.text_input("Catalog ID / Object Name", placeholder="e.g. 25544 or STARLINK")
score_filter = st.sidebar.selectbox("Integrated Score", ["All", 0, 1, 2, 3])
ml_filter = st.sidebar.selectbox("ML Flag", ["All", "Flagged", "Nominal"])
dm_filter = st.sidebar.selectbox("DM Flag", ["All", "Flagged", "Nominal"])
temp_filter = st.sidebar.selectbox("Temporal Flag", ["All", "Flagged", "Nominal"])

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
    filtered = filtered[filtered['ml_flag'] == (1 if ml_filter == "Flagged" else 0)]
if dm_filter != "All":
    filtered = filtered[filtered['dm_flag'] == (1 if dm_filter == "Flagged" else 0)]
if temp_filter != "All":
    filtered = filtered[filtered['temporal_flag'] == (1 if temp_filter == "Flagged" else 0)]

st.caption(f"Displaying **{len(filtered):,}** matching records")

display_cols = ['NORAD_CAT_ID', 'OBJECT_NAME', 'anomaly_score', 'ml_flag', 'dm_flag', 'temporal_flag']
display_df = filtered[display_cols].copy()
display_df['ml_flag'] = display_df['ml_flag'].map({1: '⚠️', 0: '✓'})
display_df['dm_flag'] = display_df['dm_flag'].map({1: '⚠️', 0: '✓'})
display_df['temporal_flag'] = display_df['temporal_flag'].map({1: '⚠️', 0: '✓'})

st.dataframe(display_df.rename(columns={
    'OBJECT_NAME': 'Object Name', 'NORAD_CAT_ID': 'Catalog ID', 'anomaly_score': 'Final Score',
    'ml_flag': 'ML', 'dm_flag': 'DM', 'temporal_flag': 'Temporal'
}), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### Detailed Object Inspection")

sat_options = filtered['NORAD_CAT_ID'].astype(str) + " - " + filtered['OBJECT_NAME']
if len(sat_options) > 0:
    selected_label = st.selectbox("Select Target", sat_options)
    selected_norad = int(selected_label.split(" - ")[0])
    sat = df[df['NORAD_CAT_ID'] == selected_norad].iloc[0]
    
    with st.container(border=True):
        col_hdr, col_score = st.columns([3, 1])
        with col_hdr:
            st.markdown(f"## {sat['OBJECT_NAME']}")
            st.markdown(f"**Catalog ID:** {sat['NORAD_CAT_ID']} &nbsp;|&nbsp; **Epoch:** {str(sat['EPOCH'])[:10] if 'EPOCH' in sat else 'N/A'}")
        with col_score:
            score_color = "#4CAF50" if sat['anomaly_score'] == 0 else ("#FFC107" if sat['anomaly_score'] in [1, 2] else "#F44336")
            st.markdown(f"<h1 style='text-align: right; color: {score_color};'>Score: {sat['anomaly_score']}/3</h1>", unsafe_allow_html=True)
        
        st.markdown("#### Evidence Matrix")
        
        def render_status(flag, name):
            color = "#F44336" if flag else "#4CAF50"
            icon = "⚠️ Flagged" if flag else "✓ Nominal"
            return f"<div style='background-color: #1E2127; padding: 10px; border-radius: 5px; border-left: 4px solid {color};'><b>{name}</b><br><span style='color: {color};'>{icon}</span></div>"

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(render_status(sat['ml_flag'], "Machine Learning"), unsafe_allow_html=True)
        with c2: st.markdown(render_status(sat['dm_flag'], "DM Graph"), unsafe_allow_html=True)
        with c3: st.markdown(render_status(sat['temporal_flag'], "Temporal Analysis"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Build explanation text
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
                
        st.info(explanation)
else:
    st.warning("No satellites match the current filter criteria.")
