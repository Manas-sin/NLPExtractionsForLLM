"""Render PDF pages to images for the NCERT preview replica."""

from pathlib import Path

import fitz  # PyMuPDF

# A form XObject covering at least this fraction of an A4 page is treated as a
# full-page overlay (watermark) when it also carries an /OC optional-content key.
_A4_AREA_PT = 595.2 * 841.92
_WATERMARK_AREA_FRACTION = 0.5


def remove_watermarks(pdf: fitz.Document) -> int:
    """Blank full-page optional-content overlays (NCERT 'not to be republished').

    NCERT PDFs draw the diagonal watermark as a full-page Form XObject that has an
    /OC (optional content) key. Real figures never carry /OC, so blanking these
    forms removes the watermark without touching any real content.

    Returns the number of watermark forms neutralised.
    """
    removed = 0
    for xref in range(1, pdf.xref_length()):
        try:
            if pdf.xref_get_key(xref, "Subtype")[1] != "/Form":
                continue
            if pdf.xref_get_key(xref, "OC")[0] == "null":
                continue
            bbox = pdf.xref_get_key(xref, "BBox")
            if bbox[0] != "array":
                continue
            nums = [float(n) for n in bbox[1].strip("[]").split()]
            if len(nums) != 4:
                continue
            area = abs((nums[2] - nums[0]) * (nums[3] - nums[1]))
            if area >= _A4_AREA_PT * _WATERMARK_AREA_FRACTION:
                pdf.update_stream(xref, b" ")
                removed += 1
        except (ValueError, IndexError, RuntimeError):
            continue
    return removed


def render_pdf_pages(pdf_path: Path, output_dir: Path, dpi: int = 130) -> list:
    """Render each PDF page to a PNG image, with watermarks removed.

    Returns a list of relative image filenames in page order.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    filenames = []
    with fitz.open(pdf_path) as pdf:
        remove_watermarks(pdf)
        for i, page in enumerate(pdf):
            pix = page.get_pixmap(matrix=matrix)
            fname = f"page_{i + 1:03d}.png"
            pix.save(str(output_dir / fname))
            filenames.append(fname)

    return filenames


def render_book(book_code: str, pdf_path: Path, base_dir: Path = None, dpi: int = 130) -> list:
    """Render a book's pages into its extraction directory under /pages."""
    base_dir = base_dir or Path("data/extracted") / book_code
    pages_dir = base_dir / "pages"
    return render_pdf_pages(pdf_path, pages_dir, dpi=dpi)


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "lech101"
    pdf = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"/Users/manassingh/Downloads/lech1dd/{code}.pdf")
    pages = render_book(code, pdf)
    print(f"Rendered {len(pages)} pages for {code}")
