# 06 — Development and Validation

## 1. Purpose

This document defines how the **ML and Discrete Mathematics Based Satellite Anomaly Detection** system will be developed, tested, and validated.

The goal is not only to make the pipeline run, but to verify that:

* the orbital features are calculated correctly,
* the ML anomaly detector behaves as intended,
* the discrete-mathematics components provide meaningful orbital-relationship information,
* temporal changes are calculated correctly,
* the different components integrate without producing misleading conclusions.

The system should report **statistically unusual orbital patterns** rather than claiming that a satellite is definitively anomalous.

---

# 2. Development Phases

Development will proceed incrementally rather than implementing the entire system at once.

### Phase 1 — Environment and project setup

Set up:

* Python 3.12 environment
* project directory structure
* dependencies
* Git repository
* test structure
* raw and processed data directories

The main environment will be:

```text
dm_env
```

---

### Phase 2 — Data collection and snapshots

Implement the CelesTrak data collector.

The system will:

1. retrieve the current satellite dataset,
2. save the raw snapshot,
3. record the collection time,
4. retain previous snapshots instead of overwriting them.

The temporal dataset will therefore develop as:

```text
data/raw/snapshots/

snapshot_01.csv
snapshot_02.csv
snapshot_03.csv
...
```

Satellites will be matched between snapshots using:

```text
NORAD_CAT_ID
```

The satellite's `EPOCH` will be used to determine the actual time difference between observations.

---

# 3. Current-State ML Pipeline

The first analytical component will answer:

> **Is the satellite's current orbital state unusual compared with comparable satellites?**

The pipeline will follow:

```text
CelesTrak snapshot
        ↓
Data cleaning
        ↓
Orbital feature engineering
        ↓
Feature selection
        ↓
Standardization
        ↓
K-Means grouping
        ↓
Cluster-specific Isolation Forest
        ↓
Current-state anomaly evidence
```

The current-state detector should primarily work with the selected orbital features rather than treating every available CelesTrak column as an anomaly feature.

---

# 4. Discrete Mathematics / Graph Component

The graph component will represent relationships between satellites based on orbital-feature similarity.

For each satellite:

```text
Satellite
    ↓
Find k nearest satellites
    ↓
Create kNN relationships
    ↓
Construct graph
```

The graph will then provide local-structure information such as:

* k-th-neighbour distance,
* incoming-neighbour count,
* local sparsity,
* connected/component structure where applicable.

A normal kNN degree should **not** be used as the anomaly signal because every satellite has approximately \(k\) outgoing neighbours by construction.

The graph should therefore be treated as **contextual evidence**, not as a standalone anomaly classifier.

---

# 5. Temporal Behaviour Component

The temporal component answers a different question:

> **Has this satellite changed unusually over time compared with comparable satellites?**

For matched satellites between observations:

$$
\Delta a = a_{t_2}-a_{t_1}
$$

$$
\Delta e = e_{t_2}-e_{t_1}
$$

$$
\Delta i = i_{t_2}-i_{t_1}
$$

The corresponding rates can be calculated using the actual time interval:

$$
\Delta a_{\text{rate}}
=
\frac{a_{t_2}-a_{t_1}}
{t_2-t_1}
$$

and similarly for \(e\) and \(i\).

The system should **not assume that two snapshots are exactly 24 hours apart**.

The change features will then be compared within a comparable orbital population.

Conceptually:

```text
Historical snapshots
        ↓
Match NORAD IDs
        ↓
Calculate orbital changes
        ↓
Calculate change rates
        ↓
Compare with comparable satellites
        ↓
Temporal anomaly evidence
```

A large change is therefore **not automatically an anomaly**.

---

# 6. Integration

The three analytical perspectives will be combined:

```text
             Current-state ML
                    │
                    ▼
             Orbit-type evidence
                    │
                    │
Graph ──────────────┼────────────── Temporal ML
                    │
                    ▼
              Combined evidence
                    │
                    ▼
             Operator-facing result
```

The system should distinguish between:

### Case 1 — Current state unusual, behaviour not unusual

Possible interpretation:

> Rare or unusual orbital configuration that appears relatively stable.

### Case 2 — Current state not unusual, behaviour unusual

Possible interpretation:

> Notable recent orbital change.

### Case 3 — Both unusual

Possible interpretation:

> Multiple analytical signals indicate that the satellite deserves further investigation.

### Case 4 — Neither unusual

Output:

> **No significant anomaly detected.**

These are interpretations of the available data, not definitive explanations of why a satellite behaved that way.

---

# 7. Evidence Independence

The system must **not** describe ML and graph results as independent evidence.

Both can use the same underlying orbital features:

$$
(a,e,i)
$$

Therefore, agreement between them should be described as:

> **complementary or converging evidence**

rather than:

> **independent confirmation**

Temporal evidence is also related to the same orbital quantities, although it examines their **changes over time** rather than only their current values.

---

# 8. Synthetic Validation

Because the project does not have a complete ground-truth dataset containing labelled real-world satellite anomalies, controlled synthetic anomalies will be used for an initial validation experiment.

The procedure will be:

