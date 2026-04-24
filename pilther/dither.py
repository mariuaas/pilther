"""Canonical error-diffusion API organized by kernel and quantizer."""

from __future__ import annotations

from enum import Enum
from typing import Callable, Sequence

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from ._native_diffusion import make_native_lib, run_native_dither
from ._native_palette_diffusion import make_native_palette_lib, run_native_palette_dither
from .colorspace import ColorSpace, normalize_color_space
from .palette import Palette, PaletteMethod, resolve_palette


class Algorithm(str, Enum):
    ATKINSON = "atkinson"
    BURKES = "burkes"
    SIERRA2 = "sierra2"
    SIERRA3 = "sierra3"
    STUCKI = "stucki"


class Quantizer(str, Enum):
    THRESHOLD = "threshold"
    PALETTE = "palette"


_FILTER_LABELS: dict[Algorithm, str] = {
    Algorithm.ATKINSON: "Atkinson",
    Algorithm.BURKES: "Burkes",
    Algorithm.SIERRA2: "Sierra-2",
    Algorithm.SIERRA3: "Sierra-3",
    Algorithm.STUCKI: "Stucki",
}


def _binary_symbol(algorithm: Algorithm) -> str:
    return f"{algorithm.value}_dither"


def _palette_symbol(algorithm: Algorithm) -> str:
    return f"{algorithm.value}_palette_dither"


_BINARY_FILTERS: dict[Algorithm, tuple[Callable[[], object], str, str]] = {
    algorithm: (make_native_lib(_binary_symbol(algorithm)), _binary_symbol(algorithm), _FILTER_LABELS[algorithm])
    for algorithm in Algorithm
}

_PALETTE_FILTERS: dict[Algorithm, tuple[Callable[[], object], str, str]] = {
    algorithm: (
        make_native_palette_lib(_palette_symbol(algorithm)),
        _palette_symbol(algorithm),
        _FILTER_LABELS[algorithm],
    )
    for algorithm in Algorithm
}


def _resolve_filter_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None,
    palette_name: str | None,
    extract_colors: int | None,
    palette_method: PaletteMethod,
    color_space: ColorSpace,
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
        space=color_space,
    )


def dither(
    image: Image.Image,
    *,
    algorithm: Algorithm,
    quantizer: Quantizer = Quantizer.THRESHOLD,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    color_space: ColorSpace | str = ColorSpace.RGB,
) -> Image.Image:
    normalized_space = normalize_color_space(color_space)

    if quantizer is Quantizer.THRESHOLD:
        native_lib, symbol_name, filter_label = _BINARY_FILTERS[algorithm]
        return run_native_dither(image, native_lib, symbol_name, filter_label)

    resolved_palette = _resolve_filter_palette(
        image,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        color_space=normalized_space,
    )
    native_lib, symbol_name, filter_label = _PALETTE_FILTERS[algorithm]
    return run_native_palette_dither(
        image,
        resolved_palette.colors,
        native_lib,
        symbol_name,
        filter_label,
        normalized_space.value,
    )


def _threshold_filter(image: Image.Image, algorithm: Algorithm) -> Image.Image:
    native_lib, symbol_name, filter_label = _BINARY_FILTERS[algorithm]
    return run_native_dither(image, native_lib, symbol_name, filter_label)


def _palette_filter(
    image: Image.Image,
    algorithm: Algorithm,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: ColorSpace | str = ColorSpace.RGB,
) -> Image.Image:
    return dither(
        image,
        algorithm=algorithm,
        quantizer=Quantizer.PALETTE,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        color_space=palette_space,
    )


def _make_threshold_entrypoint(algorithm: Algorithm) -> Callable[[Image.Image], Image.Image]:
    def _filter(image: Image.Image) -> Image.Image:
        return _threshold_filter(image, algorithm)

    _filter.__name__ = algorithm.value
    _filter.__doc__ = f"Apply {_FILTER_LABELS[algorithm]} threshold diffusion."
    return _filter


def _make_palette_entrypoint(algorithm: Algorithm) -> Callable[..., Image.Image]:
    def _filter(
        image: Image.Image,
        *,
        palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
        palette_name: str | None = None,
        extract_colors: int | None = None,
        palette_method: PaletteMethod = "median_cut",
        palette_space: ColorSpace | str = ColorSpace.RGB,
    ) -> Image.Image:
        return _palette_filter(
            image,
            algorithm,
            palette=palette,
            palette_name=palette_name,
            extract_colors=extract_colors,
            palette_method=palette_method,
            palette_space=palette_space,
        )

    _filter.__name__ = f"{algorithm.value}_palette"
    _filter.__doc__ = f"Apply {_FILTER_LABELS[algorithm]} palette diffusion."
    return _filter


atkinson = _make_threshold_entrypoint(Algorithm.ATKINSON)
burkes = _make_threshold_entrypoint(Algorithm.BURKES)
sierra2 = _make_threshold_entrypoint(Algorithm.SIERRA2)
sierra3 = _make_threshold_entrypoint(Algorithm.SIERRA3)
stucki = _make_threshold_entrypoint(Algorithm.STUCKI)

atkinson_palette = _make_palette_entrypoint(Algorithm.ATKINSON)
burkes_palette = _make_palette_entrypoint(Algorithm.BURKES)
sierra2_palette = _make_palette_entrypoint(Algorithm.SIERRA2)
sierra3_palette = _make_palette_entrypoint(Algorithm.SIERRA3)
stucki_palette = _make_palette_entrypoint(Algorithm.STUCKI)