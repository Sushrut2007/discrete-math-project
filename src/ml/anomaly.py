import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.ml.ml_config import (
    DEFAULT_ML_FEATURE_COLS,
    DEFAULT_CONTAMINATION,
    MIN_CLUSTER_SIZE_FOR_ISOLATION,
    LABEL_ANOMALOUS,
    LABEL_NORMAL,
    LABEL_NOT_EVALUATED,
    DEFAULT_SCORE_UNEVALUATED,
    RANDOM_SEED
)


def detect_cluster_anomalies(
    df,
    feature_cols=None,
    cluster_col="cluster_id",
    contamination=DEFAULT_CONTAMINATION,
    min_cluster_size=MIN_CLUSTER_SIZE_FOR_ISOLATION,
    random_state=RANDOM_SEED
):
    """
    Applies Isolation Forest within each cluster group in df.

    For clusters with at least min_cluster_size members:
        - Fits Isolation Forest on standardized features of that cluster
        - Computes anomaly_label:
            1  = normal relative to cluster
           -1  = unusual relative to cluster
        - Computes anomaly_score: decision_function (lower/negative values are more unusual)

    For clusters smaller than min_cluster_size (insufficient data):
        - Explicitly marks anomaly_label = LABEL_NOT_EVALUATED (0, not evaluated / insufficient data)
        - Assigns anomaly_score = DEFAULT_SCORE_UNEVALUATED (np.nan)
        rather than falsely asserting that they are normal.

    Returns:
        result_df: Copy of df with 'anomaly_label' and 'anomaly_score' columns added
        models: Dictionary mapping cluster_id to fitted IsolationForest model (or None)
    """
    if df is None or len(df) == 0:
        return df, {}

    if feature_cols is None:
        feature_cols = DEFAULT_ML_FEATURE_COLS

    result_df = df.copy()
    result_df["anomaly_label"] = LABEL_NOT_EVALUATED
    result_df["anomaly_score"] = DEFAULT_SCORE_UNEVALUATED

    models = {}

    # If cluster_col is not present, treat entire dataset as a single cluster
    if cluster_col not in result_df.columns:
        cluster_groups = [(0, result_df.index)]
    else:
        cluster_groups = result_df.groupby(cluster_col).groups.items()

    for cluster_id, idx_list in cluster_groups:
        cluster_indices = list(idx_list)
        cluster_size = len(cluster_indices)

        if cluster_size < min_cluster_size:
            # Cluster is too small to build a meaningful Isolation Forest model.
            # Explicitly mark as not evaluated / insufficient data rather than claiming normal.
            result_df.loc[cluster_indices, "anomaly_label"] = LABEL_NOT_EVALUATED
            result_df.loc[cluster_indices, "anomaly_score"] = DEFAULT_SCORE_UNEVALUATED
            models[cluster_id] = None
            continue

        cluster_features = result_df.loc[cluster_indices, feature_cols].to_numpy()

        iso_model = IsolationForest(
            contamination=contamination,
            random_state=random_state
        )
        iso_model.fit(cluster_features)

        labels = iso_model.predict(cluster_features)
        scores = iso_model.decision_function(cluster_features)

        result_df.loc[cluster_indices, "anomaly_label"] = labels
        result_df.loc[cluster_indices, "anomaly_score"] = scores
        models[cluster_id] = iso_model

    return result_df, models
