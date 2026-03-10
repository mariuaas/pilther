from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from . import atkinson


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pilther",
        description="Apply Atkinson dithering to an input image.",
    )
    parser.add_argument("input", type=Path, help="Input image path")
    parser.add_argument("output", type=Path, help="Output image path")
    args = parser.parse_args()

    img = Image.open(args.input)
    out = atkinson(img)
    out.save(args.output)


if __name__ == "__main__":
    main()
