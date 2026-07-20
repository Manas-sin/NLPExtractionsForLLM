#!/usr/bin/env python3
"""
Clean Marker-extracted content.md and create chapter_complete.md
No API required - just text processing.
"""

import re
from pathlib import Path


def clean_content_md(book_code: str) -> str:
    """Clean content.md and create chapter_complete.md."""

    base_dir = Path("extracted") / book_code
    content_file = base_dir / "content.md"

    if not content_file.exists():
        print(f"Error: {content_file} not found")
        return ""

    text = content_file.read_text(encoding="utf-8")

    # Remove page separators and headers
    text = re.sub(r'^---\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^## Page \d+.*$', '', text, flags=re.MULTILINE)

    # Remove page numbers (standalone numbers or "Chemistry 2", "3 Solutions" etc.)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Chemistry\s+\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\s+Chemistry\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\s+(Solutions|Electrochemistry|Chemical Kinetics|Coordination Compounds)\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^(Solutions|Electrochemistry|Chemical Kinetics)\s+\d+\s*$', '', text, flags=re.MULTILINE)

    # Remove NCERT watermarks and copyright
    text = re.sub(r'not to be republished', '', text, flags=re.IGNORECASE)
    text = re.sub(r'©\s*NCERT', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Reprint \d{4}-\d{2}', '', text)

    # Fix bullet points
    text = re.sub(r'^[·•]\s*', '- ', text, flags=re.MULTILINE)

    # Add proper markdown headers for sections
    # Pattern: "1.1 Types of Solutions" at line start
    text = re.sub(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s\-]+)$', r'## \1 \2', text, flags=re.MULTILINE)

    # Add headers for subsections
    text = re.sub(r'^(\d+\.\d+\.\d+)\s+([A-Z][A-Za-z\s\-]+)$', r'### \1 \2', text, flags=re.MULTILINE)

    # Fix example markers
    text = re.sub(r'^Example\s+(\d+\.\d+)', r'### Example \1', text, flags=re.MULTILINE)

    # Fix table markers
    text = re.sub(r'^Table\s+(\d+\.\d+):', r'### Table \1:', text, flags=re.MULTILINE)

    # Convert chemical formulas to LaTeX (basic patterns)
    # H2O, CO2, NaCl, etc.
    def convert_formula(match):
        formula = match.group(0)
        # Only convert if it has numbers
        if re.search(r'\d', formula):
            return '$\\mathrm{' + re.sub(r'(\d+)', r'_{\1}', formula) + '}$'
        return formula

    text = re.sub(r'\b([A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+)\b', convert_formula, text)

    # Convert units to LaTeX
    text = re.sub(r'(\d+)\s*mol\s*L[-–]1', r'\1 $\\text{mol L}^{-1}$', text)
    text = re.sub(r'(\d+)\s*g\s*mol[-–]1', r'\1 $\\text{g mol}^{-1}$', text)
    text = re.sub(r'(\d+)\s*K\b(?!\w)', r'\1 K', text)

    # Clean up excessive newlines
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'^\s+$', '', text, flags=re.MULTILINE)

    # Remove duplicate lines
    lines = text.split('\n')
    cleaned_lines = []
    prev_line = None
    for line in lines:
        stripped = line.strip()
        if stripped != prev_line or stripped == '':
            cleaned_lines.append(line)
            prev_line = stripped
    text = '\n'.join(cleaned_lines)

    # Add unit header if missing
    unit_match = re.search(r'Unit\s*(\d+)', text[:500], re.IGNORECASE)
    if unit_match and not text.strip().startswith('#'):
        # Find chapter title
        titles = {
            '1': 'Solutions',
            '2': 'Electrochemistry',
            '3': 'Chemical Kinetics',
            '4': 'The d- and f-Block Elements',
            '5': 'Coordination Compounds'
        }
        unit_num = unit_match.group(1)
        title = titles.get(unit_num, '')
        text = f"# Unit {unit_num}: {title}\n\n{text}"

    # Save cleaned content
    output_file = base_dir / "chapter_complete.md"
    output_file.write_text(text.strip(), encoding="utf-8")

    print(f"✅ {book_code}: Cleaned {len(text):,} chars -> {output_file.name}")

    return text


def main():
    print("="*60)
    print("CLEANING MARKER OUTPUT FOR ALL CHEMISTRY CHAPTERS")
    print("="*60)

    chapters = ["lech101", "lech102", "lech103", "lech104", "lech105"]

    for book_code in chapters:
        # Skip lech101 if it already has vision extraction
        base_dir = Path("extracted") / book_code
        vision_files = list(base_dir.glob("vision_page_*.md"))

        if len(vision_files) > 10:
            print(f"⏭️  {book_code}: Already has vision extraction ({len(vision_files)} pages)")
            continue

        clean_content_md(book_code)

    print("\nDone! All chapter_complete.md files created.")


if __name__ == "__main__":
    main()
