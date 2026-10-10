import streamlit as st
import plotly.graph_objects as go

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1300px;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #131b2e 0%, #0d1322 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        margin-bottom: 12px;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.1;
        color: #f1f5f9;
        margin-bottom: 4px;
    }
    
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
    }
    
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 6px;
    }
    
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .score-0 {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .score-1 {
        background: rgba(245, 158, 11, 0.12);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .score-2 {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.45);
    }
    
    .page-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 2px;
        letter-spacing: -0.02em;
    }
    .page-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.4rem;
    }
    
    .accent-bar {
        height: 2px;
        width: 48px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 2px;
        margin-bottom: 1rem;
    }

    .evidence-panel {
        background: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 18px;
        height: 100%;
    }
    .evidence-header {
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
        margin-right: 6px;
    }
</style>
"""

def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, subtext: str = "", color: str = "#f1f5f9", border_color: str = None):
    style_extra = f"border-left: 3px solid {border_color};" if border_color else ""
    st.markdown(f"""
    <div class="metric-card" style="{style_extra}">
        <div class="metric-value" style="color: {color};">{value}</div>
        <div class="metric-label">{label}</div>
        {f'<div class="metric-sub">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)

def get_badge_html(score: int) -> str:
    if score == 0:
        return '<span class="score-badge score-0">Score 0 · Normal</span>'
    elif score == 1:
        return '<span class="score-badge score-1">Score 1 · One Flag</span>'
    else:
        return '<span class="score-badge score-2">Score 2 · Both Flagged</span>'

def render_sidebar(df):
    with st.sidebar:
        st.markdown("### Satellite Anomaly Detection")
        st.caption("Discrete Mathematics & Machine Learning")
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 10px 14px; border-radius: 8px; margin-bottom: 16px;">
            <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">Catalog Size</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc; margin-top: 2px;">
                <span class="status-dot"></span>{len(df):,} Satellites
            </div>
            <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">Data source: CelesTrak active satellites</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### Detection Components")
        st.markdown("""
        - **ML Component:** K-Means clustering + Isolation Forest
        - **DM Component:** Directed 5-NN graph + In-degree zero rule
        - **Final Score:** Sum of flags (0, 1, or 2)
        """)
        
        st.markdown("---")
        if st.button("Reload Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

def get_plotly_layout(height=340, title=None):
    layout = dict(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 23, 42, 0.4)',
        font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
        margin=dict(l=40, r=20, t=40 if title else 20, b=40),
        height=height,
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.08)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.08)'),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=14, color="#e2e8f0"))
    return layout
