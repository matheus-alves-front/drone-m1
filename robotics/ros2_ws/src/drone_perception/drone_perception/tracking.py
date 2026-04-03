from __future__ import annotations

from dataclasses import dataclass
import math

from .detection import DetectionSample


@dataclass(frozen=True)
class TrackedSample:
    tracked: bool
    track_id: int
    label: str
    confidence: float
    center_x: float
    center_y: float
    width: float
    height: float
    age: int
    state: str


class SingleObjectTracker:
    def __init__(self, *, reacquire_distance_px: float = 48.0) -> None:
        self._reacquire_distance_px = max(float(reacquire_distance_px), 1.0)
        self._next_track_id = 1
        self._current: TrackedSample | None = None

    def update(self, detection: DetectionSample) -> TrackedSample:
        if not detection.detected:
            lost = self._build_lost_sample()
            self._current = None
            return lost

        if self._current is None:
            tracked = TrackedSample(
                tracked=True,
                track_id=self._next_track_id,
                label=detection.label,
                confidence=detection.confidence,
                center_x=detection.center_x,
                center_y=detection.center_y,
                width=detection.width,
                height=detection.height,
                age=1,
                state="locked",
            )
            self._next_track_id += 1
            self._current = tracked
            return tracked

        distance = math.hypot(
            detection.center_x - self._current.center_x,
            detection.center_y - self._current.center_y,
        )
        if distance <= self._reacquire_distance_px:
            tracked = TrackedSample(
                tracked=True,
                track_id=self._current.track_id,
                label=detection.label,
                confidence=detection.confidence,
                center_x=detection.center_x,
                center_y=detection.center_y,
                width=detection.width,
                height=detection.height,
                age=self._current.age + 1,
                state="tracking",
            )
            self._current = tracked
            return tracked

        tracked = TrackedSample(
            tracked=True,
            track_id=self._next_track_id,
            label=detection.label,
            confidence=detection.confidence,
            center_x=detection.center_x,
            center_y=detection.center_y,
            width=detection.width,
            height=detection.height,
            age=1,
            state="reacquired",
        )
        self._next_track_id += 1
        self._current = tracked
        return tracked

    def _build_lost_sample(self) -> TrackedSample:
        if self._current is None:
            return TrackedSample(
                tracked=False,
                track_id=0,
                label="",
                confidence=0.0,
                center_x=0.0,
                center_y=0.0,
                width=0.0,
                height=0.0,
                age=0,
                state="idle",
            )

        return TrackedSample(
            tracked=False,
            track_id=self._current.track_id,
            label=self._current.label,
            confidence=self._current.confidence,
            center_x=self._current.center_x,
            center_y=self._current.center_y,
            width=self._current.width,
            height=self._current.height,
            age=self._current.age,
            state="lost",
        )

