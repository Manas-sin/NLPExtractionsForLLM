"""PDF utilities using PyMuPDF."""

import re
from pathlib import Path
from typing import Iterator

import fitz

from .text import clean_text


BOOK_PAGE_RE = re.compile(r"^(\d{1,3})\n")


def extract_page_text(page: fitz.Page) -> tuple[str, int | None]:
    """Extract cleaned text from a page. Returns (text, book_page_number)."""
    raw = page.get_text("text", sort=False)
    text = clean_text(raw)

    match = BOOK_PAGE_RE.match(text)
    book_page = int(match.group(1)) if match else None

    return text, book_page


def render_page(page: fitz.Page, scale: float = 2.0) -> fitz.Pixmap:
    """Render a page to a pixmap at given scale."""
    matrix = fitz.Matrix(scale, scale)
    return page.get_pixmap(matrix=matrix)


def get_page_images(pdf_path: Path) -> Iterator[tuple[int, fitz.Page]]:
    """Iterate over pages in a PDF."""
    doc = fitz.open(pdf_path)
    try:
        for page_num, page in enumerate(doc, start=1):
            yield page_num, page
    finally:
        doc.close()


def find_figure_captions(page: fitz.Page) -> list[dict]:
    """Find all figure captions on a page with their positions."""
    FIG_CAPTION_RE = re.compile(r"(Fig\.?|Figure)\s*(\d+\.?\d*)\s*[:\.\s]*(.+)", re.IGNORECASE)

    captions = []
    blocks = page.get_text("dict", sort=True)["blocks"]

    for block in blocks:
        if block["type"] != 0:
            continue

        block_text = ""
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span.get("text", "") + " "

        match = FIG_CAPTION_RE.search(block_text.strip())
        if match:
            bbox = block["bbox"]
            captions.append({
                "y": bbox[1],
                "x0": bbox[0],
                "x1": bbox[2],
                "fig_num": match.group(2),
                "caption": match.group(3).strip()
            })

    return captions