```text
Real satellite observations
        ↓
Select valid observations
        ↓
Create controlled perturbations
        ↓
Create known synthetic anomaly labels
        ↓
Run anomaly-detection system
        ↓
Compare predictions with known labels
```

The labels must **not** be supplied to the Isolation Forest during detection.

They are used only afterward to evaluate the result.

Possible metrics include:

* Precision
* Recall
* F1-score
* PR-AUC
* ROC-AUC where appropriate

### Important limitation

Synthetic validation does **not** establish the real-world accuracy of the system.

It establishes how well the detector recognizes the **specific synthetic anomaly patterns that were created**.

Therefore, a statement such as:

> “The system has 95% real-world accuracy”

must not be made solely from synthetic testing.

---

# 9. External Validation

Where independently documented orbital events are available, they can be used as an additional validation source.

For example, an independently documented orbital maneuver could be compared with the temporal detector's output.

However:

> **A maneuver is not automatically an anomaly.**

The purpose of this comparison is to determine whether the temporal component responds to documented orbital changes, not to label every maneuver as abnormal.

---

# 10. Discrete Mathematics Validation

The mathematical structures themselves should also be checked.

Examples:

### kNN consistency

Verify that each satellite receives the expected number of outgoing nearest-neighbour relationships.

### Distance consistency

For selected satellite pairs, manually verify:

$$
D(A,B)
=
\sqrt{
(\tilde a_A-\tilde a_B)^2+
(\tilde e_A-\tilde e_B)^2+
(\tilde i_A-\tilde i_B)^2
}
$$

### Graph consistency

Check that:

* nodes correspond to satellites,
* edges correspond to calculated neighbour relationships,
* satellite IDs are preserved correctly,
* neighbour distances correspond to the correct feature vectors.

These tests ensure that the mathematical model implemented in code matches the mathematical definition used by the project.

---

# 11. Error Analysis

Validation will not stop at a single metric.

The system should investigate cases where the different components disagree.

For example:

```text
ML anomaly
      +
Graph not unusual
      +
Temporal not unusual
```

versus:

```text
ML normal
      +
Graph sparse
      +
Temporal anomaly
```

and:

```text
ML anomaly
      +
Graph sparse
      +
Temporal anomaly
```

These cases should be examined individually to understand **why** the system produced the result.

This is especially important because an unsupervised detector can produce false positives and false negatives.

---

# 12. Unit Testing

Individual mathematical and data-processing functions should be tested before integration.

Examples:

```text
Feature calculation
        ↓
Distance calculation
        ↓
kNN construction
        ↓
Snapshot matching
        ↓
Temporal differences
        ↓
ML output
```

Tests should include:

* missing values,
* duplicate satellites,
* missing snapshots,
* satellites appearing/disappearing between snapshots,
* incorrect time intervals,
* very small clusters,
* insufficient historical observations,
* identical feature vectors,
* extreme but valid orbital values.

---

# 13. Integration Testing

After individual components pass their tests, the complete pipeline should be tested.

A complete test run should verify:

```text
Data
 ↓
Preprocessing
 ↓
Feature engineering
 ↓
K-Means
 ↓
Isolation Forest
 ↓
kNN graph
 ↓
Temporal analysis
 ↓
Integration
 ↓
Final output
```

The final output should contain enough information to identify:

* satellite,
* current-state evidence,
* temporal evidence,
* graph context,
* anomaly score where applicable,
* explanation of why the satellite was flagged.

---

# 14. Known Limitations

The following limitations must remain explicit in the project.

### 14.1 No complete real-world anomaly labels

The system cannot establish a definitive real-world anomaly accuracy without suitable labelled data.

### 14.2 Synthetic validation is limited

Synthetic anomalies represent selected controlled patterns and may not represent every real-world anomaly.

### 14.3 Orbital similarity is not physical proximity

Similarity in \((a,e,i)\) does not mean two satellites are physically close in space.

The system therefore does **not** calculate:

* conjunction probability,
* collision probability,
* physical separation,
* collision risk.

### 14.4 Unusual does not mean anomalous behaviour

A satellite may occupy a rare orbital configuration while remaining stable.

### 14.5 Orbital change does not automatically mean abnormal behaviour

A change may be intentional, environmental, operational, or otherwise explainable.

### 14.6 Short temporal window

A short collection period can demonstrate short-term orbital-change analysis, but it cannot establish long-term orbital behaviour.

---

# 15. Final Development Principle

The system should follow this reasoning:

```text
Observe
  ↓
Represent orbital state
  ↓
Compare satellites
  ↓
Detect unusual current states
  ↓
Study local orbital relationships
  ↓
Observe changes over time
  ↓
Compare changes with comparable satellites
  ↓
Combine complementary evidence
  ↓
Flag cases for investigation
```

The system's conclusion should therefore be interpreted as:

> **“This satellite exhibits an orbital pattern that is statistically unusual within the analyzed data and may warrant further investigation.”**

rather than:

> **“This satellite is definitely anomalous.”**

---

### Documentation phase complete

With this file, our planned development documentation is complete:

```text
01_Project_Overview.md
02_User_Workflow.md
03_System_Architecture.md
04_ML_and_Discrete_Mathematics.md
05_Snapshot_and_Integration.md
06_Development_and_Validation.md
```


