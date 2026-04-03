#!/usr/bin/env python3
"""Publish a deterministic simulated camera feed for the Phase 6 perception pipeline."""

from __future__ import annotations

import argparse
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image

from drone_perception.contracts import CameraConfig
from drone_perception.frame_generator import generate_frame


class SimCameraPublisher(Node):
    def __init__(
        self,
        *,
        topic: str,
        publish_rate_hz: float,
        frame_width: int,
        frame_height: int,
        target_radius_px: int,
        blackout_after_s: float,
        blackout_duration_s: float,
        frame_id: str,
    ) -> None:
        super().__init__("sim_camera_publisher")
        self._config = CameraConfig(
            frame_width=frame_width,
            frame_height=frame_height,
            publish_rate_hz=publish_rate_hz,
            target_radius_px=target_radius_px,
            blackout_after_s=blackout_after_s,
            blackout_duration_s=blackout_duration_s,
            frame_id=frame_id,
        )
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._publisher = self.create_publisher(Image, topic, qos)
        self._start_monotonic_s = time.monotonic()
        self.create_timer(1.0 / max(self._config.publish_rate_hz, 1.0), self._publish_frame)

    def _publish_frame(self) -> None:
        elapsed_s = time.monotonic() - self._start_monotonic_s
        frame = generate_frame(self._config, elapsed_s)
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._config.frame_id
        msg.height = int(frame.shape[0])
        msg.width = int(frame.shape[1])
        msg.encoding = "bgr8"
        msg.is_bigendian = 0
        msg.step = int(frame.shape[1] * frame.shape[2])
        msg.data = frame.tobytes()
        self._publisher.publish(msg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="/simulation/camera/image_raw")
    parser.add_argument("--publish-rate-hz", type=float, default=10.0)
    parser.add_argument("--frame-width", type=int, default=640)
    parser.add_argument("--frame-height", type=int, default=360)
    parser.add_argument("--target-radius-px", type=int, default=28)
    parser.add_argument("--blackout-after-s", type=float, default=-1.0)
    parser.add_argument("--blackout-duration-s", type=float, default=0.0)
    parser.add_argument("--frame-id", default="sim_camera")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rclpy.init()
    node = SimCameraPublisher(
        topic=args.topic,
        publish_rate_hz=args.publish_rate_hz,
        frame_width=args.frame_width,
        frame_height=args.frame_height,
        target_radius_px=args.target_radius_px,
        blackout_after_s=args.blackout_after_s,
        blackout_duration_s=args.blackout_duration_s,
        frame_id=args.frame_id,
    )
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
