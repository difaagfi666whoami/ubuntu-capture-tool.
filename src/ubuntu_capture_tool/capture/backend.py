"""Cross-platform contract for screenshot backends."""

from __future__ import annotations

from typing import Protocol


class CaptureCancelled(Exception):
    """Raised when the user cancels a capture interaction."""


class CaptureBackendError(RuntimeError):
    """Raised when the platform capture backend cannot capture the region."""


class CaptureBackend(Protocol):
    """Platform adapter for obtaining the user-selected screenshot as PNG bytes."""

    def capture_screen(self) -> bytes:
        """Return the selected screenshot as PNG, or raise a documented error."""

