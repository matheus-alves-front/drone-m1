#!/usr/bin/env python3
"""Wait until /drone/mission_status satisfies a set of conditions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import MissionStatus


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
    last_mission_id: str = ""
    last_phase: str = ""
    last_detail: str = ""
    last_active: bool = False
    last_terminal: bool = False
    last_succeeded: bool = False
    last_completed: bool = False
    last_aborted: bool = False
    last_failed: bool = False
    last_current_waypoint_index: int = 0
    last_total_waypoints: int = 0
    last_last_command: str = ""


class MissionStatusWaiter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("mission_status_waiter")
        self._args = args
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._matched = False
        self._summary = ObservationSummary()
        self.create_subscription(MissionStatus, args.topic, self._callback, qos)

    def _callback(self, msg: MissionStatus) -> None:
        self._summary.samples += 1
        stamp_ns = (int(msg.stamp.sec) * 1_000_000_000) + int(msg.stamp.nanosec)
        self._summary.last_stamp_ns = stamp_ns
        self._summary.last_mission_id = msg.mission_id
        self._summary.last_phase = msg.phase
        self._summary.last_detail = msg.detail
        self._summary.last_active = bool(msg.active)
        self._summary.last_terminal = bool(msg.terminal)
        self._summary.last_succeeded = bool(msg.succeeded)
        self._summary.last_completed = bool(msg.completed)
        self._summary.last_aborted = bool(msg.aborted)
        self._summary.last_failed = bool(msg.failed)
        self._summary.last_current_waypoint_index = int(msg.current_waypoint_index)
        self._summary.last_total_waypoints = int(msg.total_waypoints)
        self._summary.last_last_command = msg.last_command

        if stamp_ns < self._args.min_stamp_ns:
            return

        if self._args.mission_id is not None and msg.mission_id != self._args.mission_id:
            return
        if self._args.phase is not None and msg.phase != self._args.phase:
            return
        if self._args.active is not None and bool(msg.active) != self._args.active:
            return
        if self._args.terminal is not None and bool(msg.terminal) != self._args.terminal:
            return
        if self._args.succeeded is not None and bool(msg.succeeded) != self._args.succeeded:
            return
        if self._args.completed is not None and bool(msg.completed) != self._args.completed:
            return
        if self._args.aborted is not None and bool(msg.aborted) != self._args.aborted:
            return
        if self._args.failed is not None and bool(msg.failed) != self._args.failed:
            return
        if self._args.last_command is not None and msg.last_command != self._args.last_command:
            return
        if self._args.detail_contains is not None and self._args.detail_contains not in msg.detail:
            return
        if self._args.min_waypoint_index is not None and int(msg.current_waypoint_index) < self._args.min_waypoint_index:
            return

        self.get_logger().info(
            "mission status matched "
            f"(mission_id={msg.mission_id}, phase={msg.phase}, terminal={msg.terminal}, "
            f"succeeded={msg.succeeded}, completed={msg.completed}, aborted={msg.aborted}, failed={msg.failed}, "
            f"last_command={msg.last_command}, current_waypoint_index={msg.current_waypoint_index}/{msg.total_waypoints})",
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
    parser.add_argument("--topic", default="/drone/mission_status")
    parser.add_argument("--timeout-s", type=float, default=60.0)
    parser.add_argument("--mission-id")
    parser.add_argument("--phase")
    parser.add_argument("--active")
    parser.add_argument("--terminal")
    parser.add_argument("--succeeded")
    parser.add_argument("--completed")
    parser.add_argument("--aborted")
    parser.add_argument("--failed")
    parser.add_argument("--last-command")
    parser.add_argument("--detail-contains")
    parser.add_argument("--min-waypoint-index", type=int)
    parser.add_argument("--min-stamp-ns", type=int, default=0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.active = parse_optional_bool(args.active)
    args.terminal = parse_optional_bool(args.terminal)
    args.succeeded = parse_optional_bool(args.succeeded)
    args.completed = parse_optional_bool(args.completed)
    args.aborted = parse_optional_bool(args.aborted)
    args.failed = parse_optional_bool(args.failed)

    rclpy.init()
    node = MissionStatusWaiter(args)
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
