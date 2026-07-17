#!/usr/bin/env python3
"""
Physics Class 12 NCERT Extractor
Separate pipeline from Chemistry - outputs to extracted_physics/

Usage:
    python extract_physics.py <book_code>           # Single chapter
    python extract_physics.py all                   # All chapters
    python extract_physics.py keph101 --vision      # With Mistral vision

Output:
    extracted_physics/<book_code>/
        content.md          - Marker extraction (raw)
        pages.json          - Per-page text
        renders/            - Full page images
        figures/            - Cropped figures
        figures.json        - Figure metadata
        vision_page_*.md    - Vision-extracted pages
        chapter_complete.md - Merged clean output
        structured.json     - Parsed structure
"""

import base64
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

import fitz  # PyMuPDF
from dotenv import load_dotenv

load_dotenv()

# Physics PDFs location - use clean versions (watermarks removed at PDF level)
PHYSICS_PDF_DIR = Path("/Users/manassingh/Downloads/keph1dd 2/clean")
OUTPUT_DIR = Path("extracted_physics")

# All physics chapters
PHYSICS_CHAPTERS = ["keph101", "keph102", "keph103", "keph104", "keph105", "keph106", "keph107"]


def clean_text(text: str) -> str:
    """Clean extracted text, remove watermarks."""
    text = text.replace("­", "")
    # Remove NCERT watermarks
    text = re.sub(r"not\s+to\s+be\s+republished", "", text, flags=re.IGNORECASE)
    text = re.sub(r"©\s*NCERT", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*Reprint\s+\d{4}-\d{2}\s*$", "", text, flags=re.MULTILINE)
    # Clean whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Dedupe consecutive identical lines
    lines = text.split('\n')
    deduped = []
    prev = None
    for line in lines:
        if line.strip() != prev:
            deduped.append(line)
            prev = line.strip()
    return '\n'.join(deduped).strip()


FIG_CAPTION_RE = re.compile(r"(Fig\.?|Figure)\s*(\d+\.?\d*)\s*[:\.\s]*(.+)", re.IGNORECASE)


def find_all_captions(page):
    """Find figure captions in page."""
    captions = []
    blocks = page.get_text("dict", sort=True)["blocks"]

    for block in blocks:
        if block.get("type") != 0:
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


def remove_watermark(img_path: Path) -> None:
    """Remove NCERT watermark from figure image.

    The watermark is light gray diagonal text ('not to be republished').
    We detect it by finding pixels that are:
    1. Light (R,G,B all > 180)
    2. Grayish (R,G,B values within 25 of each other)
    Then convert them to pure white.
    """
    img = Image.open(img_path).convert('RGB')
    img_array = np.array(img)

    r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]

    # Detect light grayish pixels (watermark signature)
    is_light = (r > 180) & (g > 180) & (b > 180)
    is_grayish = (
        (np.abs(r.astype(int) - g.astype(int)) < 25) &
        (np.abs(g.astype(int) - b.astype(int)) < 25) &
        (np.abs(r.astype(int) - b.astype(int)) < 25)
    )
    is_watermark = is_light & is_grayish

    # Convert watermark to pure white
    img_array[is_watermark] = [255, 255, 255]

    # Save cleaned image
    cleaned_img = Image.fromarray(img_array)
    cleaned_img.save(img_path)


def extract_figures(page, page_num, figures_dir, doc, scale=3):
    """Extract figures by rendering page regions around captions.

    Improved logic for two-column layouts:
    - If caption is in right half of page, figure is likely above it in right column
    - If caption is in left half, figure is above it in left column
    - Expand width to capture full figure, not just caption width
    - Remove NCERT watermark from extracted figures
    """
    figures = []
    page_width = page.rect.width
    page_height = page.rect.height

    captions = find_all_captions(page)

    for cap in captions:
        fig_num = cap["fig_num"]
        caption_text = cap["caption"]
        caption_y = cap["y"]
        caption_x_center = (cap["x0"] + cap["x1"]) / 2

        # Determine which column the caption is in
        is_right_column = caption_x_center > page_width / 2

        # Figure region estimation - look above the caption
        fig_height = min(250, caption_y - 20)
        margin = 30

        if is_right_column:
            # Right column: figure spans from center to right edge
            x0 = max(page_width * 0.45, cap["x0"] - margin)
            x1 = min(page_width - 10, cap["x1"] + margin)
        else:
            # Left column: figure spans from left edge to center
            x0 = max(10, cap["x0"] - margin)
            x1 = min(page_width * 0.55, cap["x1"] + margin)

        y0 = max(0, caption_y - fig_height)
        y1 = min(page_height, caption_y + 50)

        clip = fitz.Rect(x0, y0, x1, y1)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=clip)

        fig_filename = f"fig{fig_num.replace('.', '_')}.png"
        fig_path = figures_dir / fig_filename
        pix.save(fig_path)

        # Note: watermarks already removed at PDF level by remove_watermark_pdf.py

        figures.append({
            "page": page_num,
            "figure": fig_num,
            "caption": caption_text,
            "path": str(fig_path)
        })

    return figures


