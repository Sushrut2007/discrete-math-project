# Snapshot and Integration

## 1. Purpose

This document explains how satellite snapshots are collected, compared, and integrated with the current-state Machine Learning and Discrete Mathematics analysis.

The temporal component is included because a single satellite snapshot only describes the current orbital state.

By storing multiple recent snapshots, the system can also examine whether a satellite's orbital parameters have changed unusually.

---

# Part A — Snapshot Collection

## 2. Why Store Snapshots?

The current CelesTrak dataset represents the latest available orbital information.

However, the system also needs to answer:

> Has this satellite's orbital state recently changed?

To answer this, multiple snapshots of the satellite population are collected over a short observation period.

The planned observation period is approximately:

```text
7 days
```

This is intentionally a short-term temporal component.

It is not intended to model long-term orbital evolution.

---

## 3. Snapshot Contents

Each downloaded snapshot should preserve the original satellite data.

A snapshot should also record when the dataset was downloaded.

Conceptually:

```text
Snapshot
├── Download time
├── Satellite records
├── NORAD catalog ID
├── EPOCH
├── Mean motion
├── Eccentricity
├── Inclination
└── Other available orbital fields
```

The original `EPOCH` value should be preserved.

The download time and orbital epoch represent different pieces of information and should not be treated as interchangeable.

---

## 4. Snapshot Storage

Raw snapshots are stored separately from processed data.

Example:

```text
data/
└── raw/
    └── snapshots/
        ├── snapshot_2026-09-30_00.csv
        ├── snapshot_2026-09-30_12.csv
        ├── snapshot_2026-10-01_00.csv
        └── ...
```

The exact filename format can be changed during implementation.

The important requirement is that each snapshot can be identified and ordered by collection time.

---

# Part B — Matching Satellites

## 5. Satellite Identity

The same satellite must be recognized across different snapshots.

The primary identifier used for this is:

```text
NORAD_CAT_ID
```

For example:

```text
Snapshot 1             Snapshot 2

NORAD 12345            NORAD 12345
     ↓                       ↓
    Same satellite
```

Satellite names should not be used as the primary matching key because names can change or may not be unique.

---

## 6. Building a Satellite History

After matching snapshots, the system can construct a history for each satellite.

For example:

```text
Satellite: NORAD 12345

Time 1 → a₁, e₁, i₁
Time 2 → a₂, e₂, i₂
Time 3 → a₃, e₃, i₃
Time 4 → a₄, e₄, i₄
...
```

This produces a sequence of orbital observations for the same satellite.

Not every satellite is required to appear in every snapshot.

Satellites may enter or leave the active dataset, so the processing pipeline should handle missing observations.

---

# Part C — Orbital Changes

## 7. Change in Semi-Major Axis

For two observations:

```text
Δa = a₂ - a₁
```

where:

* `a₁` = earlier semi-major axis,
* `a₂` = later semi-major axis.

A positive value indicates an increase.

A negative value indicates a decrease.

---

## 8. Change in Eccentricity

The change in eccentricity is:

```text
Δe = e₂ - e₁
```

where:

* `e₁` = earlier eccentricity,
* `e₂` = later eccentricity.

---

## 9. Change in Inclination

The change in inclination is:

```text
Δi = i₂ - i₁
```

where:

* `i₁` = earlier inclination,
* `i₂` = later inclination.

Inclination is treated as an ordinary numerical orbital parameter in this project.

---

## 10. Why the Time Difference Matters

Snapshots may not represent exactly equal time intervals.

Therefore, the system should use the actual elapsed time between the two orbital epochs.

For example:

```text
Δt = t₂ - t₁
```

The change rate can then be calculated as:

```text
Δa_rate = (a₂ - a₁) / Δt
```

Similarly:

```text
Δe_rate = (e₂ - e₁) / Δt

Δi_rate = (i₂ - i₁) / Δt
```

The time unit can be normalized to days for easier interpretation.

---

# Part D — Data Quality

## 11. Why Data Quality Matters

A change between two observations is only useful if the observations are sufficiently reliable and comparable.

The temporal pipeline should therefore check:

* missing orbital values,
* missing satellite identifiers,
* invalid timestamps,
* unreasonable time intervals,
* duplicate observations,
* satellites with insufficient history.

Invalid or unreliable intervals should not be passed directly to the temporal anomaly detector.

---

## 12. Insufficient History

A satellite may have only one usable observation.

For example:

```text
Snapshot 1 → Satellite A
Snapshot 2 → Satellite A missing
Snapshot 3 → Satellite A missing
```

There is not enough information to calculate a meaningful recent change.

In this situation:

```text
Temporal result = unavailable
```

The system should not classify the satellite as temporally normal or anomalous simply because historical data is missing.

---

# Part E — Orbital Group Context

## 13. Why Compare Changes Within Groups?

Different orbital populations naturally behave differently.

For example, satellites in different orbital regimes can have different typical orbital-change patterns.

Therefore, the temporal analysis should use the orbital-group context created by K-Means.

Conceptually:

```text
Satellite
    ↓
Current orbital group
    ↓
Comparable satellites
    ↓
Compare orbital changes
```

This avoids treating every orbital change in the entire satellite population as if it had the same meaning.

---

## 14. Reference Clusters

For the initial implementation, the current-state K-Means grouping can be used as the reference grouping.

Conceptually:

```text
Reference snapshot
        ↓
     K-Means
        ↓
Stable orbital groups
        ↓
Temporal comparison
```

The groups should not be unnecessarily retrained for every snapshot in the first version.

This keeps the comparison context stable during the short observation period.

---

# Part F — Temporal Anomaly Detection

