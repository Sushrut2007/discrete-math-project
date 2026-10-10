import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout
from diagnostics import get_operator_explanation

st.set_page_config(
    page_title="Priority Watch List",
    page_icon="⚖️",
    layout="wide"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Catalog data is not available.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Flagged Satellites List</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">List of active LEO satellites flagged by Machine Learning, Discrete Math, or both.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Counts
counts = df['anomaly_score'].value_counts()
n_total = len(df)
n_score0 = counts.get(0, 0)
n_score1 = counts.get(1, 0)
n_score2 = counts.get(2, 0)

ml_only = len(df[(df['ml_flag'] == 1) & (df['dm_flag'] == 0)])
dm_only = len(df[(df['ml_flag'] == 0) & (df['dm_flag'] == 1)])
dual_flag = len(df[(df['ml_flag'] == 1) & (df['dm_flag'] == 1)])

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Flagged", f"{n_score1 + n_score2:,}", "Score 1 or Score 2", "#f8fafc")
with k2:
    render_metric_card("ML Only Flagged", f"{ml_only:,}", "Score 1 · Cluster Outlier", "#fbbf24", "#f59e0b")
with k3:
    render_metric_card("Graph Only Flagged", f"{dm_only:,}", "Score 1 · Graph Isolated", "#38bdf8", "#0284c7")
with k4:
    render_metric_card("Both Flagged", f"{dual_flag:,}", "Score 2 · Top Priority", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Visualizing Watch List
col_c1, col_c2 = st.columns([1.2, 1])

with col_c1:
    st.markdown("#### Satellites by Flag Type")
    combo_data = pd.DataFrame({
        'Category': ['Score 1 (ML Only)', 'Score 1 (Graph Only)', 'Score 2 (Both ML & Graph)'],
        'Count': [ml_only, dm_only, dual_flag],
        'Color': ['#f59e0b', '#0284c7', '#ef4444']
    })
    
    fig_combo = px.bar(
        combo_data,
        x='Count',
        y='Category',
        orientation='h',
        text='Count',
        color='Category',
        color_discrete_map={
            'Score 1 (ML Only)': '#f59e0b',
            'Score 1 (Graph Only)': '#0284c7',
            'Score 2 (Both ML & Graph)': '#ef4444'
        }
    )
    fig_combo.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        marker_line_width=0,
        hovertemplate='<b>%{y}</b><br>Satellites: %{x:,}<extra></extra>'
    )
    layout_cb = get_plotly_layout(height=260)
    layout_cb['showlegend'] = False
    layout_cb['xaxis']['title'] = "Number of Satellites"
    layout_cb['yaxis']['title'] = ""
    fig_combo.update_layout(layout_cb)
    st.plotly_chart(fig_combo, use_container_width=True)

with col_c2:
    st.markdown("#### How to Read This List")
    st.markdown("""
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px; font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">
        <p style="margin-bottom: 8px;">
            <b>Score Breakdown:</b>
        </p>
        <p style="margin-bottom: 8px;">
            • <b>Score 2 ({0} satellites):</b> Both Machine Learning and Graph analysis flagged this satellite. These have the most unusual orbits in the catalog.
        </p>
        <p style="margin-bottom: 8px;">
            • <b>Score 1 ({1} satellites):</b> One method flagged it. These satellites usually have uncommon tilts or sit near the edge of a cluster.
        </p>
        <p style="margin-bottom: 0px; font-size: 0.75rem; color: #94a3b8;">
            You can search any of these satellites in the <b>Satellite Explorer</b> page to inspect their detailed parameters.
        </p>
    </div>
    """.format(dual_flag, n_score1), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Master Table of Score 2 Spacecraft
st.markdown("#### Satellites Flagged by Both Methods (Score 2)")
st.caption(f"Showing all {dual_flag} satellites flagged by both ML and Discrete Math:")

priority_subset = df[df['anomaly_score'] == 2].copy()

def get_primary_reason(row):
    reasons = get_operator_explanation(row, df)
    for r in reasons:
        if "Oval-shaped" in r: return "High Ellipticity"
        if "Slightly oval" in r: return "Moderate Ellipticity"
        if "Very high altitude" in r: return "High Altitude (>1,200 km)"
        if "Very low altitude" in r: return "Low Altitude (<350 km)"
        if "Unusually low tilt" in r: return "Low Inclination (<35°)"
        if "Unusual tilt" in r: return "Uncommon Polar Inclination"
    return "Isolated Orbit"

priority_subset['Primary_Reason'] = priority_subset.apply(get_primary_reason, axis=1)

table_display = priority_subset[[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height', 
    'INCLINATION', 'ECCENTRICITY', 'Primary_Reason'
]].sort_values(by='orbit_height', ascending=False)

table_display.columns = [
    'NORAD ID', 'Name', 'Altitude (km)', 
    'Inclination (°)', 'Eccentricity', 'Main Reason Flagged'
]

st.dataframe(
    table_display.style.format({
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}',
        'Eccentricity': '{:.4f}'
    }),
    use_container_width=True,
    hide_index=True
)
