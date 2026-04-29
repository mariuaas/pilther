from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pytest
from PIL import Image

from pilther import Algorithm, KernelSpec, KernelStep, Quantizer, burkes, dither, get_kernel_spec, sierra2, sierra3, stucki

FilterFunc = Callable[[Image.Image], Image.Image]

FILTER_CASES = [
    (
        "sierra3",
        sierra3,
        [
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
        ],
        32,
    ),
    (
        "sierra2",
        sierra2,
        [
            (1, 0, 4),
            (2, 0, 3),
            (-2, 1, 1),
            (-1, 1, 2),
            (0, 1, 3),
            (1, 1, 2),
            (2, 1, 1),
        ],
        16,
    ),
    (
        "stucki",
        stucki,
        [
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
        ],
        42,
    ),
    (
        "burkes",
        burkes,
        [
            (1, 0, 8),
            (2, 0, 4),
            (-2, 1, 2),
            (-1, 1, 4),
            (0, 1, 8),
            (1, 1, 4),
            (2, 1, 2),
        ],
        32,
    ),
]


def _reference_dither(gray: np.ndarray, offsets: list[tuple[int, int, int]], divisor: int) -> np.ndarray:
    h, w = gray.shape
    err = np.zeros((h, w), dtype=np.int16)
    out = gray.copy()

    for y in range(h):
        for x in range(w):
            old = int(out[y, x]) + int(err[y, x])
            new_val = 255 if old >= 128 else 0
            out[y, x] = new_val
            diff = old - new_val

            for dx, dy, weight in offsets:
                nx = x + dx
                ny = y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    err[ny, nx] += math.trunc((diff * weight) / divisor)

    return out


@pytest.mark.parametrize(("_name", "func", "_offsets", "_divisor"), FILTER_CASES)
def test_returns_pil_image(
    _name: str,
    func: FilterFunc,
    _offsets: list[tuple[int, int, int]],
    _divisor: int,
    rgb_gradient_image: Image.Image,
) -> None:
    out = func(rgb_gradient_image)
    assert isinstance(out, Image.Image)


@pytest.mark.parametrize(("_name", "func", "_offsets", "_divisor"), FILTER_CASES)
def test_output_mode_size_and_binary_values(
    _name: str,
    func: FilterFunc,
    _offsets: list[tuple[int, int, int]],
    _divisor: int,
    small_gray_image: Image.Image,
) -> None:
    out = func(small_gray_image)
    arr = np.array(out)

    assert out.mode == "L"
    assert out.size == small_gray_image.size
    assert set(np.unique(arr).tolist()).issubset({0, 255})


@pytest.mark.parametrize(("_name", "func", "_offsets", "_divisor"), FILTER_CASES)
def test_handles_rgba_input(
    _name: str,
    func: FilterFunc,
    _offsets: list[tuple[int, int, int]],
    _divisor: int,
    rgba_checker_image: Image.Image,
) -> None:
    out = func(rgba_checker_image)
    assert out.mode == "L"
    assert out.size == rgba_checker_image.size


@pytest.mark.parametrize(("_name", "func", "_offsets", "_divisor"), FILTER_CASES)
def test_handles_single_pixel(
    _name: str,
    func: FilterFunc,
    _offsets: list[tuple[int, int, int]],
    _divisor: int,
) -> None:
    img = Image.fromarray(np.array([[127]], dtype=np.uint8), mode="L")
    out = func(img)
    assert np.array(out).tolist() == [[0]]


@pytest.mark.parametrize(("_name", "func", "offsets", "divisor"), FILTER_CASES)
def test_matches_reference_algorithm(
    _name: str,
    func: FilterFunc,
    offsets: list[tuple[int, int, int]],
    divisor: int,
    small_gray_image: Image.Image,
) -> None:
    inp = np.array(small_gray_image, dtype=np.uint8)
    expected = _reference_dither(inp, offsets, divisor)
    got = np.array(func(small_gray_image), dtype=np.uint8)
    assert np.array_equal(got, expected)


def test_canonical_dispatcher_supports_threshold_quantization(small_gray_image: Image.Image) -> None:
    out = dither(small_gray_image, algorithm=Algorithm.BURKES, quantizer=Quantizer.THRESHOLD)

    assert out.mode == "L"
    assert out.size == small_gray_image.size


@pytest.mark.parametrize(
    ("algorithm", "expected_steps", "expected_divisor", "expected_depth"),
    [
        (Algorithm.SIERRA3, FILTER_CASES[0][2], FILTER_CASES[0][3], 3),
        (Algorithm.SIERRA2, FILTER_CASES[1][2], FILTER_CASES[1][3], 2),
        (Algorithm.STUCKI, FILTER_CASES[2][2], FILTER_CASES[2][3], 3),
        (Algorithm.BURKES, FILTER_CASES[3][2], FILTER_CASES[3][3], 2),
    ],
)
def test_builtin_kernel_specs_match_reference_offsets(
    algorithm: Algorithm,
    expected_steps: list[tuple[int, int, int]],
    expected_divisor: int,
    expected_depth: int,
) -> None:
    spec = get_kernel_spec(algorithm)

    assert spec.divisor == expected_divisor
    assert spec.depth == expected_depth
    assert spec.steps == tuple(KernelStep(dx=dx, dy=dy, weight=weight) for dx, dy, weight in expected_steps)


def test_kernel_spec_ignores_past_weights() -> None:
    spec = KernelSpec.from_centered_matrix(
        (
            (9, 8, 7),
            (6, 5, 4),
            (3, 2, 1),
        ),
        divisor=7,
    )

    assert spec.steps == (
        KernelStep(dx=1, dy=0, weight=4),
        KernelStep(dx=-1, dy=1, weight=3),
        KernelStep(dx=0, dy=1, weight=2),
        KernelStep(dx=1, dy=1, weight=1),
    )
    assert spec.depth == 2


def test_dither_accepts_builtin_kernel_spec(small_gray_image: Image.Image) -> None:
    expected = np.array(burkes(small_gray_image), dtype=np.uint8)

    out = dither(small_gray_image, kernel=get_kernel_spec(Algorithm.BURKES))

    assert np.array_equal(np.array(out, dtype=np.uint8), expected)


def test_dither_accepts_centered_matrix_and_default_divisor(small_gray_image: Image.Image) -> None:
    spec = get_kernel_spec(Algorithm.SIERRA2)

    out = dither(small_gray_image, kernel=np.array(spec.matrix, dtype=np.int16))

    assert np.array_equal(np.array(out, dtype=np.uint8), np.array(sierra2(small_gray_image), dtype=np.uint8))


@pytest.mark.parametrize(
    ("matrix", "divisor", "match"),
    [
        (((0, 1), (1, 0)), 8, "odd number of rows|odd number of columns"),
        (((0, 0, 0), (0, 0, 0)), 8, "odd number of rows"),
        (((0, 0, 0),), 0, "divisor must be positive"),
        (((0, 0, 0), (0, 0, 0), (0, 0, 0)), 8, "at least one non-zero future weight"),
    ],
)
def test_kernel_spec_rejects_invalid_centered_matrices(matrix, divisor: int, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        KernelSpec.from_centered_matrix(matrix, divisor=divisor)


def test_dither_requires_exactly_one_kernel_selector(small_gray_image: Image.Image) -> None:
    with pytest.raises(ValueError, match="exactly one"):
        dither(small_gray_image, algorithm=Algorithm.BURKES, kernel=get_kernel_spec(Algorithm.BURKES))