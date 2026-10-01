import sys
from pathlib import Path
import pandas as pd

# Ensure project root is available in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import PROCESSED_DIR
from src.features.feature_pipeline import prepare_features
from src.dm.graph_config import (
    DEFAULT_GRAPH_FEATURE_COLS,
    DEFAULT_K_NEIGHBORS,
    DEFAULT_DISTANCE_METRIC
)
from src.dm.graph import build_knn_graph, add_graph_features


def run_graph_pipeline(
    df=None,
    feature_cols=None,
    k=DEFAULT_K_NEIGHBORS,
    metric=DEFAULT_DISTANCE_METRIC
):
    """
    Executes the Discrete Mathematics orbital similarity graph pipeline:
    1. Loads or accepts prepared feature dataset (from src/features/).
       If df does not have standardized columns, calls prepare_features(df).
    2. Builds directed kNN graph G = (V, E) in 3D standardized orbital feature space.
    3. Computes graph-level properties:
       - k-th nearest-neighbour distance ('k_nearest_distance')
       - incoming-neighbour count / in-degree ('incoming_neighbor_count')
       - mean neighbour distance ('mean_neighbor_distance')
    4. Preserves NORAD_CAT_ID, OBJECT_NAME, EPOCH and other satellite attributes.

    Returns:
        graph_df: Dataframe with graph properties added
        graph_data: Graph structure dictionary containing nodes, edges, indices, distances
    """
    if feature_cols is None:
        feature_cols = DEFAULT_GRAPH_FEATURE_COLS

    # Check if input dataframe already has the standardized features
    if df is None:
        processed_path = Path(PROCESSED_DIR) / "latest_features.csv"
        if processed_path.exists():
            df = pd.read_csv(processed_path)
        else:
            df, _ = prepare_features()
    else:
        # Check if standardized features exist, otherwise run feature pipeline
        missing_std_cols = [c for c in feature_cols if c not in df.columns]
        if missing_std_cols:
            df, _ = prepare_features(df)

    # Step 1: Construct kNN graph using spatial index
    graph_data = build_knn_graph(
        df,
        feature_cols=feature_cols,
        k=k,
        metric=metric
    )

    # Step 2: Calculate graph properties and attach to dataframe
    graph_df = add_graph_features(df, graph_data)

    return graph_df, graph_data


def run_and_save_graph_results(output_filename="latest_graph_features.csv", **kwargs):
    """
    Runs the graph pipeline and saves the resulting dataframe to data/processed/.
    """
    graph_df, graph_data = run_graph_pipeline(**kwargs)

    out_folder = Path(PROCESSED_DIR)
    out_folder.mkdir(parents=True, exist_ok=True)
    out_file = out_folder / output_filename

    graph_df.to_csv(out_file, index=False)
    print(f"Saved graph features to: {out_file}")
    return graph_df, graph_data


if __name__ == "__main__":
    print("--- Running Discrete Mathematics Graph Pipeline ---")
    df_result, g_data = run_and_save_graph_results()
    n_nodes = len(df_result)
    k_eff = g_data["k"]
    print(f"Constructed kNN similarity graph: {n_nodes} nodes, k={k_eff} neighbours per node.")
    print(f"Average k-th neighbour distance: {df_result['k_nearest_distance'].mean():.4f}")
    print(f"Average incoming neighbour count: {df_result['incoming_neighbor_count'].mean():.2f}")
