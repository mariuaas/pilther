"""Palette-aware Python error-diffusion filters."""

from __future__ import annotations

from typing import Final, Sequence

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .colorspace import convert_color_space
from .palette import Palette, PaletteMethod, resolve_palette

KernelOffsets = Sequence[tuple[int, int, int]]

_ATKINSON_OFFSETS: Final[tuple[tuple[int, int, int], ...]] = (
    (1, 0, 1),
    (2, 0, 1),
    (-1, 1, 1),
    (0, 1, 1),
    (1, 1, 1),
    (0, 2, 1),
)
_SIERRA2_OFFSETS: Final[tuple[tuple[int, int, int], ...]] = (
    (1, 0, 4),
    (2, 0, 3),
    (-2, 1, 1),
    (-1, 1, 2),
    (0, 1, 3),
    (1, 1, 2),
    (2, 1, 1),
)
_SIERRA3_OFFSETS: Final[tuple[tuple[int, int, int], ...]] = (
    (1, 0, 5),
    (2, 0, 3),
    (-2, 1, 2),
    (-1, 1, 4),
    (0, 1, 5),
    (1, 1, 4),
    (2, 1, 2),
    (-1, 2, 2),
    (0, 2, 3),
    (1, 2, 2),
)
_STUCKI_OFFSETS: Final[tuple[tuple[int, int, int], ...]] = (
    (1, 0, 8),
    (2, 0, 4),
    (-2, 1, 2),
    (-1, 1, 4),
    (0, 1, 8),
    (1, 1, 4),
    (2, 1, 2),
    (-2, 2, 1),
    (-1, 2, 2),
    (0, 2, 4),
    (1, 2, 2),
    (2, 2, 1),
)
_BURKES_OFFSETS: Final[tuple[tuple[int, int, int], ...]] = (
    (1, 0, 8),
    (2, 0, 4),
    (-2, 1, 2),
    (-1, 1, 4),
    (0, 1, 8),
    (1, 1, 4),
    (2, 1, 2),
)


def _resolve_filter_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None,
    palette_name: str | None,
    extract_colors: int | None,
    palette_method: PaletteMethod,
    palette_space: str,
) -> Palette:
    if palette is None and palette_name is None and extract_colors is None:
        raise ValueError(
            "Provide palette=..., palette_name=..., or extract_colors=... for palette-aware diffusion."
        )

    return resolve_palette(
        palette=palette,
        palette_name=palette_name,
        image=image if extract_colors is not None else None,
        colors=extract_colors,
        method=palette_method,
        space=palette_space,
    )


def _nearest_palette_color(
    rgb_color: NDArray[np.float32],
    palette_rgb: NDArray[np.float32],
    palette_space_values: NDArray[np.float32],
    palette_space: str,
) -> NDArray[np.float32]:
    color_space_value = convert_color_space(rgb_color[None, :], palette_space)[0]
    distances = np.sum((palette_space_values - color_space_value) ** 2, axis=1)
    return palette_rgb[int(np.argmin(distances))]


def palette_diffuse(
    image: Image.Image,
    offsets: KernelOffsets,
    divisor: int,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    resolved_palette = _resolve_filter_palette(
        image,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=palette_space,
    )

    src = np.asarray(image.convert("RGB"), dtype=np.float32)
    err = np.zeros_like(src, dtype=np.float32)
    out = np.empty_like(src, dtype=np.uint8)
    palette_rgb = resolved_palette.colors.astype(np.float32)
    palette_space_values = convert_color_space(palette_rgb, palette_space)
    height, width, _ = src.shape

    for y in range(height):
        for x in range(width):
            adjusted = np.clip(src[y, x] + err[y, x], 0.0, 255.0)
            chosen = _nearest_palette_color(adjusted, palette_rgb, palette_space_values, palette_space)
            out[y, x] = chosen.astype(np.uint8)
            diff = adjusted - chosen

            for dx, dy, weight in offsets:
                nx = x + dx
                ny = y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    err[ny, nx] += (diff * weight) / divisor

    return Image.fromarray(out, mode="RGB")


def atkinson_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    return palette_diffuse(
        image,
        _ATKINSON_OFFSETS,
        8,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=palette_space,
    )


def sierra2_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    return palette_diffuse(
        image,
        _SIERRA2_OFFSETS,
        16,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=palette_space,
    )


def sierra3_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    return palette_diffuse(
        image,
        _SIERRA3_OFFSETS,
        32,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=palette_space,
    )


def stucki_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    return palette_diffuse(
        image,
        _STUCKI_OFFSETS,
        42,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=palette_space,
    )


def burkes_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    return palette_diffuse(
        image,
        _BURKES_OFFSETS,
        32,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=palette_space,
    )