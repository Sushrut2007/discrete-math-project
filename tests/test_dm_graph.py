import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

# Make sure Python knows where project root is when running this test file directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.dm.graph_config import (
    DEFAULT_GRAPH_FEATURE_COLS,
    DEFAULT_K_NEIGHBORS
)
from src.dm.orbital_distance import (
    euclidean_distance_3d,
    calculate_total_possible_pairs
)
from src.dm.graph import (
    build_knn_graph,
    compute_graph_properties,
    add_graph_features
)
from src.dm.graph_pipeline import run_graph_pipeline


class TestDMGraph(unittest.TestCase):

    def setUp(self):
        # 6 satellites in controlled 3D standardized coordinates
        # Sat 0, 1, 2 form a tight equilateral-like cluster near origin
        # Sat 3, 4 form a pair near (5, 5, 5)
        # Sat 5 is an isolated satellite at (20, 20, 20)
        self.sample_df = pd.DataFrame([
            {
                "NORAD_CAT_ID": 10001,
                "OBJECT_NAME": "SAT_1",
                "EPOCH": "2026-09-30T12:00:00.000",
                "std_semi_major_axis": 0.0,
                "std_eccentricity": 0.0,
                "std_inclination": 0.0
            },
            {
                "NORAD_CAT_ID": 10002,
                "OBJECT_NAME": "SAT_2",
                "EPOCH": "2026-09-30T12:00:00.000",
                "std_semi_major_axis": 0.1,
                "std_eccentricity": 0.0,
                "std_inclination": 0.0
            },
            {
                "NORAD_CAT_ID": 10003,
                "OBJECT_NAME": "SAT_3",
                "EPOCH": "2026-09-30T12:00:00.000",
                "std_semi_major_axis": 0.0,
                "std_eccentricity": 0.1,
                "std_inclination": 0.0
            },
            {
                "NORAD_CAT_ID": 10004,
                "OBJECT_NAME": "SAT_4",
                "EPOCH": "2026-09-30T12:00:00.000",
                "std_semi_major_axis": 5.0,
                "std_eccentricity": 5.0,
                "std_inclination": 5.0
            },
            {
                "NORAD_CAT_ID": 10005,
                "OBJECT_NAME": "SAT_5",
                "EPOCH": "2026-09-30T12:00:00.000",
                "std_semi_major_axis": 5.1,
                "std_eccentricity": 5.0,
                "std_inclination": 5.0
            },
            {
                "NORAD_CAT_ID": 10006,
                "OBJECT_NAME": "SAT_6",
                "EPOCH": "2026-09-30T12:00:00.000",
                "std_semi_major_axis": 20.0,
                "std_eccentricity": 20.0,
                "std_inclination": 20.0
            }
        ])

    def test_euclidean_distance_3d_known_values(self):
        # Point 1: (0, 0, 0), Point 2: (1, 2, 2) -> dist = sqrt(1+4+4) = 3
        dist = euclidean_distance_3d([0.0, 0.0, 0.0], [1.0, 2.0, 2.0])
        self.assertAlmostEqual(dist, 3.0, places=5)

        # Distance between identical points is 0
        self.assertAlmostEqual(euclidean_distance_3d([2.5, 3.0, -1.0], [2.5, 3.0, -1.0]), 0.0)

    def test_calculate_total_possible_pairs(self):
        # C(4, 2) = 6
        self.assertEqual(calculate_total_possible_pairs(4), 6)
        # C(10, 2) = 45
        self.assertEqual(calculate_total_possible_pairs(10), 45)
        # Edge cases: 0 or 1 satellite
        self.assertEqual(calculate_total_possible_pairs(1), 0)
        self.assertEqual(calculate_total_possible_pairs(0), 0)

    def test_build_knn_graph_structure(self):
        # Build kNN graph with k=2
        k = 2
        g_data = build_knn_graph(self.sample_df, k=k)

        self.assertEqual(len(g_data["nodes"]), 6)
        self.assertEqual(g_data["k"], 2)
        self.assertEqual(g_data["neighbor_indices"].shape, (6, 2))
        self.assertEqual(g_data["neighbor_distances"].shape, (6, 2))

        # Check node 0's nearest neighbours: points 1 and 2 are distance ~0.1 away
        n0_neighbors = g_data["neighbor_indices"][0]
        self.assertIn(1, n0_neighbors)
        self.assertIn(2, n0_neighbors)
        self.assertNotIn(0, n0_neighbors)  # No self-loops

        # Check distances are non-negative and ascending
        for row in g_data["neighbor_distances"]:
            self.assertTrue(row[0] <= row[1])
            self.assertTrue(row[0] >= 0.0)

    def test_graph_properties_calculation(self):
        k = 2
        g_data = build_knn_graph(self.sample_df, k=k)
        props = compute_graph_properties(g_data)

        incoming = props["incoming_count"]
        kth_dist = props["kth_distance"]
        mean_dist = props["mean_distance"]

        # Total incoming degrees in directed graph must equal n * k
        self.assertEqual(incoming.sum(), 6 * k)

        # Node 5 is isolated at (20, 20, 20). No one should choose node 5 as nearest neighbour when k=2
        # (closest to 3 and 4 is each other and cluster near 0)
        self.assertEqual(incoming[5], 0)

        # Node 5's distance to its nearest neighbours should be very large (> 20)
        self.assertTrue(kth_dist[5] > 20.0)
        # In contrast, node 0's distance to 2nd nearest neighbour is ~0.1
        self.assertAlmostEqual(kth_dist[0], 0.1, places=3)
        self.assertTrue(mean_dist[0] < 0.15)

    def test_add_graph_features_preserves_identifiers(self):
        k = 2
        g_data = build_knn_graph(self.sample_df, k=k)
        result_df = add_graph_features(self.sample_df, g_data)

        # Check graph feature columns added
        self.assertIn("k_nearest_distance", result_df.columns)
        self.assertIn("incoming_neighbor_count", result_df.columns)
        self.assertIn("mean_neighbor_distance", result_df.columns)

        # Check original identifiers intact
        self.assertIn("NORAD_CAT_ID", result_df.columns)
        self.assertIn("OBJECT_NAME", result_df.columns)
        self.assertIn("EPOCH", result_df.columns)
        self.assertEqual(len(result_df), 6)

    def test_knn_edge_case_k_exceeds_sample_size(self):
        # Dataset has 3 satellites, requested k=5. Effective k should safely adjust to 2 (n - 1)
        small_df = self.sample_df.iloc[:3].copy()
        g_data = build_knn_graph(small_df, k=5)
        self.assertEqual(g_data["k"], 2)
        self.assertEqual(g_data["neighbor_indices"].shape, (3, 2))

    def test_knn_edge_case_single_satellite(self):
        # Dataset has only 1 satellite. Effective k should be 0 safely
        single_df = self.sample_df.iloc[:1].copy()
        g_data = build_knn_graph(single_df, k=5)
        self.assertEqual(g_data["k"], 0)
        props = compute_graph_properties(g_data)
        self.assertEqual(props["incoming_count"][0], 0)
        self.assertEqual(props["kth_distance"][0], 0.0)

    def test_run_graph_pipeline_end_to_end(self):
        graph_df, g_data = run_graph_pipeline(df=self.sample_df, k=2)

        self.assertEqual(len(graph_df), 6)
        self.assertIn("k_nearest_distance", graph_df.columns)
        self.assertIn("incoming_neighbor_count", graph_df.columns)
        self.assertIn("mean_neighbor_distance", graph_df.columns)
        self.assertEqual(g_data["k"], 2)


if __name__ == "__main__":
    unittest.main()
