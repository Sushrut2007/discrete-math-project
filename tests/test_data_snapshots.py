import sys
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

# Make sure Python knows where project root is when running this test file directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.config import REQUIRED_COLUMNS
from src.data.collector import fetch_celestrak_data, save_snapshot, cleanup_old_snapshots
from src.data.loader import (
    list_snapshots,
    load_snapshot,
    load_latest_snapshot,
    load_all_snapshots,
    check_snapshot_data,
)

SAMPLE_CSV = (
    "OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT\n"
    "CALSPHERE 1,1964-063C,2026-09-30T05:11:37.538880,13.76716850,0.00250259,90.2190,74.2002,338.1454,195.6756,0,U,900,999,8587,0.0003903766,0.00000393,0\n"
    "CALSPHERE 2,1964-063E,2026-09-30T07:15:20.123456,13.75012345,0.00195000,90.1500,75.1000,340.0000,180.0000,0,U,902,999,8580,0.0003500000,0.00000350,0\n"
)


class TestDataSnapshots(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_snapshot(self):
        saved_csv = save_snapshot(SAMPLE_CSV, save_dir=self.test_folder)

        self.assertTrue(saved_csv.exists())
        meta_file = saved_csv.with_suffix(".meta.json")
        self.assertTrue(meta_file.exists())

        # Check that saved text is exactly what was passed in
        with open(saved_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, SAMPLE_CSV)

        # Check metadata json
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["total_records"], 2)
        self.assertEqual(meta["collection_interval_hours"], 12)

    def test_list_and_load_snapshots(self):
        save_snapshot(SAMPLE_CSV, save_dir=self.test_folder)
        save_snapshot(SAMPLE_CSV, save_dir=self.test_folder)

        snapshots = list_snapshots(self.test_folder)
        self.assertEqual(len(snapshots), 2)

        # Load latest
        df = load_latest_snapshot(self.test_folder)
        self.assertEqual(len(df), 2)
        self.assertIn("NORAD_CAT_ID", df.columns)

        # Load all
        all_dfs = load_all_snapshots(self.test_folder)
        self.assertEqual(len(all_dfs), 2)

    def test_check_snapshot_data(self):
        saved_csv = save_snapshot(SAMPLE_CSV, save_dir=self.test_folder)
        df = load_snapshot(saved_csv)

        summary = check_snapshot_data(df)
        self.assertTrue(summary["is_valid"])
        self.assertEqual(summary["total_records"], 2)
        self.assertEqual(summary["unique_satellites"], 2)
        self.assertEqual(len(summary["missing_columns"]), 0)

    def test_check_snapshot_data_missing_column(self):
        bad_csv = "OBJECT_NAME,MEAN_MOTION\nSAT_A,14.2\n"
        df = pd.read_csv(pd.io.common.StringIO(bad_csv))

        summary = check_snapshot_data(df)
        self.assertFalse(summary["is_valid"])
        self.assertIn("NORAD_CAT_ID", summary["missing_columns"])
        self.assertIn("EPOCH", summary["missing_columns"])

    def test_cleanup_old_snapshots(self):
        # Create an old snapshot from 40 days ago
        old_file = self.test_folder / "snapshot_2026-08-01_000000.csv"
        old_meta = self.test_folder / "snapshot_2026-08-01_000000.meta.json"
        old_file.write_text(SAMPLE_CSV, encoding="utf-8")
        old_meta.write_text("{}", encoding="utf-8")

        # Create a fresh snapshot (its save function automatically triggers cleanup)
        fresh_file = save_snapshot(SAMPLE_CSV, save_dir=self.test_folder)

        # Verify old file was deleted automatically, fresh file remains
        self.assertFalse(old_file.exists())
        self.assertFalse(old_meta.exists())
        self.assertTrue(fresh_file.exists())

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
