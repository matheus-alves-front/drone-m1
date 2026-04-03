#!/usr/bin/env python3
"""Configure PX4 runtime parameters required by the simulation-first baseline."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ParamAssignment:
    name: str
    kind: str
    value: int | float


async def wait_connected(system: object, timeout_s: float) -> None:
    import mavsdk

    async def _wait() -> None:
        async for state in system.core.connection_state():
            if state.is_connected:
                return

    try:
        await asyncio.wait_for(_wait(), timeout_s)
    except asyncio.TimeoutError as exc:
        raise RuntimeError(f"timed out while connecting to PX4 after {timeout_s:.1f}s") from exc
    except mavsdk.SystemError as exc:  # pragma: no cover
        raise RuntimeError(f"failed to observe PX4 connection state: {exc}") from exc


async def configure_parameters(
    system_address: str,
    timeout_s: float,
    assignments: list[ParamAssignment],
) -> dict[str, int | float]:
    try:
        from mavsdk import System
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("mavsdk is not installed; install packages/shared-py/requirements-phase2.txt") from exc

    system = System()
    await system.connect(system_address=system_address)
    await wait_connected(system, timeout_s)

    applied: dict[str, int | float] = {}
    for assignment in assignments:
        name = assignment.name
        if assignment.kind == "int":
            target_value = int(assignment.value)
            await asyncio.wait_for(system.param.set_param_int(name, target_value), timeout_s)
            readback = await asyncio.wait_for(system.param.get_param_int(name), timeout_s)
            applied[name] = int(readback)
        elif assignment.kind == "float":
            target_value = float(assignment.value)
            await asyncio.wait_for(system.param.set_param_float(name, target_value), timeout_s)
            readback = await asyncio.wait_for(system.param.get_param_float(name), timeout_s)
            applied[name] = float(readback)
        else:  # pragma: no cover
            raise RuntimeError(f"unsupported PX4 param assignment kind: {assignment.kind}")

        if applied[name] != target_value:
            raise RuntimeError(f"PX4 param {name} read back as {applied[name]}, expected {target_value}")
    return applied


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system-address", default="udp://:14540")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument(
        "--set-int",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="PX4 integer parameter assignment, for example NAV_DLL_ACT=0",
    )
    parser.add_argument(
        "--set-float",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="PX4 floating-point parameter assignment, for example COM_DISARM_PRFLT=60",
    )
    return parser


def _parse_named_assignment(raw_assignment: str, *, kind: str) -> ParamAssignment:
    if "=" not in raw_assignment:
        raise ValueError(f"invalid parameter assignment: {raw_assignment!r}")
    name, raw_value = raw_assignment.split("=", 1)
    name = name.strip()
    if not name:
        raise ValueError(f"invalid parameter assignment: {raw_assignment!r}")
    if kind == "int":
        return ParamAssignment(name=name, kind=kind, value=int(raw_value.strip()))
    if kind == "float":
        return ParamAssignment(name=name, kind=kind, value=float(raw_value.strip()))
    raise ValueError(f"unsupported parameter assignment kind: {kind}")


def parse_assignments(raw_int_assignments: list[str], raw_float_assignments: list[str]) -> list[ParamAssignment]:
    assignments: list[ParamAssignment] = []
    for raw_assignment in raw_int_assignments:
        assignments.append(_parse_named_assignment(raw_assignment, kind="int"))
    for raw_assignment in raw_float_assignments:
        assignments.append(_parse_named_assignment(raw_assignment, kind="float"))
    if not assignments:
        raise ValueError("at least one PX4 parameter assignment is required")

    seen_names: set[str] = set()
    for assignment in assignments:
        if assignment.name in seen_names:
            raise ValueError(f"duplicate PX4 parameter assignment: {assignment.name}")
        seen_names.add(assignment.name)
    return assignments


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        assignments = parse_assignments(args.set_int, args.set_float)
        applied = asyncio.run(configure_parameters(args.system_address, args.timeout_s, assignments))
    except Exception as exc:
        print(f"failed to configure PX4 simulation params: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "configured",
                "system_address": args.system_address,
                "params": applied,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
