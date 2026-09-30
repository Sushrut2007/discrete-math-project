# User Workflow and Features

## 1. Purpose

This document describes what a user can do with the completed satellite anomaly-detection system.

The system should allow the user to explore the satellite population, investigate individual satellites, understand why a satellite was flagged, and examine the orbital relationships and recent changes behind the result.

The user does not need to understand Machine Learning or Discrete Mathematics to use the main interface. Technical details are available when the user wants to investigate a result further.

---

## 2. Main User Workflow

The overall user workflow is:

1. Open the application.
2. Explore the analyzed satellite population.
3. Search for or select a satellite.
4. View its current orbital information.
5. View its anomaly result.
6. Examine why the satellite was flagged.
7. Explore its orbital-similarity relationships.
8. View recent orbital changes when snapshot data is available.
9. Compare the satellite with other flagged satellites.

---

## 3. Explore the Satellite Population

The main dashboard should provide an overview of the analyzed satellite population.

The user should be able to see information such as:

- total number of analyzed satellites,
- number of satellites flagged by the system,
- orbital clusters,
- distribution of anomaly results,
- satellite table.

The satellite table can contain information such as:

| Satellite | Cluster | Anomaly Status | Anomaly Score |
|---|---:|---|---:|
| SAT-001 | 2 | No significant anomaly detected | ... |
| SAT-217 | 2 | Requires investigation | ... |
| SAT-542 | 4 | Rare orbit type | ... |

The exact dashboard layout can be decided during implementation.

---

## 4. Search or Select a Satellite

The user should be able to search for a satellite using information such as:

- satellite name,
- NORAD catalog ID.

After selecting a satellite, the application displays a dedicated analysis for that satellite.

Example:

```text
Selected satellite:
SAT-217
NORAD ID: 12345