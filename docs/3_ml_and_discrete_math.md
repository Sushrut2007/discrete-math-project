# Machine Learning and Discrete Mathematics

## 1. Purpose

This document explains the Machine Learning and Discrete Mathematics concepts used in the project.

The goal is not only to describe the algorithms, but to explain:

- what each concept means,
- why it is needed,
- how it is used in this project,
- and how the different concepts connect.

The main technical components are:

- feature representation,
- standardization,
- K-Means clustering,
- Isolation Forest,
- similarity relations,
- k-Nearest Neighbours,
- graph construction,
- graph analysis,
- combinatorics,
- and the relationship between ML and Discrete Mathematics.

---

# Part A — Machine Learning

## 2. What is Machine Learning in This Project?

The satellite dataset contains many observations.

Each satellite can be represented using numerical orbital features such as:

- semi-major axis,
- eccentricity,
- inclination,
- orbital height,
- orbital period,
- and other selected features.

The Machine Learning system attempts to discover patterns in these observations without requiring a manually labelled dataset of anomalous satellites.

This project therefore uses **unsupervised anomaly detection**.

The basic idea is:

```text
Satellite data
      ↓
Find comparable orbital groups
      ↓
Find unusual observations inside those groups
```

---

## 3. Feature Representation

A satellite can be represented as a vector of numerical features.

For example:

```text
Satellite A =
(a, e, i)
```

where:

* `a` = semi-major axis,
* `e` = eccentricity,
* `i` = inclination.

A larger feature vector can also be used:

```text
Satellite A =
(a, e, i, orbital_height, orbital_period, ...)
```

This numerical representation allows Machine Learning algorithms to compare satellites mathematically.

---

## 4. Why Standardization is Required

Different orbital features have very different numerical scales.

For example:

```text
Semi-major axis → thousands of kilometres
Eccentricity    → values close to 0
Inclination     → degrees
```

If these values were used directly in distance-based algorithms, the feature with the largest numerical scale could dominate the distance calculation.

Therefore, the selected numerical features are standardized.

A common standardization formula is:

```text
z = (x - μ) / σ
```

where:

* `x` = original feature value,
* `μ` = mean of the feature,
* `σ` = standard deviation,
* `z` = standardized value.

After standardization, the features are placed on a comparable scale.

---

# Part B — K-Means Clustering

## 5. What is K-Means?

K-Means is an unsupervised clustering algorithm.

Its purpose is to divide observations into `K` groups based on their feature similarity.

In this project, the groups represent satellites with comparable orbital characteristics.

For example:

```text
All satellites
      ↓
    K-Means
      ↓
┌─────┬─────┬─────┬─────┬─────┐
│ C1  │ C2  │ C3  │ C4  │ C5  │
└─────┴─────┴─────┴─────┴─────┘
```

The project initially uses:

```text
K = 5
```

---

## 6. How K-Means Works

K-Means works by assigning observations to cluster centres called **centroids**.

The basic process is:

1. Choose `K` initial centroids.
2. Calculate the distance between each satellite and each centroid.
3. Assign each satellite to its nearest centroid.
4. Recalculate each centroid.
5. Repeat the assignment and centroid calculation.
6. Stop when the clusters stabilize.

Conceptually:

```text
Satellite
    ↓
Calculate distance to centroids
    ↓
Choose nearest centroid
    ↓
Assign cluster
```

---

## 7. Why K-Means is Used Here

The entire satellite population contains different orbital regimes.

Comparing every satellite directly with every other satellite may not provide a useful definition of unusual behaviour.

For example, a low-Earth-orbit satellite should not necessarily be compared in the same way with a satellite from a very different orbital regime.

K-Means provides groups of comparable satellites.

Therefore:

```text
K-Means
   ↓
Comparable orbital population
   ↓
Isolation Forest
```

---

# Part C — Isolation Forest

## 8. What is Anomaly Detection?

An anomaly is an observation that differs significantly from the patterns observed in the analyzed population.

In this project, the system is looking for satellites whose orbital feature combinations are unusual.

Importantly:

**Unusual does not automatically mean wrong.**

A satellite can legitimately occupy a rare orbit.

The system therefore identifies observations that deserve further examination rather than proving that something is wrong.

---

## 9. What is Isolation Forest?

Isolation Forest is an unsupervised anomaly-detection algorithm.

Its basic idea is that unusual observations are easier to isolate from the rest of the data.

Consider:

```text
Normal observations:

● ● ● ●
 ● ● ●
● ● ● ●


Unusual observation:

● ● ● ●
 ● ● ●
● ● ● ●                 X
```

The isolated point `X` can usually be separated using fewer random partitioning steps.

Therefore, observations that are easier to isolate are treated as more unusual.

---

## 10. Why Use Isolation Forest After K-Means?

The project uses the following structure:

