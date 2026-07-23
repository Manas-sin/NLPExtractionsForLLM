#!/usr/bin/env python3
"""Ensemble extraction - combines multiple tools for best accuracy.

Usage:
    python scripts/ensemble_extract.py <pdf_path> [--page N] [--pages START-END]

Examples:
    python scripts/ensemble_extract.py data/uploads/keph101.pdf --page 5
    python scripts/ensemble_extract.py data/uploads/keph101.pdf --pages 1-10
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.ensemble_extractor import EnsembleExtractor


def main():
    parser = argparse.ArgumentParser(description="Ensemble PDF extraction")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--page", "-p", type=int, default=None, help="Single page to extract")
    parser.add_argument("--pages", type=str, default=None, help="Page range (e.g., 1-10)")
    parser.add_argument("--output", "-o", default="data/extracted", help="Output directory")

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    extractor = EnsembleExtractor()

    if args.pages:
        start, end = map(int, args.pages.split("-"))
        results = extractor.extract_chapter(pdf_path, start, end)
        print(f"\nExtracted {len(results)} pages")
        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        print(f"Average confidence: {avg_confidence:.0%}")
    else:
        page = args.page or 1
        result = extractor.extract_page(pdf_path, page)

        print("\n" + "=" * 60)
        print(f"ENSEMBLE RESULT - Page {page}")
        print("=" * 60)
        print(f"Confidence: {result.confidence_score:.0%}")
        print(f"Sources: {', '.join(result.sources_used)}")
        if result.watermarks_removed:
            print(f"Watermarks removed: {', '.join(result.watermarks_removed)}")
        print(f"Notes: {result.validation_notes}")
        print("\n--- Merged Text (first 1000 chars) ---")
        print(result.merged_text[:1000])
        print("...")


if __name__ == "__main__":
    main()
