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
st.markdown('<div class="page-title">Methodology & System Architecture</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Formal mathematical framework, pipeline architecture, and analytical limitations.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Architecture Diagram
st.markdown("### System Pipeline Architecture")
st.markdown("""
<div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
""", unsafe_allow_html=True)

st.mermaid("""
graph TD
    A["Raw CelesTrak TLE Catalog<br>(16,000+ Active Objects)"] --> B["Orbital Feature Engineering<br>(a, e, i, period, speed, height)"]
    B --> C["Standardized 6D Feature Space"]
    
    C --> D["Branch 1: Machine Learning"]
    C --> E["Branch 2: Discrete Mathematics"]
    
    D --> D1["K-Means Clustering<br>(Orbital Families)"]
    D1 --> D2["Intra-Cluster Isolation Forest<br>(Recursive Tree Partitioning)"]
    D2 --> D3["ML Flag: F_ML ∈ {0, 1}"]
    
    E --> E1["Directed k-NN Graph G = (V, E)<br>(k = 5 Out-Degree)"]
    E1 --> E2["Topological Analysis<br>(In-Degree & Mean Distance)"]
    E2 --> E3["DM Flag: F_DM ∈ {0, 1}"]
    
    D3 --> F["Score Integration: Score = F_ML + F_DM ∈ {0, 1, 2}"]
    E3 --> F
    
    F --> G["Mission Dashboard & Deep-Dive Explorer"]
    
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
st.markdown("### Formal Mathematical Framework")

col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown("""
    #### 1. Machine Learning Formulation
    
    Each satellite is mapped to a standardized orbital feature vector:
    $$\\mathbf{x} = [a, e, i, T, v_{\\text{orb}}, h] \\in \\mathbb{R}^6$$
    
    **Stage 1: K-Means Clustering**  
    Partitions the catalog $V$ into $K$ disjoint orbital clusters $S = \\{S_1, S_2, \\dots, S_K\\}$ minimizing within-cluster variance:
    $$\\arg\\min_S \\sum_{k=1}^K \\sum_{\\mathbf{x} \\in S_k} \\|\\mathbf{x} - \\boldsymbol{\\mu}_k\\|^2$$
    
    **Stage 2: Intra-Cluster Isolation Forest**  
    Within each cluster $S_k$, an ensemble of $T$ isolation trees recursively isolates samples. The anomaly score is defined as:
    $$s(\\mathbf{x}, |S_k|) = 2^{-\\frac{E(h(\\mathbf{x}))}{c(|S_k|)}}$$
    where $E(h(\\mathbf{x}))$ is the average path length and $c(n)$ is the average path length of unsuccessful searches in BSTs.
    
    $$F_{\\text{ML}}(\\mathbf{x}) = \\begin{cases} 1 & \\text{if } s(\\mathbf{x}) \\text{ exceeds cluster threshold} \\\\ 0 & \\text{otherwise} \\end{cases}$$
    """)

with col_m2:
    st.markdown("""
    #### 2. Discrete Mathematics Graph Formulation
    
    Let $V$ represent the set of satellites ($|V| = 16,612$). We construct a directed graph $G = (V, E)$.
    
    **Directed Edge Set:**  
    An edge $(u, v) \\in E$ exists if and only if $v$ is among the $k=5$ nearest neighbors of $u$ in standardized Euclidean orbital space:
    $$E = \\{(u, v) \\in V \\times V : v \\in N_k(u)\\}$$
    Each vertex has out-degree exactly $d^+(u) = k = 5$.
    
    **In-Degree & Distance:**  
    The in-degree $d^-(v)$ counts how many satellites select $v$ as a nearest neighbor:
    $$d^-(v) = |\\{u \\in V : (u, v) \\in E\\}|$$
    The mean neighbor distance is:
    $$\\bar{d}(v) = \\frac{1}{k} \\sum_{w \\in N_k(v)} \\|\\mathbf{x}_v - \\mathbf{x}_w\\|$$
    
    **Topological Isolation Flag:**
    $$F_{\\text{DM}}(v) = \\begin{cases} 1 & \\text{if } d^-(v) = 0 \\;\\land\\; \\bar{d}(v) > \\mu_{\\text{global}} \\\\ 0 & \\text{otherwise} \\end{cases}$$
    """)

st.markdown("---")

# Synthesis and Limitations
st.markdown("### Integration Model & Engineering Disclosures")

c_int, c_lim = st.columns(2)

with c_int:
    st.markdown("""
    #### Additive Integration Model
    The combined anomaly priority score is the sum of concordant indicators:
    $$\\text{Score}(v) = F_{\\text{ML}}(v) + F_{\\text{DM}}(v) \\in \\{0, 1, 2\\}$$
    
    - **Score 0:** Neither model flagged the object. Standard nominal trajectory.
    - **Score 1:** Flagged by either ML (density outlier) or DM (graph isolation). Added to moderate review queue.
    - **Score 2:** Flagged concurrently by both models. Highest priority for radar tasking and manual ephemeris inspection.
    """)

with c_lim:
    st.markdown("""
    #### Scope Limitations & Scientific Boundaries
    - **Evidence Tally, Not Probability:** The score represents the count of methods that detected atypical orbital properties. It is **not** a probability of collision or failure.
    - **Orbital Parameter Space:** The DM graph models topological similarity in standardized parameter space, **not** instantaneous physical distance between satellites in orbit.
    - **Feature Overlap:** ML and DM share fundamental orbital elements ($a, e, i$). Therefore, they are described as **complementary lenses**, not purely independent random variables.
    """)
