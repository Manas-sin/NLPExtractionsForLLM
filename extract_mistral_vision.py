#!/usr/bin/env python3
"""
Vision-based NCERT extraction using Mistral Pixtral API.
Sends page renders to Pixtral for structured markdown extraction.
FREE alternative to Claude Vision.
"""

import base64
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

EXTRACTION_PROMPT = """You are extracting content from an NCERT textbook page.
Analyze this page image and extract ALL content in structured markdown format.

Follow these rules:
1. **Reading Order**: Follow the natural reading order. Handle two-column layouts correctly.
2. **Section Headers**: Mark as ## 1.1 Title, ### 1.1.1 Subtitle
3. **Equations**: Convert ALL equations and formulas to LaTeX ($$...$$ for display, $...$ for inline)
4. **Chemical Formulas**: Use LaTeX subscripts: H₂O → $\\mathrm{H_2O}$, CO₂ → $\\mathrm{CO_2}$
5. **Tables**: Convert to proper markdown tables with | headers |
6. **Examples**: Mark as ### Example X.Y followed by problem and **Solution**
7. **Figures**: Note as [Figure X.Y: caption description]
8. **Intext Questions**: Mark as ### Intext Questions with numbered list

Extract EVERYTHING - don't summarize or skip content. Preserve all numbers, values, and formulas exactly.

Return ONLY the structured markdown, no explanations."""


def encode_image(image_path: Path) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_page_with_mistral(client: Mistral, image_path: Path, page_num: int) -> dict:
    """Extract structured content from a page image using Mistral Pixtral."""

    image_data = encode_image(image_path)

    try:
        response = client.chat.complete(
            model="pixtral-12b-2409",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": f"data:image/png;base64,{image_data}"}
                    ]
                }
            ]
        )

        markdown = response.choices[0].message.content

        return {
            "page": page_num,
            "markdown": markdown,
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }

    except Exception as e:
        print(f"  Error on page {page_num}: {e}")
        return {
            "page": page_num,
            "markdown": "",
            "error": str(e)
        }


def extract_chapter_with_mistral(book_code: str, api_key: str = None, start_page: int = 1, end_page: int = None):
    """
    Extract a chapter using Mistral Pixtral API.
    Saves individual page markdowns and creates merged chapter_complete.md.
    """
    if not api_key:
        api_key = os.environ.get("MISTRAL_API_KEY")

    if not api_key:
        raise ValueError("No Mistral API key. Set MISTRAL_API_KEY in .env")

    client = Mistral(api_key=api_key)

    base_dir = Path("extracted") / book_code
    renders_dir = base_dir / "renders"

    if not renders_dir.exists():
        raise FileNotFoundError(f"No renders at {renders_dir}. Run extract_ncert.py first.")

    page_images = sorted(renders_dir.glob("page_*.png"))

    if end_page:
        page_images = page_images[:end_page]
    if start_page > 1:
        page_images = page_images[start_page-1:]

    print(f"Extracting {len(page_images)} pages for {book_code} using Mistral Pixtral...")

    total_tokens = 0
    extracted_pages = []

    for img_path in page_images:
        match = re.search(r'page_(\d+)', img_path.stem)
        page_num = int(match.group(1)) if match else 0

        # Check if already extracted
        vision_file = base_dir / f"vision_page_{page_num:03d}.md"
        if vision_file.exists() and vision_file.stat().st_size > 100:
            print(f"  Page {page_num}: already extracted, skipping")
            extracted_pages.append(page_num)
            continue

        print(f"  Page {page_num}: extracting...")

        result = extract_page_with_mistral(client, img_path, page_num)
        total_tokens += result.get("tokens_used", 0)

        if result.get("markdown"):
            vision_file.write_text(result["markdown"], encoding="utf-8")
            extracted_pages.append(page_num)

        # Small delay to avoid rate limits
        time.sleep(0.5)

    # Merge all vision pages into chapter_complete.md
    print(f"Merging {len(extracted_pages)} pages into chapter_complete.md...")
    merge_vision_pages(base_dir)

    print(f"\nDone! Total tokens: {total_tokens:,}")
    return {"book_code": book_code, "pages": len(extracted_pages), "tokens": total_tokens}


def merge_vision_pages(extracted_dir: Path) -> str:
    """Merge all vision_page_*.md files into chapter_complete.md."""

    page_files = sorted(
        extracted_dir.glob("vision_page_*.md"),
        key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))
    )

    if not page_files:
        print("  No vision pages found to merge")
        return ""

    merged_content = []

    for i, page_file in enumerate(page_files):
        content = page_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        # For first page, keep everything
        if i == 0:
            merged_content.append(content)
            continue

        # Clean up subsequent pages
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip page numbers
            if re.match(r'^(Chemistry\s+)?\d+(\s+\w+)?$', line.strip()):
                continue
            if re.match(r'^\d+\s+(Chemistry|Solutions|Electrochemistry|Chemical Kinetics)$', line.strip()):
                continue
            # Skip duplicate unit headers
            if line.startswith('# Unit') and i > 0:
                continue
            cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines).strip()
        if content:
            merged_content.append('\n' + content)

    full_text = '\n'.join(merged_content)

    # Clean up excessive newlines
    full_text = re.sub(r'\n{4,}', '\n\n\n', full_text)

    # Save
    output_file = extracted_dir / "chapter_complete.md"
    output_file.write_text(full_text, encoding="utf-8")
    print(f"  Saved: {output_file} ({len(full_text):,} chars)")

    return full_text


def batch_extract_chemistry():
    """Extract all chemistry chapters using Mistral."""
    chapters = ["lech101", "lech102", "lech103", "lech104", "lech105"]

    print("="*70)
    print("CHEMISTRY CLASS 12 - MISTRAL VISION EXTRACTION")
    print("="*70)

    for book_code in chapters:
        print(f"\n{'='*50}")
        print(f"Processing: {book_code}")
        print(f"{'='*50}")

        try:
            result = extract_chapter_with_mistral(book_code)
            print(f"✅ {book_code}: {result['pages']} pages extracted")
        except Exception as e:
            print(f"❌ {book_code}: Error - {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_mistral_vision.py <book_code>       # Single chapter")
        print("  python extract_mistral_vision.py all               # All chemistry")
        print("")
        print("Examples:")
        print("  python extract_mistral_vision.py lech102")
        print("  python extract_mistral_vision.py lech103 1 10      # Pages 1-10 only")
        print("  python extract_mistral_vision.py all")
        sys.exit(1)

    if sys.argv[1] == "all":
        batch_extract_chemistry()
    else:
        book_code = sys.argv[1]
        start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        end_page = int(sys.argv[3]) if len(sys.argv) > 3 else None

        extract_chapter_with_mistral(book_code, start_page=start_page, end_page=end_page)
