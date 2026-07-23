"""Extraction modules for different extraction strategies."""

from .base import BaseExtractor
from .pdf_extractor import PDFExtractor
from .vision_extractor import VisionExtractor
from .ocr_extractor import OCRExtractor
from .physics_structurer import PhysicsStructurer, structure_physics_chapter
from .ncert_structurer import NCERTStructurer, structure_ncert_chapter
from .unified_structurer import UnifiedStructurer, structure_chapter
from .docling_structurer import DoclingStructurer, structure_chapter_docling
from .docling_extractor import DoclingExtractor
from .extraction_comparator import ExtractionComparator, compare_extraction

__all__ = [
    "BaseExtractor",
    "PDFExtractor",
    "VisionExtractor",
    "OCRExtractor",
    "PhysicsStructurer",
    "structure_physics_chapter",
    "NCERTStructurer",
    "structure_ncert_chapter",
    "UnifiedStructurer",
    "structure_chapter",
    "DoclingStructurer",
    "structure_chapter_docling",
    "DoclingExtractor",
    "ExtractionComparator",
    "compare_extraction",
]
