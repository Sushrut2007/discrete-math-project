import pandas as pd
import numpy as np

def get_ml_reasons(sat):
    """
    Returns both an intuitive and a technical reason for the ML detector outcome.
    """
    ml_flag = int(sat.get('ml_flag', 0))
    score = float(sat.get('ml_anomaly_score', 0.0))
    cluster_id = sat.get('cluster_id', 0)
    ecc = float(sat.get('ECCENTRICITY', 0.0))
    alt = float(sat.get('orbit_height', 0.0))
    inc = float(sat.get('INCLINATION', 0.0))

    if ml_flag == 0:
        intuitive = "Orbits consistently with other satellites in its family."
        technical = f"Isolation Forest score: {score:.4f} (>= 0, conforming in Group {cluster_id})."
        return intuitive, technical

    # Flagged: determine dominant physical feature deviation
    if ecc > 0.02:
        intuitive = f"Oval-shaped orbit (eccentricity {ecc:.4f} vs typical < 0.005 in this group)."
    elif alt > 1100:
        intuitive = f"High altitude ({alt:,.0f} km) well above standard constellation shells."
    elif alt < 350:
        intuitive = f"Very low altitude ({alt:,.0f} km) near atmospheric entry boundary."
    elif inc < 45 or (73 <= inc <= 95):
        intuitive = f"Uncommon orbital tilt ({inc:.1f}°) outside standard 53° or 97° planes."
    else:
        intuitive = "Orbital features sit at the sparse outer edge of this family."

    technical = f"Isolation Forest score: {score:.4f} (< 0 threshold in K-Means Group {cluster_id})."
    return intuitive, technical


def get_dm_reasons(sat, global_mean=0.8306):
    """
    Returns both an intuitive and a technical reason for the DM graph detector outcome.
    """
    dm_flag = int(sat.get('dm_flag', 0))
    in_deg = int(sat.get('incoming_neighbor_count', 0))
    dist = float(sat.get('mean_neighbor_distance', 0.0))
    alt = float(sat.get('orbit_height', 0.0))
    inc = float(sat.get('INCLINATION', 0.0))

    if dm_flag == 0:
        intuitive = "Surrounded by close neighboring satellites in similar orbits."
        technical = f"Incoming neighbors: {in_deg} | Avg 5-NN distance: {dist:.4f} (<= catalog average {global_mean:.4f})."
        return intuitive, technical

    # Flagged: explain why in-degree is 0 and distance is high
    if alt > 1100:
        intuitive = f"High altitude corridor ({alt:,.0f} km) where satellites are spaced far apart."
    elif alt < 350:
        intuitive = f"Low decay orbit ({alt:,.0f} km) with no other satellites nearby."
    elif inc < 45 or (75 <= inc <= 95):
        intuitive = f"Uncommon tilt ({inc:.1f}°) placing it in an empty orbital slot."
    else:
        intuitive = "Empty orbital corridor with no other satellites flying close nearby."

    technical = f"In-degree = 0 (unreciprocated in directed 5-NN graph) and avg distance = {dist:.4f} > catalog threshold ({global_mean:.4f})."
    return intuitive, technical


def get_operator_explanation(sat, df=None):
    """
    Returns clear, simple reasons why a satellite was flagged.
    """
    score = int(sat.get('anomaly_score', 0))
    if score == 0:
        return [
            "Normal orbit: Altitude, tilt, and shape look typical for Low Earth Orbit.",
            "Normal neighbors: Other satellites fly in very similar orbits nearby."
        ]

    reasons = []
    
    # 1. Eccentricity check (Normal LEO orbits are near circular < 0.005)
    ecc = float(sat.get('ECCENTRICITY', 0.0))
    if ecc > 0.05:
        reasons.append(f"Oval-shaped orbit: Eccentricity is {ecc:.4f} (most satellites in LEO are nearly circular, below 0.005).")
    elif ecc > 0.015:
        reasons.append(f"Slightly oval orbit: Eccentricity is {ecc:.4f} (typical orbits stay under 0.005).")
        
    # 2. Altitude check (Most LEO satellites sit in 500-600 km shells)
    alt = float(sat.get('orbit_height', 0.0))
    if alt > 1200:
        reasons.append(f"Very high altitude: Flies at {alt:,.0f} km (over 90% of LEO satellites stay below 600 km).")
    elif alt < 350:
        reasons.append(f"Very low altitude: Flies at {alt:,.0f} km, near the edge of the atmosphere.")

    # 3. Inclination check
    inc = float(sat.get('INCLINATION', 0.0))
    is_common_inc = (
        (51.0 <= inc <= 55.0) or 
        (69.0 <= inc <= 72.0) or 
        (96.0 <= inc <= 99.0) or 
        (41.0 <= inc <= 44.0)
    )
    if not is_common_inc:
        if inc < 35:
            reasons.append(f"Unusually low tilt: Inclination is {inc:.1f}° (rare for LEO satellites).")
        elif 73 <= inc <= 95:
            reasons.append(f"Unusual tilt: Inclination is {inc:.1f}° (outside common 53° or 97° paths).")
        else:
            reasons.append(f"Uncommon tilt: Inclination is {inc:.1f}°.")

    # 4. Discrete Math Graph / Isolation Check
    dm_flag = bool(sat.get('dm_flag', 0))
    in_deg = int(sat.get('incoming_neighbor_count', 0))
    if dm_flag:
        reasons.append("No close neighbors: No other satellite in the catalog has this satellite in its 5 nearest neighbors, and its own neighbors are unusually far.")
    elif in_deg == 0:
        reasons.append("Outer edge: Sits at the sparse outer edge of its group.")

    # 5. Machine Learning Check
    ml_flag = bool(sat.get('ml_flag', 0))
    cluster_id = sat.get('cluster_id', 'N/A')
    if ml_flag and not any("Oval" in r or "altitude" in r for r in reasons):
        reasons.append(f"Stands out in its cluster: Isolation Forest marked it as an outlier inside Group {cluster_id}.")

    if not reasons:
        reasons.append("Combined factors: Slight differences across height, tilt, and speed made the model flag it.")

    return reasons
