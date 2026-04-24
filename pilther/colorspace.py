"""Color-space helpers for palette extraction and matching."""

from __future__ import annotations

from enum import Enum

import numpy as np
from numpy.typing import NDArray


class ColorSpace(str, Enum):
    GRAYSCALE = "grayscale"
    RGB = "rgb"
    YCOCG = "ycocg"


_COLOR_SPACE_ALIASES = {
    "g": ColorSpace.GRAYSCALE,
    "gray": ColorSpace.GRAYSCALE,
    "greyscale": ColorSpace.GRAYSCALE,
    "grayscale": ColorSpace.GRAYSCALE,
    "l": ColorSpace.GRAYSCALE,
    "rgb": ColorSpace.RGB,
    "ycocg": ColorSpace.YCOCG,
}


def _as_float_rgb(values: NDArray[np.generic]) -> NDArray[np.float32]:
    arr = np.asarray(values, dtype=np.float32)
    if arr.ndim < 2 or arr.shape[-1] != 3:
        raise ValueError("Expected an array with a final RGB channel dimension of size 3")
    return arr


def normalize_color_space(space: ColorSpace | str) -> ColorSpace:
    if isinstance(space, ColorSpace):
        return space

    normalized = space.strip().lower()
    try:
        return _COLOR_SPACE_ALIASES[normalized]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported color space '{space}'. Expected one of: grayscale, rgb, ycocg."
        ) from exc


def rgb_to_grayscale(values: NDArray[np.generic]) -> NDArray[np.float32]:
    rgb = _as_float_rgb(values)
    grayscale = (0.299 * rgb[..., 0]) + (0.587 * rgb[..., 1]) + (0.114 * rgb[..., 2])
    return np.repeat(grayscale[..., np.newaxis], 3, axis=-1).astype(np.float32, copy=False)


def rgb_to_ycocg(values: NDArray[np.generic]) -> NDArray[np.float32]:
    rgb = _as_float_rgb(values)
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]

    co = r - b
    tmp = b + (co / 2.0)
    cg = g - tmp
    y = tmp + (cg / 2.0)

    return np.stack((y, co, cg), axis=-1).astype(np.float32, copy=False)


def ycocg_to_rgb(values: NDArray[np.generic]) -> NDArray[np.float32]:
    ycocg = _as_float_rgb(values)
    y = ycocg[..., 0]
    co = ycocg[..., 1]
    cg = ycocg[..., 2]

    tmp = y - (cg / 2.0)
    g = cg + tmp
    b = tmp - (co / 2.0)
    r = b + co

    return np.stack((r, g, b), axis=-1).astype(np.float32, copy=False)


def convert_color_space(values: NDArray[np.generic], space: ColorSpace | str) -> NDArray[np.float32]:
    normalized = normalize_color_space(space)
    rgb = _as_float_rgb(values)
    if normalized is ColorSpace.RGB:
        return rgb
    if normalized is ColorSpace.GRAYSCALE:
        return rgb_to_grayscale(rgb)
    return rgb_to_ycocg(rgb)
