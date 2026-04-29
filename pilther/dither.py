"""Canonical error-diffusion API organized by kernel and quantizer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from ._native_diffusion import make_native_lib, run_native_dither, run_native_kernel_dither
from ._native_palette_diffusion import make_native_palette_lib, run_native_palette_dither, run_native_kernel_palette_dither
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


@dataclass(frozen=True)
class KernelStep:
    dx: int
    dy: int
    weight: int


@dataclass(frozen=True)
class KernelSpec:
    matrix: tuple[tuple[int, ...], ...]
    divisor: int
    steps: tuple[KernelStep, ...]
    depth: int

    @classmethod
    def from_centered_matrix(
        cls,
        matrix: Sequence[Sequence[int]] | NDArray[np.generic],
        *,
        divisor: int | None = None,
    ) -> KernelSpec:
        rows = _normalize_kernel_matrix(matrix)
        resolved_divisor = _resolve_kernel_divisor(rows, divisor)

        center_y = len(rows) // 2
        center_x = len(rows[0]) // 2
        steps: list[KernelStep] = []
        max_dy = 0

        for y, row in enumerate(rows):
            for x, weight in enumerate(row):
                if weight == 0:
                    continue

                dy = y - center_y
                dx = x - center_x
                if dy < 0:
                    continue
                if dy == 0 and dx <= 0:
                    continue

                steps.append(KernelStep(dx=dx, dy=dy, weight=weight))
                max_dy = max(max_dy, dy)

        if not steps:
            raise ValueError("Kernel matrix must contain at least one non-zero future weight.")

        return cls(
            matrix=rows,
            divisor=resolved_divisor,
            steps=tuple(steps),
            depth=max_dy + 1,
        )


def _normalize_kernel_matrix(
    matrix: Sequence[Sequence[int]] | NDArray[np.generic],
) -> tuple[tuple[int, ...], ...]:
    rows = tuple(tuple(int(value) for value in row) for row in matrix)
    if not rows:
        raise ValueError("Kernel matrix must have at least one row.")
    if len(rows) % 2 == 0:
        raise ValueError("Kernel matrix must have an odd number of rows.")

    width = len(rows[0])
    if width == 0:
        raise ValueError("Kernel matrix rows must be non-empty.")
    if width % 2 == 0:
        raise ValueError("Kernel matrix must have an odd number of columns.")

    if any(len(row) != width for row in rows):
        raise ValueError("Kernel matrix rows must all have the same width.")

    return rows


def _resolve_kernel_divisor(rows: tuple[tuple[int, ...], ...], divisor: int | None) -> int:
    if divisor is None:
        divisor = sum(sum(row) for row in rows)
    if divisor <= 0:
        raise ValueError("Kernel divisor must be positive.")
    return divisor


def _coerce_kernel_spec(
    kernel: KernelSpec | Sequence[Sequence[int]] | NDArray[np.generic],
    *,
    divisor: int | None,
) -> KernelSpec:
    if isinstance(kernel, KernelSpec):
        if divisor is not None and divisor != kernel.divisor:
            raise ValueError("Provide divisor through the KernelSpec itself, or omit divisor= when passing KernelSpec.")
        return kernel
    return KernelSpec.from_centered_matrix(kernel, divisor=divisor)


def _kernel_steps_array(spec: KernelSpec) -> NDArray[np.int16]:
    return np.asarray([(step.dx, step.dy, step.weight) for step in spec.steps], dtype=np.int16).reshape(-1)


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

_BUILTIN_KERNEL_SPECS: dict[Algorithm, KernelSpec] = {
    Algorithm.ATKINSON: KernelSpec.from_centered_matrix(
        (
            (0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0),
            (0, 0, 0, 1, 1),
            (0, 1, 1, 1, 0),
            (0, 0, 1, 0, 0),
        ),
        divisor=8,
    ),
    Algorithm.SIERRA2: KernelSpec.from_centered_matrix(
        (
            (0, 0, 0, 0, 0),
            (0, 0, 0, 4, 3),
            (1, 2, 3, 2, 1),
        ),
        divisor=16,
    ),
    Algorithm.SIERRA3: KernelSpec.from_centered_matrix(
        (
            (0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0),
            (0, 0, 0, 5, 3),
            (2, 4, 5, 4, 2),
            (0, 2, 3, 2, 0),
        ),
        divisor=32,
    ),
    Algorithm.STUCKI: KernelSpec.from_centered_matrix(
        (
            (0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0),
            (0, 0, 0, 8, 4),
            (2, 4, 8, 4, 2),
            (1, 2, 4, 2, 1),
        ),
        divisor=42,
    ),
    Algorithm.BURKES: KernelSpec.from_centered_matrix(
        (
            (0, 0, 0, 0, 0),
            (0, 0, 0, 8, 4),
            (2, 4, 8, 4, 2),
        ),
        divisor=32,
    ),
}


def get_kernel_spec(algorithm: Algorithm) -> KernelSpec:
    return _BUILTIN_KERNEL_SPECS[algorithm]


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
    algorithm: Algorithm | None = None,
    kernel: KernelSpec | Sequence[Sequence[int]] | NDArray[np.generic] | None = None,
    divisor: int | None = None,
    quantizer: Quantizer = Quantizer.THRESHOLD,
    palette: Sequence[int] | Sequence[Sequence[int]] | NDArray[np.generic] | Palette | None = None,
    palette_name: str | None = None,
    extract_colors: int | None = None,
    palette_method: PaletteMethod = "median_cut",
    color_space: ColorSpace | str = ColorSpace.RGB,
) -> Image.Image:
    normalized_space = normalize_color_space(color_space)
    if (algorithm is None) == (kernel is None):
        raise ValueError("Provide exactly one of algorithm= or kernel=.")

    if kernel is None and quantizer is Quantizer.THRESHOLD:
        native_lib, symbol_name, filter_label = _BINARY_FILTERS[algorithm]
        return run_native_dither(image, native_lib, symbol_name, filter_label)

    if kernel is not None and quantizer is Quantizer.THRESHOLD:
        spec = _coerce_kernel_spec(kernel, divisor=divisor)
        return run_native_kernel_dither(
            image,
            _kernel_steps_array(spec),
            divisor=spec.divisor,
            depth=spec.depth,
        )

    resolved_palette = _resolve_filter_palette(
        image,
        palette=palette,
        palette_name=palette_name,
        extract_colors=extract_colors,
        palette_method=palette_method,
        color_space=normalized_space,
    )

    if kernel is not None:
        spec = _coerce_kernel_spec(kernel, divisor=divisor)
        return run_native_kernel_palette_dither(
            image,
            resolved_palette.colors,
            _kernel_steps_array(spec),
            divisor=spec.divisor,
            depth=spec.depth,
            palette_space=normalized_space.value,
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
    return dither(image, algorithm=algorithm)


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