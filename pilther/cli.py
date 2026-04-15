from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from PIL import Image

from .atkinson import atkinson
from .bluenoise import bluenoise
from .burkes import burkes
from .palette import list_named_palettes
from .palette_diffusion import (
    atkinson_palette,
    burkes_palette,
    sierra2_palette,
    sierra3_palette,
    stucki_palette,
)
from .sierra2 import sierra2
from .sierra3 import sierra3
from .stucki import stucki

FilterFunc = Callable[[Image.Image], Image.Image]
PaletteFilterFunc = Callable[..., Image.Image]

FILTERS: dict[str, FilterFunc] = {
    "atkinson": atkinson,
    "bluenoise": bluenoise,
    "burkes": burkes,
    "sierra2": sierra2,
    "sierra3": sierra3,
    "stucki": stucki,
}

PALETTE_FILTERS: dict[str, PaletteFilterFunc] = {
    "atkinson_palette": atkinson_palette,
    "burkes_palette": burkes_palette,
    "sierra2_palette": sierra2_palette,
    "sierra3_palette": sierra3_palette,
    "stucki_palette": stucki_palette,
}

ALL_FILTERS = {**FILTERS, **PALETTE_FILTERS}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pilther",
        description="Apply a dithering filter to an input image.",
    )
    parser.add_argument(
        "--filter",
        dest="filter_name",
        choices=tuple(ALL_FILTERS),
        default="atkinson",
        help="Dithering filter to apply (default: %(default)s)",
    )
    parser.add_argument(
        "--palette",
        dest="palette_name",
        choices=list_named_palettes(),
        help="Named palette for palette-aware filters.",
    )
    parser.add_argument(
        "--extract-colors",
        dest="extract_colors",
        type=int,
        help="Extract a palette with N colors from the input image for palette-aware filters.",
    )
    parser.add_argument(
        "--palette-method",
        dest="palette_method",
        choices=("median_cut", "mean_variance_cut", "pca_cut"),
        default="median_cut",
        help="Palette extraction method for palette-aware filters (default: %(default)s).",
    )
    parser.add_argument(
        "--palette-space",
        dest="palette_space",
        choices=("rgb", "ycocg"),
        default="rgb",
        help="Color space for palette extraction and matching (default: %(default)s).",
    )
    parser.add_argument("input", type=Path, help="Input image path")
    parser.add_argument("output", type=Path, help="Output image path")
    args = parser.parse_args()

    with Image.open(args.input) as img:
        if args.filter_name in PALETTE_FILTERS:
            out = PALETTE_FILTERS[args.filter_name](
                img,
                palette_name=args.palette_name,
                extract_colors=args.extract_colors,
                palette_method=args.palette_method,
                palette_space=args.palette_space,
            )
        else:
            if args.palette_name is not None or args.extract_colors is not None:
                parser.error("--palette and --extract-colors are only valid for palette-aware filters.")
            out = FILTERS[args.filter_name](img)
    out.save(args.output)


if __name__ == "__main__":
    main()
