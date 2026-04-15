"""Palette normalization, named palettes, and extraction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .colorspace import convert_color_space, normalize_color_space

PaletteMethod = str
_SUPPORTED_METHODS = {"median_cut", "mean_variance_cut", "pca_cut"}


def _grayscale_palette(levels: int) -> NDArray[np.uint8]:
    values = np.rint(np.linspace(0, 255, levels)).astype(np.uint8)
    return np.stack((values, values, values), axis=-1)


def _web216_palette() -> NDArray[np.uint8]:
    steps = np.array([0, 51, 102, 153, 204, 255], dtype=np.uint8)
    grid = np.stack(np.meshgrid(steps, steps, steps, indexing="ij"), axis=-1)
    return grid.reshape(-1, 3)


def _ansi16_palette() -> NDArray[np.uint8]:
    return np.array(
        [
            [0, 0, 0],
            [128, 0, 0],
            [0, 128, 0],
            [128, 128, 0],
            [0, 0, 128],
            [128, 0, 128],
            [0, 128, 128],
            [192, 192, 192],
            [128, 128, 128],
            [255, 0, 0],
            [0, 255, 0],
            [255, 255, 0],
            [0, 0, 255],
            [255, 0, 255],
            [0, 255, 255],
            [255, 255, 255],
        ],
        dtype=np.uint8,
    )


def _term256_palette() -> NDArray[np.uint8]:
    ansi16 = _ansi16_palette()
    cube_steps = np.array([0, 95, 135, 175, 215, 255], dtype=np.uint8)
    cube = np.stack(np.meshgrid(cube_steps, cube_steps, cube_steps, indexing="ij"), axis=-1).reshape(-1, 3)
    gray_values = np.arange(8, 238 + 1, 10, dtype=np.uint8)
    grayscale = np.stack((gray_values, gray_values, gray_values), axis=-1)
    return np.vstack((ansi16, cube, grayscale)).astype(np.uint8, copy=False)


_NAMED_PALETTES: dict[str, NDArray[np.uint8]] = {
    "gray2": _grayscale_palette(2),
    "gray4": _grayscale_palette(4),
    "gray8": _grayscale_palette(8),
    "gray16": _grayscale_palette(16),
    "gray32": _grayscale_palette(32),
    "cga4": np.array(
        [
            [0, 0, 0],
            [85, 255, 255],
            [255, 85, 255],
            [255, 255, 255],
        ],
        dtype=np.uint8,
    ),
    "gameboy4": np.array(
        [
            [15, 56, 15],
            [48, 98, 48],
            [139, 172, 15],
            [155, 188, 15],
        ],
        dtype=np.uint8,
    ),
    "ega16": np.array(
        [
            [0, 0, 0],
            [0, 0, 170],
            [0, 170, 0],
            [0, 170, 170],
            [170, 0, 0],
            [170, 0, 170],
            [170, 85, 0],
            [170, 170, 170],
            [85, 85, 85],
            [85, 85, 255],
            [85, 255, 85],
            [85, 255, 255],
            [255, 85, 85],
            [255, 85, 255],
            [255, 255, 85],
            [255, 255, 255],
        ],
        dtype=np.uint8,
    ),
    "ansi16": _ansi16_palette(),
    "web216": _web216_palette(),
    "term256": _term256_palette(),
}


@dataclass(frozen=True)
class Palette:
    colors: NDArray[np.uint8]
    name: str | None = None

    def __post_init__(self) -> None:
        colors = np.asarray(self.colors, dtype=np.uint8)
        if colors.ndim != 2 or colors.shape[1] != 3:
            raise ValueError("Palette colors must have shape (n, 3)")
        if colors.shape[0] == 0:
            raise ValueError("Palette must contain at least one color")
        object.__setattr__(self, "colors", colors)


@dataclass(frozen=True)
class _Bucket:
    indices: NDArray[np.intp]


def normalize_palette(
    colors: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette,
    *,
    name: str | None = None,
) -> Palette:
    if isinstance(colors, Palette):
        if name is None or colors.name == name:
            return colors
        return Palette(colors=colors.colors.copy(), name=name)

    arr = np.asarray(colors)
    if arr.ndim == 1:
        arr = np.stack((arr, arr, arr), axis=-1)

    if arr.ndim != 2 or arr.shape[1] not in {3, 4}:
        raise ValueError("Palette values must be grayscale, RGB, or RGBA colors")

    rgb = np.asarray(arr[:, :3], dtype=np.float32)
    rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    unique = _unique_rows(rgb)
    return Palette(colors=unique, name=name)


def list_named_palettes() -> tuple[str, ...]:
    return tuple(sorted(_NAMED_PALETTES))


def get_named_palette(name: str) -> Palette:
    normalized = name.strip().lower()
    try:
        colors = _NAMED_PALETTES[normalized]
    except KeyError as exc:
        expected = ", ".join(list_named_palettes())
        raise ValueError(f"Unknown palette '{name}'. Expected one of: {expected}.") from exc
    return Palette(colors=colors.copy(), name=normalized)


def extract_palette(
    image: Image.Image,
    colors: int,
    *,
    method: PaletteMethod = "median_cut",
    space: str = "rgb",
) -> Palette:
    if colors <= 0:
        raise ValueError("colors must be a positive integer")

    normalized_method = _normalize_method(method)
    normalized_space = normalize_color_space(space)

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    pixels = rgb.reshape(-1, 3)
    unique_rgb, inverse = np.unique(pixels, axis=0, return_inverse=True)
    counts = np.bincount(inverse)

    if unique_rgb.shape[0] <= colors:
        return Palette(colors=unique_rgb.astype(np.uint8, copy=False))

    transformed = convert_color_space(unique_rgb, normalized_space)
    palette_colors = _split_palette(unique_rgb, transformed, counts, colors, normalized_method)
    return Palette(colors=palette_colors)


def resolve_palette(
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    image: Image.Image | None = None,
    colors: int | None = None,
    method: PaletteMethod = "median_cut",
    space: str = "rgb",
    name: str | None = None,
) -> Palette:
    if palette is not None:
        return normalize_palette(palette, name=name)

    if palette_name is not None:
        resolved = get_named_palette(palette_name)
        if name is None or resolved.name == name:
            return resolved
        return Palette(colors=resolved.colors.copy(), name=name)

    if image is None or colors is None:
        raise ValueError("Provide palette=..., palette_name=..., or both image=... and colors=...")

    return extract_palette(image, colors, method=method, space=space)


def _normalize_method(method: str) -> PaletteMethod:
    normalized = method.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in _SUPPORTED_METHODS:
        expected = ", ".join(sorted(_SUPPORTED_METHODS))
        raise ValueError(f"Unsupported palette extraction method '{method}'. Expected one of: {expected}.")
    return normalized


def _split_palette(
    rgb: NDArray[np.uint8],
    transformed: NDArray[np.float32],
    counts: NDArray[np.int64] | NDArray[np.int32],
    target_colors: int,
    method: PaletteMethod,
) -> NDArray[np.uint8]:
    buckets = [_Bucket(indices=np.arange(rgb.shape[0], dtype=np.intp))]

    while len(buckets) < target_colors:
        candidates: list[tuple[float, int, tuple[_Bucket, _Bucket] | None]] = []
        for bucket_index, bucket in enumerate(buckets):
            split = _split_bucket(bucket, transformed, counts, method)
            if split is None:
                continue
            score = _bucket_score(bucket, transformed, counts, method)
            candidates.append((score, bucket_index, split))

        if not candidates:
            break

        _, bucket_index, split = max(candidates, key=lambda item: (item[0], -item[1]))
        left, right = split
        buckets[bucket_index] = left
        buckets.insert(bucket_index + 1, right)

    colors = [_bucket_color(bucket, rgb, counts) for bucket in buckets]
    palette = np.asarray(colors, dtype=np.uint8)
    return _unique_rows(palette)


def _bucket_score(
    bucket: _Bucket,
    transformed: NDArray[np.float32],
    counts: NDArray[np.int64] | NDArray[np.int32],
    method: PaletteMethod,
) -> float:
    values = transformed[bucket.indices]
    weights = counts[bucket.indices].astype(np.float32)
    if method == "median_cut":
        ranges = values.max(axis=0) - values.min(axis=0)
        return float(ranges.max() * weights.sum())

    centered = values - _weighted_mean(values, weights)
    variances = np.average(centered * centered, axis=0, weights=weights)
    if method == "mean_variance_cut":
        return float(variances.max() * weights.sum())
    return float(variances.sum() * weights.sum())


def _split_bucket(
    bucket: _Bucket,
    transformed: NDArray[np.float32],
    counts: NDArray[np.int64] | NDArray[np.int32],
    method: PaletteMethod,
) -> tuple[_Bucket, _Bucket] | None:
    if bucket.indices.size < 2:
        return None

    values = transformed[bucket.indices]
    weights = counts[bucket.indices].astype(np.float32)

    if method == "median_cut":
        ranges = values.max(axis=0) - values.min(axis=0)
        channel = int(np.argmax(ranges))
        order = np.argsort(values[:, channel], kind="stable")
        return _split_sorted_bucket(bucket.indices[order], weights[order])

    if method == "mean_variance_cut":
        centered = values - _weighted_mean(values, weights)
        variances = np.average(centered * centered, axis=0, weights=weights)
        channel = int(np.argmax(variances))
        order = np.argsort(values[:, channel], kind="stable")
        ordered_indices = bucket.indices[order]
        ordered_values = values[order, channel]
        ordered_weights = weights[order]
        threshold = _weighted_mean(ordered_values[:, None], ordered_weights)[0]
        split_at = int(np.searchsorted(ordered_values, threshold, side="right"))
        split_at = _clamp_split_index(split_at, ordered_indices.size)
        return _make_split(ordered_indices, split_at)

    centered = values - _weighted_mean(values, weights)
    covariance = _weighted_covariance(centered, weights)
    _, eigenvectors = np.linalg.eigh(covariance)
    axis = eigenvectors[:, -1]
    projections = centered @ axis
    order = np.argsort(projections, kind="stable")
    return _split_sorted_bucket(bucket.indices[order], weights[order])


def _split_sorted_bucket(
    ordered_indices: NDArray[np.intp],
    ordered_weights: NDArray[np.float32],
) -> tuple[_Bucket, _Bucket] | None:
    cumulative = np.cumsum(ordered_weights)
    total = float(cumulative[-1])
    split_at = int(np.searchsorted(cumulative, total / 2.0, side="left")) + 1
    split_at = _clamp_split_index(split_at, ordered_indices.size)
    return _make_split(ordered_indices, split_at)


def _make_split(
    ordered_indices: NDArray[np.intp],
    split_at: int,
) -> tuple[_Bucket, _Bucket] | None:
    if split_at <= 0 or split_at >= ordered_indices.size:
        return None
    return _Bucket(indices=ordered_indices[:split_at]), _Bucket(indices=ordered_indices[split_at:])


def _clamp_split_index(split_at: int, size: int) -> int:
    return max(1, min(size - 1, split_at))


def _bucket_color(
    bucket: _Bucket,
    rgb: NDArray[np.uint8],
    counts: NDArray[np.int64] | NDArray[np.int32],
) -> NDArray[np.uint8]:
    values = rgb[bucket.indices].astype(np.float32)
    weights = counts[bucket.indices].astype(np.float32)
    mean = _weighted_mean(values, weights)
    return np.clip(np.rint(mean), 0, 255).astype(np.uint8)


def _weighted_mean(values: NDArray[np.float32], weights: NDArray[np.float32]) -> NDArray[np.float32]:
    total = float(weights.sum())
    if total == 0:
        return np.zeros(values.shape[1], dtype=np.float32)
    return np.average(values, axis=0, weights=weights).astype(np.float32, copy=False)


def _weighted_covariance(values: NDArray[np.float32], weights: NDArray[np.float32]) -> NDArray[np.float32]:
    total = float(weights.sum())
    if total == 0:
        return np.zeros((values.shape[1], values.shape[1]), dtype=np.float32)
    weighted = values * weights[:, None]
    covariance = (values.T @ weighted) / total
    return covariance.astype(np.float32, copy=False)


def _unique_rows(values: NDArray[np.uint8]) -> NDArray[np.uint8]:
    unique, indices = np.unique(values, axis=0, return_index=True)
    order = np.argsort(indices, kind="stable")
    return unique[order]
