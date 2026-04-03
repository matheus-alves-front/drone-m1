#!/usr/bin/env python3
"""Wait until /drone/perception/tracked_object satisfies the requested conditions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import TrackedObject


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
    last_tracked: bool = False
    last_track_id: int = 0
    last_label: str = ""
    last_age: int = 0
    last_state: str = ""


class TrackedObjectWaiter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("tracked_object_waiter")
        self._args = args
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._matched = False
        self._summary = ObservationSummary()
        self.create_subscription(TrackedObject, args.topic, self._callback, qos)

    def _callback(self, msg: TrackedObject) -> None:
        self._summary.samples += 1
        stamp_ns = (int(msg.stamp.sec) * 1_000_000_000) + int(msg.stamp.nanosec)
        self._summary.last_stamp_ns = stamp_ns
        self._summary.last_tracked = bool(msg.tracked)
        self._summary.last_track_id = int(msg.track_id)
        self._summary.last_label = msg.label
        self._summary.last_age = int(msg.age)
        self._summary.last_state = msg.state

        if stamp_ns < self._args.min_stamp_ns:
            return
        if self._args.tracked is not None and bool(msg.tracked) != self._args.tracked:
            return
        if self._args.label is not None and msg.label != self._args.label:
            return
        if self._args.min_age is not None and int(msg.age) < self._args.min_age:
            return
        if self._args.state is not None and msg.state != self._args.state:
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
    parser.add_argument("--topic", default="/drone/perception/tracked_object")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--tracked")
    parser.add_argument("--label")
    parser.add_argument("--min-age", type=int)
    parser.add_argument("--state")
    parser.add_argument("--min-stamp-ns", type=int, default=0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.tracked = parse_optional_bool(args.tracked)

    rclpy.init()
    node = TrackedObjectWaiter(args)
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
