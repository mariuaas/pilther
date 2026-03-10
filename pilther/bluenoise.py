from __future__ import annotations

from PIL import Image
import numpy as np
from numpy.typing import NDArray


def _colored_noise_2d(
    height: int,
    width: int,
    alpha: float = 0.0,
    seed: int | None = None,
) -> NDArray[np.float32]:
    """
    Generate zero-mean, unit-std 2D colored noise.

    PSD scales approximately as |f|^alpha:
        alpha =  0  -> white
        alpha =  1  -> blue
        alpha = -1  -> pink
        alpha = -2  -> brown/red
    """
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((height, width))

    fy = np.fft.fftfreq(height)
    fx = np.fft.fftfreq(width)
    fx, fy = np.meshgrid(fx, fy, indexing="xy")
    r = np.sqrt(fx**2 + fy**2)
    r[0, 0] = 1.0

    H = r ** (alpha / 2.0)

    noise_f = np.fft.fft2(white) * H
    noise = np.fft.ifft2(noise_f).real

    noise -= noise.mean()
    noise /= max(noise.std(), 1e-8)
    return noise.astype(np.float32)


def _add_colored_noise_uint8(
    image: NDArray[np.uint8],
    alpha: float = 0.0,
    strength: float = 32.0,
    per_channel: bool = False,
    seed: int | None = None,
) -> NDArray[np.uint8]:
    """
    Add colored noise to a uint8 image.

    Parameters
    ----------
    image
        HxW or HxWxC uint8 image.
    alpha
        Spectral exponent of the noise PSD.
    strength
        Noise std in pixel values.
    per_channel
        If True, generate independent noise per channel.
        If False, share one noise field across channels.
    """
    if image.dtype != np.uint8:
        raise ValueError("Expected uint8 image")

    rng = np.random.default_rng(seed)
    out = image.astype(np.float32)

    if image.ndim == 2:
        h,w = image.shape
        noise = _colored_noise_2d(h, w, alpha=alpha, seed=seed)
        out = out + strength * noise

    elif image.ndim == 3:
        h, w, c = image.shape

        if per_channel:
            for k in range(c):
                noise = _colored_noise_2d(
                    h, w, alpha=alpha,
                    seed=int(rng.integers(0, 2**32 - 1))
                )
                out[..., k] += strength * noise
        else:
            noise = _colored_noise_2d(h, w, alpha=alpha, seed=seed)
            out += strength * noise[..., None]

    else:
        raise ValueError("Expected image shape HxW or HxWxC")

    return np.clip(np.rint(out), 0, 255)


def bluenoise(
    image: Image.Image,
    strength: float = 48.0,
    seed: int | None = None,
) -> Image.Image:
    """
    Add blue noise to a PIL image and return a dithered binary result.
    
    Parameters
    ----------
    image
        Input image in any mode (converted to grayscale internally).
    strength
        Noise strength in pixel values. Higher values produce more dithering.
    seed
        Random seed for noise generation.

    Returns
    -------
    Image.Image
        1-bit dithered image (mode "1", values 0 or 1)
    """
    gray = image.convert("L")
    arr = np.asarray(gray, dtype=np.float32)
    noise = _colored_noise_2d(arr.shape[0], arr.shape[1], alpha=1.0, seed=seed)
    binary = (arr + strength * noise) >= 128.0
    out = (binary.astype(np.uint8) * 255)
    return Image.fromarray(out, mode="L").convert("1")