import sys
from pathlib import Path
import json
import pandas as pd

# Add project root so imports work smoothly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import SNAPSHOT_DIR, REQUIRED_COLUMNS


def list_snapshots(snapshot_dir=SNAPSHOT_DIR):
    """
    Finds all saved CSV snapshots and returns them in order from oldest to newest.
    """
    folder = Path(snapshot_dir)
    if not folder.exists():
        return []

    # Pick up files starting with snapshot_ and ending with .csv
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.name.startswith("snapshot_") and f.suffix == ".csv"
    ]

    # Sort files by name so they stay in chronological order
    files.sort(key=lambda x: x.name)
    return files


def load_snapshot(filepath):
    """
    Loads one snapshot CSV file into a pandas dataframe without changing anything.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return pd.read_csv(path)


def load_latest_snapshot(snapshot_dir=SNAPSHOT_DIR):
    """
    Finds and loads the most recent snapshot file.
    """
    files = list_snapshots(snapshot_dir)
    if not files:
        raise FileNotFoundError(f"No snapshot files found in: {snapshot_dir}")

    latest_file = files[-1]
    return load_snapshot(latest_file)


def load_all_snapshots(snapshot_dir=SNAPSHOT_DIR):
    """
    Loads all snapshots into a dictionary: {filename: dataframe}.
    This will help us calculate changes over time in later stages.
    """
    files = list_snapshots(snapshot_dir)
    snapshots = {}
    for f in files:
        snapshots[f.name] = load_snapshot(f)
    return snapshots


def load_snapshot_metadata(filepath):
    """
    Reads the companion .meta.json file if it exists.
    """
    path = Path(filepath)
    meta_path = path.with_suffix(".meta.json")
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def check_snapshot_data(df):
    """
    Checks if the dataframe has our required columns
    and counts missing values and total satellites.
    """
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    is_valid = len(missing_cols) == 0

    total_rows = len(df)
    unique_satellites = df["NORAD_CAT_ID"].nunique() if "NORAD_CAT_ID" in df.columns else 0

    # Count empty cells in required columns
    null_counts = {}
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            null_counts[col] = int(df[col].isna().sum())

    # Date range of the observations
    epoch_min = None
    epoch_max = None
    if "EPOCH" in df.columns and total_rows > 0:
        epochs = pd.to_datetime(df["EPOCH"], errors="coerce")
        epoch_min = str(epochs.min())
        epoch_max = str(epochs.max())

    return {
        "is_valid": is_valid,
        "total_records": total_rows,
        "unique_satellites": unique_satellites,
        "missing_columns": missing_cols,
        "null_counts": null_counts,
        "epoch_min": epoch_min,
        "epoch_max": epoch_max
    }
