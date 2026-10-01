import sys
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib
import requests

# Add project root so imports work smoothly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import (
    CELESTRAK_URL,
    SNAPSHOT_DIR,
    COLLECTION_INTERVAL_HOURS,
    RETENTION_DAYS
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_celestrak_data(url=CELESTRAK_URL, timeout=30):
    """
    Downloads raw satellite data directly from Celestrak as CSV text.
    """
    print(f"Connecting to Celestrak: {url}")

    response = requests.get(url, headers=headers, timeout=timeout)

    # Celestrak updates every 2 hours and pauses duplicate requests in between
    if response.status_code == 403 and "GP data has not updated" in response.text:
        print("\nNotice from Celestrak:")
        print(response.text.strip())
        print(f"\nCelestrak updates its data every 2 hours.")
        print(f"Our production pipeline will run every {COLLECTION_INTERVAL_HOURS} hours, which easily fits within this limit.")
        return None

    response.raise_for_status()
    raw_text = response.text

    if not raw_text or not raw_text.strip():
        raise ValueError("Received an empty file from Celestrak.")

    # Check that the header has our expected satellite columns
    first_line = raw_text.splitlines()[0]
    if "NORAD_CAT_ID" not in first_line or "EPOCH" not in first_line:
        raise ValueError(f"Received file does not have expected satellite columns: {first_line[:80]}")

    return raw_text


def cleanup_old_snapshots(save_dir=SNAPSHOT_DIR, max_days=RETENTION_DAYS):
    """
    Removes snapshots older than max_days to keep a clean 30-day rolling window.
    """
    folder = Path(save_dir)
    if not folder.exists():
        return 0

    now = datetime.now(timezone.utc)
    deleted_count = 0

    for csv_file in folder.glob("snapshot_*.csv"):
        name_part = csv_file.stem.replace("snapshot_", "")
        date_str = name_part[:17]  # YYYY-MM-DD_HHMMSS
        try:
            file_time = datetime.strptime(date_str, "%Y-%m-%d_%H%M%S").replace(tzinfo=timezone.utc)
            age_days = (now - file_time).total_seconds() / 86400.0
            if age_days > max_days:
                csv_file.unlink(missing_ok=True)
                meta_file = csv_file.with_suffix(".meta.json")
                if meta_file.exists():
                    meta_file.unlink(missing_ok=True)
                deleted_count += 1
        except ValueError:
            continue

    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} snapshot(s) older than {max_days} days.")
    return deleted_count


def save_snapshot(csv_text, save_dir=SNAPSHOT_DIR):
    """
    Saves the downloaded CSV text to data/raw/snapshots/ without changing any values.
    Also creates a small companion metadata file with download info.
    """
    save_folder = Path(save_dir)
    save_folder.mkdir(parents=True, exist_ok=True)

    # Build filename with current UTC timestamp
    now = datetime.now(timezone.utc)
    timestamp_string = now.strftime("%Y-%m-%d_%H%M%S")
    base_name = f"snapshot_{timestamp_string}"

    csv_file = save_folder / f"{base_name}.csv"
    meta_file = save_folder / f"{base_name}.meta.json"

    # Avoid replacing if two files are saved in the same second
    counter = 1
    while csv_file.exists():
        csv_file = save_folder / f"{base_name}_{counter:02d}.csv"
        meta_file = save_folder / f"{base_name}_{counter:02d}.meta.json"
        counter += 1

    # Write exact raw text to disk
    raw_bytes = csv_text.encode("utf-8")
    with open(csv_file, "wb") as f:
        f.write(raw_bytes)

    # Count rows and calculate file hash for tracking
    lines = csv_text.splitlines()
    total_satellites = max(0, len(lines) - 1)
    file_checksum = hashlib.sha256(raw_bytes).hexdigest()

    metadata = {
        "filename": csv_file.name,
        "download_time_utc": now.isoformat(),
        "total_records": total_satellites,
        "file_size_bytes": len(raw_bytes),
        "sha256": file_checksum,
        "collection_interval_hours": COLLECTION_INTERVAL_HOURS,
        "retention_days": RETENTION_DAYS
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Snapshot saved: {csv_file.name} ({total_satellites} satellites)")

    # Automatically clean up any snapshots older than 30 days
    cleanup_old_snapshots(save_dir=save_folder, max_days=RETENTION_DAYS)

    return csv_file


def collect_new_snapshot(url=CELESTRAK_URL, save_dir=SNAPSHOT_DIR):
    """
    Convenience function that downloads and saves a new snapshot in one call.
    """
    raw_text = fetch_celestrak_data(url=url)
    if raw_text is None:
        return None
    return save_snapshot(raw_text, save_dir=save_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download and save active satellite snapshots from Celestrak.")
    parser.add_argument("--url", default=CELESTRAK_URL, help="Custom download URL if needed")
    args = parser.parse_args()

    print("==================================================")
    print(" Satellite Snapshot Fetcher")
    print(f" URL: {args.url}")
    print(f" Cadence: Every {COLLECTION_INTERVAL_HOURS} hours")
    print(f" Rolling Retention: Keep last {RETENTION_DAYS} days (~60 snapshots)")
    print("==================================================")

    saved_file = collect_new_snapshot(url=args.url)
    if saved_file:
        print(f"\nDone! File saved to: {saved_file}")
    else:
        print("\nNo file saved at this time.")
