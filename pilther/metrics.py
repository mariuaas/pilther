"""Image quality metrics used by the showcase generator."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
from PIL import Image


def _as_rgb_array(image: Image.Image) -> NDArray[np.float32]:
    return np.asarray(image.convert("RGB"), dtype=np.float32)


def _as_gray_array(image: Image.Image) -> NDArray[np.float32]:
    return np.asarray(image.convert("L"), dtype=np.float32)


def _box_blur(array: NDArray[np.float32], radius: int = 3) -> NDArray[np.float32]:
    padded = np.pad(array, radius, mode="reflect")
    integral = np.pad(padded, ((1, 0), (1, 0)), mode="constant").cumsum(axis=0).cumsum(axis=1)
    window = (2 * radius) + 1
    total = (
        integral[window:, window:]
        - integral[:-window, window:]
        - integral[window:, :-window]
        + integral[:-window, :-window]
    )
    return total / float(window * window)


def mean_squared_error(reference: Image.Image, candidate: Image.Image) -> float:
    ref = _as_rgb_array(reference)
    cand = _as_rgb_array(candidate)
    return float(np.mean((ref - cand) ** 2))


def peak_signal_to_noise_ratio(reference: Image.Image, candidate: Image.Image) -> float:
    mse = mean_squared_error(reference, candidate)
    if mse == 0.0:
        return math.inf
    return float(20.0 * math.log10(255.0) - 10.0 * math.log10(mse))


def structural_similarity(reference: Image.Image, candidate: Image.Image) -> float:
    ref = _as_gray_array(reference)
    cand = _as_gray_array(candidate)

    mu_ref = _box_blur(ref)
    mu_cand = _box_blur(cand)

    sigma_ref_sq = _box_blur(ref * ref) - (mu_ref ** 2)
    sigma_cand_sq = _box_blur(cand * cand) - (mu_cand ** 2)
    sigma_ref_cand = _box_blur(ref * cand) - (mu_ref * mu_cand)

    sigma_ref_sq = np.maximum(sigma_ref_sq, 0.0)
    sigma_cand_sq = np.maximum(sigma_cand_sq, 0.0)

    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    numerator = (2.0 * mu_ref * mu_cand + c1) * (2.0 * sigma_ref_cand + c2)
    denominator = (mu_ref ** 2 + mu_cand ** 2 + c1) * (sigma_ref_sq + sigma_cand_sq + c2)
    ssim_map = numerator / np.maximum(denominator, 1e-8)
    return float(np.clip(np.mean(ssim_map), 0.0, 1.0))


def metric_summary(reference: Image.Image, candidate: Image.Image) -> dict[str, float]:
    return {
        "mse": mean_squared_error(reference, candidate),
        "psnr": peak_signal_to_noise_ratio(reference, candidate),
        "ssim": structural_similarity(reference, candidate),
    }