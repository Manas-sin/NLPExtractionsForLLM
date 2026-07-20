#!/usr/bin/env python3
"""
Batch extraction for multiple PDFs.

Usage:
    python scripts/batch_extract.py <pdf_dir> [--subject chemistry|physics|biology]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors import PDFExtractor, VisionExtractor
from src.processors import process_figures_folder


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/batch_extract.py <pdf_dir> [--subject chemistry]")
        sys.exit(1)

    pdf_dir = Path(sys.argv[1])
    subject_filter = None

    if "--subject" in sys.argv:
        idx = sys.argv.index("--subject")
        if idx + 1 < len(sys.argv):
            subject_filter = sys.argv[idx + 1]

    if not pdf_dir.exists():
        print(f"Error: {pdf_dir} not found")
        sys.exit(1)

    pdfs = list(pdf_dir.glob("*.pdf"))
    if subject_filter:
        prefix_map = {"chemistry": "lech", "physics": "keph", "biology": "kebo", "maths": "kemh"}
        prefix = prefix_map.get(subject_filter, subject_filter)
        pdfs = [p for p in pdfs if p.stem.startswith(prefix)]

    print(f"Found {len(pdfs)} PDFs to process")
    print("=" * 50)

    for i, pdf_path in enumerate(sorted(pdfs), 1):
        print(f"\n[{i}/{len(pdfs)}] {pdf_path.name}")

        book_code = pdf_path.stem
        output_dir = Path("data/extracted") / book_code

        if (output_dir / "pages.json").exists():
            print("  Already extracted, skipping")
            continue

        extractor = PDFExtractor(output_dir)
        result = extractor.extract(pdf_path)
        print(f"  Pages: {result['pages']}, Figures: {result['figures']}")

        count = process_figures_folder(output_dir / "figures")
        print(f"  Watermarks removed: {count}")

    print("\n" + "=" * 50)
    print("Batch extraction complete!")


if __name__ == "__main__":
    main()
