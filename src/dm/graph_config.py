# Standard standardized orbital features used for graph similarity (3D feature space)
DEFAULT_GRAPH_FEATURE_COLS = [
    "std_semi_major_axis",
    "std_eccentricity",
    "std_inclination"
]

# Default number of nearest orbital neighbours (k in kNN graph)
DEFAULT_K_NEIGHBORS = 5

# Metric for orbital-feature similarity
DEFAULT_DISTANCE_METRIC = "euclidean"
