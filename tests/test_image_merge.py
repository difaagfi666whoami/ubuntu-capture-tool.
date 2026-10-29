from pathlib import Path

import pytest
from PIL import Image

from ubuntu_capture_tool.image_merge import (
    Alignment,
    ImageMergeError,
    MergeOptions,
    Orientation,
    compose_images,
    save_png,
)


def make_image(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> Path:
    Image.new("RGB", size, color).save(path)
    return path


def test_vertical_preserves_order_and_dimensions(tmp_path: Path) -> None:
    red = make_image(tmp_path / "red.png", (2, 3), (255, 0, 0))
    blue = make_image(tmp_path / "blue.png", (4, 1), (0, 0, 255))

    output = compose_images([red, blue], MergeOptions(Orientation.VERTICAL, Alignment.START))

    assert output.size == (4, 4)
    assert output.getpixel((0, 0)) == (255, 0, 0)
    assert output.getpixel((0, 3)) == (0, 0, 255)
    assert output.getpixel((3, 0)) == (255, 255, 255)


@pytest.mark.parametrize(
    ("alignment", "expected_y"),
    [(Alignment.START, 0), (Alignment.CENTER, 1), (Alignment.END, 2)],
)
def test_horizontal_alignment_preserves_order(
    tmp_path: Path, alignment: Alignment, expected_y: int
) -> None:
    short = make_image(tmp_path / "short.png", (2, 1), (0, 255, 0))
    tall = make_image(tmp_path / "tall.png", (1, 3), (255, 0, 0))

    output = compose_images([short, tall], MergeOptions(Orientation.HORIZONTAL, alignment))

    assert output.size == (3, 3)
    assert output.getpixel((0, expected_y)) == (0, 255, 0)
    assert output.getpixel((2, 0)) == (255, 0, 0)


def test_vertical_alignment_start_center_end(tmp_path: Path) -> None:
    narrow = make_image(tmp_path / "narrow.png", (1, 1), (0, 255, 0))
    wide = make_image(tmp_path / "wide.png", (3, 1), (255, 0, 0))

    for alignment, expected_x in (
        (Alignment.START, 0),
        (Alignment.CENTER, 1),
        (Alignment.END, 2),
    ):
        output = compose_images([narrow, wide], MergeOptions(Orientation.VERTICAL, alignment))
        assert output.getpixel((expected_x, 0)) == (0, 255, 0)


def test_requires_two_images_and_reports_bad_input(tmp_path: Path) -> None:
    one = make_image(tmp_path / "one.png", (1, 1), (0, 0, 0))
    with pytest.raises(ImageMergeError, match="at least two"):
        compose_images([one])

    invalid = tmp_path / "bad.png"
    invalid.write_text("not an image")
    with pytest.raises(ImageMergeError, match="Could not read image"):
        compose_images([one, invalid])


def test_png_export_refuses_overwrite_and_preserves_sources(tmp_path: Path) -> None:
    source_a = make_image(tmp_path / "a.png", (1, 1), (255, 0, 0))
    source_b = make_image(tmp_path / "b.png", (1, 1), (0, 0, 255))
    original_a = source_a.read_bytes()
    original_b = source_b.read_bytes()
    output = compose_images([source_a, source_b])
    target = tmp_path / "combined.png"

    assert save_png(output, target) == target
    with pytest.raises(FileExistsError, match="already exists"):
        save_png(output, target)
    with pytest.raises(ImageMergeError, match="cannot replace a selected source"):
        save_png(output, source_a, overwrite=True, protected_paths=[source_a, source_b])
    assert source_a.read_bytes() == original_a
    assert source_b.read_bytes() == original_b
    with Image.open(target) as saved:
        assert saved.format == "PNG"


def test_failed_export_preserves_existing_output(tmp_path: Path) -> None:
    target = tmp_path / "existing.png"
    target.write_bytes(b"original output")

    class BrokenImage:
        def save(self, *_args, **_kwargs) -> None:
            raise OSError("simulated disk failure")

    with pytest.raises(OSError, match="simulated disk failure"):
        save_png(BrokenImage(), target, overwrite=True)  # type: ignore[arg-type]

    assert target.read_bytes() == b"original output"
    assert list(tmp_path.iterdir()) == [target]

