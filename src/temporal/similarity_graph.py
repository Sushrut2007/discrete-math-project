import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.features.orbital_features import calculate_semi_major_axis
from src.temporal.temporal_config import (
    DEFAULT_SIMILARITY_THRESHOLD,
    TRANSITION_FEATURE_COLS,
    LABEL_CONSISTENT,
    LABEL_INTERMEDIATE,
    LABEL_UNUSUAL,
    STATUS_CONSISTENT,
    STATUS_INTERMEDIATE,
    STATUS_UNUSUAL,
    STATUS_INSUFFICIENT,
    DEGREE_UNUSUAL_MAX,
    DEGREE_INTERMEDIATE_MAX,
    DEGREE_CONSISTENT_MIN,
    MIN_DELTA_T_SECONDS,
)


def extract_consecutive_transitions(snapshot_dfs):
    """
    Extracts orbital changes between consecutive snapshots for each satellite.

    For each consecutive pair of snapshots (step 1 to N-1):
    1. Matches satellites strictly by NORAD_CAT_ID.
    2. Calculates elapsed time delta_t = epoch2 - epoch1 (in days).
    3. Calculates change in semi-major axis (delta_a in km),
       eccentricity (delta_e), and inclination (delta_i in degrees).
    """
    if not snapshot_dfs or len(snapshot_dfs) < 2:
        return pd.DataFrame()

    transitions_list = []

    for step_idx in range(1, len(snapshot_dfs)):
        df1 = snapshot_dfs[step_idx - 1]
        df2 = snapshot_dfs[step_idx]

        if df1.empty or df2.empty:
            continue

        merged = pd.merge(
            df1,
            df2,
            on="NORAD_CAT_ID",
            suffixes=("_t1", "_t2"),
            how="inner"
        )

        if merged.empty:
            continue

        # Calculate observation time difference
        t1 = pd.to_datetime(merged["EPOCH_t1"], errors="coerce")
        t2 = pd.to_datetime(merged["EPOCH_t2"], errors="coerce")
        delta_t_days = (t2 - t1).dt.total_seconds() / 86400.0

        # Filter out invalid or zero-elapsed-time records
        valid_mask = delta_t_days > (MIN_DELTA_T_SECONDS / 86400.0)
        merged = merged[valid_mask].copy()
        delta_t_days = delta_t_days[valid_mask]

        if merged.empty:
            continue

        # Get semi-major axis (compute from mean motion if missing)
        if "semi_major_axis_t1" in merged.columns:
            a1 = merged["semi_major_axis_t1"]
        else:
            a1 = calculate_semi_major_axis(merged["MEAN_MOTION_t1"])

        if "semi_major_axis_t2" in merged.columns:
            a2 = merged["semi_major_axis_t2"]
        else:
            a2 = calculate_semi_major_axis(merged["MEAN_MOTION_t2"])

        # Compute differences: delta_a, delta_e, delta_i
        merged["step_idx"] = step_idx
        merged["delta_t_days"] = delta_t_days
        merged["delta_a"] = a2 - a1
        merged["delta_e"] = merged["ECCENTRICITY_t2"] - merged["ECCENTRICITY_t1"]
        merged["delta_i"] = merged["INCLINATION_t2"] - merged["INCLINATION_t1"]

        # Keep primary identifiers and transition values
        keep_cols = [
            "NORAD_CAT_ID",
            "OBJECT_NAME_t2",
            "EPOCH_t2",
            "step_idx",
            "delta_t_days",
            "delta_a",
            "delta_e",
            "delta_i",
        ]
        if "cluster_id_t2" in merged.columns:
            keep_cols.append("cluster_id_t2")

        clean_sub = merged[keep_cols].rename(
            columns={
                "OBJECT_NAME_t2": "OBJECT_NAME",
                "EPOCH_t2": "EPOCH",
                "cluster_id_t2": "cluster_id",
            }
        )
        transitions_list.append(clean_sub)

    if not transitions_list:
        return pd.DataFrame()

    return pd.concat(transitions_list, ignore_index=True)


