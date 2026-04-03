"""Mission-domain exceptions."""


class MissionError(RuntimeError):
    """Base mission-domain failure."""


class MissionConnectionFailure(MissionError):
    """Raised when the vehicle cannot be reached."""


class MissionCommandFailed(MissionError):
    """Raised when an actuation command fails."""


class MissionTimeout(MissionError):
    """Raised when a mission step times out."""


class MissionAbortRequested(MissionError):
    """Raised to interrupt the active mission with a controlled abort."""
