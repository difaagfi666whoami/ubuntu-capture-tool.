"""XDG Desktop Portal screenshot backend for GNOME Wayland."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl, Slot
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

from .backend import CaptureBackendError, CaptureCancelled

PORTAL = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SCREENSHOT_INTERFACE = "org.freedesktop.portal.Screenshot"
REQUEST_INTERFACE = "org.freedesktop.portal.Request"


class _Response(QObject):
    def __init__(self, loop: QEventLoop) -> None:
        super().__init__()
        self.loop = loop
        self.status: int | None = None
        self.results: dict = {}

    @Slot("uint", "QVariantMap")
    def receive(self, status: int, results: dict) -> None:
        self.status = status
        self.results = results
        self.loop.quit()


class XdgPortalScreenshotBackend:
    """Capture a desktop frame through the consent-controlled screenshot portal."""

    def __init__(
        self,
        *,
        connection: QDBusConnection | None = None,
        timeout_seconds: int = 300,
        environment: dict[str, str] | None = None,
    ) -> None:
        self.connection = connection or QDBusConnection.sessionBus()
        self.timeout_seconds = timeout_seconds
        self.environment = environment if environment is not None else os.environ

    @classmethod
    def from_current_session(cls) -> XdgPortalScreenshotBackend:
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        if session_type != "wayland" or "GNOME" not in desktop:
            raise CaptureBackendError("Area capture currently requires GNOME on Wayland.")
        connection = QDBusConnection.sessionBus()
        if not connection.isConnected():
            raise CaptureBackendError("Could not connect to the desktop session D-Bus.")
        if not connection.interface().isServiceRegistered(PORTAL):
            raise CaptureBackendError(
                "The XDG Desktop Portal is unavailable. Check that xdg-desktop-portal and "
                "xdg-desktop-portal-gnome are installed and running."
            )
        return cls(connection=connection)

    def capture_screen(self) -> bytes:
        token = uuid.uuid4().hex
        bus_name = self.connection.baseService().lstrip(":").replace(".", "_")
        request_path = f"/org/freedesktop/portal/desktop/request/{bus_name}/{token}"
        loop = QEventLoop()
        response = _Response(loop)
        connected = self.connection.connect(
            PORTAL, request_path, REQUEST_INTERFACE, "Response", response, "receive"
        )
        if not connected:
            raise CaptureBackendError("Could not listen for the screenshot portal response.")

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(self.timeout_seconds * 1000)

        interface = QDBusInterface(PORTAL, PORTAL_PATH, SCREENSHOT_INTERFACE, self.connection)
        # GNOME 46 rejects an empty parent identifier. Its portal accepts the
        # documented Wayland identifier prefix when no stable surface token exists.
        parent_window = "wayland:" if self.environment.get("XDG_SESSION_TYPE") == "wayland" else ""
        reply = interface.call(
            "Screenshot",
            parent_window,
            {"handle_token": token, "interactive": False},
        )
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            self.connection.disconnect(
                PORTAL, request_path, REQUEST_INTERFACE, "Response", response, "receive"
            )
            raise CaptureBackendError(f"Screenshot portal request failed: {reply.errorMessage()}")
        loop.exec()
        timer.stop()
        self.connection.disconnect(
            PORTAL, request_path, REQUEST_INTERFACE, "Response", response, "receive"
        )

        if response.status is None:
            raise CaptureBackendError("The screenshot portal did not respond before timeout.")
        if response.status == 1:
            raise CaptureCancelled("Screenshot permission was cancelled.")
        if response.status != 0:
            raise CaptureBackendError("The screenshot portal could not capture the screen.")
        uri = response.results.get("uri", "")
        local_path = QUrl(uri).toLocalFile()
        if not local_path:
            raise CaptureBackendError("The screenshot portal returned an invalid local image URI.")
        screenshot_path = Path(local_path)
        try:
            image_data = screenshot_path.read_bytes()
        except OSError as exc:
            raise CaptureBackendError("Could not read the screenshot returned by the portal.") from exc
        finally:
            # The portal creates this image for this request; remove its full-screen
            # temporary output after loading it so only the chosen crop is retained.
            screenshot_path.unlink(missing_ok=True)
        if not image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise CaptureBackendError("The screenshot portal returned a file that is not PNG.")
        return image_data