def build_self_history_similarity_graph(
    transitions_df,
    threshold_eps=DEFAULT_SIMILARITY_THRESHOLD
):
    """
    Builds the discrete mathematics similarity graph for each satellite's history:
    1. Standardizes transition features (delta_a, delta_e, delta_i).
    2. Compares each satellite's latest transition with its past transitions
       using Euclidean distance.
    3. Counts similar past transitions (distance <= threshold_eps) to determine
       the degree of the latest transition in its history graph.
    4. Categorizes the satellite based on its degree:
       - 0 to 1: highly unusual temporal change
       - 2 to 5: intermediate / uncertain
       - 6 or more: consistent with recent history
    """
    if transitions_df.empty:
        return pd.DataFrame(), None

    # Step 1: Standardize transition features across all transitions
    scaler = StandardScaler()
    std_values = scaler.fit_transform(transitions_df[TRANSITION_FEATURE_COLS])
    df = transitions_df.copy()
    df["std_delta_a"] = std_values[:, 0]
    df["std_delta_e"] = std_values[:, 1]
    df["std_delta_i"] = std_values[:, 2]

    # Step 2: Separate latest transition from past history
    latest_step = df["step_idx"].max()
    hist_steps = [s for s in range(1, latest_step)]

    if not hist_steps:
        # Only one transition step available, cannot compare against history
        latest_df = df[df["step_idx"] == latest_step].copy()
        latest_df["history_transitions_count"] = 0
        latest_df["similar_transition_count"] = 0
        latest_df["mean_dist_to_history"] = np.nan
        latest_df["min_dist_to_history"] = np.nan
        latest_df["temporal_dm_label"] = LABEL_INTERMEDIATE
        latest_df["temporal_dm_category"] = STATUS_INSUFFICIENT
        return latest_df, scaler

    # Step 3: Only evaluate satellites present in the latest transition step
    active_norad_ids = df[df["step_idx"] == latest_step]["NORAD_CAT_ID"].unique()
    pivoted = df.pivot(
        index="NORAD_CAT_ID",
        columns="step_idx",
        values=["std_delta_a", "std_delta_e", "std_delta_i"]
    ).loc[active_norad_ids]
    norad_ids = pivoted.index.values

    # Latest transition features for active satellites
    latest_a = pivoted[("std_delta_a", latest_step)].values
    latest_e = pivoted[("std_delta_e", latest_step)].values
    latest_i = pivoted[("std_delta_i", latest_step)].values

    # Step 4: Calculate Euclidean distance to each historical transition
    n_sats = len(pivoted)
    n_hist = len(hist_steps)
    distances_matrix = np.full((n_sats, n_hist), np.nan)

    for col_idx, s in enumerate(hist_steps):
        if ("std_delta_a", s) in pivoted.columns:
            tk_a = pivoted[("std_delta_a", s)].values
            tk_e = pivoted[("std_delta_e", s)].values
            tk_i = pivoted[("std_delta_i", s)].values
            dist = np.sqrt((latest_a - tk_a) ** 2 + (latest_e - tk_e) ** 2 + (latest_i - tk_i) ** 2)
            distances_matrix[:, col_idx] = dist

    # Step 5: Degree calculation and statistics
    is_similar = distances_matrix <= threshold_eps
    similar_counts = np.nan_to_num(is_similar.sum(axis=1), nan=0).astype(int)
    valid_hist_counts = (~np.isnan(distances_matrix)).sum(axis=1)

    # Compute mean and min distance for satellites with valid history
    mean_dists = np.full(n_sats, np.nan)
    min_dists = np.full(n_sats, np.nan)
    has_history = valid_hist_counts > 0
    if np.any(has_history):
        mean_dists[has_history] = np.nanmean(distances_matrix[has_history], axis=1)
        min_dists[has_history] = np.nanmin(distances_matrix[has_history], axis=1)

    # Step 6: Categorize by graph degree
    labels = []
    categories = []

    for count, valid_m in zip(similar_counts, valid_hist_counts):
        if valid_m == 0:
            labels.append(LABEL_INTERMEDIATE)
            categories.append(STATUS_INSUFFICIENT)
        elif valid_m >= DEGREE_CONSISTENT_MIN:
            # Full history available (e.g. 12 steps)
            if count <= DEGREE_UNUSUAL_MAX:
                labels.append(LABEL_UNUSUAL)
                categories.append(STATUS_UNUSUAL)
            elif count <= DEGREE_INTERMEDIATE_MAX:
                labels.append(LABEL_INTERMEDIATE)
                categories.append(STATUS_INTERMEDIATE)
            else:
                labels.append(LABEL_CONSISTENT)
                categories.append(STATUS_CONSISTENT)
        else:
            # Short history (fewer than 6 transitions)
            if count == 0:
                labels.append(LABEL_UNUSUAL)
                categories.append(STATUS_UNUSUAL)
            elif count == valid_m:
                labels.append(LABEL_CONSISTENT)
                categories.append(STATUS_CONSISTENT)
            else:
                labels.append(LABEL_INTERMEDIATE)
                categories.append(STATUS_INTERMEDIATE)

    # Latest metadata lookup
    meta_df = df[df["step_idx"] == latest_step].set_index("NORAD_CAT_ID")

    result_df = pd.DataFrame({
        "NORAD_CAT_ID": norad_ids,
        "OBJECT_NAME": [meta_df.loc[nid, "OBJECT_NAME"] if nid in meta_df.index else "" for nid in norad_ids],
        "latest_epoch": [meta_df.loc[nid, "EPOCH"] if nid in meta_df.index else "" for nid in norad_ids],
        "latest_delta_t_days": [meta_df.loc[nid, "delta_t_days"] if nid in meta_df.index else np.nan for nid in norad_ids],
        "latest_delta_a": [meta_df.loc[nid, "delta_a"] if nid in meta_df.index else np.nan for nid in norad_ids],
        "latest_delta_e": [meta_df.loc[nid, "delta_e"] if nid in meta_df.index else np.nan for nid in norad_ids],
        "latest_delta_i": [meta_df.loc[nid, "delta_i"] if nid in meta_df.index else np.nan for nid in norad_ids],
        "history_transitions_count": valid_hist_counts,
        "similar_transition_count": similar_counts,
        "mean_dist_to_history": np.round(mean_dists, 4),
        "min_dist_to_history": np.round(min_dists, 4),
        "temporal_dm_label": labels,
        "temporal_dm_category": categories,
    })

    if "cluster_id" in meta_df.columns:
        result_df["cluster_id"] = [meta_df.loc[nid, "cluster_id"] if nid in meta_df.index else np.nan for nid in norad_ids]

    return result_df, scaler


def interpret_combined_status(static_label, temporal_label):
    """
    Combines static ML anomaly status and temporal DM graph status:
    - Normal (1) & Consistent (1) -> 'Nominal (Stable Orbit)'
    - Normal (1) & Unusual (-1)   -> 'Active Orbital Change'
    - Anomaly (-1) & Consistent (1)-> 'Consistent Outlier (Rare Orbit)'
    - Anomaly (-1) & Unusual (-1) -> 'Critical Anomaly (Unusual & Active)'
    - Any intermediate (0)        -> 'Monitoring / Uncertain'
    """
    if pd.isna(static_label) or pd.isna(temporal_label):
        return "Monitoring / Uncertain"

    s = int(static_label)
    t = int(temporal_label)

    if s == 1 and t == 1:
        return "Nominal (Stable Orbit)"
    elif s == 1 and t == -1:
        return "Active Orbital Change"
    elif s == -1 and t == 1:
        return "Consistent Outlier (Rare Orbit)"
    elif s == -1 and t == -1:
        return "Critical Anomaly (Unusual & Active)"
    else:
        return "Monitoring / Uncertain"