```text
Satellite population
        ↓
     K-Means
        ↓
Orbital groups
        ↓
Isolation Forest
        ↓
Anomaly detection
```

The reason is that anomaly detection becomes more meaningful when satellites are compared within comparable orbital groups.

For example:

```text
Cluster 1 → Isolation Forest
Cluster 2 → Isolation Forest
Cluster 3 → Isolation Forest
...
```

This produces a cluster-specific anomaly result.

---

## 11. Anomaly Score

Isolation Forest produces a numerical score related to how unusual an observation is.

The exact implementation and score interpretation depend on the model configuration.

The project should use the score as an **anomaly indicator**, not as:

```text
Probability of danger
```

or:

```text
Probability of collision
```

The score describes unusualness within the analyzed dataset.

---

# Part D — Discrete Mathematics

## 12. Why Discrete Mathematics?

Machine Learning identifies unusual orbital observations.

Discrete Mathematics provides a formal way to represent relationships between satellites.

The satellites can be represented as a set:

```text
S = {s₁, s₂, s₃, ..., sₙ}
```

Each element of the set represents one satellite.

We then define a relationship based on orbital similarity.

---

## 13. Relations

A relation defines how elements of a set are connected to one another.

For satellites, we can define:

```text
A R B
```

to mean:

> Satellite A is sufficiently similar to satellite B according to the selected orbital features.

The exact definition of similarity is determined by the project.

---

## 14. Similarity is Not an Equivalence Relation

It is important not to confuse the orbital-similarity relation with an equivalence relation.

For example, if:

```text
A is similar to B
B is similar to C
```

it does not necessarily follow that:

```text
A is similar to C
```

Therefore, the similarity relation is generally **not transitive**.

It can be:

* reflexive, depending on the definition,
* symmetric,
* but not necessarily transitive.

Therefore, it should be treated as a **similarity/tolerance relationship**, not as an equivalence relation.

---

# Part E — Orbital Similarity

## 15. Feature Space

For the core similarity representation, the project uses selected orbital characteristics such as:

```text
(a, e, i)
```

where:

* `a` = semi-major axis,
* `e` = eccentricity,
* `i` = inclination.

After standardization, a satellite can be represented as:

```text
x = (ã, ẽ, ĩ)
```

where the tilde indicates standardized values.

---

## 16. Distance Between Satellites

The similarity between two satellites can be represented using Euclidean distance.

For satellites A and B:

```text
D(A,B) =
√[(ãA - ãB)²
 + (ẽA - ẽB)²
 + (ĩA - ĩB)²]
```

A smaller distance means that the satellites are more similar according to this representation.

A larger distance means that their selected orbital characteristics are more different.

---

## 17. Important Interpretation

This distance represents **orbital-feature similarity**.

It does not represent:

* physical distance between satellites,
* collision probability,
* conjunction probability,
* or actual spatial separation.

For example:

```text
Small orbital-feature distance
            ≠
Physical proximity
```

Two satellites can have similar orbital parameters while being at very different positions along their orbits.

---

# Part F — k-Nearest Neighbours

## 18. What is kNN?

The k-Nearest Neighbours approach identifies the `k` closest observations to each satellite according to the chosen distance measure.

For example, if:

```text
k = 5
```

the system identifies the five nearest satellites in the selected orbital feature space.

Conceptually:

```text
                 B
                 |
                 |
           A --- X --- C
                 |
                 |
                 D

X = selected satellite
A, B, C, D = nearby satellites
```

The actual graph can contain `k` neighbours for each satellite.

---

## 19. Why Use kNN?

Satellite populations may have regions with different densities.

A single global distance threshold can behave differently in dense and sparse regions.

For example:

```text
Dense region:

● ● ● ● ● ● ●


Sparse region:

●          ●          ●
```

A fixed threshold may create very different graph structures in these two regions.

kNN instead gives every satellite a local set of nearest neighbours.

This makes it useful for representing local orbital structure.

---

# Part G — Graph Theory

## 20. Graph Representation

The satellite similarity relationships can be represented as a graph:

```text
G = (V, E)
```

where:

* `V` = set of satellite vertices,
* `E` = set of similarity edges.

Example:

```text
      B
      |
      |
A --- C --- D
      |
      E
```

Each node represents a satellite.

Each edge represents an orbital-similarity relationship.

---

## 21. Directed or Undirected Interpretation

A kNN relationship can naturally be represented as a directed relationship:

```text
A → B
```

meaning:

> B is one of A's nearest neighbours.

It does not necessarily mean:

```text
B → A
```

because A may not be among B's nearest neighbours.

Therefore, the implementation should explicitly decide whether it uses:

* a directed kNN graph,
* or a symmetrized graph.

For neighbour-selection analysis, the directed interpretation is particularly useful because it allows us to measure how many other satellites select a given satellite as a neighbour.

---

## 22. Incoming Neighbour Count

