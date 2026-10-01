import sys
from pathlib import Path
import pandas as pd

# Ensure project root is available in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import PROCESSED_DIR
from src.features.feature_pipeline import prepare_features
from src.ml.ml_config import (
    DEFAULT_ML_FEATURE_COLS,
    DEFAULT_N_CLUSTERS,
    DEFAULT_CONTAMINATION,
    MIN_CLUSTER_SIZE_FOR_ISOLATION,
    RANDOM_SEED
)
from src.ml.clustering import cluster_satellites
from src.ml.anomaly import detect_cluster_anomalies


def run_ml_pipeline(
    df=None,
    feature_cols=None,
    n_clusters=DEFAULT_N_CLUSTERS,
    contamination=DEFAULT_CONTAMINATION,
    min_cluster_size=MIN_CLUSTER_SIZE_FOR_ISOLATION,
    random_state=RANDOM_SEED
):
    """
    Executes the full current-state Machine Learning pipeline:
    1. Loads or accepts prepared feature dataset (from src/features/).
       If df does not have standardized columns, calls prepare_features(df).
    2. Clusters satellites using K-Means into broad orbital groups (cluster_id).
    3. Detects unusual observations using Isolation Forest within each cluster
       (anomaly_label, anomaly_score).
    4. Preserves NORAD_CAT_ID, OBJECT_NAME, EPOCH and other metadata.

    Returns:
        ml_df: Dataframe with cluster_id, anomaly_label, anomaly_score
        artifacts: Dictionary containing fitted kmeans model and cluster anomaly models
    """
    if feature_cols is None:
        feature_cols = DEFAULT_ML_FEATURE_COLS

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

    # Step 1: K-Means clustering
    clustered_df, kmeans_model = cluster_satellites(
        df,
        feature_cols=feature_cols,
        n_clusters=n_clusters,
        random_state=random_state
    )

    # Step 2: Cluster-specific Isolation Forest
    ml_df, iso_models = detect_cluster_anomalies(
        clustered_df,
        feature_cols=feature_cols,
        cluster_col="cluster_id",
        contamination=contamination,
        min_cluster_size=min_cluster_size,
        random_state=random_state
    )

    artifacts = {
        "kmeans": kmeans_model,
        "isolation_forests": iso_models,
        "feature_cols": feature_cols,
        "n_clusters": n_clusters
    }

    return ml_df, artifacts


def run_and_save_ml_results(output_filename="latest_ml_anomalies.csv", **kwargs):
    """
    Runs the ML anomaly detection pipeline and saves the resulting dataframe to data/processed/.
    """
    ml_df, artifacts = run_ml_pipeline(**kwargs)

    out_folder = Path(PROCESSED_DIR)
    out_folder.mkdir(parents=True, exist_ok=True)
    out_file = out_folder / output_filename

    ml_df.to_csv(out_file, index=False)
    print(f"Saved ML anomaly results to: {out_file}")
    return ml_df, artifacts


if __name__ == "__main__":
    print("--- Running ML Anomaly Detection Pipeline ---")
    df_result, _ = run_and_save_ml_results()
    n_anomalies = (df_result["anomaly_label"] == -1).sum()
    n_total = len(df_result)
    print(f"Done! Evaluated {n_total} satellites.")
    print(f"Identified {n_anomalies} satellites with unusual orbital features (anomaly_label == -1).")
