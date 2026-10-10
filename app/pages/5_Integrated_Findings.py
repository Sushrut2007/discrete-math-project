import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_full_data
from theme import apply_theme, render_sidebar, render_metric_card, get_plotly_layout

st.set_page_config(
    page_title="Integrated Findings & Priority",
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
st.markdown('<div class="page-title">Integrated Findings & Priority Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Synthesis of statistical Machine Learning and Discrete Math topological evidence into an additive 0–2 score.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Counts
counts = df['anomaly_score'].value_counts()
n_total = len(df)
n_score0 = counts.get(0, 0)
n_score1 = counts.get(1, 0)
n_score2 = counts.get(2, 0)

# Combination Breakdown
ml_only = len(df[(df['ml_flag'] == 1) & (df['dm_flag'] == 0)])
dm_only = len(df[(df['ml_flag'] == 0) & (df['dm_flag'] == 1)])
dual_flag = len(df[(df['ml_flag'] == 1) & (df['dm_flag'] == 1)])

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_metric_card("Total Flagged", f"{n_score1 + n_score2:,}", "Score 1 or Score 2", "#f8fafc")
with k2:
    render_metric_card("ML Only Flagged", f"{ml_only:,}", "Score 1 · Statistical Outlier", "#fbbf24", "#f59e0b")
with k3:
    render_metric_card("DM Only Flagged", f"{dm_only:,}", "Score 1 · Graph Isolated", "#38bdf8", "#0284c7")
with k4:
    render_metric_card("Dual Flagged", f"{dual_flag:,}", "Score 2 · Maximum Priority", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Visualizing Concordance
col_c1, col_c2 = st.columns([1.2, 1])

with col_c1:
    st.markdown("#### Evidence Trigger Combinations")
    combo_data = pd.DataFrame({
        'Category': ['Score 0 (Neither Flagged)', 'Score 1 (ML Only)', 'Score 1 (DM Only)', 'Score 2 (Both ML & DM)'],
        'Count': [n_score0, ml_only, dm_only, dual_flag],
        'Color': ['#10b981', '#f59e0b', '#0284c7', '#ef4444']
    })
    
    # Plot non-zero anomalies
    anom_combo = combo_data[combo_data['Count'] != n_score0].copy()
    fig_combo = px.bar(
        anom_combo,
        x='Count',
        y='Category',
        orientation='h',
        text='Count',
        color='Category',
        color_discrete_map={
            'Score 1 (ML Only)': '#f59e0b',
            'Score 1 (DM Only)': '#0284c7',
            'Score 2 (Both ML & DM)': '#ef4444'
        }
    )
    fig_combo.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        marker_line_width=0,
        hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>'
    )
    layout_cb = get_plotly_layout(height=260)
    layout_cb['showlegend'] = False
    layout_cb['xaxis']['title'] = "Number of Spacecraft"
    layout_cb['yaxis']['title'] = ""
    fig_combo.update_layout(layout_cb)
    st.plotly_chart(fig_combo, use_container_width=True)

with col_c2:
    st.markdown("#### Operational Interpretation")
    st.markdown("""
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px; font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">
        <p style="margin-bottom: 8px;">
            <b>Why is the Score an Evidence Tally?</b><br>
            The integration score is defined as:
        </p>
        <div style="font-family: 'JetBrains Mono', monospace; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; color: #f8fafc; margin-bottom: 10px;">
            Score = F_ML + F_DM ∈ {0, 1, 2}
        </div>
        <p style="margin-bottom: 6px;">
            • <b>Score 2 (23 spacecraft):</b> Represents the highest priority for sensor tasking and verification because two distinct methodologies independently identified unusual features.
        </p>
        <p style="margin-bottom: 0px;">
            • <b>Complementarity:</b> ML is effective at finding atypical orbits relative to orbital regimes. DM graph topology excels at finding spacecraft in physically sparse corridors regardless of cluster definition.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Master Table of Score 2 Spacecraft
st.markdown("#### High Priority Spacecraft Registry (Score = 2)")
st.caption(f"Showing all {dual_flag} spacecraft flagged concurrently by both Machine Learning and Discrete Mathematics:")

priority_df = df[df['anomaly_score'] == 2][[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'cluster_id', 'orbit_height', 
    'INCLINATION', 'ECCENTRICITY', 'ml_anomaly_score', 'mean_neighbor_distance', 'incoming_neighbor_count'
]].sort_values(by='mean_neighbor_distance', ascending=False)

priority_df.columns = [
    'NORAD ID', 'Name', 'Cluster', 'Altitude (km)', 'Inclination (°)', 
    'Eccentricity', 'ML Score', 'Mean 5-NN Dist', 'In-Degree'
]

st.dataframe(
    priority_df.style.format({
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}',
        'Eccentricity': '{:.4f}',
        'ML Score': '{:.4f}',
        'Mean 5-NN Dist': '{:.4f}',
        'In-Degree': '{:d}'
    }),
    use_container_width=True,
    hide_index=True
)
