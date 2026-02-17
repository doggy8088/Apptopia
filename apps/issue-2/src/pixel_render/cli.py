from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


RGBAColor = tuple[int, int, int, int]
ColorCell = RGBAColor | None
Frame = list[list[ColorCell]]
NEAREST = Image.Resampling.NEAREST


class PixelRenderError(ValueError):
    """Domain error for predictable user-facing failures."""


@dataclass(frozen=True)
class PixelAnimation:
    width: int
    height: int
    fps: int
    frames: list[Frame]


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PixelRenderError(f"'{field_name}' must be a positive integer.")
    return value


def parse_hex_color(value: str) -> tuple[int, int, int, int]:
    text = value.strip()
    if not text.startswith("#"):
        raise PixelRenderError(f"Invalid color '{value}'. Expected a hex color starting with '#'.")

    hex_part = text[1:]
    if len(hex_part) not in {3, 4, 6, 8}:
        raise PixelRenderError(
            f"Invalid color '{value}'. Use #RGB, #RGBA, #RRGGBB, or #RRGGBBAA."
        )

    if any(ch not in "0123456789abcdefABCDEF" for ch in hex_part):
        raise PixelRenderError(f"Invalid color '{value}'. Contains non-hex characters.")

    if len(hex_part) in {3, 4}:
        hex_part = "".join(ch * 2 for ch in hex_part)

    if len(hex_part) == 6:
        hex_part += "FF"

    red = int(hex_part[0:2], 16)
    green = int(hex_part[2:4], 16)
    blue = int(hex_part[4:6], 16)
    alpha = int(hex_part[6:8], 16)
    return red, green, blue, alpha


def _load_animation(path: Path, fps_override: int | None) -> PixelAnimation:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PixelRenderError(f"Unable to read '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PixelRenderError(
            f"Input file is not valid JSON (line {exc.lineno}, column {exc.colno})."
        ) from exc

    if not isinstance(payload, dict):
        raise PixelRenderError("Input JSON root must be an object.")

    width = _positive_int(payload.get("width"), "width")
    height = _positive_int(payload.get("height"), "height")

    fps_value: object = payload.get("fps")
    if fps_override is not None:
        fps_value = fps_override
    fps = _positive_int(fps_value, "fps")

    raw_frames = payload.get("frames")
    if not isinstance(raw_frames, list) or not raw_frames:
        raise PixelRenderError("'frames' must be a non-empty array.")

    frames: list[Frame] = []
    for frame_index, raw_frame in enumerate(raw_frames, start=1):
        if not isinstance(raw_frame, list) or len(raw_frame) != height:
            raise PixelRenderError(
                f"Frame {frame_index} must contain exactly {height} rows."
            )

        frame_rows: Frame = []
        for row_index, raw_row in enumerate(raw_frame, start=1):
            if not isinstance(raw_row, list) or len(raw_row) != width:
                raise PixelRenderError(
                    f"Frame {frame_index}, row {row_index} must contain exactly {width} columns."
                )

            row: list[ColorCell] = []
            for col_index, raw_color in enumerate(raw_row, start=1):
                if raw_color is None:
                    row.append(None)
                    continue

                if not isinstance(raw_color, str):
                    raise PixelRenderError(
                        f"Frame {frame_index}, row {row_index}, col {col_index} must be string or null."
                    )

                try:
                    parsed_color = parse_hex_color(raw_color)
                except PixelRenderError as exc:
                    raise PixelRenderError(
                        f"Frame {frame_index}, row {row_index}, col {col_index}: {exc}"
                    ) from exc

                row.append(parsed_color)

            frame_rows.append(row)
        frames.append(frame_rows)

    return PixelAnimation(width=width, height=height, fps=fps, frames=frames)


def _render_frame(frame: Frame, width: int, height: int, scale: int) -> Image.Image:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()

    for y, row in enumerate(frame):
        for x, color in enumerate(row):
            if color is None:
                continue
            pixels[x, y] = color

    if scale != 1:
        image = image.resize((width * scale, height * scale), NEAREST)
    return image


def _save_gif(images: list[Image.Image], output_path: Path, fps: int) -> None:
    duration_ms = max(1, round(1000 / fps))
    first, *rest = images
    first.save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=rest,
        duration=duration_ms,
        loop=0,
        disposal=2,
        optimize=False,
    )


def _save_png(images: list[Image.Image], output_path: Path) -> None:
    if len(images) == 1:
        images[0].save(output_path, format="PNG")
        return

    frame_width, frame_height = images[0].size
    sprite_sheet = Image.new(
        "RGBA", (frame_width * len(images), frame_height), (0, 0, 0, 0)
    )
    for index, image in enumerate(images):
        sprite_sheet.paste(image, (index * frame_width, 0))
    sprite_sheet.save(output_path, format="PNG")


def _render(input_path: Path, output_path: Path, scale: int, fps_override: int | None) -> None:
    animation = _load_animation(input_path, fps_override=fps_override)
    images = [
        _render_frame(frame, width=animation.width, height=animation.height, scale=scale)
        for frame in animation.frames
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = output_path.suffix.lower()
    if suffix == ".gif":
        _save_gif(images, output_path, fps=animation.fps)
        return
    if suffix == ".png":
        _save_png(images, output_path)
        return

    raise PixelRenderError("Output file extension must be .gif or .png.")


def _build_parser(prog_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog_name,
        description="Render pixel matrix JSON into GIF or PNG images.",
    )
    parser.add_argument("input", help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--out",
        dest="output",
        required=True,
        help="Path to output image (.gif or .png).",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=1,
        help="Nearest-neighbor scale factor. Default: 1.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help="Override fps from JSON.",
    )
    return parser


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "generate":
        parser = _build_parser("pixel-render generate")
        return parser.parse_args(args[1:])
    parser = _build_parser("pixel-render")
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        scale = _positive_int(args.scale, "scale")
        fps_override = None if args.fps is None else _positive_int(args.fps, "fps")
        _render(
            input_path=Path(args.input),
            output_path=Path(args.output),
            scale=scale,
            fps_override=fps_override,
        )
        return 0
    except PixelRenderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def run() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    run()
