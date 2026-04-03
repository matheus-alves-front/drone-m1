from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import threading


class MissionPhase(str, Enum):
    IDLE = "idle"
    WAITING_FOR_SYSTEM = "waiting_for_system"
    ARMING = "arming"
    TAKEOFF = "takeoff"
    HOVER = "hover"
    PATROL = "patrol"
    RETURN_TO_HOME = "return_to_home"
    LANDING = "landing"
    ABORTING = "aborting"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass(frozen=True)
class MissionSnapshot:
    mission_id: str
    phase: MissionPhase
    detail: str
    active: bool
    completed: bool
    aborted: bool
    failed: bool
    current_waypoint_index: int
    total_waypoints: int


def _build_snapshot(
    mission_id: str,
    phase: MissionPhase,
    detail: str,
    current_waypoint_index: int,
    total_waypoints: int,
) -> MissionSnapshot:
    return MissionSnapshot(
        mission_id=mission_id,
        phase=phase,
        detail=detail,
        active=phase
        not in {
            MissionPhase.IDLE,
            MissionPhase.COMPLETED,
            MissionPhase.ABORTED,
            MissionPhase.FAILED,
        },
        completed=phase == MissionPhase.COMPLETED,
        aborted=phase == MissionPhase.ABORTED,
        failed=phase == MissionPhase.FAILED,
        current_waypoint_index=current_waypoint_index,
        total_waypoints=total_waypoints,
    )


ALLOWED_TRANSITIONS: dict[MissionPhase, set[MissionPhase]] = {
    MissionPhase.IDLE: {MissionPhase.WAITING_FOR_SYSTEM},
    MissionPhase.WAITING_FOR_SYSTEM: {MissionPhase.ARMING, MissionPhase.ABORTING, MissionPhase.FAILED},
    MissionPhase.ARMING: {MissionPhase.TAKEOFF, MissionPhase.ABORTING, MissionPhase.FAILED},
    MissionPhase.TAKEOFF: {MissionPhase.HOVER, MissionPhase.ABORTING, MissionPhase.FAILED},
    MissionPhase.HOVER: {MissionPhase.PATROL, MissionPhase.ABORTING, MissionPhase.FAILED},
    MissionPhase.PATROL: {MissionPhase.PATROL, MissionPhase.RETURN_TO_HOME, MissionPhase.ABORTING, MissionPhase.FAILED},
    MissionPhase.RETURN_TO_HOME: {MissionPhase.LANDING, MissionPhase.ABORTING, MissionPhase.FAILED},
    MissionPhase.LANDING: {MissionPhase.COMPLETED, MissionPhase.ABORTED, MissionPhase.FAILED},
    MissionPhase.ABORTING: {MissionPhase.ABORTED, MissionPhase.FAILED},
    MissionPhase.COMPLETED: {MissionPhase.IDLE},
    MissionPhase.ABORTED: {MissionPhase.IDLE},
    MissionPhase.FAILED: {MissionPhase.IDLE},
}


class MissionStateMachine:
    def __init__(self, mission_id: str, total_waypoints: int) -> None:
        self._lock = threading.Lock()
        self._snapshot = _build_snapshot(
            mission_id=mission_id,
            phase=MissionPhase.IDLE,
            detail="mission idle",
            current_waypoint_index=0,
            total_waypoints=total_waypoints,
        )

    @property
    def snapshot(self) -> MissionSnapshot:
        with self._lock:
            return self._snapshot

    def transition(
        self,
        phase: MissionPhase,
        *,
        detail: str,
        current_waypoint_index: int | None = None,
    ) -> MissionSnapshot:
        with self._lock:
            if phase != self._snapshot.phase and phase not in ALLOWED_TRANSITIONS[self._snapshot.phase]:
                raise ValueError(f"invalid transition from {self._snapshot.phase.value} to {phase.value}")

            waypoint_index = (
                self._snapshot.current_waypoint_index if current_waypoint_index is None else current_waypoint_index
            )
            self._snapshot = _build_snapshot(
                mission_id=self._snapshot.mission_id,
                phase=phase,
                detail=detail,
                current_waypoint_index=waypoint_index,
                total_waypoints=self._snapshot.total_waypoints,
            )
            return self._snapshot

    def reset(self, detail: str = "mission reset") -> MissionSnapshot:
        with self._lock:
            self._snapshot = replace(
                self._snapshot,
                phase=MissionPhase.IDLE,
                detail=detail,
                active=False,
                completed=False,
                aborted=False,
                failed=False,
                current_waypoint_index=0,
            )
            return self._snapshot
