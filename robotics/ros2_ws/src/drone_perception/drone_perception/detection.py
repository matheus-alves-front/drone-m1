from __future__ import annotations

from dataclasses import dataclass


def _import_cv2():
    import cv2

    return cv2


def _import_numpy():
    import numpy as np

    return np


@dataclass(frozen=True)
class DetectionSample:
    detected: bool
    label: str
    confidence: float
    center_x: float
    center_y: float
    width: float
    height: float
    area_ratio: float


def detect_primary_target(
    frame_bgr,
    *,
    label: str = "sim_target",
    min_area_ratio: float = 0.002,
) -> DetectionSample:
    cv2 = _import_cv2()
    np = _import_numpy()

    height, width = frame_bgr.shape[:2]
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    lower_red_1 = np.array([0, 120, 80], dtype=np.uint8)
    upper_red_1 = np.array([10, 255, 255], dtype=np.uint8)
    lower_red_2 = np.array([170, 120, 80], dtype=np.uint8)
    upper_red_2 = np.array([180, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_red_1, upper_red_1) | cv2.inRange(hsv, lower_red_2, upper_red_2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), dtype=np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), dtype=np.uint8))

    contours, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return DetectionSample(
            detected=False,
            label=label,
            confidence=0.0,
            center_x=0.0,
            center_y=0.0,
            width=0.0,
            height=0.0,
            area_ratio=0.0,
        )

    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    area_ratio = area / float(width * height)
    if area_ratio < float(min_area_ratio):
        return DetectionSample(
            detected=False,
            label=label,
            confidence=0.0,
            center_x=0.0,
            center_y=0.0,
            width=0.0,
            height=0.0,
            area_ratio=area_ratio,
        )

    x, y, box_w, box_h = cv2.boundingRect(contour)
    confidence = min(1.0, area_ratio / max(float(min_area_ratio), 1e-6))
    return DetectionSample(
        detected=True,
        label=label,
        confidence=confidence,
        center_x=float(x + (box_w / 2.0)),
        center_y=float(y + (box_h / 2.0)),
        width=float(box_w),
        height=float(box_h),
        area_ratio=area_ratio,
    )
