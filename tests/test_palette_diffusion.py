from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from pilther import Algorithm, ColorSpace, Quantizer, atkinson_palette, burkes_palette, dither, sierra2_palette, sierra3_palette, stucki_palette

PALETTE_FILTERS = [
    atkinson_palette,
    burkes_palette,
    sierra2_palette,
    sierra3_palette,
    stucki_palette,
]


@pytest.mark.parametrize("func", PALETTE_FILTERS)
def test_palette_variant_returns_rgb_image_with_named_palette(
    func,
    rgb_gradient_image: Image.Image,
) -> None:
    out = func(rgb_gradient_image, palette_name="ega16")

    assert isinstance(out, Image.Image)
    assert out.mode == "RGB"
    assert out.size == rgb_gradient_image.size


@pytest.mark.parametrize("func", PALETTE_FILTERS)
def test_palette_variant_uses_only_named_palette_colors(func) -> None:
    img = Image.fromarray(
        np.array(
            [
                [[10, 10, 10], [120, 120, 120]],
                [[200, 200, 200], [250, 250, 250]],
            ],
            dtype=np.uint8,
        ),
        mode="RGB",
    )

    out = np.asarray(func(img, palette_name="gray4"), dtype=np.uint8)
    unique = np.unique(out.reshape(-1, 3), axis=0)
    expected = {
        (0, 0, 0),
        (85, 85, 85),
        (170, 170, 170),
        (255, 255, 255),
    }

    assert {tuple(color.tolist()) for color in unique}.issubset(expected)


@pytest.mark.parametrize("func", PALETTE_FILTERS)
def test_palette_variant_supports_extract_colors(func, rgb_gradient_image: Image.Image) -> None:
    out = func(
        rgb_gradient_image,
        extract_colors=3,
        palette_method="mean_variance_cut",
        palette_space="ycocg",
    )

    assert out.mode == "RGB"
    assert out.size == rgb_gradient_image.size


@pytest.mark.parametrize("func", PALETTE_FILTERS)
def test_palette_variant_handles_rgba_input(func, rgba_checker_image: Image.Image) -> None:
    out = func(rgba_checker_image, palette_name="gameboy4")

    assert out.mode == "RGB"
    assert out.size == rgba_checker_image.size


@pytest.mark.parametrize("func", PALETTE_FILTERS)
def test_palette_variant_requires_palette_source(func, rgb_gradient_image: Image.Image) -> None:
    with pytest.raises(ValueError, match="Provide palette"):
        func(rgb_gradient_image)


@pytest.mark.parametrize(
    ("func", "expected"),
    [
        (atkinson_palette, [[[255, 255, 255], [0, 0, 0]], [[255, 255, 255], [0, 0, 0]]]),
        (burkes_palette, [[[255, 255, 255], [0, 0, 0]], [[0, 0, 0], [255, 255, 255]]]),
        (sierra2_palette, [[[255, 255, 255], [0, 0, 0]], [[255, 255, 255], [0, 0, 0]]]),
        (sierra3_palette, [[[255, 255, 255], [0, 0, 0]], [[255, 255, 255], [0, 0, 0]]]),
        (stucki_palette, [[[255, 255, 255], [0, 0, 0]], [[255, 255, 255], [255, 255, 255]]]),
    ],
)
def test_palette_variant_matches_reference_on_tiny_gray2_case(func, expected) -> None:
    img = Image.fromarray(np.full((2, 2, 3), 140, dtype=np.uint8), mode="RGB")

    out = np.asarray(func(img, palette_name="gray2"), dtype=np.uint8)

    assert np.array_equal(out, np.array(expected, dtype=np.uint8))


@pytest.mark.parametrize("func", PALETTE_FILTERS)
def test_palette_variant_matches_reference_on_tiny_rgb_palette_case(func) -> None:
    img = Image.fromarray(
        np.array(
            [
                [[200, 10, 10], [120, 10, 10]],
                [[10, 200, 10], [10, 10, 200]],
            ],
            dtype=np.uint8,
        ),
        mode="RGB",
    )
    palette = [[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]]

    out = np.asarray(func(img, palette=palette), dtype=np.uint8)

    assert np.array_equal(
        out,
        np.array(
            [
                [[255, 0, 0], [0, 0, 0]],
                [[0, 255, 0], [0, 0, 255]],
            ],
            dtype=np.uint8,
        ),
    )


def test_canonical_dispatcher_supports_palette_quantization(rgb_gradient_image: Image.Image) -> None:
    out = dither(
        rgb_gradient_image,
        algorithm=Algorithm.ATKINSON,
        quantizer=Quantizer.PALETTE,
        palette_name="gray4",
        color_space=ColorSpace.GRAYSCALE,
    )

    assert out.mode == "RGB"
    assert out.size == rgb_gradient_image.size