For a directed kNN graph, we can count how many satellites choose a given satellite as one of their neighbours.

For satellite A:

```text
Incoming neighbour count(A)
=
number of satellites that select A
```

This can provide information about how centrally located A is within the local orbital feature distribution.

A low incoming-neighbour count means that relatively few satellites consider A to be among their closest neighbours.

However:

```text
Low neighbour count
        ≠
Anomaly
```

It is only one piece of structural evidence.

---

## 23. Neighbour Distance

The distance from a satellite to its nearest neighbours can also be examined.

For example:

```text
Satellite A

Nearest neighbour distance = d₁
2nd nearest distance       = d₂
...
k-th nearest distance      = dₖ
```

A large distance to nearby neighbours can indicate that the satellite occupies a relatively sparse region of the selected orbital feature space.

Again, this does not automatically mean that the satellite is anomalous.

---

## 24. Local Graph Structure

The graph allows us to examine the local neighbourhood of a satellite.

For example:

```text
             B
             |
             |
       A --- X --- C
             |
             D
```

For `X`, we can examine:

* its nearest neighbours,
* neighbour distances,
* incoming neighbour count,
* and local structure.

This gives structural context to the Machine Learning result.

---

# Part H — Combinatorics

## 25. Number of Possible Satellite Pairs

For `n` satellites, the number of possible unordered pairs is:

```text
C(n,2) = n(n-1)/2
```

This is a basic combinatorial result.

For example, if there are 4 satellites:

```text
C(4,2)
= 4 × 3 / 2
= 6
```

The six possible pairs are:

```text
(A,B)
(A,C)
(A,D)
(B,C)
(B,D)
(C,D)
```

---

## 26. Why Combinatorics Matters

The number of possible satellite relationships grows rapidly as the number of satellites increases.

For a large satellite population, explicitly checking every possible pair becomes expensive.

This helps motivate the use of nearest-neighbour methods rather than constructing a full pairwise similarity matrix.

The combinatorial calculation is therefore mainly used to explain the scale of the relationship problem.

It is not itself an anomaly-detection method.

---

# Part I — Machine Learning + Discrete Mathematics

## 27. Why Combine Them?

The two approaches answer different questions.

### Machine Learning

Asks:

> Which satellite observations are unusual?

### Graph / Discrete Mathematics

Asks:

> How is a satellite positioned relative to other satellites in the orbital feature space?

Together:

```text
             Satellite
                 |
        ┌────────┴────────┐
        ↓                 ↓
   ML Analysis       Graph Analysis
        ↓                 ↓
  Unusualness       Relationship
        ↓                 ↓
        └────────┬────────┘
                 ↓
        Complementary evidence
```

---

## 28. They Are Not Independent Evidence

The Machine Learning and graph components use related orbital features.

For example, both may use:

```text
(a, e, i)
```

Therefore, if both systems identify something unusual, this should not be described as two statistically independent detections.

Instead, the project uses the terms:

* complementary evidence,
* converging evidence,
* supporting evidence.

---

# Part J — Putting Everything Together

## 29. Complete Technical Chain

The complete technical logic is:

```text
CelesTrak data
      ↓
Feature engineering
      ↓
Standardization
      ↓
K-Means
      ↓
Comparable orbital groups
      ↓
┌─────────────────────────────┐
│                             │
↓                             ↓
Isolation Forest          Similarity / kNN
│                             │
↓                             ↓
Current-state anomaly      Graph evidence
│                             │
└──────────────┬──────────────┘
               │
               ↓
      Evidence integration
               ↓
       Final interpretation
```

---

## 30. Final Interpretation

The system can produce interpretations such as:

### 0: No significant anomaly detected

The available evidence does not indicate a significant unusual orbital state from either component.

### 1: Rare orbit type

The current orbital state is unusual according to one component.

### 2: Requires investigation

Multiple sources of evidence indicate that the satellite deserves further examination.

These interpretations describe the output of the analysis.

They do not establish that a satellite is malfunctioning or dangerous.

---

## 31. Important Distinctions

The following concepts must not be confused:

| Concept               | Meaning                                             |
| --------------------- | --------------------------------------------------- |
| Orbital anomaly       | Statistically unusual orbital observation           |
| Orbital similarity    | Similarity in selected orbital features             |
| Physical proximity    | Actual spatial distance between satellites          |
| Conjunction           | A predicted close approach in space and time        |
| Collision probability | Probability associated with a conjunction           |
| Risk assessment       | Broader evaluation of potential consequences        |

This project focuses on **orbital anomaly detection**.

It does not perform conjunction prediction or collision-probability calculation.

---

## 32. Key Takeaway

The project's technical idea can be summarized as:

> **Machine Learning detects unusual orbital patterns, while Discrete Mathematics represents the relationships between satellites and provides structural context.**

The two components are then integrated to produce an explainable anomaly-detection result.
