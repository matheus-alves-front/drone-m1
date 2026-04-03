from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CameraConfig:
    frame_width: int = 640
    frame_height: int = 360
    publish_rate_hz: float = 10.0
    target_radius_px: int = 28
    blackout_after_s: float = -1.0
    blackout_duration_s: float = 0.0
    frame_id: str = "sim_camera"
    target_label: str = "sim_target"
    image_format: str = "jpeg"
    blur_kernel_size: int = 5
    contrast_alpha: float = 1.1
    brightness_beta: float = 6.0


@dataclass(frozen=True)
class DetectorConfig:
    label: str = "sim_target"
    min_area_ratio: float = 0.002
    processing_delay_ms: float = 0.0
    processing_delay_after_s: float = -1.0


@dataclass(frozen=True)
class DetectionResult:
    detected: bool
    label: str = ""
    confidence: float = 0.0
    center_x: float = 0.0
    center_y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    area_ratio: float = 0.0


@dataclass(frozen=True)
class TrackState:
    active: bool = False
    track_id: int = 0
    age: int = 0
    label: str = ""
    confidence: float = 0.0
    center_x: float = 0.0
    center_y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    state: str = "idle"
    event_type: str = ""


@dataclass(frozen=True)
class TrackerConfig:
    lost_timeout_s: float = 1.0
