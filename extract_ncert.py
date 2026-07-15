#!/usr/bin/env python3
"""
NCERT PDF Extractor - extracts text, page renders, and figures with captions.

Usage:
    python extract_ncert.py <pdf_path>

Output:
    extracted/<pdf_stem>/
        content.md          - markdown
        pages.json          - per-page text
        pages/              - text files
        renders/            - full page images
        figures/            - cropped figures with captions
        figures.json        - figure metadata
"""

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF


def clean_text(text: str) -> str:
    text = text.replace("­", "")
    text = re.sub(r"^\s*Reprint\s+\d{4}-\d{2}\s*$", "", text, flags=re.MULTILINE)
    # Remove NCERT watermark text
    text = re.sub(r"not\s+to\s+be\s+republished", "", text, flags=re.IGNORECASE)
    text = re.sub(r"©\s*NCERT", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = text.split('\n')
    deduped = []
    prev = None
    for line in lines:
        if line.strip() != prev:
            deduped.append(line)
            prev = line.strip()
    return '\n'.join(deduped).strip()


BOOK_PAGE_RE = re.compile(r"^(\d{1,3})\n")
FIG_CAPTION_RE = re.compile(r"(Fig\.?|Figure)\s*(\d+\.?\d*)\s*[:\.\s]*(.+)", re.IGNORECASE)


def extract_figures(page, page_num, figures_dir, doc, scale=3):
    """Extract figures by rendering page regions around captions."""
    figures = []
    page_width = page.rect.width
    page_height = page.rect.height

    # Find all figure captions
    captions = find_all_captions(page)

    # Also check for non-background images that might be actual figures
    image_info = page.get_image_info()
    content_images = []
    for img in image_info:
        bbox = img["bbox"]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        # Skip full-page backgrounds and tiny images
        if width < 80 or height < 80:
            continue
        if width > page_width * 0.9 and height > page_height * 0.9:
            continue
        content_images.append(bbox)

    # Extract figures based on captions
    for cap in captions:
        fig_num = cap["fig_num"]
        caption_text = cap["caption"]
        caption_y = cap["y"]
        caption_x0 = cap["x0"]
        caption_x1 = cap["x1"]

        # Look for image regions near this caption
        best_region = None
        for img_bbox in content_images:
            img_bottom = img_bbox[3]
            # Image should be above caption (within 100px)
            if 0 < caption_y - img_bottom < 100:
                best_region = img_bbox
                break
            # Or caption might be inside/below the image region
            if img_bbox[1] < caption_y < img_bbox[3] + 50:
                best_region = img_bbox
                break

        if best_region:
            # Render the image region
            x0, y0, x1, y1 = best_region
            # Add some padding
            x0 = max(0, x0 - 10)
            y0 = max(0, y0 - 10)
            x1 = min(page_width, x1 + 10)
            y1 = min(page_height, y1 + 10)
        else:
            # Fallback: crop area above caption
            fig_height = estimate_figure_height(page, caption_y, caption_x0, caption_x1)
            x0 = max(0, caption_x0 - 20)
            x1 = min(page_width, caption_x1 + 20)
            y0 = max(0, caption_y - fig_height)
            y1 = caption_y - 5

        if y1 - y0 < 30 or x1 - x0 < 30:
            continue

        clip = fitz.Rect(x0, y0, x1, y1)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=clip)

        fig_name = f"fig{fig_num.replace('.', '_')}.png"
        pix.save(figures_dir / fig_name)

        figures.append({
            "page": page_num,
            "figure": fig_num,
            "caption": caption_text,
            "image": fig_name
        })

    return figures


def estimate_figure_height(page, caption_y, caption_x0, caption_x1):
    """Estimate figure height by finding where continuous graphics/whitespace starts."""
    page_width = page.rect.width

    # Get drawings (vector graphics) on the page
    drawings = page.get_drawings()

    # Find drawings that are above the caption and horizontally aligned
    drawing_tops = []
    for d in drawings:
        if "rect" in d:
            r = d["rect"]
            # Check if drawing is above caption and overlaps horizontally
            if r.y1 < caption_y and r.y0 > 20:
                # Check horizontal overlap with caption area
                if r.x0 < caption_x1 + 50 and r.x1 > caption_x0 - 50:
                    drawing_tops.append(r.y0)

    if drawing_tops:
        # Figure starts at topmost drawing
        top_y = min(drawing_tops)
        height = caption_y - top_y + 10
        return max(80, min(height, 500))

    # Fallback: look for text blocks
    blocks = page.get_text("dict", sort=True)["blocks"]
    text_blocks_above = []

    for block in blocks:
        if block["type"] == 0:
            bbox = block["bbox"]
            # Text block that's above caption and overlaps horizontally
            if bbox[3] < caption_y - 20:
                if bbox[0] < caption_x1 and bbox[2] > caption_x0:
                    text_blocks_above.append(bbox[3])

    if text_blocks_above:
        last_text_y = max(text_blocks_above)
        height = caption_y - last_text_y - 15
        return max(80, min(height, 400))

    return 250  # Default height for diagrams


