import numpy as np


def euclidean_distance_3d(v1, v2):
    """
    Computes Euclidean distance between two 3D orbital feature vectors:
        D(u, v) = sqrt((std_a_u - std_a_v)^2 + (std_e_u - std_e_v)^2 + (std_i_u - std_i_v)^2)

    Note: This measures orbital-feature similarity, NOT physical spatial distance.
    """
    diff = np.asarray(v1) - np.asarray(v2)
    return float(np.sqrt(np.sum(diff ** 2)))


def calculate_total_possible_pairs(n):
    """
    Combinatorics function from Discrete Mathematics:
    Calculates number of unordered 2-combinations C(n, 2) = n * (n - 1) / 2.
    Demonstrates why pairwise matrix construction is O(n^2) and motivates kNN indexing.
    """
    if n < 2:
        return 0
    return (n * (n - 1)) // 2
