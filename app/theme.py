import os
from pathlib import Path
from datetime import datetime, timezone
import requests
import streamlit as st

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }
    
    .metric-card {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.15;
        color: #f8fafc;
        margin-bottom: 3px;
    }
    
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
    }
    
    .metric-sub {
        font-size: 0.74rem;
        color: #64748b;
        margin-top: 4px;
    }
    
    .score-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .score-0 {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .score-1 {
        background: rgba(245, 158, 11, 0.12);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .score-2 {
        background: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    
    .page-title {
        font-size: 1.7rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
        letter-spacing: -0.02em;
    }
    .page-subtitle {
        font-size: 0.92rem;
        color: #94a3b8;
        margin-bottom: 1.2rem;
    }
    
    .info-box {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        padding: 14px 18px;
        font-size: 0.86rem;
        color: #cbd5e1;
        line-height: 1.5;
        margin-bottom: 16px;
    }
</style>
"""

def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, subtext: str = "", color: str = "#f8fafc", border_color: str = None):
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
        return '<span class="score-badge score-0">Score 0 — No flags</span>'
    elif score == 1:
        return '<span class="score-badge score-1">Score 1 — One flag</span>'
    else:
        return '<span class="score-badge score-2">Score 2 — Both flagged</span>'

def get_latest_data_timestamp() -> str:
    raw_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "latest_satellite_data.csv"
    if raw_path.exists():
        mtime = raw_path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        return dt.strftime("%d %b %Y, %H:%M UTC")
    return "Not available"


def render_sidebar(df):
    with st.sidebar:
        st.markdown("### Satellite Monitoring")
        st.caption("Low Earth Orbit Dataset")
        
        timestamp = get_latest_data_timestamp()
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 10px 14px; border-radius: 6px; margin-bottom: 16px;">
            <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">Total Satellites</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #f8fafc; margin-top: 2px;">
                {len(df):,} LEO Satellites
            </div>
            <div style="font-size: 0.72rem; color: #64748b; margin-top: 4px;">Source: CelesTrak active satellites</div>
            <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
                Last fetched: <span style="color: #f8fafc; font-weight: 500;">{timestamp}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### Score Reference")
        st.markdown("""
        - **Score 0 — No flags**: Neither method flagged the satellite.
        - **Score 1 — One flag**: Either ML or DM flagged the satellite.
        - **Score 2 — Both flagged**: Both methods flagged the satellite. Review first.
        """)
        
        st.caption("The score counts flags; it is not a collision probability or failure rating.")
        
        st.markdown("---")
        if st.button("Check for New Satellite Data", use_container_width=True):
            with st.spinner("Checking for new orbital data..."):
                from src.data.fetch import collect_latest_data
                from data_loader import rerun_full_pipeline
                
                # Check for GitHub token to trigger remote GitHub Action workflow
                token = os.environ.get("GITHUB_TOKEN")
                if not token:
                    try:
                        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
                            token = st.secrets["GITHUB_TOKEN"]
                    except Exception:
                        token = None
                
                gh_triggered = False
                if token:
                    try:
                        resp = requests.post(
                            "https://api.github.com/repos/Sushrut2007/discrete-math-project/actions/workflows/data_collection.yml/dispatches",
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Accept": "application/vnd.github.v3+json"
                            },
                            json={"ref": "main"},
                            timeout=10
                        )
                        if resp.status_code == 204:
                            gh_triggered = True
                    except Exception:
                        pass
                
                # Check and fetch data
                updated_file = collect_latest_data()
                if updated_file:
                    rerun_full_pipeline()
                    st.success("New data downloaded! Analysis refreshed.")
                    st.rerun()
                else:
                    if gh_triggered:
                        st.info("GitHub Action started. Local data is already up to date.")
                    else:
                        st.info("Data is already up to date. CelesTrak updates its elements every 2 hours.")

PLOTLY_CONFIG = {
    'displayModeBar': False,
    'responsive': True
}

def get_plotly_layout(height=260, title=None):
    layout = dict(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 23, 42, 0.5)',
        font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
        margin=dict(l=45, r=20, t=30 if title else 15, b=40),
        height=height,
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.06)', 
            zerolinecolor='rgba(255,255,255,0.08)'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.06)', 
            zerolinecolor='rgba(255,255,255,0.08)'
        ),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=13, color="#e2e8f0"))
    return layout
