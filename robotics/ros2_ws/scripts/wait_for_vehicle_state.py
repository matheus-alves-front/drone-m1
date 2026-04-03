#!/usr/bin/env python3
"""Wait until /drone/vehicle_state satisfies a set of conditions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from drone_msgs.msg import VehicleState


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
    max_altitude_m: float = 0.0
    saw_connected: bool = False
    saw_armed: bool = False
    saw_airborne: bool = False
    saw_landed_after_airborne: bool = False
    last_connected: bool = False
    last_armed: bool = False
    last_landed: bool = False
    last_failsafe: bool = False
    last_preflight_checks_pass: bool = False
    last_position_valid: bool = False
    last_nav_state: str = ""
    last_altitude_m: float = 0.0


class VehicleStateWaiter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("vehicle_state_waiter")
        self._args = args
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._matched = False
        self._summary = ObservationSummary()
        self.create_subscription(VehicleState, args.topic, self._callback, qos)

    def _callback(self, msg: VehicleState) -> None:
        self._summary.samples += 1
        stamp_ns = (int(msg.stamp.sec) * 1_000_000_000) + int(msg.stamp.nanosec)
        self._summary.last_stamp_ns = stamp_ns
        self._summary.max_altitude_m = max(self._summary.max_altitude_m, float(msg.altitude_m))
        self._summary.saw_connected = self._summary.saw_connected or bool(msg.connected)
        self._summary.saw_armed = self._summary.saw_armed or bool(msg.armed)
        self._summary.saw_airborne = self._summary.saw_airborne or (
            self._args.min_altitude_m is not None and msg.altitude_m >= self._args.min_altitude_m
        )
        if self._summary.saw_airborne and msg.landed:
            self._summary.saw_landed_after_airborne = True

        self._summary.last_connected = bool(msg.connected)
        self._summary.last_armed = bool(msg.armed)
        self._summary.last_landed = bool(msg.landed)
        self._summary.last_failsafe = bool(msg.failsafe)
        self._summary.last_preflight_checks_pass = bool(msg.preflight_checks_pass)
        self._summary.last_position_valid = bool(msg.position_valid)
        self._summary.last_nav_state = msg.nav_state
        self._summary.last_altitude_m = float(msg.altitude_m)

        if stamp_ns < self._args.min_stamp_ns:
            return

        if self._args.connected is not None and msg.connected != self._args.connected:
            return
        if self._args.armed is not None and msg.armed != self._args.armed:
            return
        if self._args.landed is not None and msg.landed != self._args.landed:
            return
        if self._args.failsafe is not None and msg.failsafe != self._args.failsafe:
            return
        if (
            self._args.preflight_checks_pass is not None
            and msg.preflight_checks_pass != self._args.preflight_checks_pass
        ):
            return
        if self._args.position_valid is not None and msg.position_valid != self._args.position_valid:
            return
        if self._args.nav_state is not None and msg.nav_state != self._args.nav_state:
            return
        if self._args.min_altitude_m is not None:
            if self._args.require_airborne or self._args.require_landed_after_airborne:
                if not self._summary.saw_airborne:
                    return
            elif msg.altitude_m < self._args.min_altitude_m:
                return
        if self._args.max_altitude_m is not None and msg.altitude_m > self._args.max_altitude_m:
            return
        if self._args.require_airborne and not self._summary.saw_airborne:
            return
        if self._args.require_landed_after_airborne and not self._summary.saw_landed_after_airborne:
            return

        self.get_logger().info(
            "vehicle state matched "
            f"(connected={msg.connected}, armed={msg.armed}, landed={msg.landed}, "
            f"failsafe={msg.failsafe}, preflight_checks_pass={msg.preflight_checks_pass}, "
            f"position_valid={msg.position_valid}, "
            f"nav_state={msg.nav_state}, altitude_m={msg.altitude_m:.2f})",
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
    parser.add_argument("--topic", default="/drone/vehicle_state")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--connected")
    parser.add_argument("--armed")
    parser.add_argument("--landed")
    parser.add_argument("--failsafe")
    parser.add_argument("--preflight-checks-pass")
    parser.add_argument("--position-valid")
    parser.add_argument("--nav-state")
    parser.add_argument("--min-altitude-m", type=float)
    parser.add_argument("--max-altitude-m", type=float)
    parser.add_argument("--require-airborne", action="store_true")
    parser.add_argument("--require-landed-after-airborne", action="store_true")
    parser.add_argument("--min-stamp-ns", type=int, default=0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.connected = parse_optional_bool(args.connected)
    args.armed = parse_optional_bool(args.armed)
    args.landed = parse_optional_bool(args.landed)
    args.failsafe = parse_optional_bool(args.failsafe)
    args.preflight_checks_pass = parse_optional_bool(args.preflight_checks_pass)
    args.position_valid = parse_optional_bool(args.position_valid)

    rclpy.init()
    node = VehicleStateWaiter(args)
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
