"""Extract figure images from NCERT PDF pages by cropping around captions."""

import re
from pathlib import Path

import fitz  # PyMuPDF

from .page_renderer import remove_watermarks

CAPTION_RE = re.compile(r"Fig(?:ure)?\.?\s*(\d+\.\d+)", re.IGNORECASE)

_MAX_ABOVE = 340       # max points a figure rises above its caption
_GROW_PAD = 6          # horizontal slack when testing overlap during region grow
_GAP_BRIDGE = 26       # vertical gap (points) the grow may jump between figure parts
_FINAL_PAD = 8         # padding around the final crop
_RENDER_DPI = 200


def _caption_rects(page):
    """Return list of (figure_number, caption_rect) for real figure captions.

    Only lines that START with 'Fig' are captions; a 'Fig. 1.1' appearing mid
    sentence is an inline reference and is ignored.
    """
    found = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"]).strip()
            # A real caption is "Fig. X.Y <description>": the number is followed by
            # whitespace/colon/end. "Fig. 1.1(a) and ..." is an inline reference.
            m = re.match(r"^Fig(?:ure)?\.?\s*(\d+\.\d+)(?=[\s:]|$)", text, re.IGNORECASE)
            if m:
                found.append((m.group(1), fitz.Rect(line["bbox"])))
    return found


_PROSE_MIN_WIDTH = 190   # points; body-text lines fill the column, labels don't
_PROSE_MIN_WORDS = 6


def _text_line_rects(page):
    """Return rects of body-text (prose) lines used as an upper boundary for figures.

    Only wide, multi-word lines count as prose. Short centered figure labels such as
    'Solution containing salt of Zinc' are deliberately excluded so they stay part of
    the figure crop.
    """
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            txt = "".join(s["text"] for s in line["spans"]).strip()
            rect = fitz.Rect(line["bbox"])
            if len(txt.split()) >= _PROSE_MIN_WORDS and rect.width >= _PROSE_MIN_WIDTH:
                lines.append(rect)
    return lines


def _column_band(page, caption_rect):
    """Return the (x0, x1) column the caption belongs to: left, right, or full width."""
    pw = page.rect.width
    mid = page.rect.x0 + pw / 2
    cap_mid = (caption_rect.x0 + caption_rect.x1) / 2
    # Caption clearly in one half -> restrict to that half; else span full width.
    if caption_rect.x1 < mid + 40:
        return page.rect.x0 + 20, mid + 15
    if caption_rect.x0 > mid - 40:
        return mid - 15, page.rect.x1 - 20
    return page.rect.x0 + 20, page.rect.x1 - 20


def _figure_bbox(page, caption_rect):
    """Compute a figure's bounding box: all graphical elements in the caption's
    column between the prose paragraph above and the caption itself.

    This handles figures whose parts are visually disconnected (apparatus + labels)
    which a touch-based region grow would miss.
    """
    col_x0, col_x1 = _column_band(page, caption_rect)

    graphics = [fitz.Rect(d["rect"]) for d in page.get_drawings()]
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if abs(r) < abs(page.rect) * 0.85:
                graphics.append(fitz.Rect(r))

    # Upper bound: bottom of the nearest wide prose line above the caption whose
    # centre lies in this column (so left-column text can't clamp a right-column figure).
    top_limit = caption_rect.y0 - _MAX_ABOVE
    for t in _text_line_rects(page):
        if t.y1 <= caption_rect.y0 - 4 and t.y1 > top_limit:
            tcx = (t.x0 + t.x1) / 2
            if col_x0 <= tcx <= col_x1:
                top_limit = t.y1
    top_limit = max(page.rect.y0, top_limit)

    # Union every graphic in the column, in the vertical band above the caption.
    # Skip page-spanning rules (header/footer lines) that are wider than the column.
    band_width = col_x1 - col_x0
    max_graphic_width = min(band_width * 1.15, page.rect.width * 0.8)
    box = fitz.Rect(caption_rect)
    for r in graphics:
        if r.y1 > caption_rect.y0 + 5 or r.y0 < top_limit:
            continue
        if r.width > max_graphic_width:
            continue
        cx = (r.x0 + r.x1) / 2
        if cx < col_x0 or cx > col_x1:
            continue
        box |= r

    box.x0 = max(0, box.x0 - _FINAL_PAD)
    box.y0 = max(0, box.y0 - _FINAL_PAD)
    box.x1 = min(page.rect.x1, box.x1 + _FINAL_PAD)
    box.y1 = min(page.rect.y1, box.y1 + _FINAL_PAD)
    return box


def extract_figures(pdf_path: Path, output_dir: Path, dpi: int = _RENDER_DPI) -> dict:
    """Crop each detected figure into an image. Returns {figure_number: filename}."""
    output_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    result = {}
    with fitz.open(pdf_path) as pdf:
        remove_watermarks(pdf)
        for page in pdf:
            for fig_num, caption_rect in _caption_rects(page):
                if fig_num in result:
                    continue  # first occurrence wins
                bbox = _figure_bbox(page, caption_rect)
                # Skip degenerate crops (caption with no figure above it)
                if bbox.height < 25 or bbox.width < 25:
                    continue
                pix = page.get_pixmap(matrix=matrix, clip=bbox)
                fname = f"fig_{fig_num.replace('.', '_')}.png"
                pix.save(str(output_dir / fname))
                result[fig_num] = fname

    return result


def extract_book_figures(book_code: str, pdf_path: Path, base_dir: Path = None) -> dict:
    """Extract figures for a book into its extraction dir under /figures."""
    base_dir = base_dir or Path("data/extracted") / book_code
    figures_dir = base_dir / "figures"
    return extract_figures(pdf_path, figures_dir)


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "keph101"
    pdf = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"/Users/manassingh/Downloads/keph1dd/{code}.pdf")
    figs = extract_book_figures(code, pdf)
    print(f"Extracted {len(figs)} figures for {code}: {list(figs)}")
