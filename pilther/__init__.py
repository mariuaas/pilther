"""pilther: fast Pillow dithering filters backed by Zig."""

from .atkinson import atkinson
from .bluenoise import bluenoise
from .burkes import burkes
from .sierra2 import sierra2
from .sierra3 import sierra3
from .stucki import stucki

__all__ = ["atkinson", "bluenoise", "burkes", "sierra2", "sierra3", "stucki"]
