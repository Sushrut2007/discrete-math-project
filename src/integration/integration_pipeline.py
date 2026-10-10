import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.constants import PROCESSED_DIR

def combine_evidence(ml_df, graph_df):
    """
    Combines ML and DM graph evidence into a single anomaly score (0 to 2).
    """
    # Merge ML and Graph
    merged_df = pd.merge(
        ml_df[['NORAD_CAT_ID', 'OBJECT_NAME', 'anomaly_label']], 
        graph_df[['NORAD_CAT_ID', 'incoming_neighbor_count', 'mean_neighbor_distance']], 
        on='NORAD_CAT_ID', 
        how='inner'
    )
    
    # 1. ML Flag: anomaly_label == -1
    merged_df['ml_flag'] = (merged_df['anomaly_label'] == -1).astype(int)
    
    # 2. DM Flag: incoming_neighbor_count == 0 AND mean_neighbor_distance > global_mean
    global_mean_dist = merged_df['mean_neighbor_distance'].mean()
    merged_df['dm_flag'] = (
        (merged_df['incoming_neighbor_count'] == 0) & 
        (merged_df['mean_neighbor_distance'] > global_mean_dist)
    ).astype(int)
    
    # Sum the flags
    merged_df['anomaly_score'] = merged_df['ml_flag'] + merged_df['dm_flag']
    
    # Interpretation Map
    score_mapping = {
        0: 'Neither ML nor DM flagged the satellite',
        1: 'Either ML or DM flagged the satellite',
        2: 'Both ML and DM flagged the satellite'
    }
    merged_df['interpretation'] = merged_df['anomaly_score'].map(score_mapping)
    
    return merged_df

def run_integration_pipeline():
    """
    Loads processed outputs from ML and DM pipelines and computes final scores.
    """
    ml_path = Path(PROCESSED_DIR) / "latest_ml_anomalies.csv"
    graph_path = Path(PROCESSED_DIR) / "latest_graph_features.csv"
    
    if not ml_path.exists() or not graph_path.exists():
        raise FileNotFoundError(f"Missing one or more pipeline outputs in {PROCESSED_DIR}")
        
    ml_df = pd.read_csv(ml_path)
    graph_df = pd.read_csv(graph_path)
    
    final_df = combine_evidence(ml_df, graph_df)
    
    out_file = Path(PROCESSED_DIR) / "latest_integrated_results.csv"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(out_file, index=False)
    
    return final_df

if __name__ == "__main__":
    final_results = run_integration_pipeline()
    print("--- Integration Pipeline ---")
    
    counts = final_results['anomaly_score'].value_counts().sort_index()
    print("\nAnomaly Score Distribution:")
    for score in range(3):
        count = counts.get(score, 0)
        print(f"Score {score}: {count} satellites")