## 15. Temporal Question

The temporal component asks:

> Is this satellite's recent orbital change unusual compared with the changes observed for comparable satellites?

This is different from the current-state question.

### Current-state analysis

```text
Is the satellite's current orbit unusual?
```

### Temporal analysis

```text
Is the satellite's recent change unusual?
```

These two questions are related but not identical.

---

## 16. Temporal Features

The temporal model can use features such as:

```text
Δa
Δe
Δi
```

and, when appropriate:

```text
Δa_rate
Δe_rate
Δi_rate
```

The exact feature set can be finalized after inspecting the collected data.

The project should avoid adding extra temporal features simply for complexity.

---

## 17. Temporal Isolation Forest

A temporal anomaly detector can be applied to the change features.

Conceptually:

```text
Snapshot history
       ↓
Calculate Δa, Δe, Δi
       ↓
Group by orbital context
       ↓
Temporal Isolation Forest
       ↓
Recent-change anomaly result
```

The model looks for unusual change patterns rather than unusual absolute orbital values.

---

# Part G — Important Interpretation

## 18. Orbital Change Does Not Automatically Mean Anomaly

An orbital parameter changing does not automatically indicate a problem.

For example:

```text
Orbital change
      ≠
Anomalous behaviour
```

The important question is whether the change is unusual relative to comparable observations.

Similarly:

```text
Anomaly
      ≠
Malfunction
```

and:

```text
Anomaly
      ≠
Intentional maneuver
```

The system detects statistical unusualness.

It does not determine the cause of that unusualness.

---

# Part H — Combining Current and Temporal Analysis

## 19. Two Main Questions

The complete system evaluates two major dimensions.

### Question 1 — Current Orbital State

```text
Latest snapshot
      ↓
K-Means
      ↓
Cluster-specific Isolation Forest
      ↓
Current-state evidence
```

This determines whether the satellite's current orbital state is unusual.

---

### Question 2 — Recent Orbital Behaviour

```text
Multiple snapshots
      ↓
Match by NORAD ID
      ↓
Calculate orbital changes
      ↓
Temporal anomaly detection
      ↓
Recent-change evidence
```

This determines whether its recent change is unusual.

---

# Part I — Graph Integration

## 20. Role of the Similarity Graph

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
    +
Temporal result
```

are used together.

---

## 21. Complementary Evidence

The three components should be interpreted as complementary evidence.

They are not statistically independent because the current-state ML and graph analysis use related orbital features.

Therefore, the system should avoid statements such as:

```text
3 independent models detected the anomaly
```

Instead, use wording such as:

```text
Multiple complementary indicators support further investigation.
```

---

# Part J — Evidence Integration

## 22. Integration Inputs

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

### Temporal analysis

* Δa,
* Δe,
* Δi,
* change rates,
* temporal anomaly result.

---

## 23. Interpretation Matrix

The initial interpretation logic can be represented as:

| Current State | Recent Change | Interpretation                  |
| ------------- | ------------- | ------------------------------- |
| Not unusual   | Not unusual   | No significant anomaly detected |
| Unusual       | Not unusual   | Rare orbit type                 |
| Not unusual   | Unusual       | Notable orbital change          |
| Unusual       | Unusual       | Requires investigation          |

The graph information is used as supporting context rather than as a simple fourth yes/no condition.

---

## 24. Why the Graph is Not a Simple Boolean Rule

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

# Part K — Final Result

## 25. Example Result

A selected satellite could produce:

```text
Satellite:
NORAD 12345

Current-state analysis:
Unusual

Temporal analysis:
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

Current-state analysis:
Unusual

Temporal analysis:
Not unusual

Graph context:
Comparable satellites are present nearby
in orbital feature space

Interpretation:
Rare orbit type
```

The result describes the evidence observed by the system.

---

# Part L — Seven-Day Limitation

## 26. Scope of the Temporal Dataset

The temporal component is intentionally limited to a short collection period.

Approximately seven days of snapshots can provide:

* recent orbital changes,
* short-term change patterns,
* a demonstration of temporal anomaly detection.

However, it cannot establish:

* long-term orbital evolution,
* seasonal behaviour,
* long-term maneuver patterns,
* reliable lifetime trends.

Therefore, the project should describe the temporal component as:

> **Short-term orbital change analysis**

rather than a complete orbital-history model.

---

# Part M — Future Extension

## 27. Possible Future Improvements

With a larger historical dataset, the system could investigate:

* longer-term orbital trends,
* recurring orbital changes,
* maneuver patterns,
* larger temporal windows,
* more robust change baselines,
* external maneuver/event data,
* improved temporal models.

These are future extensions and are not required for the first working version.

---

# Part N — Complete Temporal Pipeline

## 28. Final Pipeline

The complete snapshot and temporal workflow is:

```text
CelesTrak
    ↓
Collect snapshots
    ↓
Store raw snapshots
    ↓
Match satellites by NORAD_CAT_ID
    ↓
Preserve actual orbital EPOCH
    ↓
Build satellite histories
    ↓
Validate observation intervals
    ↓
Calculate Δa, Δe, Δi
    ↓
Calculate change rates
    ↓
Use orbital-group context
    ↓
Temporal anomaly detection
    ↓
Recent-change evidence
    ↓
Evidence integration
    ↓
Final interpretation
```

---

## 29. Key Takeaway

The snapshot component adds a second dimension to anomaly detection.

Instead of asking only:

> **"Is this satellite unusual now?"**

the system can also ask:

> **"Has this satellite changed unusually recently?"**

The combination of current-state analysis, orbital-similarity structure, and recent-change analysis provides a more informative basis for investigating unusual satellite behaviour.


