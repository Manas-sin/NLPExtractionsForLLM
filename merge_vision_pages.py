#!/usr/bin/env python3
"""
Merge all vision_page_*.md files into a single structured markdown file.
Removes page breaks and creates a continuous document.
"""

import re
from pathlib import Path


def merge_vision_pages(extracted_dir: Path) -> str:
    """Merge all vision page markdown files into one document."""

    # Find all vision page files
    page_files = sorted(
        extracted_dir.glob("vision_page_*.md"),
        key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))
    )

    if not page_files:
        raise FileNotFoundError(f"No vision_page_*.md files found in {extracted_dir}")

    print(f"Found {len(page_files)} pages to merge")

    merged_content = []
    prev_ends_mid_sentence = False

    for i, page_file in enumerate(page_files):
        content = page_file.read_text(encoding="utf-8").strip()

        # Skip empty pages
        if not content:
            continue

        # For first page, keep the header
        if i == 0:
            merged_content.append(content)
            prev_ends_mid_sentence = not content.rstrip().endswith(('.', ':', '?', '!', '|'))
            continue

        # Remove duplicate headers from subsequent pages
        # (Sometimes Vision repeats "# Unit 1: Solutions" etc.)
        lines = content.split('\n')
        cleaned_lines = []
        skip_until_content = False

        for line in lines:
            # Skip page numbers like "Chemistry 2" or "3 Solutions"
            if re.match(r'^(Chemistry\s+)?\d+(\s+Solutions)?$', line.strip()):
                continue
            if re.match(r'^\d+\s+(Chemistry|Solutions)$', line.strip()):
                continue

            # Skip if it's a duplicate unit header we already have
            if line.startswith('# Unit') and i > 0:
                continue

            cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines).strip()

        if not content:
            continue

        # Check if previous page ended mid-sentence (should join without break)
        if prev_ends_mid_sentence and not content.startswith('#'):
            # Join continuation without extra newlines
            merged_content.append(content)
        else:
            # Add proper spacing between sections
            merged_content.append('\n' + content)

        prev_ends_mid_sentence = not content.rstrip().endswith(('.', ':', '?', '!', '|', '-'))

    # Join all content
    full_text = '\n'.join(merged_content)

    # Clean up excessive newlines
    full_text = re.sub(r'\n{4,}', '\n\n\n', full_text)

    # Clean up any remaining page artifacts
    full_text = re.sub(r'\n(Chemistry\s+)?\d+\s*\n', '\n', full_text)
    full_text = re.sub(r'\n\d+\s+(Chemistry|Solutions)\s*\n', '\n', full_text)

    return full_text


def main():
    import sys

    if len(sys.argv) > 1:
        extracted_dir = Path(sys.argv[1])
    else:
        extracted_dir = Path("extracted/lech101")

    if not extracted_dir.exists():
        print(f"Directory not found: {extracted_dir}")
        sys.exit(1)

    print(f"Merging pages from: {extracted_dir}")

    merged = merge_vision_pages(extracted_dir)

    # Write output
    output_file = extracted_dir / "chapter_complete.md"
    output_file.write_text(merged, encoding="utf-8")

    print(f"Merged content written to: {output_file}")
    print(f"Total characters: {len(merged):,}")

    # Also create a summary
    sections = re.findall(r'^##\s+(\d+\.\d+.*?)$', merged, re.MULTILINE)
    print(f"\nSections found:")
    for sec in sections[:15]:
        print(f"  - {sec}")
    if len(sections) > 15:
        print(f"  ... and {len(sections) - 15} more")


if __name__ == "__main__":
    main()
