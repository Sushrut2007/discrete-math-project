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
    total_flagged = n_score1 + n_score2
    combo_data = pd.DataFrame({
        'Category': ['Score 2 (Both Flagged)', 'Score 1 (Graph Only)', 'Score 1 (ML Only)'],
        'Count': [dual_flag, dm_only, ml_only],
        'Color': ['#ef4444', '#0284c7', '#f59e0b'],
        'TextLabel': [
            f"{dual_flag:,} ({dual_flag/total_flagged*100:.1f}%) · Top Priority",
            f"{dm_only:,} ({dm_only/total_flagged*100:.1f}%) · Isolated Spacing",
            f"{ml_only:,} ({ml_only/total_flagged*100:.1f}%) · Cluster Outliers"
        ]
    })
    
    fig_combo = px.bar(
        combo_data,
        x='Count',
        y='Category',
        orientation='h',
        text='TextLabel',
        color='Category',
        color_discrete_map={
            'Score 1 (ML Only)': '#f59e0b',
            'Score 1 (Graph Only)': '#0284c7',
            'Score 2 (Both Flagged)': '#ef4444'
        }
    )
    fig_combo.update_traces(
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
    st.markdown("#### How the Two Methods Compare")
    st.markdown(f"""
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px; font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 6px; padding: 10px;">
                <div style="font-size: 0.72rem; color: #fbbf24; text-transform: uppercase; font-weight: 600;">ML Flagged</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc;">792</div>
                <div style="font-size: 0.7rem; color: #94a3b8;">5.0% of LEO catalog</div>
            </div>
            <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 10px;">
                <div style="font-size: 0.72rem; color: #38bdf8; text-transform: uppercase; font-weight: 600;">Graph Flagged</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc;">64</div>
                <div style="font-size: 0.7rem; color: #94a3b8;">0.4% of LEO catalog</div>
            </div>
        </div>
        <div style="background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #f87171;">Dual Confirmation: 22 Satellites</div>
            <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">
                These 22 satellites were independently caught by <b>both</b> methods. They have the most unusual orbits in the entire active LEO catalog.
            </div>
        </div>
        <div style="font-size: 0.75rem; color: #94a3b8; line-height: 1.4;">
            <b>Why combine both?</b> ML catches satellites that deviate from their altitude group, while Graph catches satellites that have no close peers in space.
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    'NORAD ID', 'Satellite Name', 'Altitude (km)', 
    'Inclination (°)', 'Orbit Shape (Ecc.)', 'Main Reason Flagged'
]

st.dataframe(
    table_display.style.format({
        'Altitude (km)': '{:,.1f}',
        'Inclination (°)': '{:.2f}',
        'Orbit Shape (Ecc.)': '{:.4f}'
    }),
    use_container_width=True,
    hide_index=True
)
