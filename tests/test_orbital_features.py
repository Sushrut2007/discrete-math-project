import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

# Make sure Python knows where project root is when running this test file directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.features.cleaner import clean_raw_data
from src.features.orbital import (
    calculate_orbital_period,
    calculate_semi_major_axis,
    calculate_orbit_height,
    calculate_perigee,
    calculate_apogee,
    calculate_orbital_speed,
    add_orbital_features,
    filter_leo_satellites,
    LEO_MAX_ALTITUDE_KM,
    EARTH_RADIUS_KM
)
from src.features.scaler import (
    standardize_features,
    apply_standardization,
    get_feature_matrix
)
from src.features.pipeline import prepare_features


class TestOrbitalFeatures(unittest.TestCase):

    def setUp(self):
        # Sample realistic satellite data (one LEO, one GEO, one duplicate/invalid)
        self.sample_data = pd.DataFrame([
            {
                "NORAD_CAT_ID": 25544,
                "OBJECT_NAME": "ISS (ZARYA)",
                "EPOCH": "2026-09-30T12:00:00.000",
                "MEAN_MOTION": 15.49,
                "ECCENTRICITY": 0.0007,
                "INCLINATION": 51.64
            },
            {
                "NORAD_CAT_ID": 28885,
                "OBJECT_NAME": "SYRACUSE 3A",
                "EPOCH": "2026-09-30T12:00:00.000",
                "MEAN_MOTION": 1.0027,
                "ECCENTRICITY": 0.0002,
                "INCLINATION": 0.05
            },
            {
                "NORAD_CAT_ID": 99999,
                "OBJECT_NAME": "INVALID_SAT",
                "EPOCH": "2026-09-30T12:00:00.000",
                "MEAN_MOTION": -5.0,  # Unphysical
                "ECCENTRICITY": 1.5,   # Unphysical (hyperbolic)
                "INCLINATION": 200.0   # Unphysical (> 180)
            },
            {
                "NORAD_CAT_ID": 25544,  # Duplicate of ISS with earlier epoch
                "OBJECT_NAME": "ISS (ZARYA)",
                "EPOCH": "2026-09-29T12:00:00.000",
                "MEAN_MOTION": 15.48,
                "ECCENTRICITY": 0.0007,
                "INCLINATION": 51.64
            }
        ])

    def test_clean_raw_data(self):
        cleaned = clean_raw_data(self.sample_data)

        # Should drop the invalid sat and the older duplicate of ISS
        self.assertEqual(len(cleaned), 2)
        self.assertIn(25544, cleaned["NORAD_CAT_ID"].values)
        self.assertIn(28885, cleaned["NORAD_CAT_ID"].values)
        self.assertNotIn(99999, cleaned["NORAD_CAT_ID"].values)

        # Make sure latest epoch was kept for ISS
        iss_row = cleaned[cleaned["NORAD_CAT_ID"] == 25544].iloc[0]
        self.assertEqual(iss_row["EPOCH"], "2026-09-30T12:00:00.000")

    def test_orbital_calculations_known_values(self):
        # Test for typical LEO satellite: mean motion ~ 15.5 revs/day
        n = 15.5
        e = 0.001

        period = calculate_orbital_period(n)
        self.assertAlmostEqual(period, 1440.0 / 15.5, places=2)

        a = calculate_semi_major_axis(n)
        # Expected radius ~ 6790 to 6800 km for ~400km altitude
        self.assertTrue(6700 < a < 6900)

        height = calculate_orbit_height(a)
        self.assertTrue(350 < height < 500)

        perigee = calculate_perigee(a, e)
        apogee = calculate_apogee(a, e)
        self.assertTrue(perigee < height < apogee)
        self.assertAlmostEqual((perigee + apogee) / 2.0, height, places=4)

        speed = calculate_orbital_speed(a)
        # LEO orbital speed is approximately 7.5 to 7.8 km/s
        self.assertTrue(7.5 < speed < 7.8)

    def test_add_orbital_features_preserves_identifiers(self):
        cleaned = clean_raw_data(self.sample_data)
        featured = add_orbital_features(cleaned)

        # Check all new columns exist
        expected_cols = [
            "orbital_period", "semi_major_axis", "orbit_height",
            "perigee", "apogee", "orbital_speed"
        ]
        for col in expected_cols:
            self.assertIn(col, featured.columns)

        # Check original identifiers exist
        self.assertIn("NORAD_CAT_ID", featured.columns)
        self.assertIn("OBJECT_NAME", featured.columns)
        self.assertIn("EPOCH", featured.columns)

    def test_standardize_features(self):
        cleaned = clean_raw_data(self.sample_data)
        featured = add_orbital_features(cleaned)

        scaled_df, params = standardize_features(featured)

        # Check that std_ columns were added
        self.assertIn("std_semi_major_axis", scaled_df.columns)
        self.assertIn("std_eccentricity", scaled_df.columns)
        self.assertIn("std_inclination", scaled_df.columns)

        # Check matrix extractor
        matrix = get_feature_matrix(scaled_df)
        self.assertEqual(matrix.shape, (len(scaled_df), 3))

        # Check applying existing parameters
        new_scaled = apply_standardization(featured, params)
        np.testing.assert_allclose(
            scaled_df["std_semi_major_axis"].values,
            new_scaled["std_semi_major_axis"].values
        )

    def test_filter_leo_satellites(self):
        cleaned = clean_raw_data(self.sample_data)
        featured = add_orbital_features(cleaned)

        # Before filter: ISS (LEO, ~400km) and SYRACUSE 3A (GEO, ~35,786km)
        self.assertEqual(len(featured), 2)

        # After filter: Only ISS should remain in LEO
        leo_only = filter_leo_satellites(featured)
        self.assertEqual(len(leo_only), 1)
        self.assertEqual(leo_only.iloc[0]["NORAD_CAT_ID"], 25544)
        self.assertLessEqual(leo_only.iloc[0]["orbit_height"], LEO_MAX_ALTITUDE_KM)

    def test_prepare_features_pipeline(self):
        # Default pipeline filters for LEO
        result_df, params = prepare_features(self.sample_data, leo_only=True)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df.iloc[0]["NORAD_CAT_ID"], 25544)
        self.assertIn("std_semi_major_axis", result_df.columns)
        self.assertIn("orbital_speed", result_df.columns)

        # With leo_only=False, both satellites should remain
        all_orbit_df, _ = prepare_features(self.sample_data, leo_only=False)
        self.assertEqual(len(all_orbit_df), 2)


if __name__ == "__main__":
    unittest.main()

