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
    temp_path = proc_dir / "latest_temporal_features.csv"
    
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
    
    if temp_path.exists():
        df_temp = pd.read_csv(temp_path)[['NORAD_CAT_ID', 'latest_delta_a', 'latest_delta_e', 'latest_delta_i', 'history_transitions_count']]
        df = pd.merge(df, df_temp, on='NORAD_CAT_ID', how='left')
    else:
        df['latest_delta_a'] = np.nan
        df['latest_delta_e'] = np.nan
        df['latest_delta_i'] = np.nan
        df['history_transitions_count'] = 0
        
    df['global_mean_dist'] = df['mean_neighbor_distance'].mean()
    df['anomaly_score'] = df['anomaly_score'].fillna(0).astype(int)
    
    return df