def extract_pdf(book_code: str):
    """Extract PDF to raw text, renders, and figures."""
    # Try clean version first, fall back to original
    pdf_path = PHYSICS_PDF_DIR / f"{book_code}_clean.pdf"
    if not pdf_path.exists():
        pdf_path = PHYSICS_PDF_DIR.parent / f"{book_code}.pdf"
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        return None

    doc = fitz.open(pdf_path)
    out_dir = OUTPUT_DIR / book_code
    pages_dir = out_dir / "pages"
    renders_dir = out_dir / "renders"
    figures_dir = out_dir / "figures"

    for d in [pages_dir, renders_dir, figures_dir]:
        d.mkdir(parents=True, exist_ok=True)

    pages_data = []
    all_figures = []
    all_text = []

    print(f"Extracting {book_code}: {len(doc)} pages")

    for page_num, page in enumerate(doc, start=1):
        # Extract text
        raw = page.get_text("text", sort=False)
        text = clean_text(raw)

        pages_data.append({
            "page": page_num,
            "char_count": len(text),
            "text": text
        })

        (pages_dir / f"page_{page_num:03d}.txt").write_text(text, encoding="utf-8")

        all_text.append(f"\n---\n## Page {page_num}\n")
        all_text.append(text)

        # Render full page
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        pix.save(renders_dir / f"page_{page_num:03d}.png")

        # Extract figures
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

    print(f"  ✅ Extracted: {len(pages_data)} pages, {len(all_figures)} figures")
    return {"pages": len(pages_data), "figures": len(all_figures)}


def extract_with_vision(book_code: str):
    """Extract using Mistral Pixtral vision API."""
    from mistralai.client import Mistral

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set in .env")
        return None

    client = Mistral(api_key=api_key)
    out_dir = OUTPUT_DIR / book_code
    renders_dir = out_dir / "renders"

    if not renders_dir.exists():
        print(f"No renders found. Running PDF extraction first...")
        extract_pdf(book_code)

    page_images = sorted(renders_dir.glob("page_*.png"))
    print(f"Vision extraction: {len(page_images)} pages")

    EXTRACTION_PROMPT = """You are extracting content from an NCERT Physics textbook page.
Analyze this page image and extract ALL content in structured markdown format.

Follow these rules:
1. **Reading Order**: Follow the natural reading order. Handle two-column layouts correctly.
2. **Section Headers**: Mark as ## 1.1 Title, ### 1.1.1 Subtitle
3. **Equations**: Convert ALL equations and formulas to LaTeX ($$...$$ for display, $...$ for inline)
4. **Physics Formulas**: Use proper LaTeX: F = ma → $F = ma$, E = mc² → $E = mc^2$
5. **Vectors**: Use \\vec{} notation: $\\vec{F}$, $\\vec{v}$
6. **Tables**: Convert to proper markdown tables with | headers |
7. **Examples**: Mark as ### Example X.Y followed by problem and **Solution**
8. **Figures**: Note as [Figure X.Y: caption description]
9. **Intext Questions**: Mark as ### Intext Questions with numbered list

Extract EVERYTHING - don't summarize or skip content. Preserve all numbers, values, and formulas exactly.

Return ONLY the structured markdown, no explanations."""

    total_tokens = 0
    extracted_pages = []

    for img_path in page_images:
        match = re.search(r'page_(\d+)', img_path.stem)
        page_num = int(match.group(1)) if match else 0

        vision_file = out_dir / f"vision_page_{page_num:03d}.md"
        if vision_file.exists() and vision_file.stat().st_size > 100:
            print(f"  Page {page_num}: already extracted, skipping")
            extracted_pages.append(page_num)
            continue

        print(f"  Page {page_num}: extracting...")

        with open(img_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        try:
            response = client.chat.complete(
                model="pixtral-12b-2409",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": f"data:image/png;base64,{image_data}"}
                    ]
                }]
            )

            markdown = response.choices[0].message.content
            total_tokens += response.usage.total_tokens if response.usage else 0

            vision_file.write_text(markdown, encoding="utf-8")
            extracted_pages.append(page_num)

        except Exception as e:
            print(f"    Error: {e}")

        time.sleep(0.5)

    # Merge vision pages
    merge_vision_pages(out_dir)

    print(f"  ✅ Vision extracted: {len(extracted_pages)} pages, {total_tokens:,} tokens")
    return {"pages": len(extracted_pages), "tokens": total_tokens}


