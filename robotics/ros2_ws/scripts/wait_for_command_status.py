#!/usr/bin/env python3
"""Wait until /drone/vehicle_command_status satisfies a set of conditions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import VehicleCommandStatus


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
    last_command: str = ""
    last_px4_command: int = 0
    last_result: int = 0
    last_accepted: bool = False
    last_result_label: str = ""


class VehicleCommandStatusWaiter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("vehicle_command_status_waiter")
        self._args = args
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._matched = False
        self._summary = ObservationSummary()
        self.create_subscription(VehicleCommandStatus, args.topic, self._callback, qos)

    def _callback(self, msg: VehicleCommandStatus) -> None:
        self._summary.samples += 1
        stamp_ns = (int(msg.stamp.sec) * 1_000_000_000) + int(msg.stamp.nanosec)
        self._summary.last_stamp_ns = stamp_ns
        self._summary.last_command = msg.command
        self._summary.last_px4_command = int(msg.px4_command)
        self._summary.last_result = int(msg.result)
        self._summary.last_accepted = bool(msg.accepted)
        self._summary.last_result_label = msg.result_label

        if stamp_ns < self._args.min_stamp_ns:
            return

        if self._args.command is not None and msg.command != self._args.command:
            return
        if self._args.px4_command is not None and int(msg.px4_command) != self._args.px4_command:
            return
        if self._args.accepted is not None and bool(msg.accepted) != self._args.accepted:
            return
        if self._args.result is not None and int(msg.result) != self._args.result:
            return
        if self._args.result_label is not None and msg.result_label != self._args.result_label:
            return

        self.get_logger().info(
            "vehicle command status matched "
            f"(command={msg.command}, px4_command={msg.px4_command}, result={msg.result}, "
            f"accepted={msg.accepted}, result_label={msg.result_label})",
        )
        self._matched = True

    @property
    def matched(self) -> bool:
        return self._matched

    @property
    def summary(self) -> ObservationSummary:
        return self._summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="/drone/vehicle_command_status")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--command")
    parser.add_argument("--px4-command", type=int)
    parser.add_argument("--accepted")
    parser.add_argument("--result", type=int)
    parser.add_argument("--result-label")
    parser.add_argument("--min-stamp-ns", type=int, default=0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.accepted = parse_optional_bool(args.accepted)

    rclpy.init()
    node = VehicleCommandStatusWaiter(args)
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
    print(
        f"timed out waiting for {args.topic} after {args.timeout_s:.1f}s",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
