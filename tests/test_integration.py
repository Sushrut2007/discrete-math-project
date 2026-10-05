import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from src.integration.integration_pipeline import combine_evidence

def test_combine_evidence():
    # Mock ML DataFrame
    ml_df = pd.DataFrame({
        'NORAD_CAT_ID': [1, 2, 3, 4],
        'OBJECT_NAME': ['SAT1', 'SAT2', 'SAT3', 'SAT4'],
        'anomaly_label': [1, -1, 1, -1] # 2 and 4 are anomalous
    })
    
    # Mock DM Graph DataFrame
    graph_df = pd.DataFrame({
        'NORAD_CAT_ID': [1, 2, 3, 4],
        'incoming_neighbor_count': [5, 0, 0, 0],
        'mean_neighbor_distance': [0.01, 0.5, 0.001, 0.8] 
        # Mean distance is ~0.327
        # 1: Not anomaly (in_degree > 0)
        # 2: Anomaly (in_degree == 0, dist > mean)
        # 3: Not anomaly (in_degree == 0, dist < mean)
        # 4: Anomaly (in_degree == 0, dist > mean)
    })
    
    # Mock Temporal DataFrame (Satellite 3 is missing, just to test left join)
    temporal_df = pd.DataFrame({
        'NORAD_CAT_ID': [1, 2, 4],
        'temporal_dm_label': [1, 1, -1]
        # 1: Normal
        # 2: Normal
        # 4: Anomaly
    })
    
    result = combine_evidence(ml_df, graph_df, temporal_df)
    
    # Check Satellite 1: ML=0, DM=0, Temp=0 -> Score = 0
    sat1 = result[result['NORAD_CAT_ID'] == 1].iloc[0]
    assert sat1['ml_flag'] == 0
    assert sat1['dm_flag'] == 0
    assert sat1['temporal_flag'] == 0
    assert sat1['anomaly_score'] == 0
    
    # Check Satellite 2: ML=1, DM=1, Temp=0 -> Score = 2
    sat2 = result[result['NORAD_CAT_ID'] == 2].iloc[0]
    assert sat2['ml_flag'] == 1
    assert sat2['dm_flag'] == 1
    assert sat2['temporal_flag'] == 0
    assert sat2['anomaly_score'] == 2
    
    # Check Satellite 3: ML=0, DM=0, Temp=0 (missing handled) -> Score = 0
    sat3 = result[result['NORAD_CAT_ID'] == 3].iloc[0]
    assert sat3['ml_flag'] == 0
    assert sat3['dm_flag'] == 0
    assert sat3['temporal_flag'] == 0
    assert sat3['anomaly_score'] == 0
    
    # Check Satellite 4: ML=1, DM=1, Temp=1 -> Score = 3
    sat4 = result[result['NORAD_CAT_ID'] == 4].iloc[0]
    assert sat4['ml_flag'] == 1
    assert sat4['dm_flag'] == 1
    assert sat4['temporal_flag'] == 1
    assert sat4['anomaly_score'] == 3

    assert sat4['interpretation'] == 'All three detected an anomaly'
    
    print("All integration tests passed!")

if __name__ == "__main__":
    test_combine_evidence()
