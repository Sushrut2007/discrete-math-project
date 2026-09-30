# System Architecture

## 1. Purpose

This document describes how the different parts of the project connect together.

The system combines:

- CelesTrak satellite data
- orbital feature engineering
- Machine Learning
- Discrete Mathematics and graph theory
- temporal satellite snapshots
- result integration
- Streamlit-based user interface

The architecture is designed so that each part has a clear responsibility.

---

## 2. Overall Architecture

The complete system can be represented as:

![System Architecture Diagram](../assets/project_plan_images/system_architecture.png)

---

## 3. Data Source

The project uses active satellite orbital data from CelesTrak.

The main dataset contains orbital elements and satellite identification information.

Important fields include:

* `OBJECT_NAME`
* `OBJECT_ID`
* `EPOCH`
* `MEAN_MOTION`
* `ECCENTRICITY`
* `INCLINATION`
* `RA_OF_ASC_NODE`
* `ARG_OF_PERICENTER`
* `MEAN_ANOMALY`
* `NORAD_CAT_ID`
* `BSTAR`
* `MEAN_MOTION_DOT`
* `MEAN_MOTION_DDOT`

The initial Machine Learning and Discrete Mathematics analysis focuses mainly on:

* semi-major axis,
* eccentricity,
* inclination.

Other fields can be retained in the dataset for identification, additional analysis, or future extensions.

---

## 4. Data Collection Layer

The data collection layer obtains the latest active satellite data.

For the temporal component, multiple snapshots are stored.

Each snapshot should preserve:

* the original satellite data,
* download time,
* orbital `EPOCH`,
* NORAD catalog ID.

A simplified structure is:

```text
data/
└── raw/
    └── snapshots/
        ├── snapshot_01.csv
        ├── snapshot_02.csv
        ├── snapshot_03.csv
        └── ...
```

The raw snapshots should not be modified after collection.

This allows the processing pipeline to reproduce the temporal calculations later.

---

## 5. Preprocessing Layer

The preprocessing layer prepares the raw satellite data for analysis.

Typical operations include:

1. remove duplicate records,
2. handle missing values,
3. validate required columns,
4. convert data types where necessary,
5. remove records that cannot be used for analysis.

The goal is to create a consistent dataset for feature engineering.

---

## 6. Feature Engineering Layer

The raw orbital elements are transformed into useful physical features.

### Semi-Major Axis

Semi-major axis is derived from mean motion.

The orbital period is:

```text
T = 86400 / n
```

where:

* `T` = orbital period in seconds,
* `n` = mean motion in revolutions per day.

The semi-major axis can then be derived using the orbital relationship between period and orbital size.

The project uses the resulting semi-major axis as an important orbital feature.

---

### Other Derived Features

The feature-engineering layer can also calculate quantities such as:

* orbital height,
* orbital period,
* perigee,
* apogee,
* orbital speed.

Only features that are useful and appropriate for the final model should be retained.

---

## 7. Current Orbital Analysis

After feature engineering, the latest usable satellite snapshot becomes the main current-state dataset.

The current-state analysis answers:

> Is this satellite's current orbital state unusual compared with comparable satellites?

The pipeline is:

```text
Latest snapshot
      ↓
Feature engineering
      ↓
Standardization
      ↓
K-Means
      ↓
Orbital groups
      ↓
Cluster-specific Isolation Forest
      ↓
Current-state anomaly result
```

---

## 8. K-Means Layer

K-Means groups satellites according to their selected orbital features.

For example:

```text
Satellite population
        ↓
      K-Means
        ↓
┌───────┬───────┬───────┬───────┬───────┐
│Group 1│Group 2│Group 3│Group 4│Group 5│
└───────┴───────┴───────┴───────┴───────┘
```

The purpose of the groups is to provide comparable orbital populations.

A satellite should generally be compared with satellites occupying similar orbital regimes rather than with every satellite in the dataset.

The cluster label is therefore used as context for the anomaly detector.

---

## 9. Isolation Forest Layer

Isolation Forest is used to detect unusual observations inside the orbital groups.

Instead of applying one anomaly detector blindly to the entire population, the system can analyze satellites within their respective orbital groups.

Conceptually:

```text
Cluster 1 → Isolation Forest
Cluster 2 → Isolation Forest
Cluster 3 → Isolation Forest
Cluster 4 → Isolation Forest
Cluster 5 → Isolation Forest
```

The output includes an anomaly indication and anomaly score.

The score is used as evidence rather than as a probability of danger.

---

## 10. Discrete Mathematics Layer

The Discrete Mathematics component represents relationships between satellites.

Each satellite becomes a vertex:

```text
V = {v1, v2, ..., vn}
```

A similarity rule determines whether two satellites should be connected.

The similarity is based on selected orbital features.

For example, using standardized orbital features:

```text
x = (a, e, i)
```

the distance between satellites A and B can be represented as:

```text
D(A,B) =
√[(aA - aB)² + (eA - eB)² + (iA - iB)²]
```

The standardized values are used in the actual comparison so that differences in feature scale do not dominate the distance.

---

## 11. Similarity Graph

The similarity relationships form a graph:

```text
G = (V, E)
```

where:

* `V` = satellites,
* `E` = orbital-similarity relationships.

The project uses a nearest-neighbour approach to construct the local similarity structure.

Conceptually:

```text
             Satellite B
                  |
                  |
Satellite A — Satellite C — Satellite D
                  |
             Satellite E
```

An edge means that the satellites are similar according to the selected orbital representation.

