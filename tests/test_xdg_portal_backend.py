from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from ubuntu_capture_tool.capture.backend import CaptureBackendError, CaptureCancelled
from ubuntu_capture_tool.capture import xdg_portal
from ubuntu_capture_tool.capture.xdg_portal import XdgPortalScreenshotBackend


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (7, 4), (20, 30, 40)).save(output, format="PNG")
    return output.getvalue()


class FakeLoop:
    def quit(self) -> None:
        pass

    def exec(self) -> None:
        pass


class FakeSignal:
    def connect(self, _callback) -> None:
        pass


class FakeTimer:
    def setSingleShot(self, _value: bool) -> None:
        pass

    @property
    def timeout(self):
        return FakeSignal()

    def start(self, _milliseconds: int) -> None:
        pass

    def stop(self) -> None:
        pass


class FakeMessage:
    class MessageType:
        ErrorMessage = "error"

    def type(self):
        return "method-return"


class FakeConnection:
    def __init__(self) -> None:
        self.receiver = None
        self.signal_path = None
        self.slot = None

    def baseService(self) -> str:
        return ":1.42"

    def connect(self, _service, path, _interface, _signal, receiver, slot) -> bool:
        self.receiver = receiver
        self.signal_path = path
        self.slot = slot
        return True

    def disconnect(self, *_args) -> bool:
        return True


def test_portal_capture_reads_and_removes_temporary_full_screen_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    screenshot_path = tmp_path / "portal-full-screen.png"
    screenshot_path.write_bytes(png_bytes())
    connection = FakeConnection()

    class FakeInterface:
        def __init__(self, *_args) -> None:
            pass

        def call(self, *_args):
            assert connection.receiver is not None
            connection.receiver.receive(0, {"uri": screenshot_path.as_uri()})
            return FakeMessage()

    class FakeUrl:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def toLocalFile(self) -> str:
            return Path(self.uri.removeprefix("file://")).as_posix()

    monkeypatch.setattr(xdg_portal, "QEventLoop", FakeLoop)
    monkeypatch.setattr(xdg_portal, "QTimer", FakeTimer)
    monkeypatch.setattr(xdg_portal, "QDBusInterface", FakeInterface)
    monkeypatch.setattr(xdg_portal, "QDBusMessage", FakeMessage)
    monkeypatch.setattr(xdg_portal, "QUrl", FakeUrl)

    result = XdgPortalScreenshotBackend(connection=connection).capture_screen()

    assert result == png_bytes()
    assert connection.signal_path.startswith(
        "/org/freedesktop/portal/desktop/request/1_42/"
    )
    assert connection.slot == "1receive(uint,QVariantMap)"
    assert not screenshot_path.exists()


def test_portal_cancel_response_is_reported_as_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()

    class FakeInterface:
        def __init__(self, *_args) -> None:
            pass

        def call(self, *_args):
            connection.receiver.receive(1, {})
            return FakeMessage()

    monkeypatch.setattr(xdg_portal, "QEventLoop", FakeLoop)
    monkeypatch.setattr(xdg_portal, "QTimer", FakeTimer)
    monkeypatch.setattr(xdg_portal, "QDBusInterface", FakeInterface)
    monkeypatch.setattr(xdg_portal, "QDBusMessage", FakeMessage)

    with pytest.raises(CaptureCancelled):
        XdgPortalScreenshotBackend(connection=connection).capture_screen()
