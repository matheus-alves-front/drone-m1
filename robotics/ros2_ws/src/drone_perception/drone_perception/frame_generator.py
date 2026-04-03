from __future__ import annotations

import math

import cv2
import numpy as np

from .contracts import CameraConfig


TARGET_COLOR_BGR = (0, 0, 255)
BACKGROUND_BGR = (24, 24, 24)


def synthetic_target_center(width: int, height: int, elapsed_s: float) -> tuple[int, int]:
    center_x = int(width * (0.5 + 0.32 * math.sin(0.55 * elapsed_s)))
    center_y = int(height * (0.5 + 0.22 * math.cos(0.85 * elapsed_s)))
    return center_x, center_y


def in_blackout_window(config: CameraConfig, elapsed_s: float) -> bool:
    return (
        config.blackout_after_s >= 0.0
        and config.blackout_duration_s > 0.0
        and config.blackout_after_s <= elapsed_s < (config.blackout_after_s + config.blackout_duration_s)
    )


def generate_frame(config: CameraConfig, elapsed_s: float) -> np.ndarray:
    frame = np.full((config.frame_height, config.frame_width, 3), BACKGROUND_BGR, dtype=np.uint8)

    for x in range(0, config.frame_width, 80):
        cv2.line(frame, (x, 0), (x, config.frame_height), (36, 36, 36), 1)
    for y in range(0, config.frame_height, 60):
        cv2.line(frame, (0, y), (config.frame_width, y), (36, 36, 36), 1)

    cv2.putText(
        frame,
        "SIM CAM",
        (16, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (180, 180, 180),
        2,
        cv2.LINE_AA,
    )

    if not in_blackout_window(config, elapsed_s):
        center = synthetic_target_center(config.frame_width, config.frame_height, elapsed_s)
        cv2.circle(frame, center, config.target_radius_px, TARGET_COLOR_BGR, -1)
        cv2.circle(frame, center, max(config.target_radius_px // 2, 6), (255, 255, 255), 2)

    return frame


def encode_frame(frame: np.ndarray, image_format: str) -> bytes:
    extension = ".jpg" if image_format == "jpeg" else ".png"
    ok, encoded = cv2.imencode(extension, frame)
    if not ok:
        raise RuntimeError("failed to encode synthetic frame")
    return encoded.tobytes()
