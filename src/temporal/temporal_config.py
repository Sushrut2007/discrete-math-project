# Default threshold for standardized Euclidean distance between transitions
DEFAULT_SIMILARITY_THRESHOLD = 1.50

# Features used to represent orbital change in each transition
TRANSITION_FEATURE_COLS = ["delta_a", "delta_e", "delta_i"]

# Categorical labels and degree thresholds for self-history graph
LABEL_CONSISTENT = 1
LABEL_INTERMEDIATE = 0
LABEL_UNUSUAL = -1

STATUS_CONSISTENT = "consistent with recent history"
STATUS_INTERMEDIATE = "intermediate / uncertain"
STATUS_UNUSUAL = "highly unusual temporal change"
STATUS_INSUFFICIENT = "insufficient history"

# Thresholds for degree in 12-transition history (from 14 snapshots)
DEGREE_UNUSUAL_MAX = 1       # 0 to 1 similar past transitions
DEGREE_INTERMEDIATE_MAX = 5  # 2 to 5 similar past transitions
DEGREE_CONSISTENT_MIN = 6    # 6 to 12 similar past transitions

# Minimum time difference in seconds to consider consecutive observations valid
MIN_DELTA_T_SECONDS = 60.0
