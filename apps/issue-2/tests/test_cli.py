from __future__ import annotations

import json
import tempfile
from pathlib import Path

from PIL import Image

from pixel_render.cli import main


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_gif_with_scale_and_two_frames() -> None:
    black = [["#000000"] * 8 for _ in range(8)]
    white = [["#FFFFFF"] * 8 for _ in range(8)]
    payload = {
        "width": 8,
        "height": 8,
        "fps": 2,
        "frames": [black, white],
    }

    with tempfile.TemporaryDirectory(prefix="pixel-render-") as temp_dir:
        tmp_path = Path(temp_dir)
        input_file = tmp_path / "blink.json"
        output_file = tmp_path / "blink.gif"
        _write_json(input_file, payload)

        exit_code = main(
            ["generate", str(input_file), "--out", str(output_file), "--scale", "10"]
        )
        assert exit_code == 0
        assert output_file.exists()

        with Image.open(output_file) as image:
            assert image.size == (80, 80)
            assert getattr(image, "n_frames", 1) == 2


def test_generate_single_frame_png_from_issue_example() -> None:
    payload = {
        "width": 5,
        "height": 5,
        "fps": 2,
        "frames": [
            [
                ["#fff", "#f00", "#fff", "#f00", "#fff"],
                ["#f00", "#f00", "#f00", "#f00", "#f00"],
                ["#f00", "#f00", "#f00", "#f00", "#f00"],
                ["#fff", "#f00", "#f00", "#f00", "#fff"],
                ["#fff", "#fff", "#f00", "#fff", "#fff"],
            ]
        ],
    }

    with tempfile.TemporaryDirectory(prefix="pixel-render-") as temp_dir:
        tmp_path = Path(temp_dir)
        input_file = tmp_path / "heart.json"
        output_file = tmp_path / "heart.png"
        _write_json(input_file, payload)

        exit_code = main([str(input_file), "--out", str(output_file), "--scale", "20"])
        assert exit_code == 0

        with Image.open(output_file) as image:
            assert image.size == (100, 100)
            rgba = image.convert("RGBA")
            assert rgba.getpixel((50, 50))[:3] == (255, 0, 0)


def test_generate_png_sprite_sheet_for_multiple_frames() -> None:
    payload = {
        "width": 2,
        "height": 1,
        "fps": 3,
        "frames": [
            [["#000000", "#ffffff"]],
            [["#ffffff", "#000000"]],
        ],
    }

    with tempfile.TemporaryDirectory(prefix="pixel-render-") as temp_dir:
        tmp_path = Path(temp_dir)
        input_file = tmp_path / "two-frames.json"
        output_file = tmp_path / "sheet.png"
        _write_json(input_file, payload)

        exit_code = main([str(input_file), "--out", str(output_file), "--scale", "4"])
        assert exit_code == 0

        with Image.open(output_file) as image:
            assert image.size == (16, 4)


def test_png_keeps_transparent_pixels_and_alpha_hex() -> None:
    payload = {
        "width": 2,
        "height": 2,
        "fps": 1,
        "frames": [
            [
                [None, "#ff0000"],
                ["#00ff00", "#0000ff80"],
            ]
        ],
    }

    with tempfile.TemporaryDirectory(prefix="pixel-render-") as temp_dir:
        tmp_path = Path(temp_dir)
        input_file = tmp_path / "alpha.json"
        output_file = tmp_path / "alpha.png"
        _write_json(input_file, payload)

        exit_code = main([str(input_file), "--out", str(output_file)])
        assert exit_code == 0

        with Image.open(output_file) as image:
            rgba = image.convert("RGBA")
            assert rgba.getpixel((0, 0))[3] == 0
            assert rgba.getpixel((1, 1)) == (0, 0, 255, 128)


def test_invalid_output_extension_returns_error() -> None:
    payload = {
        "width": 1,
        "height": 1,
        "fps": 1,
        "frames": [[["#000"]]],
    }

    with tempfile.TemporaryDirectory(prefix="pixel-render-") as temp_dir:
        tmp_path = Path(temp_dir)
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.jpg"
        _write_json(input_file, payload)

        exit_code = main([str(input_file), "--out", str(output_file)])
        assert exit_code == 1