def merge_vision_pages(out_dir: Path):
    """Merge vision_page_*.md into chapter_complete.md."""
    page_files = sorted(
        out_dir.glob("vision_page_*.md"),
        key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))
    )

    if not page_files:
        print("  No vision pages to merge")
        return

    merged = []
    for i, page_file in enumerate(page_files):
        content = page_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        if i == 0:
            merged.append(content)
            continue

        lines = content.split('\n')
        cleaned = []
        for line in lines:
            # Skip page numbers
            if re.match(r'^(Physics\s+)?\d+(\s+\w+)?$', line.strip()):
                continue
            if re.match(r'^\d+\s+(Physics|Electric|Current|Magnetic).*$', line.strip()):
                continue
            # Skip duplicate unit headers
            if line.startswith('# Unit') or line.startswith('# Chapter'):
                continue
            cleaned.append(line)

        content = '\n'.join(cleaned).strip()
        if content:
            merged.append('\n' + content)

    full_text = '\n'.join(merged)
    full_text = re.sub(r'\n{4,}', '\n\n\n', full_text)

    output_file = out_dir / "chapter_complete.md"
    output_file.write_text(full_text, encoding="utf-8")
    print(f"  Merged: {output_file.name} ({len(full_text):,} chars)")


def structure_chapter(book_code: str):
    """Run structure_ncert.py on the chapter."""
    import subprocess

    # Update structure_ncert.py to use physics output dir
    result = subprocess.run(
        ["python3", "structure_ncert.py", book_code, "--physics"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  ✅ Structured: {book_code}")
    else:
        print(f"  ⚠️ Structure warning: {result.stderr[:200]}")


def validate_chapter(book_code: str):
    """Run validation on the chapter."""
    import subprocess

    result = subprocess.run(
        ["python3", "validate_extraction.py", book_code, "--physics"],
        capture_output=True, text=True
    )

    for line in result.stdout.split('\n'):
        if 'Status:' in line or 'Errors:' in line:
            print(f"  {line.strip()}")


def extract_chapter(book_code: str, use_vision: bool = True):
    """Full extraction pipeline for a chapter."""
    print(f"\n{'='*60}")
    print(f"EXTRACTING: {book_code}")
    print(f"{'='*60}")

    # Step 1: PDF extraction (raw)
    print("\n[1/3] PDF extraction...")
    extract_pdf(book_code)

    # Step 2: Vision extraction (if enabled)
    if use_vision:
        print("\n[2/3] Vision extraction (Mistral Pixtral)...")
        extract_with_vision(book_code)
    else:
        print("\n[2/3] Vision extraction: SKIPPED")

    # Step 3: Structure and validate
    print("\n[3/3] Structuring...")
    # We'll do this manually since structure_ncert.py needs updating

    print(f"\n✅ {book_code} extraction complete!")


def batch_extract(use_vision: bool = True):
    """Extract all physics chapters."""
    print("="*70)
    print("PHYSICS CLASS 12 - FULL EXTRACTION")
    print("="*70)

    results = []
    for book_code in PHYSICS_CHAPTERS:
        try:
            extract_chapter(book_code, use_vision)
            results.append((book_code, "SUCCESS"))
        except Exception as e:
            print(f"❌ {book_code}: {e}")
            results.append((book_code, f"FAILED: {e}"))

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for code, status in results:
        print(f"  {code}: {status}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_physics.py <book_code>       # Single chapter")
        print("  python extract_physics.py <book_code> --no-vision")
        print("  python extract_physics.py all               # All chapters")
        print("")
        print("Examples:")
        print("  python extract_physics.py keph101")
        print("  python extract_physics.py keph101 --no-vision")
        print("  python extract_physics.py all")
        sys.exit(0)

    use_vision = "--no-vision" not in sys.argv

    if sys.argv[1] == "all":
        batch_extract(use_vision)
    else:
        book_code = sys.argv[1]
        extract_chapter(book_code, use_vision)
