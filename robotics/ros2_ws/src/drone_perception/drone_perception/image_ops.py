from __future__ import annotations

from dataclasses import dataclass


def _import_cv2():
    import cv2

    return cv2


def _import_numpy():
    import numpy as np

    return np


@dataclass(frozen=True)
class FrameSample:
    width: int
    height: int
    channels: int


def ros_image_to_bgr(image_msg):
    np = _import_numpy()
    cv2 = _import_cv2()

    width = int(image_msg.width)
    height = int(image_msg.height)
    encoding = str(image_msg.encoding).lower()
    raw = np.frombuffer(bytes(image_msg.data), dtype=np.uint8)

    if encoding in {"rgb8", "bgr8"}:
        expected_size = width * height * 3
        if raw.size != expected_size:
            raise ValueError(f"expected {expected_size} bytes for {encoding}, got {raw.size}")
        frame = raw.reshape((height, width, 3))
        if encoding == "rgb8":
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame

    if encoding == "mono8":
        expected_size = width * height
        if raw.size != expected_size:
            raise ValueError(f"expected {expected_size} bytes for mono8, got {raw.size}")
        frame = raw.reshape((height, width))
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    raise ValueError(f"unsupported image encoding: {image_msg.encoding}")


def preprocess_bgr_frame(frame, *, blur_kernel_size: int = 5):
    cv2 = _import_cv2()

    kernel = max(int(blur_kernel_size), 1)
    if kernel % 2 == 0:
        kernel += 1
    return cv2.GaussianBlur(frame, (kernel, kernel), 0.0)

