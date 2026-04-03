from __future__ import annotations

import math
from typing import Iterable

from .contracts import SafetyConfig, SafetyDecision, SafetySignals

EARTH_RADIUS_M = 6_371_000.0


def horizontal_distance_m(
    lat_a_deg: float,
    lon_a_deg: float,
    lat_b_deg: float,
    lon_b_deg: float,
) -> float:
    lat_a_rad = math.radians(lat_a_deg)
    lon_a_rad = math.radians(lon_a_deg)
    lat_b_rad = math.radians(lat_b_deg)
    lon_b_rad = math.radians(lon_b_deg)

    delta_lat = lat_b_rad - lat_a_rad
    delta_lon = lon_b_rad - lon_a_rad
    haversine = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat_a_rad) * math.cos(lat_b_rad) * math.sin(delta_lon / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(max(0.0, min(1.0, haversine))))


def evaluate_safety(config: SafetyConfig, signals: SafetySignals) -> SafetyDecision | None:
    monitoring_window = signals.vehicle_armed or (signals.mission_active and not signals.vehicle_landed)

    if not monitoring_window:
        return None

    if signals.vehicle_connected and signals.vehicle_failsafe:
        return SafetyDecision(
            rule="px4_failsafe_active",
            action="abort_mission",
            source="vehicle_state",
            detail="PX4 entered failsafe state during safety monitoring",
        )

    if (
        config.geofence_enabled
        and signals.home_position_valid
        and signals.position_valid
        and (
            signals.distance_from_home_m > config.geofence_max_distance_m
            or signals.relative_altitude_m > config.geofence_max_altitude_m
        )
    ):
        return SafetyDecision(
            rule="geofence_breach",
            action=config.geofence_action,
            source="vehicle_state",
            detail=(
                "geofence rule triggered "
                f"(distance_m={signals.distance_from_home_m:.2f}, "
                f"relative_altitude_m={signals.relative_altitude_m:.2f})"
            ),
        )

    if signals.gps_lost:
        return SafetyDecision(
            rule="gps_loss",
            action=config.gps_loss_action,
            source="vehicle_state",
            detail="GPS position became invalid during safety monitoring",
        )

    if signals.rc_lost:
        return SafetyDecision(
            rule="rc_loss",
            action=config.rc_loss_action,
            source="fault_injection",
            detail="RC loss fault triggered in simulation",
        )

    if signals.data_link_lost:
        return SafetyDecision(
            rule="data_link_loss",
            action=config.data_link_loss_action,
            source="fault_injection",
            detail="Data link loss fault triggered in simulation",
        )

    if signals.perception_timeout:
        return SafetyDecision(
            rule="perception_timeout",
            action=config.perception_timeout_action,
            source="perception_watchdog",
            detail="Perception heartbeat timed out",
        )

    if signals.perception_latency_exceeded:
        return SafetyDecision(
            rule="perception_latency",
            action=config.perception_latency_action,
            source="perception_watchdog",
            detail="Perception pipeline latency exceeded the configured limit",
        )

    return None