def find_all_captions(page):
    """Find all figure captions on a page with their positions."""
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


def extract_pdf(pdf_path: Path):
    doc = fitz.open(pdf_path)
    out_dir = Path("extracted") / pdf_path.stem
    pages_dir = out_dir / "pages"
    renders_dir = out_dir / "renders"
    figures_dir = out_dir / "figures"

    for d in [pages_dir, renders_dir, figures_dir]:
        d.mkdir(parents=True, exist_ok=True)

    pages_data = []
    all_figures = []
    all_text = []

    for page_num, page in enumerate(doc, start=1):
        # Extract text
        raw = page.get_text("text", sort=False)
        text = clean_text(raw)

        m = BOOK_PAGE_RE.match(text)
        book_page = int(m.group(1)) if m else None

        pages_data.append({
            "page": page_num,
            "book_page": book_page,
            "char_count": len(text),
            "text": text
        })

        (pages_dir / f"page_{page_num:03d}.txt").write_text(text, encoding="utf-8")

        # Build markdown
        if book_page:
            all_text.append(f"\n---\n## Page {book_page}\n")
        else:
            all_text.append(f"\n---\n## Page {page_num} (unnumbered)\n")
        all_text.append(text)

        # Render full page
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        pix.save(renders_dir / f"page_{page_num:03d}.png")

        # Extract figures with captions
        figures = extract_figures(page, page_num, figures_dir, doc)
        all_figures.extend(figures)

    doc.close()

    # Save outputs
    (out_dir / "content.md").write_text("\n".join(all_text), encoding="utf-8")
    (out_dir / "pages.json").write_text(
        json.dumps(pages_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "figures.json").write_text(
        json.dumps(all_figures, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    total_chars = sum(p["char_count"] for p in pages_data)
    print(f"Extracted: {pdf_path.name}")
    print(f"  Pages: {len(pages_data)}")
    print(f"  Chars: {total_chars:,}")
    print(f"  Figures: {len(all_figures)}")
    print(f"  Output: {out_dir}/")

    return pages_data, all_figures


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_ncert.py <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    book_code = pdf_path.stem
    out_dir = Path("extracted") / book_code

    # Step 1: Extract raw pages
    print("=" * 50)
    print("STEP 1: Extracting PDF pages...")
    print("=" * 50)
    extract_pdf(pdf_path)

    # Step 2: Generate structured.json
    print("\n" + "=" * 50)
    print("STEP 2: Generating structured.json with LaTeX...")
    print("=" * 50)
    try:
        from structure_ncert import structure_book
        structure_book(book_code)
    except Exception as e:
        print(f"Error: {e}")
        print("Run manually: python structure_ncert.py " + book_code)

    # Step 3: Remove watermarks from figures
    print("\n" + "=" * 50)
    print("STEP 3: Removing watermarks from figures...")
    print("=" * 50)
    try:
        from remove_watermark import process_figures_folder
        figures_dir = out_dir / "figures"
        process_figures_folder(figures_dir)
    except Exception as e:
        print(f"Watermark removal skipped: {e}")

    # Step 4: Recreate diagrams
    print("\n" + "=" * 50)
    print("STEP 4: Recreating clean diagrams...")
    print("=" * 50)
    try:
        from recreate_diagram import recreate_diagrams
        recreate_diagrams(book_code)
    except Exception as e:
        print(f"Error: {e}")
        print("Run manually: python recreate_diagram.py " + book_code)

    # Step 5: Re-run structure to add diagram paths
    print("\n" + "=" * 50)
    print("STEP 5: Updating structured.json with diagram paths...")
    print("=" * 50)
    try:
        from structure_ncert import structure_book
        structure_book(book_code)
    except Exception as e:
        print(f"Error: {e}")

    # Final summary
    print("\n" + "=" * 50)
    print("EXTRACTION COMPLETE!")
    print("=" * 50)
    print(f"\nOutput directory: {out_dir}/")
    print("\nFiles created:")

    for f in sorted(out_dir.iterdir()):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {f.name} ({size:,} bytes)")
        elif f.is_dir():
            count = len(list(f.iterdir()))
            print(f"  {f.name}/ ({count} files)")

    # Show final output location
    final_file = out_dir / "final_output.json"
    structured_file = out_dir / "structured.json"

    if final_file.exists():
        print(f"\n*** FINAL OUTPUT: {final_file} ***")
        print("    (Contains: pages + structured data + diagram paths)")
    elif structured_file.exists():
        print(f"\n*** OUTPUT: {structured_file} ***")
    else:
        print("\nWARNING: Output files were not created!")
