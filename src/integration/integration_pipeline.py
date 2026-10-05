import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import PROCESSED_DIR

def combine_evidence(ml_df, graph_df, temporal_df):
    """
    Combines ML, DM graph, and temporal evidence into a single anomaly score (0 to 3).
    """
    # Merge ML and Graph
    merged_df = pd.merge(
        ml_df[['NORAD_CAT_ID', 'OBJECT_NAME', 'anomaly_label']], 
        graph_df[['NORAD_CAT_ID', 'incoming_neighbor_count', 'mean_neighbor_distance']], 
        on='NORAD_CAT_ID', 
        how='inner'
    )
    
    # Merge Temporal (Left join because not all satellites may have temporal history)
    merged_df = pd.merge(
        merged_df,
        temporal_df[['NORAD_CAT_ID', 'temporal_dm_label']],
        on='NORAD_CAT_ID',
        how='left'
    )
    
    # 1. ML Flag: anomaly_label == -1
    merged_df['ml_flag'] = (merged_df['anomaly_label'] == -1).astype(int)
    
    # 2. DM Flag: incoming_neighbor_count == 0 AND mean_neighbor_distance > global_mean
    global_mean_dist = merged_df['mean_neighbor_distance'].mean()
    merged_df['dm_flag'] = (
        (merged_df['incoming_neighbor_count'] == 0) & 
        (merged_df['mean_neighbor_distance'] > global_mean_dist)
    ).astype(int)
    
    # 3. Temporal Flag: temporal_dm_label == -1
    merged_df['temporal_flag'] = (merged_df['temporal_dm_label'] == -1).astype(int)
    
    # Sum the flags
    merged_df['anomaly_score'] = merged_df['ml_flag'] + merged_df['dm_flag'] + merged_df['temporal_flag']
    
    # Interpretation Map
    score_mapping = {
        0: 'No anomaly detected',
        1: 'One source detected an anomaly',
        2: 'Two sources detected an anomaly',
        3: 'All three detected an anomaly'
    }
    merged_df['interpretation'] = merged_df['anomaly_score'].map(score_mapping)
    
    return merged_df

def run_integration_pipeline():
    """
    Loads processed outputs from ML, DM, and Temporal pipelines and computes final scores.
    """
    ml_path = Path(PROCESSED_DIR) / "latest_ml_anomalies.csv"
    graph_path = Path(PROCESSED_DIR) / "latest_graph_features.csv"
    temporal_path = Path(PROCESSED_DIR) / "latest_temporal_features.csv"
    
    if not ml_path.exists() or not graph_path.exists() or not temporal_path.exists():
        raise FileNotFoundError(f"Missing one or more pipeline outputs in {PROCESSED_DIR}")
        
    ml_df = pd.read_csv(ml_path)
    graph_df = pd.read_csv(graph_path)
    temporal_df = pd.read_csv(temporal_path)
    
    final_df = combine_evidence(ml_df, graph_df, temporal_df)
    
    out_file = Path(PROCESSED_DIR) / "latest_integrated_results.csv"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(out_file, index=False)
    
    return final_df

if __name__ == "__main__":
    final_results = run_integration_pipeline()
    print("--- Integration Pipeline ---")
    
    counts = final_results['anomaly_score'].value_counts().sort_index()
    print("\nAnomaly Score Distribution:")
    for score in range(4):
        count = counts.get(score, 0)
        print(f"Score {score}: {count} satellites")
