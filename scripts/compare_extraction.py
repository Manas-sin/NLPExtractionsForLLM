#!/usr/bin/env python3
"""Compare extraction techniques on a PDF page.

Usage:
    python scripts/compare_extraction.py <pdf_path> [--page N] [--techniques pymupdf,docling,ocr,vision]

Examples:
    python scripts/compare_extraction.py data/pdfs/keph101.pdf
    python scripts/compare_extraction.py data/pdfs/keph101.pdf --page 5
    python scripts/compare_extraction.py data/pdfs/keph101.pdf --techniques pymupdf,docling
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.extraction_comparator import compare_extraction


def main():
    parser = argparse.ArgumentParser(description="Compare PDF extraction techniques")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--page", "-p", type=int, default=1, help="Page number to compare (default: 1)")
    parser.add_argument("--techniques", "-t", default="pymupdf,docling,ocr",
                        help="Comma-separated list of techniques: pymupdf,docling,ocr,vision")
    parser.add_argument("--output", "-o", default="data/comparisons", help="Output directory")

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    techniques = [t.strip() for t in args.techniques.split(",")]

    print(f"\nComparing: {pdf_path}")
    print(f"Page: {args.page}")
    print(f"Techniques: {techniques}")
    print()

    result = compare_extraction(
        str(pdf_path),
        page=args.page,
        techniques=techniques,
        output_dir=args.output
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
