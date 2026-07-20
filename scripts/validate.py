#!/usr/bin/env python3
"""
CLI for validating NCERT extractions.

Usage:
    python scripts/validate.py <book_code>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validators import validate_extraction


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate.py <book_code>")
        print("Example: python scripts/validate.py lech101")
        sys.exit(1)

    book_code = sys.argv[1]
    base_dir = Path("data/extracted") / book_code

    if not base_dir.exists():
        base_dir = Path("extracted") / book_code

    if not base_dir.exists():
        print(f"Error: Directory not found for {book_code}")
        sys.exit(1)

    report = validate_extraction(book_code, base_dir)

    print(f"\n{'='*50}")
    print(f"VALIDATION REPORT: {book_code}")
    print(f"{'='*50}")
    print(f"Status: {report['status']}")
    print(f"Errors: {report['error_count']}")
    print(f"Warnings: {report['warning_count']}")

    if report['errors']:
        print(f"\n--- ERRORS ---")
        for e in report['errors']:
            print(f"  ❌ {e}")

    if report['warnings']:
        print(f"\n--- WARNINGS ---")
        for w in report['warnings'][:10]:
            print(f"  ⚠️  {w}")

    report_file = base_dir / "validation_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nReport saved: {report_file}")


if __name__ == "__main__":
    main()
