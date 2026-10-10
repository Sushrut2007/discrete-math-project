import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

# Make sure Python knows where project root is when running this test file directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ml.ml_config import (
    DEFAULT_ML_FEATURE_COLS,
    DEFAULT_N_CLUSTERS,
    DEFAULT_CONTAMINATION,
    MIN_CLUSTER_SIZE_FOR_ISOLATION,
    LABEL_ANOMALOUS,
    LABEL_NORMAL,
    LABEL_NOT_EVALUATED
)
from src.ml.clustering import fit_kmeans, assign_clusters, cluster_satellites
from src.ml.anomaly import detect_cluster_anomalies
from src.ml.ml_pipeline import run_ml_pipeline


class TestMLAnomaly(unittest.TestCase):

    def setUp(self):
        # Create a synthetic dataset of 60 satellites:
        # Group A: 30 satellites in LEO-like cluster
        # Group B: 28 satellites in GEO-like cluster
        # Group C: 2 outliers (1 in LEO, 1 forming tiny cluster or far out)
        np.random.seed(42)

        leo_sma = np.random.normal(loc=-0.5, scale=0.05, size=30)
        leo_ecc = np.random.normal(loc=-0.1, scale=0.02, size=30)
        leo_inc = np.random.normal(loc=0.2, scale=0.05, size=30)

        geo_sma = np.random.normal(loc=4.5, scale=0.05, size=28)
        geo_ecc = np.random.normal(loc=-0.05, scale=0.02, size=28)
        geo_inc = np.random.normal(loc=-2.0, scale=0.05, size=28)

        # Inject 1 outlier inside LEO group with high eccentricity
        leo_sma[0] = -0.5
        leo_ecc[0] = 5.0
        leo_inc[0] = 0.2

        all_sma = np.concatenate([leo_sma, geo_sma, [10.0, 10.2]])
        all_ecc = np.concatenate([leo_ecc, geo_ecc, [8.0, 8.1]])
        all_inc = np.concatenate([leo_inc, geo_inc, [3.0, 3.1]])

        n_total = len(all_sma)
        self.sample_features_df = pd.DataFrame({
            "NORAD_CAT_ID": [10000 + i for i in range(n_total)],
            "OBJECT_NAME": [f"SAT_{10000 + i}" for i in range(n_total)],
            "EPOCH": ["2026-09-30T12:00:00.000"] * n_total,
            "std_semi_major_axis": all_sma,
            "std_eccentricity": all_ecc,
            "std_inclination": all_inc
        })

    def test_fit_and_assign_kmeans(self):
        # Test basic K-Means fitting and assignment
        model = fit_kmeans(self.sample_features_df, n_clusters=3, random_state=42)
        self.assertIsNotNone(model)
        self.assertEqual(model.n_clusters, 3)

        clustered_df = assign_clusters(self.sample_features_df, model)
        self.assertIn("cluster_id", clustered_df.columns)
        self.assertEqual(len(clustered_df["cluster_id"].unique()), 3)

    def test_cluster_satellites_configurable_clusters(self):
        # Test cluster_satellites wrapper with 2 clusters
        clustered_2, model_2 = cluster_satellites(
            self.sample_features_df,
            n_clusters=2,
            random_state=42
        )
        self.assertEqual(len(clustered_2["cluster_id"].unique()), 2)
        self.assertEqual(model_2.n_clusters, 2)

        # Test cluster_satellites wrapper with 4 clusters
        clustered_4, model_4 = cluster_satellites(
            self.sample_features_df,
            n_clusters=4,
            random_state=42
        )
        self.assertEqual(len(clustered_4["cluster_id"].unique()), 4)
        self.assertEqual(model_4.n_clusters, 4)

    def test_kmeans_fewer_samples_than_clusters(self):
        # If dataset has 2 satellites but n_clusters=5 requested, it should safely adjust
        tiny_df = self.sample_features_df.iloc[:2].copy()
        clustered_tiny, model_tiny = cluster_satellites(
            tiny_df,
            n_clusters=5,
            random_state=42
        )
        self.assertEqual(len(clustered_tiny), 2)
        self.assertLessEqual(model_tiny.n_clusters, 2)
        self.assertIn("cluster_id", clustered_tiny.columns)

    def test_detect_cluster_anomalies_populates_columns(self):
        # Run clustering first
        clustered_df, _ = cluster_satellites(
            self.sample_features_df,
            n_clusters=3,
            random_state=42
        )

        result_df, models = detect_cluster_anomalies(
            clustered_df,
            contamination=0.1,
            random_state=42
        )

        self.assertIn("anomaly_label", result_df.columns)
        self.assertIn("anomaly_score", result_df.columns)
        self.assertEqual(len(result_df), len(self.sample_features_df))

        # Labels should be 1 (normal), -1 (unusual), or 0 (not evaluated due to small cluster)
        unique_labels = set(result_df["anomaly_label"].unique())
        self.assertTrue(unique_labels.issubset({LABEL_ANOMALOUS, LABEL_NOT_EVALUATED, LABEL_NORMAL}))

        # Scores should be floating point values
        self.assertTrue(pd.api.types.is_float_dtype(result_df["anomaly_score"]))

    def test_detect_cluster_anomalies_small_cluster_safety(self):
        # Create a dataframe where one cluster has only 2 satellites (< min_cluster_size=5)
        clustered_df = self.sample_features_df.copy()
        # Force the last 2 satellites into a isolated small cluster ID 99
        clustered_df.loc[clustered_df.index[-2:], "cluster_id"] = 99
        # Rest into cluster 0
        clustered_df.loc[clustered_df.index[:-2], "cluster_id"] = 0

        result_df, models = detect_cluster_anomalies(
            clustered_df,
            min_cluster_size=5,
            random_state=42
        )

        # For cluster 99, size is 2 (< 5), so it should be safely marked as not evaluated / insufficient data
        small_cluster_rows = result_df[result_df["cluster_id"] == 99]
        self.assertEqual(len(small_cluster_rows), 2)
        self.assertTrue((small_cluster_rows["anomaly_label"] == LABEL_NOT_EVALUATED).all())
        self.assertTrue(np.isnan(small_cluster_rows["anomaly_score"]).all())
        self.assertIsNone(models[99])

    def test_detect_cluster_anomalies_flags_injected_outlier(self):
        # Check that the deliberately injected outlier (index 0) gets flagged as unusual
        clustered_df, _ = cluster_satellites(
            self.sample_features_df,
            n_clusters=2,
            random_state=42
        )

        result_df, _ = detect_cluster_anomalies(
            clustered_df,
            contamination=0.05,
            random_state=42
        )

        # Sat at index 0 had an extreme std_eccentricity=5.0
        outlier_row = result_df.iloc[0]
        self.assertEqual(outlier_row["anomaly_label"], -1)
        self.assertLess(outlier_row["anomaly_score"], 0.0)

    def test_run_ml_pipeline_end_to_end_with_feature_dataset(self):
        # End-to-end test with already standardized feature dataframe
        ml_df, artifacts = run_ml_pipeline(
            df=self.sample_features_df,
            n_clusters=3,
            random_state=42
        )

        # Verify required outputs
        self.assertIn("cluster_id", ml_df.columns)
        self.assertIn("anomaly_label", ml_df.columns)
        self.assertIn("anomaly_score", ml_df.columns)

        # Verify preserved identifiers
        self.assertIn("NORAD_CAT_ID", ml_df.columns)
        self.assertIn("OBJECT_NAME", ml_df.columns)
        self.assertIn("EPOCH", ml_df.columns)

        # Verify artifacts
        self.assertIn("kmeans", artifacts)
        self.assertIn("isolation_forests", artifacts)
        self.assertEqual(artifacts["n_clusters"], 3)

    def test_run_ml_pipeline_with_raw_unstandardized_data(self):
        # End-to-end test passing unstandardized data: pipeline should invoke prepare_features
        raw_df = pd.DataFrame([
            {
                "NORAD_CAT_ID": 25544,
                "OBJECT_NAME": "ISS (ZARYA)",
                "EPOCH": "2026-09-30T12:00:00.000",
                "MEAN_MOTION": 15.49,
                "ECCENTRICITY": 0.0007,
                "INCLINATION": 51.64
            },
            {
                "NORAD_CAT_ID": 48274,
                "OBJECT_NAME": "TIANGONG",
                "EPOCH": "2026-09-30T12:00:00.000",
                "MEAN_MOTION": 15.65,
                "ECCENTRICITY": 0.0005,
                "INCLINATION": 41.47
            }
        ])

        ml_df, artifacts = run_ml_pipeline(df=raw_df, n_clusters=2)
        self.assertEqual(len(ml_df), 2)
        self.assertIn("cluster_id", ml_df.columns)
        self.assertIn("anomaly_label", ml_df.columns)
        self.assertIn("anomaly_score", ml_df.columns)
        self.assertIn("std_semi_major_axis", ml_df.columns)


if __name__ == "__main__":
    unittest.main()
