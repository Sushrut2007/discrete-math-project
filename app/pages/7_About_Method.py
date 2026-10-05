import streamlit as st

st.set_page_config(page_title="About / Method", layout="wide")

st.title("About / Method")
st.markdown("### System Pipeline")
st.code("""
CelesTrak satellite data
         ↓
Orbital features
         ↓
┌──────────────┬──────────────┬──────────────┐
│      ML      │      DM      │   Temporal   │
│ Current      │ Similarity   │ Recent       │
│ orbital      │ graph        │ orbital      │
│ state        │              │ change       │
└──────────────┴──────────────┴──────────────┘
                   ↓
            0–3 final score
""", language="text")

st.markdown("""
- **ML:** Evaluates the current orbital state against K-Means derived orbital families.
- **DM:** Evaluates topological isolation using a directed 5-Nearest Neighbour similarity graph.
- **Temporal:** Evaluates recent sequential orbital changes against the satellite's own historical transitions.

The **final score** is a simple count of how many methods flagged the satellite (from 0 to 3).
""")

st.markdown("---")
st.markdown("### Limitations")
st.warning("""
- An anomaly means unusualness, not necessarily danger.
- The DM graph represents orbital similarity, not physical distance.
- A temporal flag does not prove a maneuver occurred.
- The system does not directly calculate collision probability.
- The temporal analysis covers only the available recent observation window.
- The final score is an evidence count from the three methods, not a probability that something is wrong.
""")
