import unittest
import numpy as np
import pandas as pd

from src.temporal.temporal_config import (
    DEFAULT_SIMILARITY_THRESHOLD,
    LABEL_CONSISTENT,
    LABEL_INTERMEDIATE,
    LABEL_UNUSUAL,
    STATUS_CONSISTENT,
    STATUS_INTERMEDIATE,
    STATUS_UNUSUAL,
    STATUS_INSUFFICIENT,
)
from src.temporal.similarity_graph import (
    extract_consecutive_transitions,
    build_self_history_similarity_graph,
    interpret_combined_status,
)
from src.temporal.temporal_pipeline import run_temporal_pipeline


class TestTemporalAnalysis(unittest.TestCase):
    def setUp(self):
        # Create a small 5-snapshot series for 3 test satellites:
        # Sat 1: Steady orbit across all steps (expected: high degree)
        # Sat 2: Sudden altitude jump at latest step (expected: low degree / isolated)
        # Sat 3: Dropped at latest step (tests matching edge cases)
        self.snapshots = []
        base_time = pd.to_datetime("2026-10-01T00:00:00.000")

        for s in range(5):
            epoch_str = (base_time + pd.to_timedelta(12 * s, unit="h")).strftime("%Y-%m-%dT%H:%M:%S.000")

            records = [
                {
                    "NORAD_CAT_ID": 101,
                    "OBJECT_NAME": "SAT_STEADY",
                    "EPOCH": epoch_str,
                    "MEAN_MOTION": 15.0 + (s * 0.0001),  # tiny smooth drift
                    "ECCENTRICITY": 0.0010 + (s * 0.00001),
                    "INCLINATION": 51.64,
                },
                {
                    "NORAD_CAT_ID": 102,
                    "OBJECT_NAME": "SAT_JUMP",
                    "EPOCH": epoch_str,
                    # Step 4 undergoes an abrupt orbital maneuver
                    "MEAN_MOTION": 15.0 if s < 4 else 14.2,
                    "ECCENTRICITY": 0.0010 if s < 4 else 0.015,
                    "INCLINATION": 51.64 if s < 4 else 53.0,
                },
            ]

            if s < 4:
                records.append({
                    "NORAD_CAT_ID": 103,
                    "OBJECT_NAME": "SAT_LOST",
                    "EPOCH": epoch_str,
                    "MEAN_MOTION": 14.8,
                    "ECCENTRICITY": 0.002,
                    "INCLINATION": 60.0,
                })

            self.snapshots.append(pd.DataFrame(records))

    def test_extract_consecutive_transitions(self):
        """
        Verifies that consecutive transitions are correctly extracted and matched by NORAD_CAT_ID.
        """
        transitions = extract_consecutive_transitions(self.snapshots)

        self.assertFalse(transitions.empty)
        self.assertEqual(transitions["step_idx"].nunique(), 4)  # 5 snapshots -> 4 transitions
        self.assertIn("delta_a", transitions.columns)
        self.assertIn("delta_e", transitions.columns)
        self.assertIn("delta_i", transitions.columns)
        self.assertIn("delta_t_days", transitions.columns)

        # Elapsed time should be positive (~0.5 days)
        self.assertTrue((transitions["delta_t_days"] > 0).all())

        # SAT_LOST should only have transitions for steps 1, 2, 3
        sat_lost_trans = transitions[transitions["NORAD_CAT_ID"] == 103]
        self.assertEqual(len(sat_lost_trans), 3)

    def test_self_history_graph_degree(self):
        """
        Verifies that steady satellites have higher degree and sudden changes have lower degree.
        """
        transitions = extract_consecutive_transitions(self.snapshots)
        result_df, scaler = build_self_history_similarity_graph(transitions, threshold_eps=1.50)

        self.assertIsNotNone(scaler)
        self.assertEqual(len(result_df), 2)  # only sats 101 and 102 exist at latest step 4

        sat_steady = result_df[result_df["NORAD_CAT_ID"] == 101].iloc[0]
        sat_jump = result_df[result_df["NORAD_CAT_ID"] == 102].iloc[0]

        # Sat 101 had 3 historical transitions (steps 1, 2, 3) identical/very close to step 4
        self.assertEqual(sat_steady["history_transitions_count"], 3)
        self.assertEqual(sat_steady["similar_transition_count"], 3)
        self.assertEqual(sat_steady["temporal_dm_label"], LABEL_CONSISTENT)

        # Sat 102 had step 4 jump far from its steps 1-3 history
        self.assertEqual(sat_jump["history_transitions_count"], 3)
        self.assertEqual(sat_jump["similar_transition_count"], 0)
        self.assertEqual(sat_jump["temporal_dm_label"], LABEL_UNUSUAL)
        self.assertEqual(sat_jump["temporal_dm_category"], STATUS_UNUSUAL)

    def test_full_12_step_degree_tier_categorization(self):
        """
        Verifies the exact degree tier boundaries for a 12-step history:
        - 0 to 1 -> unusual (-1)
        - 2 to 5 -> intermediate (0)
        - 6 to 12 -> consistent (1)
        """
        # Create a synthetic dataset with 13 transitions (step 1 to 13)
        records = []
        for step in range(1, 14):
            # Satellite 1: identical transitions (degree = 12)
            records.append({
                "NORAD_CAT_ID": 201, "OBJECT_NAME": "SAT_CONSISTENT", "EPOCH": "2026-10-01",
                "step_idx": step, "delta_t_days": 0.5, "delta_a": 0.01, "delta_e": 0.0001, "delta_i": 0.001
            })
            # Satellite 2: latest transition jumps (degree = 0)
            records.append({
                "NORAD_CAT_ID": 202, "OBJECT_NAME": "SAT_UNUSUAL", "EPOCH": "2026-10-01",
                "step_idx": step, "delta_t_days": 0.5,
                "delta_a": 0.01 if step < 13 else 25.0,
                "delta_e": 0.0001 if step < 13 else 0.05,
                "delta_i": 0.001 if step < 13 else 2.5
            })

        df_trans = pd.DataFrame(records)
        res_df, _ = build_self_history_similarity_graph(df_trans, threshold_eps=1.50)

        sat_c = res_df[res_df["NORAD_CAT_ID"] == 201].iloc[0]
        sat_u = res_df[res_df["NORAD_CAT_ID"] == 202].iloc[0]

        self.assertEqual(sat_c["similar_transition_count"], 12)
        self.assertEqual(sat_c["temporal_dm_label"], LABEL_CONSISTENT)
        self.assertEqual(sat_c["temporal_dm_category"], STATUS_CONSISTENT)

        self.assertEqual(sat_u["similar_transition_count"], 0)
        self.assertEqual(sat_u["temporal_dm_label"], LABEL_UNUSUAL)
        self.assertEqual(sat_u["temporal_dm_category"], STATUS_UNUSUAL)

    def test_combined_status_mapping(self):
        """
        Verifies the combined state interpretation across static ML and temporal DM.
        """
        self.assertEqual(interpret_combined_status(1, 1), "Nominal (Stable Orbit)")
        self.assertEqual(interpret_combined_status(1, -1), "Active Orbital Change")
        self.assertEqual(interpret_combined_status(-1, 1), "Consistent Outlier (Rare Orbit)")
        self.assertEqual(interpret_combined_status(-1, -1), "Critical Anomaly (Unusual & Active)")
        self.assertEqual(interpret_combined_status(1, 0), "Monitoring / Uncertain")
        self.assertEqual(interpret_combined_status(np.nan, 1), "Monitoring / Uncertain")

    def test_pipeline_execution_with_snapshots(self):
        """
        Verifies that run_temporal_pipeline executes cleanly with provided snapshot dataframes.
        """
        temporal_df, summary = run_temporal_pipeline(
            snapshots=self.snapshots,
            threshold_eps=1.50,
            merge_static_ml=False
        )

        self.assertEqual(len(temporal_df), 2)
        self.assertIn("NORAD_CAT_ID", temporal_df.columns)
        self.assertIn("similar_transition_count", temporal_df.columns)
        self.assertIn("temporal_dm_label", temporal_df.columns)
        self.assertIn("temporal_dm_category", temporal_df.columns)
        self.assertEqual(summary["total_evaluated"], 2)
        self.assertEqual(summary["transitions_count"], 4)


if __name__ == "__main__":
    unittest.main()
