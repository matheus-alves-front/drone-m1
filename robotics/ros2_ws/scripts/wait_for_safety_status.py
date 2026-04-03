#!/usr/bin/env python3
"""Wait until /drone/safety_status satisfies a set of conditions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import SafetyStatus


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
    last_active: bool = False
    last_mission_abort_requested: bool = False
    last_vehicle_command_sent: bool = False
    last_rule: str = ""
    last_action: str = ""
    last_source: str = ""
    last_detail: str = ""
    last_trigger_count: int = 0


class SafetyStatusWaiter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("safety_status_waiter")
        self._args = args
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._matched = False
        self._summary = ObservationSummary()
        self.create_subscription(SafetyStatus, args.topic, self._callback, qos)

    def _callback(self, msg: SafetyStatus) -> None:
        self._summary.samples += 1
        stamp_ns = (int(msg.stamp.sec) * 1_000_000_000) + int(msg.stamp.nanosec)
        self._summary.last_stamp_ns = stamp_ns
        self._summary.last_active = bool(msg.active)
        self._summary.last_mission_abort_requested = bool(msg.mission_abort_requested)
        self._summary.last_vehicle_command_sent = bool(msg.vehicle_command_sent)
        self._summary.last_rule = msg.rule
        self._summary.last_action = msg.action
        self._summary.last_source = msg.source
        self._summary.last_detail = msg.detail
        self._summary.last_trigger_count = int(msg.trigger_count)

        if stamp_ns < self._args.min_stamp_ns:
            return
        if self._args.active is not None and bool(msg.active) != self._args.active:
            return
        if (
            self._args.mission_abort_requested is not None
            and bool(msg.mission_abort_requested) != self._args.mission_abort_requested
        ):
            return
        if (
            self._args.vehicle_command_sent is not None
            and bool(msg.vehicle_command_sent) != self._args.vehicle_command_sent
        ):
            return
        if self._args.rule is not None and msg.rule != self._args.rule:
            return
        if self._args.action is not None and msg.action != self._args.action:
            return
        if self._args.source is not None and msg.source != self._args.source:
            return
        if self._args.min_trigger_count is not None and int(msg.trigger_count) < self._args.min_trigger_count:
            return

        self.get_logger().info(
            "safety status matched "
            f"(active={msg.active}, rule={msg.rule}, action={msg.action}, source={msg.source}, "
            f"mission_abort_requested={msg.mission_abort_requested}, "
            f"vehicle_command_sent={msg.vehicle_command_sent}, trigger_count={msg.trigger_count})",
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
    parser.add_argument("--topic", default="/drone/safety_status")
    parser.add_argument("--timeout-s", type=float, default=60.0)
    parser.add_argument("--active")
    parser.add_argument("--mission-abort-requested")
    parser.add_argument("--vehicle-command-sent")
    parser.add_argument("--rule")
    parser.add_argument("--action")
    parser.add_argument("--source")
    parser.add_argument("--min-trigger-count", type=int)
    parser.add_argument("--min-stamp-ns", type=int, default=0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.active = parse_optional_bool(args.active)
    args.mission_abort_requested = parse_optional_bool(args.mission_abort_requested)
    args.vehicle_command_sent = parse_optional_bool(args.vehicle_command_sent)

    rclpy.init()
    node = SafetyStatusWaiter(args)
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
