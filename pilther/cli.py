from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from .bluenoise import bluenoise
from .colorspace import ColorSpace
from .dither import Algorithm, Quantizer, dither
from .palette import list_named_palettes

ALGORITHMS = tuple(member.value for member in Algorithm)
QUANTIZERS = (Quantizer.THRESHOLD.value, Quantizer.PALETTE.value, "bluenoise")
COLOR_SPACES = tuple(member.value for member in ColorSpace)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pilther",
        description="Apply a dithering filter to an input image.",
    )
    parser.add_argument(
        "--algorithm",
        choices=ALGORITHMS,
        default=Algorithm.ATKINSON.value,
        help="Diffusion kernel to apply (default: %(default)s)",
    )
    parser.add_argument(
        "--quantizer",
        choices=QUANTIZERS,
        default=Quantizer.THRESHOLD.value,
        help="Quantization strategy to apply (default: %(default)s)",
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
        choices=COLOR_SPACES,
        default=ColorSpace.RGB.value,
        help="Color space for palette extraction and matching (default: %(default)s).",
    )
    parser.add_argument("input", type=Path, help="Input image path")
    parser.add_argument("output", type=Path, help="Output image path")
    args = parser.parse_args()

    with Image.open(args.input) as img:
        if args.quantizer == "bluenoise":
            if args.palette_name is not None or args.extract_colors is not None:
                parser.error("--palette and --extract-colors are only valid for palette quantization.")
            out = bluenoise(img)
        else:
            quantizer = Quantizer(args.quantizer)
            if quantizer is Quantizer.THRESHOLD and (args.palette_name is not None or args.extract_colors is not None):
                parser.error("--palette and --extract-colors are only valid for palette quantization.")

            out = dither(
                img,
                algorithm=Algorithm(args.algorithm),
                quantizer=quantizer,
                palette_name=args.palette_name,
                extract_colors=args.extract_colors,
                palette_method=args.palette_method,
                color_space=ColorSpace(args.palette_space),
            )
    out.save(args.output)


if __name__ == "__main__":
    main()
