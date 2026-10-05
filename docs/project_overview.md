# ML and DM Based Satellite Anomaly Detection

## 1. Introduction and Problem Statement

The Earth's orbit is currently populated by over 16,000 tracked objects, including active satellites, dead payloads, and debris. Monitoring this environment traditionally relies on calculating direct physical collision probabilities. However, physical conjunction is only one part of Space Situational Awareness (SSA). 

We also need to identify **orbital anomalies**—satellites that are behaving unusually or occupy strange orbits. An anomaly could indicate:
- An active orbital maneuver (station-keeping or collision avoidance).
- A hardware failure (e.g., a satellite stranded in a transfer orbit).
- An experimental mission profile (e.g., solar sails, space tugs).
- Orbital decay due to atmospheric drag.

The goal of this project is to build an anomaly detection pipeline that does not rely on a single algorithm. Instead, it evaluates the satellite catalog through three distinct mathematical lenses:
1. **Machine Learning (ML)** for statistical deviation.
2. **Discrete Mathematics (DM)** for structural and topological isolation.
3. **Temporal Analysis** for recent behavioral shifts.

By combining these three methods, we can filter the catalog of 16,000 objects down to a small list of genuinely unusual satellites, reducing false positives and providing a clear reason for why a satellite was flagged.

---

## 2. Core Workflow

The system operates on daily snapshots of Two-Line Element (TLE) data provided by CelesTrak. 

1. **Feature Extraction:** We parse TLEs into classical Keplerian elements: Semi-major axis ($a$), Eccentricity ($e$), and Inclination ($i$). We also calculate derived physical metrics like Apogee, Perigee, and Orbital Period.
2. **Standardization:** Since altitude ranges in thousands of kilometers while eccentricity is between 0 and 1, we standardize the data using z-scores so all features share a common scale:
   $$ Z = \frac{X - \mu}{\sigma} $$
3. **Parallel Processing:** The standardized data is passed through the ML, DM, and Temporal pipelines simultaneously.
4. **Integration:** Each pipeline outputs a binary flag ($0$ or $1$). The final system tallies these flags to produce an anomaly score from $0$ to $3$.

---

## 3. Machine Learning: Statistical Orbital State

The ML pipeline identifies satellites that are statistically unusual compared to their peers. 

### How it works
If we evaluate the entire catalog at once, almost all Low Earth Orbit (LEO) satellites look normal, and all High Earth Orbit (HEO) satellites look like outliers simply because there are fewer of them. To fix this, we use a two-step approach:

1. **K-Means Clustering:** We group the catalog into $k$ distinct orbital families (clusters) based on $a, e,$ and $i$. This separates the LEOs, Medium Earth Orbits (MEOs), and Geosynchronous Orbits (GEOs) into their natural groups.
2. **Isolation Forest:** Within each specific cluster, we run an Isolation Forest algorithm. This algorithm builds random decision trees to isolate individual data points. 

### Scientific Justification
Isolation Forest works on a simple principle: **anomalies are easier to isolate**. If a satellite is deep inside a dense cluster (e.g., a standard Starlink satellite), it takes many tree splits to separate it from its neighbors. If a satellite is on the edge of the cluster, it takes very few splits. 

Satellites that require a shorter path length to isolate are given a negative anomaly score and are assigned the **ML Flag** ($F_{ML} = 1$). This means the satellite is statistically unusual *for its specific orbital regime*.

---

## 4. Discrete Mathematics: Orbital Similarity Graph

The ML pipeline looks at statistical density. The DM pipeline looks at **structural topology**. We represent the entire satellite catalog as a mathematical graph $G = (V, E)$.

### How it works
- **Vertices ($V$):** Each satellite is a node.
- **Edges ($E$):** We create a directed edge from satellite $A$ to satellite $B$ if $B$ is one of the $k=5$ nearest neighbors to $A$ in the standardized orbital feature space.
- **Distance Metric:** We use the Euclidean distance between the standardized orbital elements. 

*Note: This graph represents orbital similarity, not physical distance in space.*

### The DM Anomaly Rule
A satellite is flagged by the DM system ($F_{DM} = 1$) if it satisfies two strict conditions:
1. **In-degree is zero:** No other satellite in the entire catalog considers this satellite as one of its 5 closest neighbors.
   $$ \text{incoming\_neighbor\_count} = 0 $$
2. **High outward distance:** The mean distance to its own 5 nearest neighbors is strictly greater than the global average neighbor distance across the whole graph.
   $$ \text{mean\_neighbor\_distance} > \mu_{\text{global\_distance}} $$

### Scientific Justification
Why do we need both conditions? If we only look for an in-degree of 0, we accidentally flag satellites that are sitting on the outer edge of massive, tight clusters (like Starlink). These satellites have no incoming edges because the core satellites all point to each other, but they are still extremely close to the cluster. 

By adding the second rule, we ensure the satellite is both **unpopular** (in-degree = 0) and **genuinely isolated** (large outward distance). This successfully filters out edge-cases and finds satellites that are truly disconnected from the rest of the catalog structure.

---

## 5. Temporal Analysis: Recent Orbital Change

The ML and DM pipelines evaluate a single daily snapshot. The Temporal pipeline evaluates the satellite's history over a 7-day window.

### How it works
Satellites naturally drift due to atmospheric drag, and active satellites frequently perform station-keeping maneuvers. We cannot use a hardcoded threshold (e.g., "flag any satellite that changes altitude by 5 km") because 5 km is a massive maneuver for a GEO satellite but a completely normal daily fluctuation for an experimental LEO satellite.

Instead, we use **self-history similarity**:
1. We calculate the day-to-day changes (transitions) for each satellite:
   $$ \Delta a_t = a_t - a_{t-1} $$
   $$ \Delta e_t = e_t - e_{t-1} $$
2. We compare the *latest* transition to the satellite's *historical* transitions over the past week.
3. If the latest transition exceeds the 95th percentile of its own historical changes, we assign the **Temporal Flag** ($F_{Temp} = 1$).

### Scientific Justification
By making the satellite its own baseline, the algorithm adapts to the specific physics of that object. It ignores routine, expected drift and only triggers when a satellite does something highly unusual compared to its own recent behavior. While this flag does not definitively prove a thruster fired, it effectively highlights sudden orbital shifts.

---

## 6. Integration: The Evidence Tally

Anomaly detection in large datasets is prone to false positives. To solve this, we do not allow any single algorithm to make the final decision. 

We integrate the three pipelines using a simple evidence tally:
$$ \text{Final Score} = F_{ML} + F_{DM} + F_{Temp} $$

The result is a highly interpretable 0 to 3 scale:
*   **Score 0 (Nominal):** No detectors flagged the satellite.
*   **Score 1 (Low Warning):** Only one detector found an issue. Often a minor statistical outlier or routine maneuver.
*   **Score 2 (High Warning):** Two detectors agreed. For example, a satellite that is statistically unusual (ML) and actively changing orbit (Temporal).
*   **Score 3 (Critical):** Unanimous consensus. The satellite is statistically sparse, structurally isolated, and undergoing a sudden orbital change. 

### Summary of Benefits
This approach is extremely transparent. Unlike deep learning models ("black boxes"), this pipeline allows an operator to see exactly *why* a satellite was flagged. The integration of Discrete Mathematics provides a rigid, structural verification that standard statistical Machine Learning often misses, ensuring that only the most genuinely anomalous objects reach Score 3.
