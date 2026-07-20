#!/usr/bin/env python3
"""
CLI for NCERT PDF extraction.

Usage:
    python scripts/extract.py <pdf_path> [--vision] [--validate]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors import PDFExtractor, VisionExtractor
from src.processors import process_figures_folder
from src.validators import validate_extraction


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract.py <pdf_path> [--vision] [--validate]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    use_vision = "--vision" in sys.argv
    do_validate = "--validate" in sys.argv

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    book_code = pdf_path.stem
    output_dir = Path("data/extracted") / book_code

    print(f"Extracting: {pdf_path.name}")
    print(f"Output: {output_dir}/")
    print("=" * 50)

    print("\nStep 1: PDF extraction...")
    extractor = PDFExtractor(output_dir)
    result = extractor.extract(pdf_path)
    print(f"  Pages: {result['pages']}, Figures: {result['figures']}, Chars: {result['total_chars']:,}")

    print("\nStep 2: Removing watermarks from figures...")
    count = process_figures_folder(output_dir / "figures")
    print(f"  Processed {count} images")

    if use_vision:
        print("\nStep 3: Vision extraction...")
        vision_extractor = VisionExtractor(output_dir)
        vision_result = vision_extractor.extract(output_dir / "renders")
        print(f"  Pages: {vision_result['pages']}, Tokens: {vision_result['total_tokens']:,}")

    if do_validate:
        print("\nValidation...")
        report = validate_extraction(book_code, output_dir)
        print(f"  Status: {report['status']}")
        if report['errors']:
            for e in report['errors']:
                print(f"  ❌ {e}")

    print("\n" + "=" * 50)
    print("DONE!")
    print(f"Output: {output_dir}/")


if __name__ == "__main__":
    main()
