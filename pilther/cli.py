from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from PIL import Image

from .atkinson import atkinson
from .bluenoise import bluenoise
from .burkes import burkes
from .sierra2 import sierra2
from .sierra3 import sierra3
from .stucki import stucki

FilterFunc = Callable[[Image.Image], Image.Image]

FILTERS: dict[str, FilterFunc] = {
    "atkinson": atkinson,
    "bluenoise": bluenoise,
    "burkes": burkes,
    "sierra2": sierra2,
    "sierra3": sierra3,
    "stucki": stucki,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pilther",
        description="Apply a dithering filter to an input image.",
    )
    parser.add_argument(
        "--filter",
        dest="filter_name",
        choices=tuple(FILTERS),
        default="atkinson",
        help="Dithering filter to apply (default: %(default)s)",
    )
    parser.add_argument("input", type=Path, help="Input image path")
    parser.add_argument("output", type=Path, help="Output image path")
    args = parser.parse_args()

    with Image.open(args.input) as img:
        out = FILTERS[args.filter_name](img)
    out.save(args.output)


if __name__ == "__main__":
    main()
