"""Domain errors for Phase 2 scenario execution."""

from __future__ import annotations


class ScenarioError(RuntimeError):
    """Base class for scenario runner failures."""


class ScenarioValidationError(ScenarioError):
    """Raised when a scenario contract is malformed."""


class ScenarioDependencyError(ScenarioError):
    """Raised when an optional runtime dependency is missing."""


class ConnectionFailure(ScenarioError):
    """Raised when the runner cannot discover or connect to the vehicle."""


class ScenarioTimeout(ScenarioError):
    """Raised when a scenario step does not reach the expected state in time."""


class ScenarioAssertionFailed(ScenarioError):
    """Raised when telemetry violates a scenario assertion."""


class ScenarioCommandFailed(ScenarioError):
    """Raised when the control backend rejects or fails a command."""
