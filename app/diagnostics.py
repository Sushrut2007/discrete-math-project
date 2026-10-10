import pandas as pd
import numpy as np

def get_operator_explanation(sat, df):
    """
    Generates plain-English, physical orbital reasons why a satellite was flagged.
    Translates raw numbers into operational insights for a satellite operator.
    """
    score = int(sat.get('anomaly_score', 0))
    if score == 0:
        return [
            "Nominal Orbit: All orbital parameters (altitude, eccentricity, inclination) align closely with common LEO constellation shells.",
            "Normal Neighborhood: Closely surrounded by peer satellites sharing the same orbital plane."
        ]

    reasons = []
    
    # 1. Eccentricity check (Normal LEO orbits are near circular < 0.005)
    ecc = float(sat.get('ECCENTRICITY', 0.0))
    if ecc > 0.05:
        reasons.append(f"Highly Elliptical Orbit: Eccentricity is {ecc:.4f} (typical LEO satellites are nearly circular, below 0.005).")
    elif ecc > 0.015:
        reasons.append(f"Moderate Ellipticity: Eccentricity is {ecc:.4f} (above typical constellation bounds of < 0.005).")
        
    # 2. Altitude check (Most LEO satellites sit in 500-600 km mega-constellation shells)
    alt = float(sat.get('orbit_height', 0.0))
    if alt > 1200:
        reasons.append(f"High LEO Altitude: Orbiting at {alt:,.1f} km, near the upper boundary of Low Earth Orbit (over 90% of LEO traffic is below 600 km).")
    elif alt < 350:
        reasons.append(f"Very Low Orbit: Orbiting at {alt:,.1f} km, experiencing elevated atmospheric drag.")

    # 3. Inclination check
    inc = float(sat.get('INCLINATION', 0.0))
    # Common LEO bands: ~53 deg (Starlink), ~70 deg, ~97-98 deg (SSO), ~51.6 deg (ISS)
    is_common_inc = (
        (51.0 <= inc <= 55.0) or 
        (69.0 <= inc <= 72.0) or 
        (96.0 <= inc <= 99.0) or 
        (41.0 <= inc <= 44.0)
    )
    if not is_common_inc:
        if inc < 35:
            reasons.append(f"Uncommon Low Inclination: Orbit tilted at {inc:.2f}° (infrequent for active LEO spacecraft).")
        elif 73 <= inc <= 95:
            reasons.append(f"Non-Standard Polar Inclination: Orbit tilted at {inc:.2f}° (outside standard Sun-Synchronous corridors).")
        else:
            reasons.append(f"Uncommon Inclination: Orbit tilted at {inc:.2f}°.")

    # 4. Discrete Math Graph / Isolation Check
    dm_flag = bool(sat.get('dm_flag', 0))
    in_deg = int(sat.get('incoming_neighbor_count', 0))
    if dm_flag:
        reasons.append("Isolated Orbital Corridor: No other satellites share this trajectory, leaving it structurally isolated in the catalog.")
    elif in_deg == 0:
        reasons.append("Corridor Boundary: Positioned at the sparse outer edge of its orbital cluster.")

    # 5. Machine Learning Check
    ml_flag = bool(sat.get('ml_flag', 0))
    cluster_id = sat.get('cluster_id', 'N/A')
    if ml_flag and not any("Elliptical" in r or "Altitude" in r for r in reasons):
        reasons.append(f"Cluster Outlier: Statistical features deviate significantly from other satellites in Cluster {cluster_id}.")

    if not reasons:
        reasons.append("Subtle Multi-Parameter Deviation: Combination of altitude, inclination, and motion slightly outside standard bounds.")

    return reasons
