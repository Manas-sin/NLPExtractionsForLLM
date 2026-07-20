#!/usr/bin/env python3
"""
Batch Vision extraction for Chemistry chapters.
Uses Claude Vision API to extract clean markdown from page renders.
"""

import json
import os
import sys
import time
from pathlib import Path

# Ensure we can import local modules
sys.path.insert(0, str(Path(__file__).parent))

from extract_vision import extract_chapter_with_vision


CHEMISTRY_CHAPTERS = [
    "lech101",  # Solutions
    "lech102",  # Electrochemistry
    "lech103",  # Chemical Kinetics
    "lech104",  # d- and f-Block Elements
    "lech105",  # Coordination Compounds
]


def main():
    print("="*70)
    print("CHEMISTRY CLASS 12 - VISION EXTRACTION")
    print("="*70)
    print("This uses Claude Vision API to extract clean markdown from page images.")
    print("Cost: ~$0.05-0.10 per chapter (26-30 pages each)")
    print()

    results = []

    for book_code in CHEMISTRY_CHAPTERS:
        out_dir = Path("extracted") / book_code
        renders_dir = out_dir / "renders"

        # Check if renders exist
        if not renders_dir.exists():
            print(f"❌ {book_code}: No renders found. Run extract_ncert.py first.")
            continue

        # Check if already extracted
        vision_files = list(out_dir.glob("vision_page_*.md"))
        if len(vision_files) > 20:
            print(f"✅ {book_code}: Already extracted ({len(vision_files)} pages)")
            results.append({"book_code": book_code, "status": "exists", "pages": len(vision_files)})
            continue

        # Run vision extraction
        print(f"\n🔄 {book_code}: Starting vision extraction...")
        try:
            extract_chapter_with_vision(book_code)
            vision_files = list(out_dir.glob("vision_page_*.md"))
            print(f"✅ {book_code}: Extracted {len(vision_files)} pages")
            results.append({"book_code": book_code, "status": "complete", "pages": len(vision_files)})
        except Exception as e:
            print(f"❌ {book_code}: Error - {e}")
            results.append({"book_code": book_code, "status": "error", "error": str(e)})

        # Small delay between chapters to avoid rate limits
        time.sleep(2)

    # Summary
    print("\n" + "="*70)
    print("VISION EXTRACTION SUMMARY")
    print("="*70)
    for r in results:
        status = "✅" if r["status"] in ["complete", "exists"] else "❌"
        print(f"{status} {r['book_code']}: {r.get('pages', 0)} pages - {r['status']}")


if __name__ == "__main__":
    main()
