from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from pilther.palette import (
    Palette,
    extract_palette,
    get_named_palette,
    list_named_palettes,
    normalize_palette,
    resolve_palette,
)


def test_normalize_palette_promotes_grayscale_values() -> None:
    palette = normalize_palette([0, 127, 255], name="gray3")

    assert isinstance(palette, Palette)
    assert palette.name == "gray3"
    assert np.array_equal(
        palette.colors,
        np.array([[0, 0, 0], [127, 127, 127], [255, 255, 255]], dtype=np.uint8),
    )


def test_extract_palette_returns_requested_count_for_colorful_image() -> None:
    arr = np.array(
        [
            [[255, 0, 0], [255, 128, 0], [255, 255, 0], [128, 255, 0]],
            [[0, 255, 0], [0, 255, 128], [0, 255, 255], [0, 128, 255]],
            [[0, 0, 255], [128, 0, 255], [255, 0, 255], [255, 0, 128]],
            [[32, 32, 32], [96, 96, 96], [160, 160, 160], [224, 224, 224]],
        ],
        dtype=np.uint8,
    )
    image = Image.fromarray(arr, mode="RGB")

    palette = extract_palette(image, 4, method="median_cut", space="rgb")

    assert palette.colors.shape == (4, 3)
    assert palette.colors.dtype == np.uint8


@pytest.mark.parametrize("method", ["median_cut", "mean_variance_cut", "pca_cut"])
@pytest.mark.parametrize("space", ["rgb", "ycocg"])
def test_extract_palette_supports_configured_methods_and_spaces(
    method: str,
    space: str,
    rgb_gradient_image: Image.Image,
) -> None:
    palette = extract_palette(rgb_gradient_image, 3, method=method, space=space)

    assert isinstance(palette, Palette)
    assert palette.colors.shape[1] == 3
    assert 1 <= palette.colors.shape[0] <= 3


def test_extract_palette_returns_all_unique_colors_when_request_exceeds_unique_count() -> None:
    image = Image.fromarray(
        np.array(
            [
                [[0, 0, 0], [255, 255, 255]],
                [[255, 255, 255], [0, 0, 0]],
            ],
            dtype=np.uint8,
        ),
        mode="RGB",
    )

    palette = extract_palette(image, 8)

    assert np.array_equal(
        palette.colors,
        np.array([[0, 0, 0], [255, 255, 255]], dtype=np.uint8),
    )


def test_resolve_palette_extracts_from_image(rgb_gradient_image: Image.Image) -> None:
    palette = resolve_palette(image=rgb_gradient_image, colors=2, method="median_cut", space="rgb")

    assert isinstance(palette, Palette)
    assert palette.colors.shape[0] <= 2


def test_get_named_palette_returns_named_palette() -> None:
    palette = get_named_palette("gray4")

    assert palette.name == "gray4"
    assert palette.colors.shape == (4, 3)
    assert np.array_equal(palette.colors[:, 0], palette.colors[:, 1])
    assert np.array_equal(palette.colors[:, 1], palette.colors[:, 2])


def test_list_named_palettes_contains_expected_entries() -> None:
    names = list_named_palettes()

    assert "gray2" in names
    assert "cga4" in names
    assert "ega16" in names
    assert "ansi16" in names
    assert "web216" in names
    assert "term256" in names


def test_resolve_palette_supports_palette_name() -> None:
    palette = resolve_palette(palette_name="gameboy4")

    assert isinstance(palette, Palette)
    assert palette.name == "gameboy4"
    assert palette.colors.shape == (4, 3)


def test_get_named_palette_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown palette"):
        get_named_palette("unknown")


def test_get_named_palette_term256_has_expected_shape_and_samples() -> None:
    palette = get_named_palette("term256")

    assert palette.colors.shape == (256, 3)
    assert tuple(palette.colors[0]) == (0, 0, 0)
    assert tuple(palette.colors[15]) == (255, 255, 255)
    assert tuple(palette.colors[16]) == (0, 0, 0)
    assert tuple(palette.colors[-1]) == (238, 238, 238)


def test_extract_palette_rejects_unsupported_method(rgb_gradient_image: Image.Image) -> None:
    with pytest.raises(ValueError, match="Unsupported palette extraction method"):
        extract_palette(rgb_gradient_image, 2, method="octree")