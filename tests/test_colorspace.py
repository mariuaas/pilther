from __future__ import annotations

import numpy as np
import pytest

from pilther.colorspace import ColorSpace, convert_color_space, normalize_color_space, rgb_to_grayscale, rgb_to_ycocg, ycocg_to_rgb


def test_rgb_ycocg_roundtrip_preserves_values() -> None:
    rgb = np.array(
        [
            [[0, 0, 0], [255, 255, 255], [255, 0, 0]],
            [[0, 255, 0], [0, 0, 255], [64, 128, 192]],
        ],
        dtype=np.uint8,
    )

    transformed = rgb_to_ycocg(rgb)
    restored = ycocg_to_rgb(transformed)

    assert np.allclose(restored, rgb.astype(np.float32), atol=1e-4)


def test_convert_color_space_rgb_is_identity() -> None:
    rgb = np.array([[[12, 34, 56]]], dtype=np.uint8)
    converted = convert_color_space(rgb, ColorSpace.RGB)
    assert np.array_equal(converted, rgb.astype(np.float32))


def test_convert_color_space_grayscale_collapses_channels() -> None:
    rgb = np.array([[[10, 20, 30]]], dtype=np.uint8)

    converted = convert_color_space(rgb, ColorSpace.GRAYSCALE)

    expected = rgb_to_grayscale(rgb)
    assert np.array_equal(converted, expected)
    assert converted.shape == rgb.shape


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("rgb", ColorSpace.RGB),
        ("ycocg", ColorSpace.YCOCG),
        ("gray", ColorSpace.GRAYSCALE),
        ("greyscale", ColorSpace.GRAYSCALE),
        ("L", ColorSpace.GRAYSCALE),
        (ColorSpace.GRAYSCALE, ColorSpace.GRAYSCALE),
    ],
)
def test_normalize_color_space_accepts_aliases(value: ColorSpace | str, expected: ColorSpace) -> None:
    assert normalize_color_space(value) is expected


def test_convert_color_space_rejects_unknown_space() -> None:
    rgb = np.array([[[12, 34, 56]]], dtype=np.uint8)
    with pytest.raises(ValueError, match="Unsupported color space"):
        convert_color_space(rgb, "lab")
