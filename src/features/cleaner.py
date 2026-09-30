import pandas as pd

# List of essential columns that must not be empty
MANDATORY_COLUMNS = [
    "NORAD_CAT_ID",
    "EPOCH",
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION"
]


def clean_raw_data(df):
    """
    Cleans raw satellite dataframe:
    - Removes duplicate rows
    - Keeps the newest record if NORAD_CAT_ID appears multiple times
    - Drops any rows with missing values in required orbital columns
    - Filters out unphysical orbital numbers (e.g. negative speed or impossible eccentricity)
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    cleaned = df.copy()

    # Drop full duplicate rows
    cleaned = cleaned.drop_duplicates()

    # Drop rows missing any mandatory columns
    available_mandatory = [c for c in MANDATORY_COLUMNS if c in cleaned.columns]
    cleaned = cleaned.dropna(subset=available_mandatory)

    # Convert numeric columns to numeric types in case they were strings
    numeric_cols = ["MEAN_MOTION", "ECCENTRICITY", "INCLINATION"]
    for col in numeric_cols:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    if "NORAD_CAT_ID" in cleaned.columns:
        cleaned["NORAD_CAT_ID"] = pd.to_numeric(cleaned["NORAD_CAT_ID"], errors="coerce")

    # Drop any rows that failed conversion
    cleaned = cleaned.dropna(subset=available_mandatory)

    # Make NORAD_CAT_ID integer
    cleaned["NORAD_CAT_ID"] = cleaned["NORAD_CAT_ID"].astype(int)

    # Filter out unphysical orbital parameters:
    # 1. Mean motion must be positive (satellite must be orbiting)
    cleaned = cleaned[cleaned["MEAN_MOTION"] > 0]

    # 2. Eccentricity must be between 0 (circle) and < 1 (parabola/escape) for closed orbits
    cleaned = cleaned[(cleaned["ECCENTRICITY"] >= 0) & (cleaned["ECCENTRICITY"] < 1.0)]

    # 3. Inclination is between 0 and 180 degrees
    cleaned = cleaned[(cleaned["INCLINATION"] >= 0) & (cleaned["INCLINATION"] <= 180)]

    # If same satellite has multiple records in same file, keep the latest by EPOCH
    if "EPOCH" in cleaned.columns:
        cleaned["_epoch_dt"] = pd.to_datetime(cleaned["EPOCH"], errors="coerce")
        cleaned = cleaned.sort_values(by="_epoch_dt").drop_duplicates(subset=["NORAD_CAT_ID"], keep="last")
        cleaned = cleaned.drop(columns=["_epoch_dt"])
    else:
        cleaned = cleaned.drop_duplicates(subset=["NORAD_CAT_ID"], keep="last")

    cleaned = cleaned.reset_index(drop=True)
    return cleaned
