from __future__ import annotations

import math

import numpy as np
from PIL import Image

from pilther import atkinson


def _reference_atkinson(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape
    err = np.zeros((h, w), dtype=np.int16)
    out = gray.copy()

    for y in range(h):
        for x in range(w):
            old = int(out[y, x]) + int(err[y, x])
            new_val = 255 if old >= 128 else 0
            out[y, x] = new_val
            diff = math.trunc((old - new_val) / 8)

            if x + 1 < w:
                err[y, x + 1] += diff
            if x + 2 < w:
                err[y, x + 2] += diff
            if y + 1 < h:
                if x > 0:
                    err[y + 1, x - 1] += diff
                err[y + 1, x] += diff
                if x + 1 < w:
                    err[y + 1, x + 1] += diff
            if y + 2 < h:
                err[y + 2, x] += diff

    return out


def test_returns_pil_image(rgb_gradient_image: Image.Image) -> None:
    out = atkinson(rgb_gradient_image)
    assert isinstance(out, Image.Image)


def test_output_mode_size_and_binary_values(small_gray_image: Image.Image) -> None:
    out = atkinson(small_gray_image)
    arr = np.array(out)

    assert out.mode == "L"
    assert out.size == small_gray_image.size
    assert set(np.unique(arr).tolist()).issubset({0, 255})


def test_handles_rgba_input(rgba_checker_image: Image.Image) -> None:
    out = atkinson(rgba_checker_image)
    assert out.mode == "L"
    assert out.size == rgba_checker_image.size


def test_handles_single_pixel() -> None:
    img = Image.fromarray(np.array([[127]], dtype=np.uint8), mode="L")
    out = atkinson(img)
    assert np.array(out).tolist() == [[0]]


def test_matches_reference_algorithm(small_gray_image: Image.Image) -> None:
    inp = np.array(small_gray_image, dtype=np.uint8)
    expected = _reference_atkinson(inp)
    got = np.array(atkinson(small_gray_image), dtype=np.uint8)
    assert np.array_equal(got, expected)
