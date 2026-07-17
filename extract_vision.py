#!/usr/bin/env python3
"""
Vision-based NCERT extraction using Claude API.
Sends page renders to Claude Vision for structured markdown extraction.
"""

import base64
import json
import os
import re
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

EXTRACTION_PROMPT = """You are extracting content from an NCERT textbook page.
Analyze this page image and extract ALL content in structured markdown format.

Follow these rules:
1. **Reading Order**: Follow the natural reading order. Handle two-column layouts correctly - read left column fully before right column.
2. **Section Headers**: Mark as ## 1.1 Title, ### 1.1.1 Subtitle
3. **Equations**: Convert ALL equations and formulas to LaTeX ($$...$$  for display, $...$ for inline)
4. **Chemical Formulas**: Use LaTeX subscripts: H₂O → $\mathrm{H_2O}$, CO₂ → $\mathrm{CO_2}$
5. **Tables**: Convert to proper markdown tables with | headers |
6. **Examples**: Mark as **Example X.Y** followed by problem and solution
7. **Exercises**: Mark as **Exercise X.Y** with full question text
8. **Figures**: Note as [Figure X.Y: caption description]
9. **Margin Notes/Boxes**: Include but mark clearly as > blockquotes
10. **Intext Questions**: Mark as **Intext Question X.Y**

Extract EVERYTHING - don't summarize or skip content. Preserve all numbers, values, and formulas exactly.

Return ONLY the structured markdown, no explanations."""


def encode_image(image_path: Path) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_page_with_vision(client: Anthropic, image_path: Path, page_num: int) -> dict:
    """Extract structured content from a page image using Claude Vision."""

    image_data = encode_image(image_path)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT
                        }
                    ]
                }
            ]
        )

        markdown = response.content[0].text

        return {
            "page": page_num,
            "markdown": markdown,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }

    except Exception as e:
        print(f"  Error on page {page_num}: {e}")
        return {
            "page": page_num,
            "markdown": "",
            "error": str(e)
        }


def extract_with_vision(book_code: str, api_key: str = None, start_page: int = 1, end_page: int = None):
    """Extract all pages using Claude Vision."""

    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: No Anthropic API key. Set ANTHROPIC_API_KEY in .env")
        return None

    client = Anthropic(api_key=api_key)

    base_dir = Path("extracted") / book_code
    renders_dir = base_dir / "renders"

    if not renders_dir.exists():
        print(f"Error: No renders found at {renders_dir}")
        print("Run extract_ncert.py first to generate page renders.")
        return None

    # Get all page images
    page_images = sorted(renders_dir.glob("page_*.png"))

    if end_page:
        page_images = page_images[:end_page]
    if start_page > 1:
        page_images = page_images[start_page-1:]

    print(f"Extracting {len(page_images)} pages with Claude Vision...")

    results = []
    total_tokens = 0

    for img_path in page_images:
        # Extract page number from filename
        match = re.search(r'page_(\d+)', img_path.stem)
        page_num = int(match.group(1)) if match else 0

        print(f"  Processing page {page_num}...")

        result = extract_page_with_vision(client, img_path, page_num)
        results.append(result)
        total_tokens += result.get("tokens_used", 0)

    # Combine all markdown
    full_markdown = ""
    for r in results:
        if r.get("markdown"):
            full_markdown += f"\n\n---\n## Page {r['page']}\n\n{r['markdown']}"

    # Save results
    output = {
        "book_code": book_code,
        "pages": results,
        "full_markdown": full_markdown,
        "total_tokens": total_tokens,
        "estimated_cost": round(total_tokens * 0.000003, 4)  # Rough estimate
    }

    output_file = base_dir / "vision_extracted.json"
    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    # Also save markdown
    md_file = base_dir / "content_vision.md"
    md_file.write_text(full_markdown)

    print(f"\nExtraction complete!")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Estimated cost: ${output['estimated_cost']:.4f}")
    print(f"  Output: {output_file}")
    print(f"  Markdown: {md_file}")

    return output


def parse_vision_output(book_code: str):
    """Parse the vision-extracted markdown into structured JSON."""

    base_dir = Path("extracted") / book_code
    vision_file = base_dir / "vision_extracted.json"

    if not vision_file.exists():
        print(f"Error: {vision_file} not found. Run extract_with_vision first.")
        return None

    data = json.loads(vision_file.read_text())
    full_md = data.get("full_markdown", "")

    # Parse sections
    sections = []
    section_pattern = re.compile(r'^##\s+(\d+\.\d+)\s+(.+?)$', re.MULTILINE)

    matches = list(section_pattern.finditer(full_md))
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(full_md)
        content = full_md[start:end].strip()

        sections.append({
            "number": match.group(1),
            "title": match.group(2).strip(),
            "content": content[:2000],  # Limit for JSON size
            "content_length": len(content)
        })

    # Parse examples
    examples = []
    example_pattern = re.compile(r'\*\*Example\s+(\d+\.\d+)\*\*\s*(.+?)(?=\*\*Example|\*\*Exercise|##|$)', re.DOTALL)
    for match in example_pattern.finditer(full_md):
        examples.append({
            "number": match.group(1),
            "content": match.group(2).strip()[:1000]
        })

    # Parse exercises
    exercises = []
    exercise_pattern = re.compile(r'\*\*Exercise\s+(\d+\.\d+)\*\*\s*(.+?)(?=\*\*Exercise|##|$)', re.DOTALL)
    for match in exercise_pattern.finditer(full_md):
        exercises.append({
            "number": match.group(1),
            "text": match.group(2).strip()[:500]
        })

    # Parse equations
    equations = re.findall(r'\$\$(.+?)\$\$', full_md, re.DOTALL)

    # Parse intext questions
    intext = []
    intext_pattern = re.compile(r'\*\*Intext Question\s+(\d+\.\d+)\*\*\s*(.+?)(?=\*\*Intext|##|$)', re.DOTALL)
    for match in intext_pattern.finditer(full_md):
        intext.append({
            "number": match.group(1),
            "text": match.group(2).strip()[:500]
        })

    # Build structured output
    structured = {
        "book_code": book_code,
        "sections": sections,
        "examples": examples,
        "exercises": exercises,
        "intext_questions": intext,
        "equations": equations[:50],  # Limit
        "statistics": {
            "section_count": len(sections),
            "example_count": len(examples),
            "exercise_count": len(exercises),
            "intext_count": len(intext),
            "equation_count": len(equations)
        }
    }

    # Save
    output_file = base_dir / "structured_vision.json"
    output_file.write_text(json.dumps(structured, ensure_ascii=False, indent=2))
    print(f"Parsed structured output: {output_file}")

    return structured


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_vision.py <book_code> [api_key] [start_page] [end_page]")
        print("Example: python extract_vision.py lech101")
        print("         python extract_vision.py lech101 sk-xxx 1 5  # Pages 1-5 only")
        sys.exit(1)

    book_code = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    start_page = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    end_page = int(sys.argv[4]) if len(sys.argv) > 4 else None

    extract_with_vision(book_code, api_key, start_page, end_page)
    parse_vision_output(book_code)
