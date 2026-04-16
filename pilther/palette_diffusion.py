"""Palette-aware error-diffusion filters backed by Zig."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from ._native_palette_diffusion import make_native_palette_lib, run_native_palette_dither
from .colorspace import normalize_color_space
from .palette import Palette, PaletteMethod, resolve_palette

_ATKINSON_NATIVE_LIB = make_native_palette_lib("atkinson_palette_dither")
_SIERRA2_NATIVE_LIB = make_native_palette_lib("sierra2_palette_dither")
_SIERRA3_NATIVE_LIB = make_native_palette_lib("sierra3_palette_dither")
_STUCKI_NATIVE_LIB = make_native_palette_lib("stucki_palette_dither")
_BURKES_NATIVE_LIB = make_native_palette_lib("burkes_palette_dither")


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


def _run_palette_dither(
    image: Image.Image,
    *,
    native_lib,
    symbol_name: str,
    filter_label: str,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    normalized_space = normalize_color_space(palette_space)
    resolved_palette = _resolve_filter_palette(
        image,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=normalized_space,
    )
    return run_native_palette_dither(
        image,
        resolved_palette.colors,
        native_lib,
        symbol_name,
        filter_label,
        normalized_space,
    )


def atkinson_palette(
    image: Image.Image,
    *,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    palette_space: str = "rgb",
) -> Image.Image:
    return _run_palette_dither(
        image,
        native_lib=_ATKINSON_NATIVE_LIB,
        symbol_name="atkinson_palette_dither",
        filter_label="Atkinson",
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
    return _run_palette_dither(
        image,
        native_lib=_SIERRA2_NATIVE_LIB,
        symbol_name="sierra2_palette_dither",
        filter_label="Sierra-2",
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
    return _run_palette_dither(
        image,
        native_lib=_SIERRA3_NATIVE_LIB,
        symbol_name="sierra3_palette_dither",
        filter_label="Sierra-3",
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
    return _run_palette_dither(
        image,
        native_lib=_STUCKI_NATIVE_LIB,
        symbol_name="stucki_palette_dither",
        filter_label="Stucki",
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
    return _run_palette_dither(
        image,
        native_lib=_BURKES_NATIVE_LIB,
        symbol_name="burkes_palette_dither",
        filter_label="Burkes",
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        palette_space=palette_space,
    )