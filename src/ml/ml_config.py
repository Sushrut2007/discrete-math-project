import numpy as np

# Standard numerical orbital features used for ML analysis
DEFAULT_ML_FEATURE_COLS = [
    "std_semi_major_axis",
    "std_eccentricity",
    "std_inclination"
]

# Default number of orbital clusters
DEFAULT_N_CLUSTERS = 5

# Default contamination rate for Isolation Forest (expected proportion of outliers)
DEFAULT_CONTAMINATION = 0.05

# Minimum satellites in a cluster to run Isolation Forest reliably
MIN_CLUSTER_SIZE_FOR_ISOLATION = 5

# Anomaly status labels
LABEL_ANOMALOUS = -1       # Unusual compared to comparable cluster members
LABEL_NORMAL = 1          # Normal compared to comparable cluster members
LABEL_NOT_EVALUATED = 0   # Insufficient data in cluster to reliably evaluate

# Default anomaly score for unevaluated satellites (e.g. cluster too small)
DEFAULT_SCORE_UNEVALUATED = np.nan

# Random seed for reproducible clustering and anomaly scores
RANDOM_SEED = 42
