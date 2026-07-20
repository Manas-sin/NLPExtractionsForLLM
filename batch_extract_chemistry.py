#!/usr/bin/env python3
"""
Batch extraction for all Chemistry Class 12 chapters.
Extracts raw pages, generates structured JSON, and creates merged markdown.
"""

import json
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Chemistry chapters to process
CHEMISTRY_CHAPTERS = [
    ("lech101", "Unit 1: Solutions"),
    ("lech102", "Unit 2: Electrochemistry"),
    ("lech103", "Unit 3: Chemical Kinetics"),
    ("lech104", "Unit 4: The d- and f-Block Elements"),
    ("lech105", "Unit 5: Coordination Compounds"),
]

UPLOADS_DIR = Path("uploads")
EXTRACTED_DIR = Path("extracted")


def extract_chapter(book_code: str, title: str) -> dict:
    """Extract a single chapter."""
    result = {
        "book_code": book_code,
        "title": title,
        "status": "pending",
        "pages": 0,
        "errors": []
    }

    pdf_path = UPLOADS_DIR / f"{book_code}.pdf"
    if not pdf_path.exists():
        result["status"] = "error"
        result["errors"].append(f"PDF not found: {pdf_path}")
        return result

    try:
        # Step 1: Extract raw pages
        print(f"\n{'='*60}")
        print(f"Processing: {book_code} - {title}")
        print(f"{'='*60}")

        proc = subprocess.run(
            ["python", "extract_ncert.py", str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if proc.returncode != 0:
            result["errors"].append(f"Extraction failed: {proc.stderr[:500]}")

        # Step 2: Check output
        out_dir = EXTRACTED_DIR / book_code
        pages_file = out_dir / "pages.json"

        if pages_file.exists():
            pages = json.loads(pages_file.read_text())
            result["pages"] = len(pages)
            result["status"] = "extracted"
        else:
            result["errors"].append("pages.json not created")

        # Step 3: Validate
        structured_file = out_dir / "structured.json"
        if structured_file.exists():
            data = json.loads(structured_file.read_text())
            result["sections"] = data.get("statistics", {}).get("section_count", 0)
            result["examples"] = data.get("statistics", {}).get("example_count", 0)
            result["exercises"] = data.get("statistics", {}).get("exercise_count", 0)
            result["status"] = "complete"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["errors"].append("Extraction timed out after 5 minutes")
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))

    return result


def main():
    print("="*70)
    print("CHEMISTRY CLASS 12 - BATCH EXTRACTION")
    print("="*70)

    results = []

    # Process chapters sequentially (to avoid memory issues)
    for book_code, title in CHEMISTRY_CHAPTERS:
        result = extract_chapter(book_code, title)
        results.append(result)
        print(f"\n{book_code}: {result['status']} ({result.get('pages', 0)} pages)")

    # Summary
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)

    total_pages = 0
    for r in results:
        status_icon = "✅" if r["status"] == "complete" else "❌" if r["status"] == "error" else "⚠️"
        print(f"{status_icon} {r['book_code']}: {r['title']}")
        print(f"   Pages: {r.get('pages', 0)}, Sections: {r.get('sections', 0)}, "
              f"Examples: {r.get('examples', 0)}, Exercises: {r.get('exercises', 0)}")
        if r.get("errors"):
            for e in r["errors"][:2]:
                print(f"   ⚠️ {e[:80]}")
        total_pages += r.get("pages", 0)

    print(f"\nTotal pages processed: {total_pages}")

    # Save summary
    summary_file = EXTRACTED_DIR / "chemistry_extraction_summary.json"
    summary_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
