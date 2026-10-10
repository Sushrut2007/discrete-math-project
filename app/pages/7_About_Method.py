import streamlit as st

st.set_page_config(page_title="About / Method", layout="wide")

st.title("About / Method")
st.markdown("### System Pipeline")
st.code("""
CelesTrak satellite data
         |
Orbital features
         |
+--------------+--------------+
|      ML      |      DM      |
| Current      | Similarity   |
| orbital      | graph        |
| state        |              |
+--------------+--------------+
                   |
            0-2 final score
""", language="text")

st.markdown("""
- **ML:** Evaluates the current orbital state against K-Means derived orbital families.
- **DM:** Evaluates topological isolation using a directed 5-Nearest Neighbour similarity graph.

The **final score** is a simple count of how many methods flagged the satellite (from 0 to 2).
""")

st.markdown("---")
st.markdown("### Limitations")
st.warning("""
- An anomaly means unusualness, not necessarily danger.
- The DM graph represents orbital similarity, not physical distance.
- The system does not directly calculate collision probability.
- The final score is an evidence count from the two methods, not a probability that something is wrong.
- ML and DM use some of the same orbital features, so they are not completely independent methods.
""")
