# ML and Discrete Mathematics Based Satellite Anomaly Detection

## 1. Project Overview

This project combines Machine Learning (ML) and Discrete Mathematics (DM) to analyze satellite orbital data and identify satellites whose current orbital state is statistically unusual.

The project uses active satellite orbital data from CelesTrak. The system analyzes the orbital characteristics of satellites, groups satellites with comparable orbital characteristics, detects unusual observations using Machine Learning, and represents orbital similarity relationships using Discrete Mathematics and graph theory.

The final system does not attempt to predict collisions or determine whether a satellite is physically dangerous. Instead, it identifies statistically unusual orbital states and provides evidence that can be used for further investigation.

---

## 2. Problem

A satellite population can contain thousands of objects with different orbital characteristics.

Looking at a single satellite independently makes it difficult to determine whether its orbital state is unusual.

For example, a satellite may have:

- an unusual altitude,
- an unusual eccentricity,
- an unusual inclination,
- or an unusual combination of these parameters.

However, an unusual value does not automatically mean that something is wrong. Some satellites naturally occupy uncommon orbital regimes.

Therefore, the system needs to answer the question:

1. **Is the satellite's current orbital state unusual compared with comparable satellites?**

The project addresses this question using Machine Learning and Discrete Mathematics.

---

## 3. Main Idea

The system first analyzes the complete satellite population rather than starting with a single satellite.

The general process is:

CelesTrak satellite data  
↓  
Data preparation and feature engineering  
↓  
Group satellites with comparable orbital characteristics  
↓  
Detect unusual current orbital states using Machine Learning  
↓  
Represent orbital similarity relationships using Discrete Mathematics and graph theory  
↓  
Integrate the evidence  
↓  
Present the result to the user

The important idea is that the two sources of information have different roles:

- **Machine Learning** identifies unusual orbital observations.
- **Discrete Mathematics** represents and analyzes relationships between satellites.

These provide complementary evidence rather than completely independent forms of evidence.

---

## 4. Why Machine Learning?

The satellite population is large, and it is difficult to manually determine which combinations of orbital parameters are unusual.

Machine Learning allows the system to learn patterns from the analyzed satellite population.

The project uses:

### K-Means

K-Means groups satellites with similar orbital characteristics.

This creates comparable orbital populations so that a satellite can be evaluated relative to satellites with similar characteristics.

### Isolation Forest

Isolation Forest identifies observations that are unusual within these comparable groups.

The output provides an anomaly indication and an anomaly score for each satellite.

---

## 5. Why Discrete Mathematics?

Discrete Mathematics provides the mathematical structure used to represent relationships between satellites.

The analyzed satellites can be represented as a set:

S = {s1, s2, ..., sn}

A similarity relationship is then defined between satellites based on their selected orbital characteristics.

If two satellites have sufficiently similar orbital characteristics, they can be treated as neighbours in the orbital feature space.

These relationships can be represented as a graph:

G = (V, E)

where:

- V represents the satellites.
- E represents orbital-similarity relationships.

Graph properties can then describe how a satellite is positioned within the overall structure of the orbital population.

For example, we can examine:

- neighbouring satellites,
- how many other satellites select a satellite as a neighbour,
- distance to nearby satellites,
- and the structure of the satellite's local neighbourhood.

The graph therefore provides additional structural context for interpreting Machine Learning results.

The similarity relationship is about similarity in selected orbital characteristics. It does **not** represent physical distance between satellites in space.

---

## 6. What the Final System Produces

The system provides an integrated interpretation for satellites in the analyzed population. The final integration score ranges from 0 to 2, representing the number of components (ML and DM) that flag the satellite as unusual.

For a selected satellite, the user can see:

- satellite identification,
- current orbital information,
- orbital cluster,
- anomaly indication,
- anomaly score,
- relevant anomaly evidence,
- orbital similarity information,
- graph-based context.

Possible interpretations based on the score include:

### 0: No significant anomaly detected

The current orbital state does not provide significant unusual evidence from either component.

### 1: Rare orbit type

The current orbital state is flagged as unusual by one component (either ML or DM).

### 2: Requires investigation

Multiple sources of evidence (both ML and DM) indicate that the satellite's current orbital state is unusual and deserves further examination.

These interpretations do not prove that a satellite is malfunctioning or dangerous.

---

## 7. Project Boundaries

The system is designed for satellite orbital anomaly analysis.

It does **not**:

- predict collision probability,
- calculate physical conjunctions,
- determine whether two satellites are physically close in space,
- determine whether a detected anomaly is intentional or unintentional,
- claim that an anomalous satellite is malfunctioning,
- provide a percentage probability of danger.

The system should instead describe results as statistically unusual orbital states that may deserve further investigation.

---

## 8. Final Concept

The project can be summarized as:

**Machine Learning identifies unusual orbital patterns.**

**Discrete Mathematics represents and analyzes the relationships between satellites.**

The final system integrates these two forms of information to provide an explainable satellite anomaly-detection result.