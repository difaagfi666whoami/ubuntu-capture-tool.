"""Safe local saving for screenshot bytes."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .backend import CaptureBackendError


def default_capture_directory() -> Path:
    pictures = Path.home() / "Pictures"
    return pictures if pictures.is_dir() else Path.home()


def save_capture_png(image_data: bytes, directory: str | Path) -> Path:
    """Validate screenshot bytes and write a unique PNG without overwriting."""
    try:
        with Image.open(BytesIO(image_data)) as image:
            if image.format != "PNG":
                raise CaptureBackendError("The capture backend must return a PNG image.")
            image.verify()
    except (OSError, UnidentifiedImageError) as exc:
        raise CaptureBackendError(f"The screenshot data is not a valid PNG: {exc}") from exc

    target_directory = Path(directory).expanduser()
    try:
        target_directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CaptureBackendError(f"Cannot create screenshot folder '{target_directory}': {exc}") from exc

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = f"capture_{timestamp}"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix=".capture-",
            suffix=".tmp",
            dir=target_directory,
            delete=False,
        ) as output:
            temp_path = Path(output.name)
            output.write(image_data)
            output.flush()
            os.fsync(output.fileno())

        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            destination = target_directory / f"{stem}{suffix}.png"
            try:
                os.link(temp_path, destination)
                return destination
            except FileExistsError:
                index += 1
    except OSError as exc:
        raise CaptureBackendError(f"Could not save screenshot in '{target_directory}': {exc}") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
