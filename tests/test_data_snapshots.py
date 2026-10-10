import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

# Make sure Python knows where project root is when running this test file directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.fetch import fetch_celestrak_data, save_raw_data
from src.data.snapshot_loader import load_latest_data

SAMPLE_CSV = (
    "OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT\n"
    "CALSPHERE 1,1964-063C,2026-09-30T05:11:37.538880,13.76716850,0.00250259,90.2190,74.2002,338.1454,195.6756,0,U,900,999,8587,0.0003903766,0.00000393,0\n"
    "CALSPHERE 2,1964-063E,2026-09-30T07:15:20.123456,13.75012345,0.00195000,90.1500,75.1000,340.0000,180.0000,0,U,902,999,8580,0.0003500000,0.00000350,0\n"
)


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_data(self):
        saved_csv = save_raw_data(SAMPLE_CSV, save_dir=self.test_folder)

        self.assertTrue(saved_csv.exists())

        # Check that saved text is exactly what was passed in
        with open(saved_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, SAMPLE_CSV)

        # Load latest
        df = load_latest_data(self.test_folder)
        self.assertEqual(len(df), 2)
        self.assertIn("NORAD_CAT_ID", df.columns)


    @patch("requests.get")
    def test_fetch_celestrak_data(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_CSV
        mock_get.return_value = mock_response

        text = fetch_celestrak_data()
        self.assertEqual(text, SAMPLE_CSV)

    @patch("requests.get")
    def test_fetch_empty_data_raises_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "   "
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            fetch_celestrak_data()


if __name__ == "__main__":
    unittest.main()
