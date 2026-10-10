import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data, rerun_full_pipeline
from theme import apply_theme, render_metric_card, render_sidebar, get_plotly_layout

st.set_page_config(
    page_title="LEO Satellite Monitor · Overview",
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
    with st.expander("Update Catalog Data", expanded=False):
        st.caption("Re-run feature engineering, ML, graph analysis, and integration on the raw data.")
        if st.button("Run Full Pipeline", type="primary", use_container_width=True):
            with st.spinner("Processing LEO catalog..."):
                try:
                    rerun_full_pipeline()
                    st.success("Catalog updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# Header
st.markdown('<div class="page-title">Low Earth Orbit (LEO) Satellite Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Operational traffic monitoring and anomaly detection across active Low Earth Orbit satellites.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Top KPIs
counts = df['anomaly_score'].value_counts()
n_total = len(df)
n_score0 = counts.get(0, 0)
n_score1 = counts.get(1, 0)
n_score2 = counts.get(2, 0)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    render_metric_card("Active LEO Satellites", f"{n_total:,}", "Altitude < 2,000 km", "#f8fafc", "#3b82f6")
with kpi2:
    pct0 = (n_score0 / n_total) * 100
    render_metric_card("Nominal (Score 0)", f"{n_score0:,}", f"{pct0:.1f}% normal orbits", "#34d399", "#10b981")
with kpi3:
    pct1 = (n_score1 / n_total) * 100
    render_metric_card("Review List (Score 1)", f"{n_score1:,}", f"{pct1:.1f}% single flag", "#fbbf24", "#f59e0b")
with kpi4:
    pct2 = (n_score2 / n_total) * 100
    render_metric_card("High Attention (Score 2)", f"{n_score2:,}", f"{pct2:.2f}% dual-flagged", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Main Grid
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("#### Catalog Status Breakdown")
    dist_df = pd.DataFrame({
        'Status': ['Nominal (Score 0)', 'Review List (Score 1)', 'High Attention (Score 2)'],
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
            'Nominal (Score 0)': '#10b981',
            'Review List (Score 1)': '#f59e0b',
            'High Attention (Score 2)': '#ef4444'
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
    st.markdown("#### Alert Level Guide")
    st.markdown("""
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; color: #cbd5e1;">
            <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left;">
                    <th style="padding: 8px 6px;">Level</th>
                    <th style="padding: 8px 6px;">What it indicates</th>
                    <th style="padding: 8px 6px;">Operator Action</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 8px 6px;"><span class="score-badge score-0">Score 0</span></td>
                    <td style="padding: 8px 6px;">Within standard constellation parameters</td>
                    <td style="padding: 8px 6px; color: #34d399;">Routine monitoring</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 8px 6px;"><span class="score-badge score-1">Score 1</span></td>
                    <td style="padding: 8px 6px;">Flagged by either statistical check or spacing check</td>
                    <td style="padding: 8px 6px; color: #fbbf24;">Watch list review</td>
                </tr>
                <tr>
                    <td style="padding: 8px 6px;"><span class="score-badge score-2">Score 2</span></td>
                    <td style="padding: 8px 6px;">Flagged by <b>both</b> checks simultaneously</td>
                    <td style="padding: 8px 6px; color: #f87171; font-weight: 600;">Immediate investigation</td>
                </tr>
            </tbody>
        </table>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 12px; line-height: 1.4;">
            <b>Operator Notice:</b> A flag indicates an atypical orbit or sparse corridor—not an immediate collision warning.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# LEO Altitude Shell Breakdown (Practical for LEO operator)
st.markdown("#### LEO Operational Shells")
shell_lower = len(df[df['orbit_height'] < 500])
shell_mid = len(df[(df['orbit_height'] >= 500) & (df['orbit_height'] <= 600)])
shell_upper = len(df[df['orbit_height'] > 600])

c_s1, c_s2, c_s3 = st.columns(3)
with c_s1:
    render_metric_card("Lower LEO", f"{shell_lower:,}", "Altitude < 500 km (ISS, Tiangong)", "#60a5fa")
with c_s2:
    render_metric_card("Mega-Constellation Shell", f"{shell_mid:,}", "500–600 km (Starlink, OneWeb)", "#818cf8")
with c_s3:
    render_metric_card("Upper LEO", f"{shell_upper:,}", "600–2,000 km (Iridium, Earth Obs)", "#a78bfa")

# Scatter overview
st.markdown("#### Altitude vs. Inclination Map")
sample_df = df.sample(n=min(3000, len(df)), random_state=42)
fig_scatter = px.scatter(
    sample_df,
    x='orbit_height',
    y='INCLINATION',
    color='anomaly_score',
    color_continuous_scale=[(0, '#10b981'), (0.5, '#f59e0b'), (1, '#ef4444')],
    hover_data=['NORAD_CAT_ID', 'OBJECT_NAME', 'anomaly_score'],
    labels={'orbit_height': 'Altitude (km)', 'INCLINATION': 'Inclination (degrees)', 'anomaly_score': 'Score'},
)
fig_scatter.update_traces(marker=dict(size=4, opacity=0.75))
scatter_layout = get_plotly_layout(height=360)
scatter_layout['coloraxis_colorbar'] = dict(
    title="Score",
    tickvals=[0, 1, 2],
    ticktext=["0 (Nominal)", "1 (Watch)", "2 (Critical)"],
    len=0.7
)
fig_scatter.update_layout(scatter_layout)
st.plotly_chart(fig_scatter, use_container_width=True)
st.caption("Showing 3,000 sampled LEO satellites. Notice the dense clusters at 53° (Starlink) and 97° (Sun-Synchronous). Outliers appear in isolated altitude/inclination bands.")
