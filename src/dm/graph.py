import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from src.dm.graph_config import (
    DEFAULT_GRAPH_FEATURE_COLS,
    DEFAULT_K_NEIGHBORS,
    DEFAULT_DISTANCE_METRIC
)


def build_knn_graph(df, feature_cols=None, k=DEFAULT_K_NEIGHBORS, metric=DEFAULT_DISTANCE_METRIC):
    """
    Constructs a directed k-Nearest Neighbour (kNN) graph G = (V, E)
    in the 3D standardized orbital feature space (std_semi_major_axis, std_eccentricity, std_inclination).

    Each satellite is a node v in V.
    Directed edges (u -> v) in E represent that v is one of u's k closest orbital neighbours.

    Uses spatial indexing (KD-Tree) for O(n log n) efficiency rather than
    constructing an expensive O(n^2) pairwise distance matrix.

    Returns:
        graph_data: Dictionary containing:
            - 'nodes': List of satellite IDs or row indices
            - 'k': Effective number of neighbours per node
            - 'neighbor_indices': 2D numpy array of shape (n, k), where row i has neighbour indices
            - 'neighbor_distances': 2D numpy array of shape (n, k), corresponding orbital distances
            - 'model': Fitted NearestNeighbors indexer
    """
    if df is None or len(df) == 0:
        return {
            "nodes": [],
            "k": 0,
            "neighbor_indices": np.empty((0, 0), dtype=int),
            "neighbor_distances": np.empty((0, 0), dtype=float),
            "model": None
        }

    if feature_cols is None:
        feature_cols = DEFAULT_GRAPH_FEATURE_COLS

    n_samples = len(df)
    # Node can have at most (n_samples - 1) neighbours
    effective_k = max(0, min(k, n_samples - 1))

    nodes = df["NORAD_CAT_ID"].tolist() if "NORAD_CAT_ID" in df.columns else list(range(n_samples))

    if effective_k == 0:
        return {
            "nodes": nodes,
            "k": 0,
            "neighbor_indices": np.empty((n_samples, 0), dtype=int),
            "neighbor_distances": np.empty((n_samples, 0), dtype=float),
            "model": None
        }

    X = df[feature_cols].to_numpy()

    # Query for (effective_k + 1) neighbours so we can omit the satellite's self-loop at distance 0
    nn_model = NearestNeighbors(
        n_neighbors=effective_k + 1,
        metric=metric,
        algorithm="kd_tree"
    )
    nn_model.fit(X)
    distances, indices = nn_model.kneighbors(X)

    # First column is the node itself (distance 0), so slice [:, 1:]
    neighbor_indices = indices[:, 1:]
    neighbor_distances = distances[:, 1:]

    return {
        "nodes": nodes,
        "k": effective_k,
        "neighbor_indices": neighbor_indices,
        "neighbor_distances": neighbor_distances,
        "model": nn_model
    }


def compute_graph_properties(graph_data):
    """
    Calculates Discrete Mathematics graph-level properties from the kNN graph:
    1. Incoming-neighbour count (in-degree): How many other satellites select node v as a neighbour.
       Provides structural evidence of how central/dense node v's orbital neighborhood is.
    2. k-th nearest-neighbour distance: Distance to the k-th closest orbital neighbour.
       Indicates local sparsity of the orbital feature space around node v.
    3. Mean k-neighbour distance: Average distance to its k closest orbital neighbours.

    Returns:
        properties: Dictionary of 1D numpy arrays:
            - 'incoming_count': Array of integer in-degrees
            - 'kth_distance': Array of float distances to k-th neighbour
            - 'mean_distance': Array of float average neighbour distances
    """
    n_nodes = len(graph_data["nodes"])
    effective_k = graph_data["k"]

    if n_nodes == 0 or effective_k == 0:
        return {
            "incoming_count": np.zeros(n_nodes, dtype=int),
            "kth_distance": np.zeros(n_nodes, dtype=float),
            "mean_distance": np.zeros(n_nodes, dtype=float)
        }

    neighbor_indices = graph_data["neighbor_indices"]
    neighbor_distances = graph_data["neighbor_distances"]

    # Calculate in-degree: count how many times each node index appears as a target
    incoming_count = np.zeros(n_nodes, dtype=int)
    flat_targets = neighbor_indices.flatten()
    unique_targets, counts = np.unique(flat_targets, return_counts=True)
    incoming_count[unique_targets] = counts

    # k-th nearest neighbour distance is the last column
    kth_distance = neighbor_distances[:, -1].astype(float)

    # Average distance to the k nearest neighbours
    mean_distance = neighbor_distances.mean(axis=1).astype(float)

    return {
        "incoming_count": incoming_count,
        "kth_distance": kth_distance,
        "mean_distance": mean_distance
    }


def add_graph_features(df, graph_data):
    """
    Appends graph structural properties directly to a satellite dataframe:
    - 'k_nearest_distance': distance to k-th orbital neighbour
    - 'incoming_neighbor_count': directed in-degree in similarity graph
    - 'mean_neighbor_distance': average distance to k neighbours
    """
    if df is None or len(df) == 0:
        return df

    props = compute_graph_properties(graph_data)

    result_df = df.copy()
    result_df["k_nearest_distance"] = props["kth_distance"]
    result_df["incoming_neighbor_count"] = props["incoming_count"]
    result_df["mean_neighbor_distance"] = props["mean_distance"]

    return result_df
