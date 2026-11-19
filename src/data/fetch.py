import sys
from pathlib import Path
import requests

# Add project root so imports work smoothly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import (
    CELESTRAK_URL,
    RAW_DATA_DIR
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

    if response.status_code == 403 and "GP data has not updated" in response.text:
        print("\nNotice from Celestrak:")
        print(response.text.strip())
        print(f"\nCelestrak updates its data every 2 hours.")
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


def save_raw_data(csv_text, save_dir=RAW_DATA_DIR, force=False):
    """
    Saves the downloaded CSV text to data/raw/latest_satellite_data.csv.
    Avoids overwriting if existing data is identical (unless force=True).
    Returns the file Path if saved/updated, or None if data was identical.
    """
    save_folder = Path(save_dir)
    save_folder.mkdir(parents=True, exist_ok=True)

    csv_file = save_folder / "latest_satellite_data.csv"
    raw_bytes = csv_text.encode("utf-8")

    # Check if existing file has identical content
    if not force and csv_file.exists():
        with open(csv_file, "rb") as f:
            existing_bytes = f.read()
        if existing_bytes == raw_bytes:
            print(f"Data unchanged: {csv_file.name} is already up to date.")
            return None

    # Write exact raw text to disk
    with open(csv_file, "wb") as f:
        f.write(raw_bytes)

    lines = csv_text.splitlines()
    total_satellites = max(0, len(lines) - 1)

    print(f"Data saved: {csv_file.name} ({total_satellites} satellites)")
    return csv_file


def collect_latest_data(url=CELESTRAK_URL, save_dir=RAW_DATA_DIR, force=False):
    """
    Convenience function that downloads and saves the latest satellite data in one call.
    Handles network errors and invalid responses gracefully.
    Returns the file Path if new data was saved, or None if unchanged or failed.
    """
    try:
        raw_text = fetch_celestrak_data(url=url)
    except requests.RequestException as e:
        print(f"Network error while connecting to Celestrak: {e}")
        return None
    except ValueError as e:
        print(f"Validation error in downloaded data: {e}")
        return None

    if raw_text is None:
        return None

    return save_raw_data(raw_text, save_dir=save_dir, force=force)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download and save active satellite data from Celestrak.")
    parser.add_argument("--url", default=CELESTRAK_URL, help="Custom download URL if needed")
    parser.add_argument("--force", action="store_true", help="Force overwrite even if data is unchanged")
    args = parser.parse_args()

    print("==================================================")
    print(" Satellite Data Fetcher")
    print(f" URL: {args.url}")
    print("==================================================")

    saved_file = collect_latest_data(url=args.url, force=args.force)
    if saved_file:
        print(f"\nDone! File updated: {saved_file}")
    else:
        print("\nNo updates saved (data is up to date or unavailable).")
