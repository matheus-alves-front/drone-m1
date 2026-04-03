#!/usr/bin/env python3
"""Wait until /drone/perception_heartbeat satisfies the requested conditions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import PerceptionHeartbeat


def parse_optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


@dataclass
class ObservationSummary:
    samples: int = 0
    last_stamp_ns: int = 0
    last_healthy: bool = False
    last_pipeline_latency_s: float = 0.0


class PerceptionHeartbeatWaiter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("perception_heartbeat_waiter")
        self._args = args
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._matched = False
        self._summary = ObservationSummary()
        self.create_subscription(PerceptionHeartbeat, args.topic, self._callback, qos)

    def _callback(self, msg: PerceptionHeartbeat) -> None:
        self._summary.samples += 1
        stamp_ns = (int(msg.stamp.sec) * 1_000_000_000) + int(msg.stamp.nanosec)
        self._summary.last_stamp_ns = stamp_ns
        self._summary.last_healthy = bool(msg.healthy)
        self._summary.last_pipeline_latency_s = float(msg.pipeline_latency_s)

        if stamp_ns < self._args.min_stamp_ns:
            return
        if self._args.healthy is not None and bool(msg.healthy) != self._args.healthy:
            return
        if self._args.max_latency_s is not None and float(msg.pipeline_latency_s) > self._args.max_latency_s:
            return
        if self._args.min_latency_s is not None and float(msg.pipeline_latency_s) < self._args.min_latency_s:
            return

        self._matched = True

    @property
    def matched(self) -> bool:
        return self._matched

    @property
    def summary(self) -> ObservationSummary:
        return self._summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="/drone/perception_heartbeat")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--healthy")
    parser.add_argument("--min-latency-s", type=float)
    parser.add_argument("--max-latency-s", type=float)
    parser.add_argument("--max-pipeline-latency-s", type=float, dest="max_latency_s")
    parser.add_argument("--min-stamp-ns", type=int, default=0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.healthy = parse_optional_bool(args.healthy)

    rclpy.init()
    node = PerceptionHeartbeatWaiter(args)
    deadline = time.monotonic() + args.timeout_s

    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.5)
            if node.matched:
                print(json.dumps(asdict(node.summary), sort_keys=True))
                return 0
    finally:
        summary_json = json.dumps(asdict(node.summary), sort_keys=True)
        node.destroy_node()
        rclpy.shutdown()

    print(summary_json)
    print(f"timed out waiting for {args.topic} after {args.timeout_s:.1f}s", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
