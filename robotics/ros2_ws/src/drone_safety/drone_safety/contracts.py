from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyConfig:
    geofence_enabled: bool = True
    geofence_max_distance_m: float = 12.0
    geofence_max_altitude_m: float = 8.0
    gps_loss_timeout_s: float = 1.5
    require_perception_heartbeat: bool = False
    perception_timeout_s: float = 2.0
    perception_max_latency_s: float = 0.5
    geofence_action: str = "return_to_home"
    gps_loss_action: str = "land"
    rc_loss_action: str = "return_to_home"
    data_link_loss_action: str = "return_to_home"
    perception_timeout_action: str = "land"
    perception_latency_action: str = "land"


@dataclass(frozen=True)
class SafetySignals:
    mission_active: bool
    vehicle_connected: bool
    vehicle_armed: bool
    vehicle_landed: bool
    vehicle_failsafe: bool
    position_valid: bool
    home_position_valid: bool
    distance_from_home_m: float = 0.0
    relative_altitude_m: float = 0.0
    gps_lost: bool = False
    rc_lost: bool = False
    data_link_lost: bool = False
    perception_timeout: bool = False
    perception_latency_exceeded: bool = False


@dataclass(frozen=True)
class SafetyDecision:
    rule: str
    action: str
    source: str
    detail: str
