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
st.markdown('<div class="page-title">Operator Priority Watch List</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Actionable queue of active LEO satellites flagged by statistical and neighborhood checks.</div>', unsafe_allow_html=True)
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
    render_metric_card("Total Flagged", f"{n_score1 + n_score2:,}", "Require Operator Attention", "#f8fafc")
with k2:
    render_metric_card("Statistical Only", f"{ml_only:,}", "Atypical Orbit Profile", "#fbbf24", "#f59e0b")
with k3:
    render_metric_card("Spacing Only", f"{dm_only:,}", "Isolated Orbital Lane", "#38bdf8", "#0284c7")
with k4:
    render_metric_card("High Priority", f"{dual_flag:,}", "Flagged by Both Systems", "#f87171", "#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# Visualizing Watch List
col_c1, col_c2 = st.columns([1.2, 1])

with col_c1:
    st.markdown("#### Flag Summary")
    combo_data = pd.DataFrame({
        'Category': ['Score 1 (Statistical Profile)', 'Score 1 (Spacing / Isolated)', 'Score 2 (Both Systems)'],
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
            'Score 1 (Statistical Profile)': '#f59e0b',
            'Score 1 (Spacing / Isolated)': '#0284c7',
            'Score 2 (Both Systems)': '#ef4444'
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
    st.markdown("#### Operator Workflow Guidance")
    st.markdown("""
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px; font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">
        <p style="margin-bottom: 8px;">
            <b>Prioritization Protocol:</b>
        </p>
        <p style="margin-bottom: 8px;">
            • <b>Score 2 Satellites ({0} total):</b> Top queue for manual ephemeris inspection. Both the clustering model and neighborhood spacing graph agree that these orbits are atypical.
        </p>
        <p style="margin-bottom: 8px;">
            • <b>Score 1 Satellites ({1} total):</b> Secondary review queue. Satellites flagged here typically have unusual inclinations or sit on the sparse outskirts of active constellation shells.
        </p>
        <p style="margin-bottom: 0px; font-size: 0.75rem; color: #94a3b8;">
            Tip: Click on any satellite in the table below and inspect it directly in the <b>Satellite Explorer</b> page.
        </p>
    </div>
    """.format(dual_flag, n_score1), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Master Table of Score 2 Spacecraft
st.markdown("#### High Priority Queue (Score = 2)")
st.caption(f"Showing all {dual_flag} satellites flagged simultaneously by both statistical and neighborhood models:")

priority_subset = df[df['anomaly_score'] == 2].copy()

# Add a concise physical diagnosis column
def get_primary_reason(row):
    reasons = get_operator_explanation(row, df)
    # pick the first non-generic reason
    for r in reasons:
        if "Highly Elliptical" in r: return "Extreme Ellipticity"
        if "Moderate Ellipticity" in r: return "Elevated Ellipticity"
        if "High LEO Altitude" in r: return "High Altitude Shell (>1,200 km)"
        if "Very Low Orbit" in r: return "Decaying / Low Orbit (<350 km)"
        if "Uncommon Low Inclination" in r: return "Rare Low Inclination (<35°)"
        if "Non-Standard Polar" in r: return "Non-Standard Polar Orbit"
    return "Isolated Orbital Corridor"

priority_subset['Primary_Reason'] = priority_subset.apply(get_primary_reason, axis=1)

table_display = priority_subset[[
    'NORAD_CAT_ID', 'OBJECT_NAME', 'orbit_height', 
    'INCLINATION', 'ECCENTRICITY', 'Primary_Reason'
]].sort_values(by='orbit_height', ascending=False)

table_display.columns = [
    'NORAD ID', 'Satellite Name', 'Altitude (km)', 
    'Inclination (°)', 'Eccentricity', 'Primary Operational Finding'
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
