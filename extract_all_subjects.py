#!/usr/bin/env python3
"""
Multi-Subject NCERT Extractor
Extracts Physics, Chemistry, and Biology with Mistral Pixtral vision.

Usage:
    python extract_all_subjects.py physics      # All physics chapters
    python extract_all_subjects.py chemistry    # All chemistry chapters  
    python extract_all_subjects.py biology      # All biology chapters
    python extract_all_subjects.py all          # All subjects
    python extract_all_subjects.py keph101      # Single chapter
"""

import base64
import json
import os
import re
import sys
import time
from pathlib import Path

import fitz
from dotenv import load_dotenv

load_dotenv()

# Subject configurations
SUBJECTS = {
    "physics": {
        "pdf_dir": Path("/Users/manassingh/Downloads/keph1dd 2/clean"),
        "output_dir": Path("extracted_physics"),
        "chapters": ["keph101", "keph102", "keph103", "keph104", "keph105", "keph106", "keph107"],
        "supplements": ["keph1ps", "keph1an", "keph1a1"],
        "class": 11,
    },
    "chemistry": {
        "pdf_dir": Path("/Users/manassingh/Downloads/lech1dd/clean"),
        "output_dir": Path("extracted_chemistry"),
        "chapters": ["lech101", "lech102", "lech103", "lech104", "lech105"],
        "supplements": ["lech1ps", "lech1an", "lech1a1"],
        "class": 12,
    },
    "biology": {
        "pdf_dir": Path("/Users/manassingh/Downloads/kebo1dd/clean"),
        "output_dir": Path("extracted_biology"),
        "chapters": [f"kebo1{i:02d}" for i in range(1, 20)],  # kebo101-119
        "supplements": ["kebo1ps"],
        "class": 11,
    },
}


def clean_text(text: str) -> str:
    """Clean extracted text."""
    text = text.replace("­", "")
    text = re.sub(r"not\s+to\s+be\s+republished", "", text, flags=re.IGNORECASE)
    text = re.sub(r"©\s*NCERT", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*Reprint\s+\d{4}-\d{2}\s*$", "", text, flags=re.MULTILINE)
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
                "y": bbox[1], "x0": bbox[0], "x1": bbox[2],
                "fig_num": match.group(2), "caption": match.group(3).strip()
            })
    return captions


def extract_figures(page, page_num, figures_dir, doc, scale=3):
    """Extract figures by rendering page regions around captions."""
    figures = []
    page_width = page.rect.width
    page_height = page.rect.height
    captions = find_all_captions(page)

    for cap in captions:
        fig_num = cap["fig_num"]
        caption_y = cap["y"]
        caption_x_center = (cap["x0"] + cap["x1"]) / 2
        is_right_column = caption_x_center > page_width / 2
        fig_height = min(250, caption_y - 20)
        margin = 30

        if is_right_column:
            x0 = max(page_width * 0.45, cap["x0"] - margin)
            x1 = min(page_width - 10, cap["x1"] + margin)
        else:
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

        figures.append({
            "page": page_num, "figure": fig_num,
            "caption": cap["caption"], "path": str(fig_path)
        })
    return figures


