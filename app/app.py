import sys
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# Ensure project root is available in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import PROCESSED_DIR
from src.ml.ml_pipeline import run_ml_pipeline
from src.ml.ml_config import LABEL_ANOMALOUS, LABEL_NORMAL, LABEL_NOT_EVALUATED

st.set_page_config(
    page_title="Satellite Orbital Anomaly Explorer",
    page_icon="🛰️",
    layout="wide"
)


@st.cache_data
def load_data():
    """
    Loads latest processed ML anomalies dataset, or runs the pipeline once if absent.
    """
    processed_path = Path(PROCESSED_DIR) / "latest_ml_anomalies.csv"
    if processed_path.exists():
        df = pd.read_csv(processed_path)
    else:
        df, _ = run_ml_pipeline()
    return df


def get_status_label(label):
    if label == LABEL_ANOMALOUS:
        return "Unusual (Outlier)"
    elif label == LABEL_NORMAL:
        return "Normal"
    else:
        return "Not Evaluated (Small Cluster)"


# Load current pipeline data
df = load_data()

# Add display status column
df["display_status"] = df["anomaly_label"].apply(get_status_label)

# App Header
st.title("🛰️ Satellite Orbital State & ML Anomaly Explorer")
st.caption(
    "Visual exploration of the current-state orbital pipeline: "
    "**CelesTrak Snapshots → Derived Features → K-Means Groups → Cluster-Specific Isolation Forest**"
)

