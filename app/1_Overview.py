import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_metric_card, render_sidebar, get_plotly_layout, PLOTLY_CONFIG

st.set_page_config(
    page_title="Satellite Anomaly Overview",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Error: Processed data files are missing. Please run the pipeline.")
    st.stop()

render_sidebar(df)

# Header
st.markdown('<div class="page-title">Satellite Anomaly Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Summary of detector flags across the active Low Earth Orbit catalog.</div>', unsafe_allow_html=True)

# Top KPIs
n_total = len(df)
counts = df['anomaly_score'].value_counts()
n_score0 = counts.get(0, 0)
n_score1 = counts.get(1, 0)
n_score2 = counts.get(2, 0)

pct0 = (n_score0 / n_total) * 100
pct1 = (n_score1 / n_total) * 100
pct2 = (n_score2 / n_total) * 100

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Analysed", f"{n_total:,}", "Active LEO satellites (< 2,000 km)", "#f8fafc")
with k2:
    render_metric_card("Score 0 — No flags", f"{n_score0:,}", f"{pct0:.1f}% of catalog", "#34d399", "#10b981")
with k3:
    render_metric_card("Score 1 — One flag", f"{n_score1:,}", f"{pct1:.1f}% of catalog", "#fbbf24", "#f59e0b")
with k4:
    render_metric_card("Score 2 — Both flagged", f"{n_score2:,}", f"{pct2:.2f}% of catalog (review first)", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Distribution and Explanation
col_chart, col_exp = st.columns([1.1, 1])

with col_chart:
    st.markdown("#### Score Distribution")
    dist_df = pd.DataFrame({
        'Score': ['Score 2 — Both flagged', 'Score 1 — One flag', 'Score 0 — No flags'],
        'Count': [n_score2, n_score1, n_score0],
        'Display': [f"{n_score2:,} ({pct2:.2f}%)", f"{n_score1:,} ({pct1:.1f}%)", f"{n_score0:,} ({pct0:.1f}%)"]
    })
    
    fig = px.bar(
        dist_df,
        y='Score',
        x='Count',
        orientation='h',
        text='Display',
        color='Score',
        color_discrete_map={
            'Score 0 — No flags': '#10b981',
            'Score 1 — One flag': '#f59e0b',
            'Score 2 — Both flagged': '#ef4444'
        }
    )
    fig.update_traces(
        textposition='outside',
        marker_line_width=0,
        hovertemplate='<b>%{y}</b><br>Satellites: %{x:,}<extra></extra>'
    )
    layout = get_plotly_layout(height=230)
    layout['showlegend'] = False
    layout['xaxis']['title'] = "Number of Satellites"
    layout['yaxis']['title'] = ""
    layout['margin'] = dict(l=40, r=40, t=10, b=35)
    fig.update_layout(layout)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

with col_exp:
    st.markdown("#### What the Scores Mean")
    st.markdown("""
    <div class="info-box">
        <p style="margin-bottom: 8px;">
            <b>0 — No flags:</b> Neither method flagged the satellite. It operates within standard orbital ranges.
        </p>
        <p style="margin-bottom: 8px;">
            <b>1 — One flag:</b> Either Machine Learning or Discrete Math flagged it.
        </p>
        <p style="margin-bottom: 8px;">
            <b>2 — Both flagged:</b> Both methods independently flagged it; review this satellite first.
        </p>
        <p style="margin-top: 12px; margin-bottom: 0px; font-size: 0.78rem; color: #94a3b8;">
            <b>Note:</b> The score counts detector flags; it does not measure collision risk or the probability of a mechanical problem. ML and DM share some orbital features, so they are not completely independent.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Table of Flagged Satellites
st.markdown("### Flagged Satellites")

selected_view = st.radio(
    "Select score to inspect:",
    [f"Score 2 — Both flagged ({n_score2} satellites)", f"Score 1 — One flag ({n_score1:,} satellites)"],
    horizontal=True
)

target_score = 2 if "Score 2" in selected_view else 1
table_data = df[df['anomaly_score'] == target_score].copy()

# Search filter
filter_query = st.text_input("Filter table by satellite name or NORAD ID:", placeholder="e.g. EXPRESS, 38745, STARLINK...")
if filter_query.strip():
    q = filter_query.strip().lower()
    table_data = table_data[
        table_data['OBJECT_NAME'].str.lower().str.contains(q, na=False) |
        table_data['NORAD_CAT_ID'].astype(str).str.contains(q, na=False)
    ]

# Sort by altitude descending by default
table_display = table_data[[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'anomaly_score', 'ml_flag', 'dm_flag',
    'orbit_height', 'INCLINATION', 'ECCENTRICITY'
]].sort_values(by='orbit_height', ascending=False)

table_display.columns = [
    'NORAD ID', 'Satellite Name', 'Final Score', 'ML Flag', 'DM Flag',
    'Altitude (km)', 'Inclination (°)', 'Eccentricity'
]

st.dataframe(
    table_display.style.format({
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}',
        'Eccentricity': '{:.4f}',
        'ML Flag': '{:d}',
        'DM Flag': '{:d}'
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(f"Showing {len(table_display):,} satellites. Use the Satellite Explorer page to view detailed diagnostics for any satellite.")
