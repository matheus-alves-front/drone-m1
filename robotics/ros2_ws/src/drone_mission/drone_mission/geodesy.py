"""Small geodesy helpers used by the mission package."""

from __future__ import annotations

import math
from typing import Any


EARTH_RADIUS_M = 6_378_137.0


def offset_wgs84(latitude_deg: float, longitude_deg: float, north_m: float, east_m: float) -> tuple[float, float]:
    delta_lat = north_m / EARTH_RADIUS_M
    cos_lat = math.cos(math.radians(latitude_deg))
    if abs(cos_lat) < 1e-6:
        raise ValueError("cannot compute east offset near the poles")

    delta_lon = east_m / (EARTH_RADIUS_M * cos_lat)
    return latitude_deg + math.degrees(delta_lat), longitude_deg + math.degrees(delta_lon)


def offset_position(origin: Any, *, north_m: float, east_m: float):
    latitude_deg, longitude_deg = offset_wgs84(
        latitude_deg=float(origin.latitude_deg),
        longitude_deg=float(origin.longitude_deg),
        north_m=north_m,
        east_m=east_m,
    )
    return type(origin)(
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        absolute_altitude_m=float(origin.absolute_altitude_m),
        relative_altitude_m=float(origin.relative_altitude_m),
    )


def horizontal_distance_m(
    latitude_a_deg: Any,
    longitude_a_deg: Any,
    latitude_b_deg: float | None = None,
    longitude_b_deg: float | None = None,
) -> float:
    if latitude_b_deg is None and longitude_b_deg is None:
        sample_a = latitude_a_deg
        sample_b = longitude_a_deg
        latitude_a_deg = float(sample_a.latitude_deg)
        longitude_a_deg = float(sample_a.longitude_deg)
        latitude_b_deg = float(sample_b.latitude_deg)
        longitude_b_deg = float(sample_b.longitude_deg)
    elif latitude_b_deg is None or longitude_b_deg is None:
        raise TypeError("horizontal_distance_m expects either two samples or four coordinates")

    lat_a = math.radians(latitude_a_deg)
    lat_b = math.radians(latitude_b_deg)
    delta_lat = lat_b - lat_a
    delta_lon = math.radians(longitude_b_deg - longitude_a_deg)
    avg_lat = (lat_a + lat_b) / 2.0

    north_m = delta_lat * EARTH_RADIUS_M
    east_m = delta_lon * EARTH_RADIUS_M * math.cos(avg_lat)
    return math.hypot(north_m, east_m)
