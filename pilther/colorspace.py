"""Color-space helpers for palette extraction and matching."""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import NDArray

ColorSpace = Literal["rgb", "ycocg"]


def _as_float_rgb(values: NDArray[np.generic]) -> NDArray[np.float32]:
    arr = np.asarray(values, dtype=np.float32)
    if arr.ndim < 2 or arr.shape[-1] != 3:
        raise ValueError("Expected an array with a final RGB channel dimension of size 3")
    return arr


def normalize_color_space(space: str) -> ColorSpace:
    normalized = space.strip().lower()
    if normalized not in {"rgb", "ycocg"}:
        raise ValueError(f"Unsupported color space '{space}'. Expected 'rgb' or 'ycocg'.")
    return normalized


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


def convert_color_space(values: NDArray[np.generic], space: str) -> NDArray[np.float32]:
    normalized = normalize_color_space(space)
    rgb = _as_float_rgb(values)
    if normalized == "rgb":
        return rgb
    return rgb_to_ycocg(rgb)
