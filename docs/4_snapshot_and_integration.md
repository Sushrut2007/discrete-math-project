# Integration

## 1. Purpose

This document explains how the current-state Machine Learning and Discrete Mathematics analysis are integrated.

---

# Part A — Graph Integration

## 2. Role of the Similarity Graph

The similarity graph provides structural context around the satellite.

The graph is constructed using selected orbital features.

It can provide information such as:

* similar satellites,
* nearest-neighbour distances,
* incoming neighbour count,
* local graph structure.

The graph does not replace the anomaly detector.

Instead:

```text
ML result
    +
Graph context
```

are used together.

---

## 3. Complementary Evidence

The two components should be interpreted as complementary evidence.

They are not statistically independent because the current-state ML and graph analysis use related orbital features.

Therefore, the system should avoid statements such as:

```text
2 independent models detected the anomaly
```

Instead, use wording such as:

```text
Multiple complementary indicators support further investigation.
```

---

# Part B — Evidence Integration

## 4. Integration Inputs

The integration layer receives:

### Current-state ML

* cluster label,
* anomaly indication,
* anomaly score,
* unusual features.

### Graph

* similar satellites,
* neighbour information,
* graph properties,
* local structural context.

---

## 5. Interpretation Matrix

The initial interpretation logic can be represented with an integration score ranging from 0 to 2:

| Score | Meaning | Interpretation                  |
| ----- | ------- | ------------------------------- |
| 0     | Neither component is unusual | No significant anomaly detected |
| 1     | Only one component is unusual | Rare orbit type |
| 2     | Both components are unusual | Requires investigation |

The graph information is used as supporting context alongside ML.

---

## 6. Why the Graph is Not a Simple Boolean Rule

It would be incorrect to define:

```text
Low graph degree → anomaly
```

or:

```text
Large neighbour distance → anomaly
```

These properties only describe the satellite's position within the orbital feature distribution.

The graph should therefore be presented as evidence that helps explain the ML result.

---

# Part C — Final Result

## 7. Example Result

A selected satellite could produce:

```text
Satellite:
NORAD 12345

Integration Score:
2

Current-state analysis:
Unusual

Graph context:
Located in a relatively sparse region of
the orbital feature space

Interpretation:
Requires investigation
```

Another satellite could produce:

```text
Satellite:
NORAD 67890

Integration Score:
1

Current-state analysis:
Unusual

Graph context:
Comparable satellites are present nearby
in orbital feature space

Interpretation:
Rare orbit type
```

The result describes the evidence observed by the system.

---

# Part D — Complete Pipeline

## 8. Final Pipeline

The complete workflow is:

```text
CelesTrak
    ↓
Collect data
    ↓
Build orbital features
    ↓
Group by orbital context
    ↓
Anomaly detection
    ↓
Graph context analysis
    ↓
Evidence integration
    ↓
Final interpretation
```

---

## 9. Key Takeaway

The combination of current-state analysis and orbital-similarity structure provides an informative basis for investigating unusual satellite behaviour.
