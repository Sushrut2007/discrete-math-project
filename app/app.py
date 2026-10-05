import sys
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Configuration
st.set_page_config(page_title="Satellite Anomaly Detection", layout="wide")

# Paths
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
proc_dir = project_root / "data" / "processed"

# --- Data Loading ---
@st.cache_data
def load_full_data():
    int_path = proc_dir / "latest_integrated_results.csv"
    ml_path = proc_dir / "latest_ml_anomalies.csv"
    dm_path = proc_dir / "latest_graph_features.csv"
    temp_path = proc_dir / "latest_temporal_features.csv"
    
    if not all(p.exists() for p in [int_path, ml_path, dm_path]):
        return pd.DataFrame()
        
    df_int = pd.read_csv(int_path)
    
    # Select columns to avoid duplication
    cols_ml = ['NORAD_CAT_ID', 'cluster_id', 'anomaly_score', 'orbit_height', 'INCLINATION', 'ECCENTRICITY', 'semi_major_axis', 'EPOCH']
    df_ml = pd.read_csv(ml_path)
    cols_ml = [c for c in cols_ml if c in df_ml.columns]
    df_ml = df_ml[cols_ml]
    
    df_dm = pd.read_csv(dm_path)[['NORAD_CAT_ID', 'incoming_neighbor_count', 'mean_neighbor_distance', 'k_nearest_distance']]
    
    # Rename ML's anomaly_score to avoid clash with integrated anomaly_score
    df_ml = df_ml.rename(columns={'anomaly_score': 'ml_anomaly_score'})
    
    df = pd.merge(df_int, df_ml, on='NORAD_CAT_ID', how='inner')
    df = pd.merge(df, df_dm, on='NORAD_CAT_ID', how='inner', suffixes=('', '_drop'))
    
    # Drop duplicated columns from merge if any
    df = df.loc[:, ~df.columns.str.endswith('_drop')]
    
    if temp_path.exists():
        df_temp = pd.read_csv(temp_path)[['NORAD_CAT_ID', 'latest_delta_a', 'latest_delta_e', 'latest_delta_i', 'history_transitions_count']]
        df = pd.merge(df, df_temp, on='NORAD_CAT_ID', how='left')
    else:
        df['latest_delta_a'] = np.nan
        df['latest_delta_e'] = np.nan
        df['latest_delta_i'] = np.nan
        df['history_transitions_count'] = 0
        
    df['global_mean_dist'] = df['mean_neighbor_distance'].mean()
    
    # Ensure correct types
    df['anomaly_score'] = df['anomaly_score'].fillna(0).astype(int)
    
    return df

df = load_full_data()

if df.empty:
    st.error("Processed data files are missing. Please run the integration pipeline first.")
    st.stop()

# --- Shared UI Components ---
def display_flag(flag_val):
    return "Flagged" if flag_val == 1 else "Not flagged"

def flag_color(flag_val):
    return "red" if flag_val == 1 else "green"

# --- Pages ---

