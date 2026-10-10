import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data, rerun_full_pipeline
from theme import apply_theme, render_metric_card, render_sidebar, get_plotly_layout

st.set_page_config(
    page_title="Satellite Anomaly Detection · Overview",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("Error: Processed data files are missing. Please run the pipeline.")
    st.stop()

# Sidebar
render_sidebar(df)
with st.sidebar:
    with st.expander("Update Data", expanded=False):
        st.caption("Re-run feature engineering, ML, graph analysis, and integration on the raw data.")
        if st.button("Run Full Pipeline", type="primary", use_container_width=True):
            with st.spinner("Processing catalog..."):
                try:
                    rerun_full_pipeline()
                    st.success("Data updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# Header
st.markdown('<div class="page-title">Satellite Anomaly Detection</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Finding unusual satellites in Low Earth Orbit using Machine Learning and Discrete Mathematics.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Top KPIs
counts = df['anomaly_score'].value_counts()
n_total = len(df)
n_score0 = counts.get(0, 0)
n_score1 = counts.get(1, 0)
n_score2 = counts.get(2, 0)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    render_metric_card("Active LEO Satellites", f"{n_total:,}", "Altitude under 2,000 km", "#f8fafc", "#3b82f6")
with kpi2:
    pct0 = (n_score0 / n_total) * 100
    render_metric_card("Score 0 · Normal", f"{n_score0:,}", f"{pct0:.1f}% normal orbits", "#34d399", "#10b981")
with kpi3:
    pct1 = (n_score1 / n_total) * 100
    render_metric_card("Score 1 · One Flag", f"{n_score1:,}", f"{pct1:.1f}% flagged by ML or DM", "#fbbf24", "#f59e0b")
with kpi4:
    pct2 = (n_score2 / n_total) * 100
    render_metric_card("Score 2 · Both Flagged", f"{n_score2:,}", f"{pct2:.2f}% dual-flagged", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Main Grid
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("#### Satellite Counts by Score")
    dist_df = pd.DataFrame({
        'Status': ['Score 0 (Normal)', 'Score 1 (One Method)', 'Score 2 (Both Methods)'],
        'Count': [n_score0, n_score1, n_score2],
        'Color': ['#10b981', '#f59e0b', '#ef4444']
    })
    
    fig = px.bar(
        dist_df,
        x='Status',
        y='Count',
        text='Count',
        color='Status',
        color_discrete_map={
            'Score 0 (Normal)': '#10b981',
            'Score 1 (One Method)': '#f59e0b',
            'Score 2 (Both Methods)': '#ef4444'
        }
    )
    fig.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        marker_line_width=0,
        hovertemplate='<b>%{x}</b><br>Satellites: %{y:,}<extra></extra>'
    )
    layout = get_plotly_layout(height=280)
    layout['showlegend'] = False
    layout['yaxis']['title'] = "Number of Satellites"
    layout['xaxis']['title'] = ""
    fig.update_layout(layout)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("#### What the Scores Mean")
    st.markdown("""
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; color: #cbd5e1;">
            <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left;">
                    <th style="padding: 8px 6px;">Score</th>
                    <th style="padding: 8px 6px;">Meaning</th>
                    <th style="padding: 8px 6px;">Priority</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 8px 6px;"><span class="score-badge score-0">Score 0</span></td>
                    <td style="padding: 8px 6px;">Neither ML nor DM flagged it</td>
                    <td style="padding: 8px 6px; color: #34d399;">Normal</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 8px 6px;"><span class="score-badge score-1">Score 1</span></td>
                    <td style="padding: 8px 6px;">Flagged by either ML or DM</td>
                    <td style="padding: 8px 6px; color: #fbbf24;">Review</td>
                </tr>
                <tr>
                    <td style="padding: 8px 6px;"><span class="score-badge score-2">Score 2</span></td>
                    <td style="padding: 8px 6px;">Flagged by <b>both</b> ML and DM</td>
                    <td style="padding: 8px 6px; color: #f87171; font-weight: 600;">High Priority</td>
                </tr>
            </tbody>
        </table>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 12px; line-height: 1.4;">
            <b>Note:</b> The score counts how many methods flagged the satellite. It is not a probability or danger rating. ML and DM share some orbital features, so they are not completely independent.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# LEO Altitude Bands
st.markdown("#### Satellites by Altitude")
shell_lower = len(df[df['orbit_height'] < 500])
shell_mid = len(df[(df['orbit_height'] >= 500) & (df['orbit_height'] <= 600)])
shell_upper = len(df[df['orbit_height'] > 600])

c_s1, c_s2, c_s3 = st.columns(3)
with c_s1:
    render_metric_card("Under 500 km", f"{shell_lower:,}", "e.g. Space Stations (ISS)", "#60a5fa")
with c_s2:
    render_metric_card("500 to 600 km", f"{shell_mid:,}", "e.g. Starlink, OneWeb constellations", "#818cf8")
with c_s3:
    render_metric_card("Above 600 km", f"{shell_upper:,}", "e.g. Weather and Earth observation", "#a78bfa")

# Scatter overview
st.markdown("#### Altitude vs. Inclination")
sample_df = df.sample(n=min(3000, len(df)), random_state=42)
fig_scatter = px.scatter(
    sample_df,
    x='orbit_height',
    y='INCLINATION',
    color='anomaly_score',
    range_x=[100, 2000],
    color_continuous_scale=[(0, '#10b981'), (0.5, '#f59e0b'), (1, '#ef4444')],
    hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'anomaly_score'],
    labels={'orbit_height': 'Altitude (km)', 'INCLINATION': 'Inclination (degrees)', 'anomaly_score': 'Score'},
)
fig_scatter.update_traces(marker=dict(size=4, opacity=0.75))
scatter_layout = get_plotly_layout(height=360)
scatter_layout['coloraxis_colorbar'] = dict(
    title="Score",
    tickvals=[0, 1, 2],
    ticktext=["0 (Normal)", "1 (One Flag)", "2 (Both Flagged)"],
    len=0.7
)
fig_scatter.update_layout(scatter_layout)
st.plotly_chart(fig_scatter, use_container_width=True)
st.caption("Plotting 3,000 sampled satellites. Colors show the final score (0 = Green, 1 = Yellow, 2 = Red).")
