from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class TelemetryEnvelope:
    run_id: str
    source: str
    kind: str
    topic: str
    stamp_ns: int
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
