import streamlit as st
import pandas as pd
from data_loader import load_full_data
from theme import apply_theme, render_sidebar

st.set_page_config(
    page_title="Methodology & Architecture",
    page_icon="📐",
    layout="wide"
)

apply_theme()
df = load_full_data()
render_sidebar(df)

# Header
st.markdown('<div class="page-title">Methodology & Architecture</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Formulas, pipeline steps, and project limitations.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Architecture Diagram
st.markdown("### System Pipeline Architecture")
st.markdown("""
<div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
""", unsafe_allow_html=True)

st.mermaid("""
graph TD
    A["Raw CelesTrak TLE Data<br>(16,000+ Active Satellites)"] --> B["Orbital Feature Calculation<br>(period, speed, height, semi-major axis)"]
    B --> C["Standardized 6D Feature Space"]
    
    C --> D["Branch 1: Machine Learning"]
    C --> E["Branch 2: Discrete Mathematics"]
    
    D --> D1["K-Means Clustering<br>(Orbital Groups)"]
    D1 --> D2["Isolation Forest<br>(Within each cluster)"]
    D2 --> D3["ML Flag: 0 or 1"]
    
    E --> E1["Directed 5-NN Graph<br>(5 arrows per node)"]
    E1 --> E2["Graph Checks<br>(In-degree = 0 & Distance > mean)"]
    E2 --> E3["DM Flag: 0 or 1"]
    
    D3 --> F["Final Score = ML Flag + DM Flag (0, 1, or 2)"]
    E3 --> F
    
    F --> G["Streamlit Web App"]
    
    style A fill:#1e293b,stroke:#475569,stroke-width:1px,color:#f8fafc
    style B fill:#1e293b,stroke:#475569,stroke-width:1px,color:#f8fafc
    style C fill:#334155,stroke:#64748b,stroke-width:1px,color:#f8fafc
    style D fill:#1e1b4b,stroke:#4f46e5,stroke-width:1px,color:#f8fafc
    style E fill:#082f49,stroke:#0284c7,stroke-width:1px,color:#f8fafc
    style F fill:#312e81,stroke:#6366f1,stroke-width:2px,color:#f8fafc
    style G fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#f8fafc
""")

st.markdown("</div>", unsafe_allow_html=True)

# Mathematical Framework
st.markdown("### Mathematical Formulations")

col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown("""
    #### 1. Machine Learning Component
    
    Each satellite has a normalized feature vector:
    $$\\mathbf{x} = [a, e, i, T, v_{\\text{orb}}, h] \\in \\mathbb{R}^6$$
    
    **Step 1: K-Means Clustering**  
    Splits satellites into $K$ orbital clusters $S_k$ by minimizing squared distances:
    $$\\arg\\min_S \\sum_{k=1}^K \\sum_{\\mathbf{x} \\in S_k} \\|\\mathbf{x} - \\boldsymbol{\\mu}_k\\|^2$$
    
    **Step 2: Intra-Cluster Isolation Forest**  
    Inside each cluster, isolation trees recursively split features. The anomaly score is:
    $$s(\\mathbf{x}) = 2^{-\\frac{E(h(\\mathbf{x}))}{c(n)}}$$
    where $E(h(\\mathbf{x}))$ is average tree depth to isolate $\\mathbf{x}$, and $c(n)$ is the average depth of an unsuccessful search in a BST.
    
    $$F_{\\text{ML}} = \\begin{cases} 1 & \\text{if score is below cluster threshold} \\\\ 0 & \\text{otherwise} \\end{cases}$$
    """)

with col_m2:
    st.markdown("""
    #### 2. Discrete Mathematics Graph Component
    
    We build a directed graph $G = (V, E)$ where vertices $V$ are satellites ($|V| = 16,612$).
    
    **Directed Edges:**  
    An edge $(u, v) \\in E$ means satellite $v$ is among the $k=5$ nearest neighbors of $u$ in standardized orbital feature space:
    $$E = \\{(u, v) \\in V \\times V : v \\in N_5(u)\\}$$
    Each node has out-degree exactly $d^+(u) = 5$.
    
    **In-Degree & Mean Distance:**  
    In-degree $d^-(v)$ is how many satellites point to $v$:
    $$d^-(v) = |\\{u \\in V : (u, v) \\in E\\}|$$
    The mean neighbor distance is:
    $$\\bar{d}(v) = \\frac{1}{5} \\sum_{w \\in N_5(v)} \\|\\mathbf{x}_v - \\mathbf{x}_w\\|$$
    
    **DM Flag Rule:**
    $$F_{\\text{DM}} = \\begin{cases} 1 & \\text{if } d^-(v) = 0 \\;\\land\\; \\bar{d}(v) > \\mu_{\\text{global}} \\\\ 0 & \\text{otherwise} \\end{cases}$$
    """)

st.markdown("---")

# Synthesis and Limitations
st.markdown("### Scoring and Project Limitations")

c_int, c_lim = st.columns(2)

with c_int:
    st.markdown("""
    #### Final Score Formula
    The integration score is just the sum of the flags:
    $$\\text{Score} = F_{\\text{ML}} + F_{\\text{DM}} \\in \\{0, 1, 2\\}$$
    
    - **Score 0:** Neither method flagged the satellite (Normal).
    - **Score 1:** Flagged by one method (Worth checking).
    - **Score 2:** Flagged by both methods (Highest priority for review).
    """)

with c_lim:
    st.markdown("""
    #### Important Limitations
    - **Not a danger rating:** The score is a count of methods that found the satellite unusual. It is **not** a probability of collision or failure.
    - **Orbital similarity vs. physical space:** The graph connects satellites with similar orbital parameters, **not** satellites that are currently close to each other in physical space.
    - **Shared features:** ML and DM use some of the same orbital features ($a, e, i$), so they are complementary checks, not completely independent tests.
    """)
