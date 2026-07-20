"""Post-processing modules for extracted content."""

from .watermark import remove_watermark_from_image, process_figures_folder
from .cleaner import clean_marker_output

__all__ = ["remove_watermark_from_image", "process_figures_folder", "clean_marker_output"]
