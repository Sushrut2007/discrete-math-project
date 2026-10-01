import numpy as np

# Standard Earth physical constants
EARTH_MU = 398600.4418      # Earth gravitational parameter in km^3 / s^2 (G * M)
EARTH_RADIUS_KM = 6378.137   # Earth equatorial radius in km (WGS84)
SECONDS_PER_DAY = 86400      # Number of seconds in one day
MINUTES_PER_DAY = 1440       # Number of minutes in one day

# Standard Low Earth Orbit (LEO) boundaries in kilometers
LEO_MIN_ALTITUDE_KM = 100.0   # Approximate atmospheric boundary
LEO_MAX_ALTITUDE_KM = 2000.0  # Standard upper ceiling for Low Earth Orbit


def calculate_orbital_period(mean_motion):
    """
    Calculates orbital period in minutes from mean motion (revolutions per day).
    Period (minutes) = 1440 / mean_motion
    """
    return MINUTES_PER_DAY / mean_motion


def calculate_semi_major_axis(mean_motion):
    """
    Calculates semi-major axis (a) in kilometers using Kepler's Third Law.
    Period T (seconds) = 86400 / mean_motion
    a = (mu * (T / (2 * pi))^2) ^ (1/3)
    """
    period_seconds = SECONDS_PER_DAY / mean_motion
    a = (EARTH_MU * (period_seconds / (2.0 * np.pi)) ** 2) ** (1.0 / 3.0)
    return a


def calculate_orbit_height(semi_major_axis):
    """
    Calculates average altitude (height) above Earth's surface in kilometers.
    height = semi_major_axis - Earth_radius
    """
    return semi_major_axis - EARTH_RADIUS_KM


def calculate_perigee(semi_major_axis, eccentricity):
    """
    Calculates lowest point of orbit (perigee altitude) in kilometers.
    perigee = a * (1 - e) - Earth_radius
    """
    return semi_major_axis * (1.0 - eccentricity) - EARTH_RADIUS_KM


def calculate_apogee(semi_major_axis, eccentricity):
    """
    Calculates highest point of orbit (apogee altitude) in kilometers.
    apogee = a * (1 + e) - Earth_radius
    """
    return semi_major_axis * (1.0 + eccentricity) - EARTH_RADIUS_KM


def calculate_orbital_speed(semi_major_axis):
    """
    Calculates average orbital speed in kilometers per second.
    speed = sqrt(mu / a)
    """
    return np.sqrt(EARTH_MU / semi_major_axis)


def add_orbital_features(df):
    """
    Takes a cleaned satellite dataframe and calculates all derived orbital features.
    Preserves all original columns (NORAD_CAT_ID, OBJECT_NAME, EPOCH, etc.).
    """
    if df is None or len(df) == 0:
        return df

    result = df.copy()

    # Extract required inputs
    n = result["MEAN_MOTION"]
    e = result["ECCENTRICITY"]

    # Calculate features
    a = calculate_semi_major_axis(n)

    result["orbital_period"] = calculate_orbital_period(n)
    result["semi_major_axis"] = a
    result["orbit_height"] = calculate_orbit_height(a)
    result["perigee"] = calculate_perigee(a, e)
    result["apogee"] = calculate_apogee(a, e)
    result["orbital_speed"] = calculate_orbital_speed(a)

    return result


def filter_leo_satellites(df, min_altitude=LEO_MIN_ALTITUDE_KM, max_altitude=LEO_MAX_ALTITUDE_KM):
    """
    Filters satellite dataframe to retain only objects in Low Earth Orbit (LEO).
    LEO is conventionally defined as orbits with mean altitude <= 2,000 km.
    Requires 'orbit_height' column (or calculates it if not present).
    """
    if df is None or len(df) == 0:
        return df

    result = df.copy()
    if "orbit_height" not in result.columns and "MEAN_MOTION" in result.columns:
        result = add_orbital_features(result)

    leo_df = result[(result["orbit_height"] >= min_altitude) & (result["orbit_height"] <= max_altitude)]
    return leo_df.reset_index(drop=True)