def page_overview():
    st.title("ML and Discrete Mathematics Based Satellite Anomaly Detection")
    st.markdown("> Analyze satellite orbital data using machine learning, a similarity graph, and recent orbital changes.")
    st.markdown("---")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    counts = df['anomaly_score'].value_counts()
    
    col1.metric("Total Satellites", f"{len(df):,}")
    col2.metric("Latest Observation", str(df['EPOCH'].iloc[0])[:10] if 'EPOCH' in df.columns else "N/A")
    col3.metric("Score 0", f"{counts.get(0, 0):,}")
    col4.metric("Score 1", f"{counts.get(1, 0):,}")
    col5.metric("Score 2", f"{counts.get(2, 0):,}")
    col6.metric("Score 3", f"{counts.get(3, 0):,}")
    
    st.markdown("### Anomaly Score Distribution")
    
    score_df = pd.DataFrame({'Score': [0, 1, 2, 3], 'Count': [counts.get(i, 0) for i in range(4)]})
    fig = px.bar(score_df, x='Score', y='Count', title="Distribution of Final Scores",
                 color='Score', color_continuous_scale=['#4CAF50', '#FFC107', '#FF9800', '#F44336'])
    fig.update_layout(xaxis=dict(tickmode='linear', dtick=1), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    - **0:** No detector flagged the satellite
    - **1:** One detector flagged it
    - **2:** Two detectors flagged it
    - **3:** All three detectors flagged it
    
    > Score 3 means that all three methods found unusual behaviour or structure. These satellites should receive the highest attention for further investigation.
    """)
    
    st.markdown("---")
    st.markdown("### Three-Method Overview")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**ML**")
        st.markdown("> Checks whether the current orbital state is unusual compared with other satellites.")
    with c2:
        st.markdown("**DM Graph**")
        st.markdown("> Checks whether the satellite is strongly isolated in the orbital-similarity graph.")
    with c3:
        st.markdown("**Temporal**")
        st.markdown("> Checks whether the satellite's recent orbital change is unusual compared with its own recent history.")

def page_explorer():
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
        
        st.markdown(f"""
        | Check | Result |
        |---|---|
        | ML | {display_flag(sat['ml_flag'])} |
        | DM | {display_flag(sat['dm_flag'])} |
        | Temporal | {display_flag(sat['temporal_flag'])} |
        """)
        
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
                
        st.markdown(f"> {explanation}")
        
def page_anomaly_analysis():
    st.title("Anomaly Analysis")
    st.markdown("### Integrated Anomaly Result")
    st.markdown("> The final score is the number of methods that detected unusual behaviour or structure.")
    
    counts = df['anomaly_score'].value_counts()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### Score 0")
        st.markdown("No method flagged the satellite.")
        st.markdown(f"**{counts.get(0, 0):,}** satellites")
    with col2:
        st.markdown("#### Score 1")
        st.markdown("One method flagged the satellite.")
        st.markdown(f"**{counts.get(1, 0):,}** satellites")
    with col3:
        st.markdown("#### Score 2")
        st.markdown("Two methods flagged the satellite.")
        st.markdown(f"**{counts.get(2, 0):,}** satellites")
    with col4:
        st.markdown("#### Score 3")
        st.markdown("All three methods flagged the satellite.")
        st.markdown(f"**{counts.get(3, 0):,}** satellites")
        
    st.markdown("---")
    st.markdown("### Score Combination Analysis")
    
    # Filter for score > 0
    anomalous = df[df['anomaly_score'] > 0].copy()
    
    # Create combination labels
    def get_combo(row):
        parts = []
        if row['ml_flag']: parts.append("ML")
        if row['dm_flag']: parts.append("DM")
        if row['temporal_flag']: parts.append("Temporal")
        return " + ".join(parts)
        
    anomalous['Combination'] = anomalous.apply(get_combo, axis=1)
    combo_counts = anomalous['Combination'].value_counts().reset_index()
    combo_counts.columns = ['Combination', 'Count']
    
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(combo_counts, use_container_width=True, hide_index=True)
    with c2:
        fig = px.bar(combo_counts, x='Count', y='Combination', orientation='h', title="Methods Flagging Satellites")
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
def page_ml():
    st.title("Machine Learning — Current Orbital State")
    st.markdown("> The ML part looks at the current orbital features and identifies satellites that are unusual compared with satellites in similar groups.")
    
    n_flagged = df['ml_flag'].sum()
    n_clusters = df['cluster_id'].nunique()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Orbital Groups (K-Means)", n_clusters)
    c2.metric("ML-Flagged Satellites", f"{n_flagged:,}")
    c3.metric("Normal Satellites", f"{len(df) - n_flagged:,}")
    
    st.markdown("### ML Anomaly Score Distribution")
    fig = px.histogram(df, x='ml_anomaly_score', nbins=50, title="Distribution of Isolation Forest Scores")
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("How it works"):
        st.markdown("""
        1. Satellites are grouped into orbital families using K-Means clustering.
        2. An Isolation Forest algorithm evaluates satellites within their specific cluster.
        3. Satellites that are statistically easy to isolate receive a negative anomaly score and are flagged.
        """)
        
    st.markdown("---")
    st.markdown("### Selected Satellite")
    sat_options = df['OBJECT_NAME'] + " (" + df['NORAD_CAT_ID'].astype(str) + ")"
    selected = st.selectbox("Select satellite:", sat_options, key="ml_sel")
    norad = int(selected.split("(")[-1].replace(")", ""))
    sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]
    
    st.markdown(f"**Cluster ID:** {sat['cluster_id']}")
    st.markdown(f"**Anomaly Label:** {'-1 (Unusual)' if sat['ml_flag'] else '1 (Normal)'}")
    st.markdown(f"**Anomaly Score:** {sat['ml_anomaly_score']:.4f}")
    
    if sat['ml_flag']:
        st.markdown("**Flagged**")
        st.markdown("> The ML model considers the satellite unusual compared with the other satellites it was evaluated against.")
    else:
        st.markdown("**Not flagged**")
        st.markdown("> The ML model did not find it unusual.")

def page_dm():
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
    selected = st.selectbox("Select satellite:", sat_options, key="dm_sel")
    norad = int(selected.split("(")[-1].replace(")", ""))
    sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("In-Degree", sat['incoming_neighbor_count'])
    c2.metric("Mean Neighbor Dist", f"{sat['mean_neighbor_distance']:.4f}")
    c3.metric("Global Mean Dist", f"{sat['global_mean_dist']:.4f}")
    c4.metric("DM Flagged", display_flag(sat['dm_flag']))
    
    if sat['dm_flag']:
        st.error("This satellite is structurally isolated in the orbital-similarity graph.")
    else:
        st.success("This satellite is connected within the orbital-similarity graph.")

def page_temporal():
    st.title("Temporal Analysis — Recent Orbital Change")
    st.markdown("> The temporal part looks at how the satellite's orbital parameters changed across the recent observation history.")
    
    st.markdown("---")
    st.markdown("### Selected Satellite")
    sat_options = df['OBJECT_NAME'] + " (" + df['NORAD_CAT_ID'].astype(str) + ")"
    selected = st.selectbox("Select satellite:", sat_options, key="temp_sel")
    norad = int(selected.split("(")[-1].replace(")", ""))
    sat = df[df['NORAD_CAT_ID'] == norad].iloc[0]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Change in Semi-Major Axis (Δa)", f"{sat['latest_delta_a']:.4f} km" if pd.notnull(sat['latest_delta_a']) else "N/A")
    c2.metric("Change in Eccentricity (Δe)", f"{sat['latest_delta_e']:.6f}" if pd.notnull(sat['latest_delta_e']) else "N/A")
    c3.metric("Change in Inclination (Δi)", f"{sat['latest_delta_i']:.4f}°" if pd.notnull(sat['latest_delta_i']) else "N/A")
    
    st.markdown(f"**Temporal Flag:** {display_flag(sat['temporal_flag'])}")
    
    st.markdown("> A temporal flag means the recent orbital change is unusual according to the method. It does not prove that a thruster maneuver occurred.")

def page_about():
    st.title("About / Method")
    st.markdown("### System Pipeline")
    st.code("""
CelesTrak satellite data
         ↓
Orbital features
         ↓
┌──────────────┬──────────────┬──────────────┐
│      ML      │      DM      │   Temporal   │
│ Current      │ Similarity   │ Recent       │
│ orbital      │ graph        │ orbital      │
│ state        │              │ change       │
└──────────────┴──────────────┴──────────────┘
                   ↓
            0–3 final score
    """, language="text")
    
    st.markdown("""
    - **ML:** Evaluates the current orbital state against K-Means derived orbital families.
    - **DM:** Evaluates topological isolation using a directed 5-Nearest Neighbour similarity graph.
    - **Temporal:** Evaluates recent sequential orbital changes against the satellite's own historical transitions.
    
    The **final score** is a simple count of how many methods flagged the satellite (from 0 to 3).
    """)
    
    st.markdown("---")
    st.markdown("### Limitations")
    st.warning("""
    - An anomaly means unusualness, not necessarily danger.
    - The DM graph represents orbital similarity, not physical distance.
    - A temporal flag does not prove a maneuver occurred.
    - The system does not directly calculate collision probability.
    - The temporal analysis covers only the available recent observation window.
    - The final score is an evidence count from the three methods, not a probability that something is wrong.
    """)

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "Overview", 
    "Satellite Explorer", 
    "Anomaly Analysis", 
    "ML Analysis", 
    "DM Graph Analysis", 
    "Temporal Analysis", 
    "About / Method"
])

if page == "Overview":
    page_overview()
elif page == "Satellite Explorer":
    page_explorer()
elif page == "Anomaly Analysis":
    page_anomaly_analysis()
elif page == "ML Analysis":
    page_ml()
elif page == "DM Graph Analysis":
    page_dm()
elif page == "Temporal Analysis":
    page_temporal()
elif page == "About / Method":
    page_about()

