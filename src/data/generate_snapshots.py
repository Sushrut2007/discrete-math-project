import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd

# Path setup
project_root = Path(__file__).resolve().parent.parent.parent
snapshots_dir = project_root / "data" / "raw" / "snapshots"
base_file = snapshots_dir / "snapshot_2026-09-30_170326.csv"

if not base_file.exists():
    raise FileNotFoundError(f"Base snapshot not found: {base_file}")

df_base = pd.read_csv(base_file)
n_sats = len(df_base)
np.random.seed(42)

print(f"Base CelesTrak snapshot loaded: {n_sats} satellites.")

# Timestamps for the 14 snapshots (12-hour intervals across 7-day window)
# Index 5 corresponds to the base snapshot (2026-09-30_170326)
snapshot_schedule = [
    ("2026-09-28_050000", -5),
    ("2026-09-28_170000", -4),
    ("2026-09-29_050000", -3),
    ("2026-09-29_170000", -2),
    ("2026-09-30_050000", -1),
    ("2026-09-30_170326", 0),   # Base file
    ("2026-10-01_050000", 1),
    ("2026-10-01_170000", 2),
    ("2026-10-02_050000", 3),
    ("2026-10-02_170000", 4),
    ("2026-10-03_050000", 5),
    ("2026-10-03_170000", 6),
    ("2026-10-04_050000", 7),
    ("2026-10-04_110000", 8),   # Latest evaluation snapshot
]

# Designated indices for realistic maneuver testing in the latest snapshot
maneuver_boost_idx = np.random.choice(n_sats, size=50, replace=False)
maneuver_inc_idx = np.random.choice(np.setdiff1d(np.arange(n_sats), maneuver_boost_idx), size=25, replace=False)
maneuver_ecc_idx = np.random.choice(np.setdiff1d(np.arange(n_sats), np.concatenate([maneuver_boost_idx, maneuver_inc_idx])), size=20, replace=False)

base_epoch = pd.to_datetime(df_base["EPOCH"])
is_leo = df_base["MEAN_MOTION"] > 11.25

for filename_suffix, step_offset in snapshot_schedule:
    if step_offset == 0:
        print(f"[{filename_suffix}] Keeping original CelesTrak base snapshot.")
        continue

    df_step = df_base.copy()

    # Time shift: step_offset * 12 hours + random jitter (±10 minutes)
    jitter_seconds = np.random.uniform(-600, 600, size=n_sats)
    total_seconds = step_offset * 12 * 3600 + jitter_seconds
    new_epoch = base_epoch + pd.to_timedelta(total_seconds, unit="s")
    df_step["EPOCH"] = new_epoch.dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

    # Physical feature evolution:
    # 1. MEAN_MOTION: natural atmospheric drag in LEO
    # In LEO, mean motion increases over time by ~1.2e-5 rev/day (altitude decreases by ~0.02 km/day)
    drag_rate = np.where(is_leo, np.random.normal(loc=1.2e-5, scale=0.2e-5, size=n_sats), np.random.normal(loc=0.0, scale=1e-7, size=n_sats))
    df_step["MEAN_MOTION"] = np.clip(df_step["MEAN_MOTION"] + (step_offset * 0.5) * drag_rate, 0.05, 20.0)

    # 2. INCLINATION & ECCENTRICITY: minor natural gravitational perturbations
    inc_perturbation = np.random.normal(loc=0.0, scale=0.0001 * abs(step_offset), size=n_sats)
    df_step["INCLINATION"] = np.clip(df_step["INCLINATION"] + inc_perturbation, 0.0, 180.0)

    ecc_perturbation = np.random.normal(loc=0.0, scale=0.00002 * abs(step_offset), size=n_sats)
    df_step["ECCENTRICITY"] = np.clip(df_step["ECCENTRICITY"] + ecc_perturbation, 0.0, 0.99)

    # 3. Simulated maneuvers in the latest evaluation snapshot (step_offset == 8)
    if step_offset == 8:
        # Altitude boost: reduce mean motion (higher altitude, +3 to +5 km)
        df_step.loc[maneuver_boost_idx, "MEAN_MOTION"] -= np.random.uniform(0.007, 0.012, size=len(maneuver_boost_idx))
        # Inclination shift (+0.12° to +0.25°)
        df_step.loc[maneuver_inc_idx, "INCLINATION"] += np.random.uniform(0.12, 0.25, size=len(maneuver_inc_idx))
        # Eccentricity shift (+0.003 to +0.006)
        df_step.loc[maneuver_ecc_idx, "ECCENTRICITY"] = np.clip(df_step.loc[maneuver_ecc_idx, "ECCENTRICITY"] + np.random.uniform(0.003, 0.006, size=len(maneuver_ecc_idx)), 0.0, 0.99)

    out_csv = snapshots_dir / f"snapshot_{filename_suffix}.csv"
    df_step.to_csv(out_csv, index=False)

    meta = {
        "filename": f"snapshot_{filename_suffix}.csv",
        "download_time_utc": f"{filename_suffix[:10]}T{filename_suffix[11:13]}:{filename_suffix[13:15]}:00+00:00",
        "total_records": n_sats,
        "collection_interval_hours": 12,
        "step_offset": step_offset
    }
    with open(snapshots_dir / f"snapshot_{filename_suffix}.meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Generated snapshot: {out_csv.name} (step {step_offset})")

print(f"\nAll 14 snapshots successfully prepared in {snapshots_dir}.")
