import sys
from pathlib import Path
import pandas as pd

# Add project root so imports work smoothly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import PROCESSED_DIR
from src.data.snapshot_loader import load_latest_data
from src.features.preprocess import clean_raw_data, standardize_features, DEFAULT_FEATURE_COLUMNS
from src.features.orbital_features import add_orbital_features


def prepare_features(df=None, feature_cols=None):
    """
    Main pipeline function for this branch:
    1. Loads the latest raw data (if df is not provided)
    2. Cleans and validates raw satellite rows
    3. Calculates derived orbital features (a, period, apogee, perigee, speed, height)
    4. Standardizes numerical features for later ML and Graph analysis
    5. Preserves all identifying fields (NORAD_CAT_ID, OBJECT_NAME, EPOCH)

    Returns:
        processed_df: Fully prepared dataframe
        scaler_params: Means and stds used for standardization
    """
    if df is None:
        print("Loading latest satellite data...")
        df = load_latest_data()

    # Step 1: Clean raw data
    cleaned_df = clean_raw_data(df)
    print(f"Cleaned data: {len(cleaned_df)} satellites retained")

    # Step 2: Add orbital features
    orbital_df = add_orbital_features(cleaned_df)
    print("Added orbital features: period, semi_major_axis, orbit_height, perigee, apogee, orbital_speed")

    # Step 3: Standardize core numerical features
    processed_df, scaler_params = standardize_features(orbital_df, feature_cols=feature_cols)
    print("Standardized features ready for ML and Graph algorithms")

    return processed_df, scaler_params


def process_and_save_latest_features(output_filename="latest_features.csv"):
    """
    Runs the full feature preparation pipeline and saves the result to data/processed/.
    """
    processed_df, scaler_params = prepare_features()

    out_folder = Path(PROCESSED_DIR)
    out_folder.mkdir(parents=True, exist_ok=True)
    out_file = out_folder / output_filename

    processed_df.to_csv(out_file, index=False)
    print(f"Saved processed features to: {out_file}")
    return processed_df


if __name__ == "__main__":
    print("--- Running Orbital Feature Pipeline ---")
    df_result = process_and_save_latest_features()
    print(f"Done! Processed {len(df_result)} satellites with {len(df_result.columns)} columns.")
