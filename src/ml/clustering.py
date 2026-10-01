import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.ml.ml_config import (
    DEFAULT_ML_FEATURE_COLS,
    DEFAULT_N_CLUSTERS,
    RANDOM_SEED
)


def fit_kmeans(df, feature_cols=None, n_clusters=DEFAULT_N_CLUSTERS, random_state=RANDOM_SEED):
    """
    Fits a K-Means model on standardized orbital features.
    
    If the number of available observations is fewer than n_clusters,
    n_clusters is automatically adjusted to max(1, len(df)).
    """
    if df is None or len(df) == 0:
        return None

    if feature_cols is None:
        feature_cols = DEFAULT_ML_FEATURE_COLS

    n_samples = len(df)
    effective_clusters = max(1, min(n_clusters, n_samples))

    X = df[feature_cols].to_numpy()
    model = KMeans(n_clusters=effective_clusters, random_state=random_state, n_init="auto")
    model.fit(X)
    return model


def assign_clusters(df, model, feature_cols=None):
    """
    Assigns cluster IDs to satellites using a fitted K-Means model.
    Adds a 'cluster_id' column to the dataframe.
    """
    if df is None or len(df) == 0:
        return df

    if feature_cols is None:
        feature_cols = DEFAULT_ML_FEATURE_COLS

    result_df = df.copy()

    if model is None:
        result_df["cluster_id"] = 0
        return result_df

    X = result_df[feature_cols].to_numpy()
    result_df["cluster_id"] = model.predict(X)
    return result_df


def cluster_satellites(df, feature_cols=None, n_clusters=DEFAULT_N_CLUSTERS, random_state=RANDOM_SEED):
    """
    Fits K-Means and assigns cluster IDs to the dataframe.
    
    Returns:
        clustered_df: Dataframe with 'cluster_id' column added
        model: Fitted KMeans model
    """
    if df is None or len(df) == 0:
        return df, None

    model = fit_kmeans(
        df,
        feature_cols=feature_cols,
        n_clusters=n_clusters,
        random_state=random_state
    )
    clustered_df = assign_clusters(df, model, feature_cols=feature_cols)
    return clustered_df, model