def extract_pdf(book_code: str, subject_config: dict):
    """Extract PDF to raw text, renders, and figures."""
    pdf_dir = subject_config["pdf_dir"]
    output_dir = subject_config["output_dir"]

    # Try clean version first
    pdf_path = pdf_dir / f"{book_code}_clean.pdf"
    if not pdf_path.exists():
        pdf_path = pdf_dir.parent / f"{book_code}.pdf"
    if not pdf_path.exists():
        print(f"Error: {book_code}.pdf not found")
        return None

    doc = fitz.open(pdf_path)
    out_dir = output_dir / book_code
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
        raw = page.get_text("text", sort=False)
        text = clean_text(raw)
        pages_data.append({"page": page_num, "char_count": len(text), "text": text})
        (pages_dir / f"page_{page_num:03d}.txt").write_text(text, encoding="utf-8")
        all_text.append(f"\n---\n## Page {page_num}\n")
        all_text.append(text)

        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        pix.save(renders_dir / f"page_{page_num:03d}.png")

        figures = extract_figures(page, page_num, figures_dir, doc)
        all_figures.extend(figures)

    doc.close()

    (out_dir / "content.md").write_text("\n".join(all_text), encoding="utf-8")
    (out_dir / "pages.json").write_text(json.dumps(pages_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "figures.json").write_text(json.dumps(all_figures, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  ✅ Extracted: {len(pages_data)} pages, {len(all_figures)} figures")
    return {"pages": len(pages_data), "figures": len(all_figures)}


def extract_with_vision(book_code: str, subject_config: dict):
    """Extract using Mistral Pixtral vision API."""
    from mistralai.client import Mistral

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set")
        return None

    client = Mistral(api_key=api_key)
    out_dir = subject_config["output_dir"] / book_code
    renders_dir = out_dir / "renders"

    if not renders_dir.exists():
        print(f"No renders found. Running PDF extraction first...")
        extract_pdf(book_code, subject_config)

    page_images = sorted(renders_dir.glob("page_*.png"))
    print(f"Vision extraction: {len(page_images)} pages")

    EXTRACTION_PROMPT = """You are extracting content from an NCERT textbook page.
Analyze this page image and extract ALL content in structured markdown format.

Rules:
1. Follow natural reading order. Handle two-column layouts correctly.
2. Section Headers: ## X.Y Title, ### X.Y.Z Subtitle
3. Equations: ALL equations in LaTeX ($$...$$ display, $...$ inline)
4. Tables: proper markdown tables with | headers |
5. Examples: ### Example X.Y followed by problem and **Solution**
6. Figures: [Figure X.Y: caption description]
7. Intext Questions: ### Intext Questions with numbered list

Extract EVERYTHING - don't summarize. Preserve all numbers and formulas exactly.
Return ONLY the structured markdown."""

    total_tokens = 0
    extracted_pages = []

    for img_path in page_images:
        match = re.search(r'page_(\d+)', img_path.stem)
        page_num = int(match.group(1)) if match else 0

        vision_file = out_dir / f"vision_page_{page_num:03d}.md"
        if vision_file.exists() and vision_file.stat().st_size > 100:
            print(f"  Page {page_num}: cached")
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

        time.sleep(0.3)

    merge_vision_pages(out_dir)
    print(f"  ✅ Vision: {len(extracted_pages)} pages, {total_tokens:,} tokens")
    return {"pages": len(extracted_pages), "tokens": total_tokens}


def merge_vision_pages(out_dir: Path):
    """Merge vision_page_*.md into chapter_complete.md."""
    page_files = sorted(
        out_dir.glob("vision_page_*.md"),
        key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))
    )
    if not page_files:
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
            if re.match(r'^\d+\s+\w+.*$', line.strip()):
                continue
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


def extract_chapter(book_code: str, subject_config: dict, use_vision: bool = True):
    """Full extraction pipeline for a chapter."""
    print(f"\n{'='*60}")
    print(f"EXTRACTING: {book_code}")
    print(f"{'='*60}")

    print("\n[1/2] PDF extraction...")
    extract_pdf(book_code, subject_config)

    if use_vision:
        print("\n[2/2] Vision extraction (Mistral Pixtral)...")
        extract_with_vision(book_code, subject_config)
    else:
        print("\n[2/2] Vision extraction: SKIPPED")

    print(f"\n✅ {book_code} complete!")


def extract_subject(subject: str, use_vision: bool = True):
    """Extract all chapters for a subject."""
    config = SUBJECTS[subject]
    print(f"\n{'='*70}")
    print(f"{subject.upper()} CLASS {config['class']} - FULL EXTRACTION")
    print(f"{'='*70}")

    all_codes = config["chapters"] + config["supplements"]
    for book_code in all_codes:
        try:
            extract_chapter(book_code, config, use_vision)
        except Exception as e:
            print(f"❌ {book_code}: {e}")


def get_subject_for_code(book_code: str) -> tuple:
    """Determine subject from book code."""
    for subject, config in SUBJECTS.items():
        all_codes = config["chapters"] + config["supplements"]
        if book_code in all_codes:
            return subject, config
    return None, None


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_all_subjects.py physics|chemistry|biology|all")
        print("  python extract_all_subjects.py <book_code>")
        sys.exit(0)

    arg = sys.argv[1].lower()
    use_vision = "--no-vision" not in sys.argv

    if arg == "all":
        for subject in ["physics", "chemistry", "biology"]:
            extract_subject(subject, use_vision)
    elif arg in SUBJECTS:
        extract_subject(arg, use_vision)
    else:
        subject, config = get_subject_for_code(arg)
        if config:
            extract_chapter(arg, config, use_vision)
        else:
            print(f"Unknown: {arg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
