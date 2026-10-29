"""Cross-platform contract for screenshot backends.

No backend is approved or implemented until it has passed integration testing
on the declared Ubuntu desktop session.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CaptureRect:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (self.x, self.y, self.width, self.height)):
            raise ValueError("Capture coordinates and dimensions must be integers.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Capture width and height must be positive.")


class CaptureCancelled(Exception):
    """Raised when the user cancels a capture interaction."""


class CaptureBackendError(RuntimeError):
    """Raised when the platform capture backend cannot capture the region."""


class CaptureBackend(Protocol):
    """Platform adapter returning PNG bytes for the requested screen region."""

    def capture(self, rectangle: CaptureRect) -> bytes:
        """Capture an explicit rectangle or raise a documented capture error."""

