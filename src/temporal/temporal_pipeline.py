import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path so imports work smoothly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import SNAPSHOT_DIR, PROCESSED_DIR
from src.data.snapshot_loader import list_snapshots, load_snapshot
from src.temporal.temporal_config import DEFAULT_SIMILARITY_THRESHOLD
from src.temporal.similarity_graph import (
    extract_consecutive_transitions,
    build_self_history_similarity_graph,
    interpret_combined_status,
)


def run_temporal_pipeline(
    snapshots=None,
    snapshot_dir=SNAPSHOT_DIR,
    threshold_eps=DEFAULT_SIMILARITY_THRESHOLD,
    merge_static_ml=True
):
    """
    Runs the temporal similarity graph pipeline:
    1. Loads available snapshots in chronological order.
    2. Extracts orbital transitions (delta_a, delta_e, delta_i) between consecutive snapshots.
    3. Builds the self-history graph for each satellite to find its degree of similarity.
    4. Optionally merges static ML anomaly labels to determine combined status.

    Returns:
        temporal_df: Dataframe with temporal degrees, categories, and labels.
        summary: Dictionary of constellation-level metrics.
    """
    # Step 1: Load snapshots if not directly provided
    if snapshots is None:
        files = list_snapshots(snapshot_dir)
        if len(files) < 2:
            raise ValueError(f"Need at least 2 snapshot files in {snapshot_dir}, found {len(files)}.")
        snapshots = [load_snapshot(f) for f in files]

    if len(snapshots) < 2:
        raise ValueError(f"Need at least 2 snapshots to compute transitions, received {len(snapshots)}.")

    # Step 2: Compute consecutive orbital transitions
    transitions_df = extract_consecutive_transitions(snapshots)
    if transitions_df.empty:
        raise ValueError("Could not extract any valid transitions from snapshots.")

    # Step 3: Build self-history similarity graph
    temporal_df, scaler = build_self_history_similarity_graph(
        transitions_df,
        threshold_eps=threshold_eps
    )

    # Step 4: Merge static ML anomaly labels if available
    if merge_static_ml:
        ml_path = Path(PROCESSED_DIR) / "latest_ml_anomalies.csv"
        if ml_path.exists():
            ml_df = pd.read_csv(ml_path)
            cols_to_merge = ["NORAD_CAT_ID"]
            for col in ["cluster_id", "anomaly_label", "anomaly_score"]:
                if col in ml_df.columns and col not in temporal_df.columns:
                    cols_to_merge.append(col)

            if len(cols_to_merge) > 1:
                temporal_df = temporal_df.merge(
                    ml_df[cols_to_merge],
                    on="NORAD_CAT_ID",
                    how="left"
                )

        # Compute combined status if static anomaly_label is present
        if "anomaly_label" in temporal_df.columns:
            temporal_df["combined_status"] = [
                interpret_combined_status(row["anomaly_label"], row["temporal_dm_label"])
                for _, row in temporal_df.iterrows()
            ]

    # Constellation summary counts
    total_evaluated = len(temporal_df)
    cat_counts = temporal_df["temporal_dm_category"].value_counts().to_dict()

    summary = {
        "total_evaluated": total_evaluated,
        "threshold_eps": threshold_eps,
        "snapshots_count": len(snapshots),
        "transitions_count": transitions_df["step_idx"].nunique(),
        "category_counts": cat_counts,
        "scaler": scaler,
    }

    return temporal_df, summary


def run_and_save_temporal_results(
    output_filename="latest_temporal_features.csv",
    **kwargs
):
    """
    Runs the temporal pipeline and saves the resulting dataframe to data/processed/.
    """
    temporal_df, summary = run_temporal_pipeline(**kwargs)

    out_folder = Path(PROCESSED_DIR)
    out_folder.mkdir(parents=True, exist_ok=True)
    out_file = out_folder / output_filename

    temporal_df.to_csv(out_file, index=False)
    print(f"Saved temporal analysis results to: {out_file}")

    return temporal_df, summary


if __name__ == "__main__":
    print("--- Running Discrete Mathematics Temporal Similarity Graph Pipeline ---")
    df_res, summ = run_and_save_temporal_results()
    print(f"Total satellites evaluated: {summ['total_evaluated']:,}")
    print(f"History window: {summ['snapshots_count']} snapshots -> {summ['transitions_count']} transitions")
    print(f"Similarity threshold: eps = {summ['threshold_eps']}")
    print("\nCategorical breakdown:")
    for cat, count in summ["category_counts"].items():
        pct = count / summ["total_evaluated"] * 100.0
        print(f"  {cat:<35s}: {count:,} ({pct:.1f}%)")