# Top metric summary cards
total_sats = len(df)
n_anomalous = (df["anomaly_label"] == LABEL_ANOMALOUS).sum()
n_normal = (df["anomaly_label"] == LABEL_NORMAL).sum()
n_unevaluated = (df["anomaly_label"] == LABEL_NOT_EVALUATED).sum()
n_clusters = df["cluster_id"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Satellites", f"{total_sats:,}")
col2.metric("Orbital Clusters", n_clusters)
col3.metric("Normal", f"{n_normal:,}")
col4.metric("Unusual (Flagged)", f"{n_anomalous:,}")
col5.metric("Not Evaluated", n_unevaluated)

st.divider()

# Sidebar filters
st.sidebar.header("🔍 Filters & Search")

# Search by Name or NORAD Cat ID
search_query = st.sidebar.text_input("Search Name or NORAD ID", placeholder="e.g. ISS, STARLINK, 25544")

# Cluster filter
cluster_options = ["All"] + sorted([int(c) for c in df["cluster_id"].unique()])
selected_cluster = st.sidebar.selectbox("Filter by Cluster", cluster_options)

# Anomaly status filter
status_options = ["All", "Unusual (Outlier)", "Normal", "Not Evaluated (Small Cluster)"]
selected_status = st.sidebar.selectbox("Filter by Anomaly Status", status_options)

# Apply filters
filtered_df = df.copy()

if search_query:
    q = search_query.strip().lower()
    filtered_df = filtered_df[
        filtered_df["OBJECT_NAME"].str.lower().str.contains(q, na=False) |
        filtered_df["NORAD_CAT_ID"].astype(str).str.contains(q, na=False)
    ]

if selected_cluster != "All":
    filtered_df = filtered_df[filtered_df["cluster_id"] == selected_cluster]

if selected_status != "All":
    filtered_df = filtered_df[filtered_df["display_status"] == selected_status]

st.sidebar.write(f"Showing **{len(filtered_df):,}** of **{len(df):,}** satellites")

# Main content: Tabs for Visualizations vs Data Table vs Single Satellite Inspection
tab1, tab2, tab3 = st.tabs(["📊 Population & Cluster Visualizations", "📋 Satellite Dataset Table", "🔎 Satellite Inspector"])

with tab1:
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Orbital Cluster Distribution")
        cluster_counts = df.groupby(["cluster_id", "display_status"]).size().reset_index(name="count")
        fig_cluster = px.bar(
            cluster_counts,
            x="cluster_id",
            y="count",
            color="display_status",
            title="Satellites per Orbital Cluster by Status",
            labels={"cluster_id": "Cluster ID", "count": "Satellite Count", "display_status": "Status"},
            color_discrete_map={
                "Normal": "#1f77b4",
                "Unusual (Outlier)": "#d62728",
                "Not Evaluated (Small Cluster)": "#7f7f7f"
            }
        )
        fig_cluster.update_layout(bargap=0.2)
        st.plotly_chart(fig_cluster, use_container_width=True)

    with col_chart2:
        st.subheader("Altitude vs Inclination Distribution")
        sample_size = min(4000, len(filtered_df))
        sampled_df = filtered_df.sample(sample_size, random_state=42) if len(filtered_df) > sample_size else filtered_df

        fig_scatter = px.scatter(
            sampled_df,
            x="INCLINATION",
            y="orbit_height",
            color="display_status",
            symbol="cluster_id",
            title=f"Orbital Regime (Showing {len(sampled_df):,} sample points)",
            labels={"INCLINATION": "Inclination (deg)", "orbit_height": "Average Altitude (km)"},
            hover_data=["OBJECT_NAME", "NORAD_CAT_ID", "cluster_id", "anomaly_score"],
            color_discrete_map={
                "Normal": "#1f77b4",
                "Unusual (Outlier)": "#d62728",
                "Not Evaluated (Small Cluster)": "#7f7f7f"
            },
            opacity=0.7
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("Standardized Orbital Feature Space (Semi-Major Axis vs Eccentricity)")
    fig_features = px.scatter(
        sampled_df,
        x="std_semi_major_axis",
        y="std_eccentricity",
        color="display_status",
        hover_data=["OBJECT_NAME", "NORAD_CAT_ID", "cluster_id", "INCLINATION", "orbit_height"],
        labels={
            "std_semi_major_axis": "Std Semi-Major Axis (z-score)",
            "std_eccentricity": "Std Eccentricity (z-score)"
        },
        color_discrete_map={
            "Normal": "#1f77b4",
            "Unusual (Outlier)": "#d62728",
            "Not Evaluated (Small Cluster)": "#7f7f7f"
        },
        opacity=0.75
    )
    st.plotly_chart(fig_features, use_container_width=True)

with tab2:
    st.subheader("Satellite Records")
    display_cols = [
        "NORAD_CAT_ID",
        "OBJECT_NAME",
        "cluster_id",
        "display_status",
        "anomaly_score",
        "orbit_height",
        "perigee",
        "apogee",
        "INCLINATION",
        "ECCENTRICITY",
        "orbital_speed",
        "EPOCH"
    ]
    st.dataframe(
        filtered_df[display_cols].sort_values(by="anomaly_score", ascending=True),
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.subheader("Investigate Individual Satellite")
    sat_options = filtered_df["OBJECT_NAME"] + " (" + filtered_df["NORAD_CAT_ID"].astype(str) + ")"
    
    if len(sat_options) > 0:
        selected_sat_label = st.selectbox("Choose a satellite to inspect:", sat_options)
        selected_norad = int(selected_sat_label.split("(")[-1].replace(")", ""))
        sat_row = df[df["NORAD_CAT_ID"] == selected_norad].iloc[0]

        card_col1, card_col2, card_col3 = st.columns(3)
        with card_col1:
            st.markdown(f"### **{sat_row['OBJECT_NAME']}**")
            st.write(f"**NORAD ID:** {sat_row['NORAD_CAT_ID']}")
            st.write(f"**Epoch:** `{sat_row['EPOCH']}`")
            st.write(f"**Assigned Cluster:** `Cluster {sat_row['cluster_id']}`")
            status_text = sat_row['display_status']
            if sat_row['anomaly_label'] == LABEL_ANOMALOUS:
                st.error(f"Status: **{status_text}**")
            elif sat_row['anomaly_label'] == LABEL_NORMAL:
                st.success(f"Status: **{status_text}**")
            else:
                st.info(f"Status: **{status_text}**")

        with card_col2:
            st.markdown("### **Physical Orbital Characteristics**")
            st.write(f"**Mean Altitude:** {sat_row['orbit_height']:.2f} km")
            st.write(f"**Perigee:** {sat_row['perigee']:.2f} km")
            st.write(f"**Apogee:** {sat_row['apogee']:.2f} km")
            st.write(f"**Semi-Major Axis:** {sat_row['semi_major_axis']:.2f} km")
            st.write(f"**Orbital Speed:** {sat_row['orbital_speed']:.2f} km/s")

        with card_col3:
            st.markdown("### **ML Anomaly Evidence**")
            st.write(f"**Anomaly Score:** `{sat_row['anomaly_score']:.4f}`" if not np.isnan(sat_row['anomaly_score']) else "**Anomaly Score:** `N/A (Unevaluated)`")
            st.caption("Negative scores indicate observations that are easier to isolate within this orbital cluster.")
            st.write(f"**Std Semi-Major Axis (z):** {sat_row['std_semi_major_axis']:.3f}")
            st.write(f"**Std Eccentricity (z):** {sat_row['std_eccentricity']:.3f}")
            st.write(f"**Std Inclination (z):** {sat_row['std_inclination']:.3f}")
    else:
        st.warning("No satellites match the current filter criteria.")
