"""Pure helpers for the real PX4-backed ROS 2 bridge."""

from __future__ import annotations

import math


NAV_STATE_NAMES = {
    0: "MANUAL",
    1: "ALTCTL",
    2: "POSCTL",
    3: "AUTO_MISSION",
    4: "AUTO_LOITER",
    5: "AUTO_RTL",
    10: "ACRO",
    12: "DESCEND",
    13: "TERMINATION",
    14: "OFFBOARD",
    15: "STAB",
    17: "AUTO_TAKEOFF",
    18: "AUTO_LAND",
    19: "AUTO_FOLLOW_TARGET",
    20: "AUTO_PRECLAND",
    21: "ORBIT",
}

EARTH_RADIUS_M = 6371000.0


def nav_state_name(nav_state: int) -> str:
    """Map PX4 navigation state enum values to readable domain names."""
    return NAV_STATE_NAMES.get(nav_state, f"UNKNOWN_{nav_state}")


def normalize_command(command: str) -> str:
    """Normalize external commands before mapping them to PX4 commands."""
    return command.strip().lower().replace("-", "_").replace(" ", "_")


def resolve_takeoff_altitude(requested_altitude_m: float, default_altitude_m: float) -> float:
    """Choose a valid takeoff altitude while keeping the contract deterministic."""
    if requested_altitude_m > 0.0:
        return requested_altitude_m
    return max(default_altitude_m, 0.5)


def geodetic_offset_m(
    origin_lat_deg: float,
    origin_lon_deg: float,
    target_lat_deg: float,
    target_lon_deg: float,
) -> tuple[float, float]:
    """Approximate north/east offsets in meters for short mission legs."""
    delta_lat_rad = math.radians(target_lat_deg - origin_lat_deg)
    delta_lon_rad = math.radians(target_lon_deg - origin_lon_deg)
    mean_lat_rad = math.radians((origin_lat_deg + target_lat_deg) / 2.0)
    north_m = delta_lat_rad * EARTH_RADIUS_M
    east_m = delta_lon_rad * EARTH_RADIUS_M * math.cos(mean_lat_rad)
    return north_m, east_m


def local_position_from_reference(
    *,
    ref_lat_deg: float,
    ref_lon_deg: float,
    ref_alt_m: float,
    target_lat_deg: float,
    target_lon_deg: float,
    target_alt_m: float,
) -> tuple[float, float, float]:
    """Convert a WGS84 target to local NED using the EKF reference origin."""
    north_m, east_m = geodetic_offset_m(ref_lat_deg, ref_lon_deg, target_lat_deg, target_lon_deg)
    down_m = ref_alt_m - target_alt_m
    return north_m, east_m, down_m
