import sys
from pathlib import Path
import pandas as pd

# Add project root so imports work smoothly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import RAW_DATA_DIR


def load_latest_data(data_dir=RAW_DATA_DIR):
    """
    Loads the latest satellite data file into a pandas dataframe.
    """
    path = Path(data_dir) / "latest_satellite_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return pd.read_csv(path)
