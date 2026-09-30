from pathlib import Path

# Main folders for our project data
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "raw" / "snapshots"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Exact link to fetch active satellites in CSV format from Celestrak
CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv"

# Required columns we need for identifying satellites and calculating orbital changes
REQUIRED_COLUMNS = [
    "NORAD_CAT_ID",
    "OBJECT_NAME",
    "EPOCH",
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION"
]

# Collection cadence for the production pipeline (every 12 hours)
COLLECTION_INTERVAL_HOURS = 12

# Rolling window retention: keep snapshots from the last 30 days (~60 snapshots)
RETENTION_DAYS = 30
