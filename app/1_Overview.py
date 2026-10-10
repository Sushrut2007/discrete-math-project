import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data, rerun_full_pipeline
from theme import apply_theme, render_metric_card, render_sidebar, get_plotly_layout

st.set_page_config(
    page_title="Orbital Anomaly Radar · Overview",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()
df = load_full_data()

if df.empty:
    st.error("System Error: Processed data files are missing. Please verify the data directory.")
    st.stop()

# Sidebar
render_sidebar(df)
with st.sidebar:
    with st.expander("Pipeline Controls", expanded=False):
        st.caption("Re-run feature extraction, ML clustering, DM graph construction, and score integration on the active catalog.")
        if st.button("Execute Pipeline", type="primary", use_container_width=True):
            with st.spinner("Processing orbital pipeline..."):
                try:
                    rerun_full_pipeline()
                    st.success("Pipeline executed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

# Header
st.markdown('<div class="page-title">Orbital Anomaly Radar</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Dual-method satellite anomaly detection powered by Machine Learning and Discrete Mathematics.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Top KPIs
counts = df['anomaly_score'].value_counts()
n_total = len(df)
n_score0 = counts.get(0, 0)
n_score1 = counts.get(1, 0)
n_score2 = counts.get(2, 0)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    render_metric_card("Tracked Satellites", f"{n_total:,}", "CelesTrak Active Elements", "#f8fafc", "#3b82f6")
with kpi2:
    pct0 = (n_score0 / n_total) * 100
    render_metric_card("Score 0 · Nominal", f"{n_score0:,}", f"{pct0:.1f}% of catalog", "#34d399", "#10b981")
with kpi3:
    pct1 = (n_score1 / n_total) * 100
    render_metric_card("Score 1 · Review", f"{n_score1:,}", f"{pct1:.1f}% single model flag", "#fbbf24", "#f59e0b")
with kpi4:
    pct2 = (n_score2 / n_total) * 100
    render_metric_card("Score 2 · High Priority", f"{n_score2:,}", f"{pct2:.2f}% dual-flagged", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Main Grid
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("#### Anomaly Score Distribution")
    dist_df = pd.DataFrame({
        'Score': ['Score 0 (Nominal)', 'Score 1 (Single Flag)', 'Score 2 (Dual Flag)'],
        'Count': [n_score0, n_score1, n_score2],
        'Color': ['#10b981', '#f59e0b', '#ef4444'],
        'Description': [
            'Neither ML nor DM flagged',
            'Either ML or DM flagged',
            'Both ML and DM flagged'
        ]
    })
    
    fig = px.bar(
        dist_df,
        x='Score',
        y='Count',
        text='Count',
        color='Score',
        color_discrete_map={
            'Score 0 (Nominal)': '#10b981',
            'Score 1 (Single Flag)': '#f59e0b',
            'Score 2 (Dual Flag)': '#ef4444'
        }
    )
    fig.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        marker_line_width=0,
        hovertemplate='<b>%{x}</b><br>Count: %{y:,}<extra></extra>'
    )
    layout = get_plotly_layout(height=280)
    layout['showlegend'] = False
    layout['yaxis']['title'] = "Satellite Count"
    layout['xaxis']['title'] = ""
    fig.update_layout(layout)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("#### Evidence Synthesis Matrix")
    st.markdown("""
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; color: #cbd5e1;">
            <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left;">
                    <th style="padding: 8px 6px;">Score</th>
                    <th style="padding: 8px 6px;">Evidence Criteria</th>
                    <th style="padding: 8px 6px;">Catalog Action</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 8px 6px;"><span class="score-badge score-0">0</span></td>
                    <td style="padding: 8px 6px;">Neither ML nor DM flagged</td>
                    <td style="padding: 8px 6px; color: #34d399;">Nominal routine tracking</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 8px 6px;"><span class="score-badge score-1">1</span></td>
                    <td style="padding: 8px 6px;">Flagged by either ML or DM</td>
                    <td style="padding: 8px 6px; color: #fbbf24;">Moderate review list</td>
                </tr>
                <tr>
                    <td style="padding: 8px 6px;"><span class="score-badge score-2">2</span></td>
                    <td style="padding: 8px 6px;">Flagged by <b>both</b> ML and DM</td>
                    <td style="padding: 8px 6px; color: #f87171; font-weight: 600;">High priority investigation</td>
                </tr>
            </tbody>
        </table>
        <div style="font-size: 0.75rem; color: #64748b; margin-top: 12px; line-height: 1.4;">
            <b>Interpretation Note:</b> The score indicates the tally of concordant methods, not a probability of collision or failure. ML and DM share orbital features and are complementary indicators.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Catalog Orbit Breakdown
st.markdown("#### Orbital Regime Distribution")
col_reg1, col_reg2, col_reg3 = st.columns(3)

leo_count = len(df[df['orbit_height'] < 2000])
meo_count = len(df[(df['orbit_height'] >= 2000) & (df['orbit_height'] < 35000)])
geo_count = len(df[df['orbit_height'] >= 35000])

with col_reg1:
    render_metric_card("LEO Spacecraft", f"{leo_count:,}", "Altitude < 2,000 km", "#60a5fa")
with col_reg2:
    render_metric_card("MEO Spacecraft", f"{meo_count:,}", "2,000 km – 35,000 km", "#a78bfa")
with col_reg3:
    render_metric_card("GEO Spacecraft", f"{geo_count:,}", "Altitude ≥ 35,000 km", "#f472b6")

# Quick scatter overview
st.markdown("#### Altitude vs Inclination Spectrum")
sample_df = df.sample(n=min(3000, len(df)), random_state=42)
fig_scatter = px.scatter(
    sample_df,
    x='orbit_height',
    y='INCLINATION',
    color='anomaly_score',
    color_continuous_scale=[(0, '#10b981'), (0.5, '#f59e0b'), (1, '#ef4444')],
    hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'anomaly_score'],
    labels={'orbit_height': 'Orbit Altitude (km)', 'INCLINATION': 'Inclination (deg)', 'anomaly_score': 'Score'},
)
fig_scatter.update_traces(marker=dict(size=4, opacity=0.75))
scatter_layout = get_plotly_layout(height=360)
scatter_layout['coloraxis_colorbar'] = dict(
    title="Score",
    tickvals=[0, 1, 2],
    ticktext=["0 (Nominal)", "1 (Review)", "2 (Priority)"],
    len=0.7
)
fig_scatter.update_layout(scatter_layout)
st.plotly_chart(fig_scatter, use_container_width=True)
st.caption("Displaying 3,000 sampled satellites for responsive rendering. Outliers in high altitudes and inclinations are highlighted.")
