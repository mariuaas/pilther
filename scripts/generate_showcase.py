from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pilther import (
    atkinson,
    atkinson_palette,
    bluenoise,
    burkes,
    burkes_palette,
    extract_palette,
    sierra2,
    sierra2_palette,
    sierra3,
    sierra3_palette,
    stucki,
    stucki_palette,
)
from pilther.colorspace import convert_color_space
from pilther.metrics import metric_summary

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "testimgs"
OUTPUT_DIR = ROOT / "docs" / "generated"

GRAYSCALE_FILTERS = {
    "atkinson": atkinson,
    "sierra2": sierra2,
    "sierra3": sierra3,
    "stucki": stucki,
    "burkes": burkes,
    "bluenoise": bluenoise,
}

COLOR_FILTERS = {
    "atkinson_palette": atkinson_palette,
    "sierra2_palette": sierra2_palette,
    "sierra3_palette": sierra3_palette,
    "stucki_palette": stucki_palette,
    "burkes_palette": burkes_palette,
}

PALETTE_STUDY = ("gameboy4", "ega16", "ansi16", "web216", "term256")
EXTRACTED_PALETTE_SPACES = ("rgb", "ycocg")
EXTRACTED_PALETTE_COLORS = 64


def _iter_input_images() -> list[Path]:
    return sorted(
        path
        for path in INPUT_DIR.iterdir()
        if path.suffix.lower() in {".bmp", ".jpg", ".jpeg", ".png", ".webp"}
    )


def _prepare_image(image: Image.Image) -> Image.Image:
    return image.convert("RGB")


def _save_image(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _annotate_with_metrics(image: Image.Image, metrics: dict[str, float]) -> Image.Image:
    base = image.convert("RGB")
    footer_height = 22
    annotated = Image.new("RGB", (base.width, base.height + footer_height), color=(255, 255, 255))
    annotated.paste(base, (0, 0))

    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default()
    psnr = "inf" if np.isinf(metrics["psnr"]) else f"{metrics['psnr']:.2f}"
    text = f"PSNR {psnr} dB | MSE {metrics['mse']:.1f} | SSIM {metrics['ssim']:.4f}"
    draw.rectangle([(0, base.height), (base.width, annotated.height)], fill=(245, 245, 245))
    draw.text((6, base.height + 5), text, fill=(0, 0, 0), font=font)
    return annotated


def _quantize_to_palette(image: Image.Image, palette_colors: np.ndarray, space: str) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    flat_rgb = rgb.reshape(-1, 3)
    palette_rgb = palette_colors.astype(np.float32)

    pixel_space = convert_color_space(flat_rgb, space)
    palette_space = convert_color_space(palette_rgb, space)
    distances = np.sum((pixel_space[:, None, :] - palette_space[None, :, :]) ** 2, axis=2)
    nearest = np.argmin(distances, axis=1)
    quantized = palette_rgb[nearest].reshape(rgb.shape).astype(np.uint8)
    return Image.fromarray(quantized, mode="RGB")


def _render_palette_strip(
    palette_colors: np.ndarray,
    swatch_width: int = 24,
    swatch_height: int = 24,
    max_columns: int = 8,
) -> Image.Image:
    palette = palette_colors.astype(np.uint8)
    columns = min(max_columns, len(palette))
    rows = int(np.ceil(len(palette) / columns))

    grid = np.zeros((rows * swatch_height, columns * swatch_width, 3), dtype=np.uint8)
    for index, color in enumerate(palette):
        row = index // columns
        column = index % columns
        y0 = row * swatch_height
        x0 = column * swatch_width
        grid[y0 : y0 + swatch_height, x0 : x0 + swatch_width] = color

    return Image.fromarray(grid, mode="RGB")


def generate_showcase() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for input_path in _iter_input_images():
        stem = input_path.stem.lower()
        image_dir = OUTPUT_DIR / stem

        with Image.open(input_path) as src:
            prepared = _prepare_image(src)
            _save_image(prepared, image_dir / "source.png")

            for filter_name, func in GRAYSCALE_FILTERS.items():
                rendered = func(prepared)
                if rendered.mode != "RGB":
                    rendered = rendered.convert("RGB")
                metrics = metric_summary(prepared, rendered)
                annotated = _annotate_with_metrics(rendered, metrics)
                _save_image(annotated, image_dir / f"grayscale_{filter_name}.png")

            for filter_name, func in COLOR_FILTERS.items():
                rendered = func(prepared, palette_name="ega16")
                rendered = rendered.convert("RGB")
                metrics = metric_summary(prepared, rendered)
                annotated = _annotate_with_metrics(rendered, metrics)
                _save_image(annotated, image_dir / f"color_{filter_name}_ega16.png")

            for palette_name in PALETTE_STUDY:
                rendered = sierra2_palette(prepared, palette_name=palette_name)
                rendered = rendered.convert("RGB")
                metrics = metric_summary(prepared, rendered)
                annotated = _annotate_with_metrics(rendered, metrics)
                _save_image(annotated, image_dir / f"palette_sierra2_{palette_name}.png")

            for palette_space in EXTRACTED_PALETTE_SPACES:
                palette = extract_palette(
                    prepared,
                    EXTRACTED_PALETTE_COLORS,
                    method="median_cut",
                    space=palette_space,
                )
                quantized = _quantize_to_palette(prepared, palette.colors, palette_space)
                palette_strip = _render_palette_strip(palette.colors)
                metrics = metric_summary(prepared, quantized)
                annotated = _annotate_with_metrics(quantized, metrics)
                _save_image(annotated, image_dir / f"extracted_quantized_{palette_space}.png")
                _save_image(palette_strip, image_dir / f"extracted_palette_{palette_space}.png")


if __name__ == "__main__":
    generate_showcase()