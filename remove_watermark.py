#!/usr/bin/env python3
"""
Watermark Remover - Removes NCERT watermarks from extracted figures.
Handles diagonal "not to be republished" style watermarks.
"""

import cv2
import numpy as np
from pathlib import Path


def remove_watermark(image_path: Path, output_path: Path = None) -> bool:
    """
    Remove watermark from an image.
    NCERT watermarks are typically light blue/cyan diagonal text.
    """
    if output_path is None:
        output_path = image_path

    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        return False

    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # NCERT watermark is typically light cyan/blue
    # HSV range for light cyan: H=80-100, S=20-100, V=180-255
    lower_cyan = np.array([80, 15, 150])
    upper_cyan = np.array([110, 80, 255])

    # Create mask for watermark color
    mask = cv2.inRange(hsv, lower_cyan, upper_cyan)

    # Dilate mask slightly to catch edges
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Inpaint - replace watermark with surrounding colors
    result = cv2.inpaint(img, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # Save result
    cv2.imwrite(str(output_path), result)
    return True


def remove_watermark_simple(image_path: Path, output_path: Path = None) -> bool:
    """
    Remove NCERT watermarks - targets faint cyan diagonal text.
    NCERT watermark: H=100-110, S=3-10, V=100-150 (very faint cyan)
    """
    if output_path is None:
        output_path = image_path

    img = cv2.imread(str(image_path))
    if img is None:
        return False

    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Target the faint cyan watermark (H=100-110, S=3-10)
    cyan_mask = ((h >= 100) & (h <= 115) & (s >= 2) & (s <= 15)).astype(np.uint8) * 255

    # Also catch slightly more saturated cyan
    cyan_mask2 = ((h >= 85) & (h <= 115) & (s > 15) & (s < 80)).astype(np.uint8) * 255
    cyan_mask = cv2.bitwise_or(cyan_mask, cyan_mask2)

    # Dilate mask to catch watermark edges
    kernel = np.ones((2, 2), np.uint8)
    cyan_mask = cv2.dilate(cyan_mask, kernel, iterations=1)

    # For faint watermark: reduce saturation to 0 and boost brightness
    s_float = s.astype(np.float32)
    s_float[cyan_mask > 0] = 0  # Remove all saturation

    v_float = v.astype(np.float32)
    # Boost brightness to match surrounding white/light areas
    v_float[cyan_mask > 0] = np.minimum(v_float[cyan_mask > 0] + 50, 255)

    s = s_float.astype(np.uint8)
    v = v_float.astype(np.uint8)

    # Merge back
    hsv_clean = cv2.merge([h, s, v])
    result = cv2.cvtColor(hsv_clean, cv2.COLOR_HSV2BGR)

    cv2.imwrite(str(output_path), result)
    return True


def process_figures_folder(figures_dir: Path):
    """Remove watermarks from all figures in a folder."""
    if not figures_dir.exists():
        print(f"Folder not found: {figures_dir}")
        return

    count = 0
    for img_path in figures_dir.glob("*.png"):
        if remove_watermark_simple(img_path):
            count += 1

    for img_path in figures_dir.glob("*.jpg"):
        if remove_watermark_simple(img_path):
            count += 1

    for img_path in figures_dir.glob("*.jpeg"):
        if remove_watermark_simple(img_path):
            count += 1

    print(f"Processed {count} images in {figures_dir}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python remove_watermark.py <book_code>")
        print("Example: python remove_watermark.py kebo101")
        sys.exit(1)

    book_code = sys.argv[1]
    figures_dir = Path("extracted") / book_code / "figures"
    process_figures_folder(figures_dir)
