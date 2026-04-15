from __future__ import annotations

import math

import numpy as np
from PIL import Image

from pilther.metrics import mean_squared_error, metric_summary, peak_signal_to_noise_ratio, structural_similarity


def test_metrics_identical_images_have_zero_mse_and_infinite_psnr() -> None:
    image = Image.fromarray(np.full((8, 8, 3), 128, dtype=np.uint8), mode="RGB")

    assert mean_squared_error(image, image) == 0.0
    assert math.isinf(peak_signal_to_noise_ratio(image, image))
    assert structural_similarity(image, image) == 1.0


def test_metrics_detect_difference() -> None:
    reference = Image.fromarray(np.zeros((8, 8, 3), dtype=np.uint8), mode="RGB")
    candidate = Image.fromarray(np.full((8, 8, 3), 255, dtype=np.uint8), mode="RGB")

    mse = mean_squared_error(reference, candidate)
    psnr = peak_signal_to_noise_ratio(reference, candidate)
    ssim = structural_similarity(reference, candidate)

    assert mse == 65025.0
    assert psnr == 0.0
    assert 0.0 <= ssim < 0.01


def test_metric_summary_returns_all_fields() -> None:
    reference = Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8), mode="RGB")
    candidate = Image.fromarray(np.full((4, 4, 3), 64, dtype=np.uint8), mode="RGB")

    summary = metric_summary(reference, candidate)

    assert set(summary) == {"mse", "psnr", "ssim"}
    assert summary["mse"] > 0.0
    assert summary["psnr"] > 0.0
    assert 0.0 <= summary["ssim"] <= 1.0