## 1. The Problem Space (Why we are doing this)

Low Earth Orbit (LEO) is getting dangerously crowded. If we aren't careful, we risk triggering **Kessler Syndrome**—a theoretical scenario where a single collision creates a cloud of debris, which hits other satellites, creating an unstoppable cascade of destruction that could make space completely unusable.

Right now, standard systems try to prevent this by using physics to predict direct collisions. But that's not enough. We want to catch satellites *before* they become a collision risk. We need to find **anomalies**. 

To us, an "anomaly" simply means a satellite that is behaving weirdly. Maybe a dead satellite is tumbling into a strange orbit, or a military satellite is quietly firing thrusters to change its path.

### The 3 Core Features
We don't track X, Y, Z spatial coordinates. We track the **shape** of the orbit using three classical elements:
1.  **Semi-major axis ($a$):** The size/average altitude of the orbit.
2.  **Eccentricity ($e$):** How circular or oval-shaped the orbit is.
3.  **Inclination ($i$):** The tilt of the orbit relative to the equator.

**Crucial Step - Standardization:** Because altitude is measured in thousands of kilometers and eccentricity is a tiny decimal, we cannot do math on them directly. We use z-scores to standardize these features into a common scale ($std\_a$, $std\_e$, $std\_i$).

---

## 2. The Overall Workflow

The pipeline runs on daily data snapshots from CelesTrak. Every satellite passes through two independent mathematical checks.

```mermaid
flowchart TD
    A[Raw CelesTrak Data: 16,000+ Satellites] --> B[Extract & Standardize: a, e, i]
    
    B --> C[1. Machine Learning: Statistical Check]
    B --> D[2. Static DM: Structural Graph]
    
    C -->|Flag 0 or 1| F[Integration: Final Tally]
    D -->|Flag 0 or 1| F
    
    F --> G[Final Anomaly Score: 0 to 2]
```

---

## 3. Component 1: Machine Learning (The Statistical Check)

This component uses statistical density to find satellites that do not fit in with their peers.

*   **Step 1 (K-Means Clustering):** We cannot compare a high-altitude weather satellite to a low-altitude Starlink. K-Means divides the entire catalog into distinct orbital families based on their features.
*   **Step 2 (Isolation Forest):** Within each specific family, we run an Isolation Forest algorithm. If a satellite is sitting in a sparse, empty region on the edge of the cluster, the algorithm easily isolates it.
*   **The Result:** If the algorithm isolates the satellite easily, it outputs an anomaly flag of `1`. Otherwise, `0`. 

---

## 4. Component 2: The Orbital Similarity Graph (Static DM)

This component uses Discrete Mathematics to map the exact structural relationships between satellites. We build a massive mathematical graph representing the "social network" of orbits.

### DM Concepts & How We Use Them:
*   **Sets & Elements:** In DM, a Set ($S$) is a collection of objects. Here, our universal set is the catalog of 16,000 satellites. Each individual satellite is an element ($x \in S$).
*   **Binary Relations:** A relation defines how elements in a set connect to each other. We define a relationship based on mathematical distance. 
*   **Directed k-Nearest Neighbor (k-NN) Graph:** We map this relation as a Digraph $G = (V, E)$, where the satellites are the Vertices ($V$). We calculate the Euclidean distance between every satellite's features. Then, using a k-NN approach (with $k=5$), every satellite draws a one-way directed Edge ($E$) to its 5 closest mathematical neighbors. Because it is a directed graph, relationships are asymmetric: Satellite A might point to B, but B doesn't have to point back to A.

### The Flagging Rule (Producing the Score):
We evaluate two specific graph properties for a satellite $v$:
1.  **Node In-Degree ($\text{deg}^-(v)$):** The number of incoming arrows pointing *at* the satellite.
2.  **Mean Outward Distance ($\text{mean\_dist}(v)$):** The average length of the 5 arrows the satellite points outward. If this number is small, the satellite is sitting right next to a cluster. If it is large, the satellite is floating out in the middle of nowhere, and even its "closest" neighbors are actually extremely far away.

The logic outputs a `1` (Anomaly) **only if both** conditions are met:
$$ \text{deg}^-(v) = 0 \quad \textbf{AND} \quad \text{mean\_dist}(v) > \mu_{\text{global\_dist}} $$

*Why both?* If a satellite has an In-Degree of 0, but its mean outward distance is tiny, it just means it is sitting on the absolute edge of a dense Starlink cluster (the Starlinks all point at each other inside the cluster, ignoring the edge). We only flag it if nobody points at it **AND** its mean outward distance is large, mathematically proving it is truly isolated in space.

---

## 5. Integration: The Final Score

Since no algorithm is perfect, we don't rely on just one. We just add the two flags together to get a final score:
$$ \text{Final Score} = F_{\text{ML}} + F_{\text{DM}} $$

*   **Score 0:** Neither ML nor DM flagged the satellite.
*   **Score 1:** Either ML or DM flagged the satellite.
*   **Score 2:** Both ML and DM flagged the satellite. This gives it the highest priority for investigation.

The main reason we do this is to get rid of false alarms. A normal satellite might accidentally fail one math check, but it is basically impossible for a normal satellite to accidentally fail both different equations at the exact same time. Note that ML and DM use some of the same orbital features, so they are not completely independent methods.
