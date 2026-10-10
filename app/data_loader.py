import sys
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

proc_dir = project_root / "data" / "processed"

@st.cache_data
def load_full_data():
    int_path = proc_dir / "latest_integrated_results.csv"
    ml_path = proc_dir / "latest_ml_anomalies.csv"
    dm_path = proc_dir / "latest_graph_features.csv"
    
    if not all(p.exists() for p in [int_path, ml_path, dm_path]):
        return pd.DataFrame()
        
    df_int = pd.read_csv(int_path)
    
    cols_ml = ['NORAD_CAT_ID', 'cluster_id', 'anomaly_score', 'orbit_height', 'INCLINATION', 'ECCENTRICITY', 'semi_major_axis', 'EPOCH']
    df_ml = pd.read_csv(ml_path)
    cols_ml = [c for c in cols_ml if c in df_ml.columns]
    df_ml = df_ml[cols_ml]
    df_ml = df_ml.rename(columns={'anomaly_score': 'ml_anomaly_score'})
    
    df_dm = pd.read_csv(dm_path)[['NORAD_CAT_ID', 'incoming_neighbor_count', 'mean_neighbor_distance', 'k_nearest_distance']]
    
    df = pd.merge(df_int, df_ml, on='NORAD_CAT_ID', how='inner')
    df = pd.merge(df, df_dm, on='NORAD_CAT_ID', how='inner', suffixes=('', '_drop'))
    df = df.loc[:, ~df.columns.str.endswith('_drop')]
    
    df['global_mean_dist'] = df['mean_neighbor_distance'].mean()
    df['anomaly_score'] = df['anomaly_score'].fillna(0).astype(int)
    
    return df

def rerun_full_pipeline():
    """Executes the full pipeline: Features -> ML -> DM Graph -> Integration."""
    from src.features.feature_pipeline import process_and_save_latest_features
    from src.ml.ml_pipeline import run_ml_pipeline
    from src.dm.graph_pipeline import run_graph_pipeline
    from src.integration.integration_pipeline import run_integration_pipeline
    
    process_and_save_latest_features()
    run_ml_pipeline()
    run_graph_pipeline()
    final_df = run_integration_pipeline()
    
    st.cache_data.clear()
    return final_df

