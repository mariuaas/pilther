from __future__ import annotations

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def rgb_gradient_image() -> Image.Image:
    arr = np.array(
        [
            [[0, 0, 0], [64, 64, 64], [128, 128, 128], [255, 255, 255]],
            [[16, 16, 16], [80, 80, 80], [144, 144, 144], [240, 240, 240]],
            [[32, 32, 32], [96, 96, 96], [160, 160, 160], [224, 224, 224]],
            [[48, 48, 48], [112, 112, 112], [176, 176, 176], [208, 208, 208]],
        ],
        dtype=np.uint8,
    )
    return Image.fromarray(arr, mode="RGB")


@pytest.fixture
def rgba_checker_image() -> Image.Image:
    arr = np.array(
        [
            [[0, 0, 0, 255], [255, 255, 255, 128]],
            [[255, 255, 255, 64], [0, 0, 0, 255]],
        ],
        dtype=np.uint8,
    )
    return Image.fromarray(arr, mode="RGBA")


@pytest.fixture
def small_gray_image() -> Image.Image:
    arr = np.array(
        [
            [0, 64, 128, 192],
            [16, 80, 144, 208],
            [32, 96, 160, 224],
            [48, 112, 176, 240],
        ],
        dtype=np.uint8,
    )
    return Image.fromarray(arr, mode="L")