It does **not** mean that the satellites are physically close to each other in space.

---

## 12. Graph Analysis

The graph can provide structural information such as:

* nearest neighbours,
* neighbour distances,
* incoming neighbour count,
* local neighbourhood structure,
* connected components when an appropriate threshold representation is used.

These properties provide context for interpreting a satellite's position within the orbital population.

Graph information should not automatically be interpreted as an anomaly.

For example:

```text
Low neighbour count
        ≠
Automatically anomalous
```

It becomes useful when considered together with the satellite's orbital characteristics and Machine Learning result.

---

## 13. Temporal Analysis Layer

The temporal layer uses multiple collected snapshots.

Satellites are matched using:

```text
NORAD_CAT_ID
```

For two observations of the same satellite:

```text
Δa = a₂ - a₁

Δe = e₂ - e₁

Δi = i₂ - i₁
```

The actual difference in time between the two orbital epochs is used when calculating rates.

For example:

```text
Δa_rate = (a₂ - a₁) / Δt
```

where `Δt` is the elapsed time in days.

The same approach can be applied to eccentricity and inclination.

---

## 14. Temporal Machine Learning

The temporal component asks:

> Did this satellite change unusually compared with satellites in a comparable orbital population?

The general process is:

```text
Multiple snapshots
        ↓
Match satellites by NORAD ID
        ↓
Calculate orbital changes
        ↓
Calculate change rates
        ↓
Use orbital-group context
        ↓
Temporal anomaly detection
        ↓
Recent-change evidence
```

The temporal model should compare changes with the behaviour of comparable satellites.

A decrease in altitude, for example, should not automatically be treated as an anomaly because some orbital regimes naturally experience orbital decay.

---

## 15. Fixed Reference Groups

For the initial implementation, the current orbital grouping can be used as a stable comparison context for the temporal analysis.

This avoids repeatedly changing the meaning of the groups every time a new snapshot is collected.

Conceptually:

```text
Reference snapshot
        ↓
K-Means
        ↓
Stable orbital groups
        ↓
Compare subsequent orbital changes
```

This approach can be revisited in future versions if longer-term data becomes available.

---

## 16. Evidence Integration

The final interpretation combines three main sources:

```text
Current-state ML
       +
Graph context
       +
Temporal analysis
       ↓
Integrated interpretation
```

The sources are complementary.

They should not be described as completely independent evidence because the Machine Learning and graph analysis use related orbital features.

Possible combinations include:

```text
Current state unusual
Recent change not unusual
        ↓
Rare orbit type
```

```text
Current state not unusual
Recent change unusual
        ↓
Notable orbital change
```

```text
Current state unusual
Recent change unusual
        ↓
Requires investigation
```

```text
Neither provides significant unusual evidence
        ↓
No significant anomaly detected
```

These are system interpretations rather than proof of an actual fault or danger.

---

## 17. Application Layer

The final results are passed to the Streamlit application.

The application provides two levels of information.

### Simple View

Displays:

* satellite information,
* anomaly interpretation,
* anomaly score,
* main evidence.

### Technical View

Displays:

* orbital features,
* K-Means cluster,
* Isolation Forest result,
* similarity graph,
* graph properties,
* temporal changes,
* Δa,
* Δe,
* Δi.

This separation allows the system to remain understandable while still exposing the technical basis of its results.

---

## 18. Proposed Source Structure

The project code is organized according to responsibility.

```text
src/
│
├── data/
│   └── data collection and preprocessing
│
├── features/
│   └── orbital feature engineering
│
├── ml/
│   └── K-Means and Isolation Forest
│
├── dm/
│   └── similarity relationships and graph analysis
│
├── temporal/
│   └── snapshot matching and orbital-change analysis
│
└── integration/
    └── combining ML, graph, and temporal evidence
```

The user interface is separated from the analysis code:

```text
app/
└── app.py
```

This prevents the Streamlit interface from containing the core Machine Learning and mathematical logic.

---

## 19. Complete Data Flow

The complete architecture can therefore be summarized as:

```text
                    CelesTrak
                        ↓
                 Data Collection
                        ↓
                 Preprocessing
                        ↓
                Feature Engineering
                        ↓
              Current Orbital Dataset
                        ↓
                 ┌──────┴──────┐
                 ↓             ↓
              K-Means       Snapshots
                 ↓             ↓
        Orbital Groups    Match by NORAD ID
                 ↓             ↓
        Isolation Forest   Δa, Δe, Δi
                 ↓             ↓
        Current Anomaly   Temporal Anomaly
                 ↓             ↓
                 └──────┬──────┘
                        ↓
               Similarity Graph
                        ↓
                Evidence Integration
                        ↓
                 Final Interpretation
                        ↓
                  Streamlit App
```

---

## 20. Architecture Principle

Each component answers a different question:

| Component           | Main Question                                                 |
| ------------------- | ------------------------------------------------------------- |
| CelesTrak           | What orbital data is available?                               |
| Feature Engineering | What useful orbital quantities can be derived?                |
| K-Means             | Which satellites have comparable orbital characteristics?     |
| Isolation Forest    | Which observations are unusual within those groups?           |
| Similarity Graph    | How is each satellite related to nearby orbital observations? |
| Temporal Analysis   | Has the satellite changed unusually over the observed period? |
| Integration         | What does the combined evidence indicate?                     |
| Streamlit           | How can the user investigate the result?                      |

The architecture is therefore based on a simple principle:

**Current orbital state + orbital relationships + recent change → explainable anomaly analysis**



