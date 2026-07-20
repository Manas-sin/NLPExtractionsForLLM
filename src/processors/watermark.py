"""Image watermark removal for NCERT figures."""

from pathlib import Path

import cv2
import numpy as np


def remove_watermark_from_image(image_path: Path, output_path: Path = None) -> bool:
    """
    Remove NCERT watermarks from an image.
    Targets faint cyan diagonal text watermarks.
    """
    if output_path is None:
        output_path = image_path

    img = cv2.imread(str(image_path))
    if img is None:
        return False

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    cyan_mask = ((h >= 100) & (h <= 115) & (s >= 2) & (s <= 15)).astype(np.uint8) * 255
    cyan_mask2 = ((h >= 85) & (h <= 115) & (s > 15) & (s < 80)).astype(np.uint8) * 255
    cyan_mask = cv2.bitwise_or(cyan_mask, cyan_mask2)

    kernel = np.ones((2, 2), np.uint8)
    cyan_mask = cv2.dilate(cyan_mask, kernel, iterations=1)

    s_float = s.astype(np.float32)
    s_float[cyan_mask > 0] = 0

    v_float = v.astype(np.float32)
    v_float[cyan_mask > 0] = np.minimum(v_float[cyan_mask > 0] + 50, 255)

    s = s_float.astype(np.uint8)
    v = v_float.astype(np.uint8)

    hsv_clean = cv2.merge([h, s, v])
    result = cv2.cvtColor(hsv_clean, cv2.COLOR_HSV2BGR)

    cv2.imwrite(str(output_path), result)
    return True


def process_figures_folder(figures_dir: Path) -> int:
    """Remove watermarks from all figures in a folder. Returns count processed."""
    if not figures_dir.exists():
        return 0

    count = 0
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        for img_path in figures_dir.glob(pattern):
            if remove_watermark_from_image(img_path):
                count += 1

    return count
