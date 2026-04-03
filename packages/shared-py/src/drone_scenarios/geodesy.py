from __future__ import annotations

import math

from .contracts import PositionSample

EARTH_RADIUS_M = 6_378_137.0


def offset_position(origin: PositionSample, north_m: float, east_m: float) -> PositionSample:
    delta_lat = north_m / EARTH_RADIUS_M
    cos_lat = math.cos(math.radians(origin.latitude_deg))
    if abs(cos_lat) < 1e-6:
        raise ValueError("cannot compute east offset near the poles")

    delta_lon = east_m / (EARTH_RADIUS_M * cos_lat)
    return PositionSample(
        latitude_deg=origin.latitude_deg + math.degrees(delta_lat),
        longitude_deg=origin.longitude_deg + math.degrees(delta_lon),
        absolute_altitude_m=origin.absolute_altitude_m,
        relative_altitude_m=origin.relative_altitude_m,
    )


def horizontal_distance_m(a: PositionSample, b: PositionSample) -> float:
    lat_a = math.radians(a.latitude_deg)
    lat_b = math.radians(b.latitude_deg)
    delta_lat = lat_b - lat_a
    delta_lon = math.radians(b.longitude_deg - a.longitude_deg)
    avg_lat = (lat_a + lat_b) / 2.0

    north_m = delta_lat * EARTH_RADIUS_M
    east_m = delta_lon * EARTH_RADIUS_M * math.cos(avg_lat)
    return math.hypot(north_m, east_m)
