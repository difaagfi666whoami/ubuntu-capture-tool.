"""Platform-independent image validation and composition."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from PIL import Image, UnidentifiedImageError


class Orientation(str, Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class Alignment(str, Enum):
    START = "start"
    CENTER = "center"
    END = "end"


class ImageMergeError(ValueError):
    """Raised when inputs cannot be composed into an output image."""


@dataclass(frozen=True)
class MergeOptions:
    orientation: Orientation = Orientation.VERTICAL
    alignment: Alignment = Alignment.CENTER
    background: tuple[int, int, int] = (255, 255, 255)


def compose_images(paths: Iterable[str | Path], options: MergeOptions | None = None) -> Image.Image:
    """Compose two or more images in order without changing their dimensions.

    Images are converted to RGBA for composition. Unused canvas space is filled
    with the configured background color; the returned image is RGB.
    """
    image_paths = [Path(path) for path in paths]
    if len(image_paths) < 2:
        raise ImageMergeError("Select at least two images to combine.")

    options = options or MergeOptions()
    images: list[Image.Image] = []
    try:
        for path in image_paths:
            try:
                with Image.open(path) as source:
                    source.load()
                    images.append(source.convert("RGBA"))
            except (OSError, UnidentifiedImageError) as exc:
                raise ImageMergeError(f"Could not read image '{path}': {exc}") from exc

        if options.orientation == Orientation.VERTICAL:
            canvas_size = (max(image.width for image in images), sum(image.height for image in images))
        else:
            canvas_size = (sum(image.width for image in images), max(image.height for image in images))

        canvas = Image.new("RGB", canvas_size, options.background)
        offset = 0
        for image in images:
            if options.orientation == Orientation.VERTICAL:
                x = _aligned_offset(canvas.width - image.width, options.alignment)
                canvas.paste(image, (x, offset), image)
                offset += image.height
            else:
                y = _aligned_offset(canvas.height - image.height, options.alignment)
                canvas.paste(image, (offset, y), image)
                offset += image.width
        return canvas
    finally:
        for image in images:
            image.close()


def save_png(
    image: Image.Image,
    destination: str | Path,
    *,
    overwrite: bool = False,
    protected_paths: Iterable[str | Path] = (),
) -> Path:
    """Save a PNG without replacing an existing file unless explicitly allowed."""
    path = Path(destination)
    if path.suffix.lower() != ".png":
        path = path.with_suffix(".png")
    resolved_output = path.resolve()
    for source in protected_paths:
        if resolved_output == Path(source).resolve():
            raise ImageMergeError(f"Output cannot replace a selected source image: {path}")
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {path}")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as output:
            temp_path = Path(output.name)
            image.save(output, format="PNG")
            output.flush()
            os.fsync(output.fileno())

        if overwrite:
            os.replace(temp_path, path)
        else:
            # Hard-link creation is atomic and fails if the destination exists.
            os.link(temp_path, path)
            temp_path.unlink()
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return path


def _aligned_offset(available_space: int, alignment: Alignment) -> int:
    if alignment == Alignment.START:
        return 0
    if alignment == Alignment.END:
        return available_space
    return available_space // 2

