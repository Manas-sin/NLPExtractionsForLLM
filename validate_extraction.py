#!/usr/bin/env python3
"""
Validation for NCERT extractions.
Checks for common issues and ensures extraction quality.
"""

import json
import re
from pathlib import Path


class ExtractionValidator:
    """Validates extracted NCERT content."""

    def __init__(self, book_code: str):
        self.book_code = book_code
        self.base_dir = Path("extracted") / book_code
        self.errors = []
        self.warnings = []

    def validate(self) -> dict:
        """Run all validations and return report."""
        self.errors = []
        self.warnings = []

        # Load data
        final_output = self.base_dir / "final_output.json"
        if not final_output.exists():
            self.errors.append("final_output.json not found")
            return self._report()

        data = json.loads(final_output.read_text())

        # Run validations
        self._validate_sections(data)
        self._validate_exercises(data)
        self._validate_examples(data)
        self._validate_equations(data)
        self._validate_figures(data)
        self._validate_text_quality(data)

        return self._report()

    def _validate_sections(self, data: dict):
        """Validate section extraction."""
        sections = data.get("sections", [])

        if not sections:
            self.errors.append("No sections extracted")
            return

        # Check section numbers are sequential
        expected_nums = []
        for s in sections:
            num = s.get("number", "")
            try:
                major, minor = map(int, num.split('.'))
                expected_nums.append((major, minor))
            except:
                self.warnings.append(f"Invalid section number: {num}")

        # Check for gaps
        if expected_nums:
            sorted_nums = sorted(expected_nums)
            for i in range(1, len(sorted_nums)):
                prev = sorted_nums[i-1]
                curr = sorted_nums[i]
                if prev[0] == curr[0] and curr[1] - prev[1] > 1:
                    self.warnings.append(f"Gap in sections: {prev[0]}.{prev[1]} to {curr[0]}.{curr[1]}")

        # Check sections have content
        empty_sections = []
        for s in sections:
            content = s.get("content_preview", "") or s.get("content", "")
            if len(content) < 50:
                empty_sections.append(s.get("number"))

        if empty_sections:
            self.errors.append(f"Empty sections: {empty_sections}")

        # Check titles aren't truncated
        for s in sections:
            title = s.get("title", "")
            if title.endswith("of") or title.endswith("and") or title.endswith("the"):
                self.warnings.append(f"Truncated title: {s.get('number')} - {title}")

    def _validate_exercises(self, data: dict):
        """Validate exercise extraction."""
        exercises = data.get("exercises", [])

        if not exercises:
            self.warnings.append("No exercises extracted")
            return

        # Check exercise numbers
        exercise_nums = []
        garbage_nums = []

        for ex in exercises:
            num_str = ex.get("number", "")
            try:
                parts = num_str.split('.')
                if len(parts) == 2:
                    major, minor = map(float, parts)
                    # Garbage detection: numbers like 0.541, 273.15
                    if major == 0 or minor > 50 or (major > 2 and minor > 20):
                        garbage_nums.append(num_str)
                    else:
                        exercise_nums.append((int(major), int(minor)))
            except:
                garbage_nums.append(num_str)

        if garbage_nums:
            self.errors.append(f"Garbage exercise numbers: {garbage_nums[:10]}")

        # Check monotonic ordering (exercises should be 1.1, 1.2, ..., 1.N)
        if exercise_nums:
            sorted_nums = sorted(exercise_nums)
            expected_minor = 1
            for major, minor in sorted_nums:
                if major == 1:  # Main exercises
                    if minor != expected_minor and minor != expected_minor + 1:
                        self.warnings.append(f"Exercise gap/jump at 1.{minor} (expected 1.{expected_minor})")
                    expected_minor = minor + 1

        # Check exercise text isn't empty
        empty_exercises = [ex.get("number") for ex in exercises if len(ex.get("text", "")) < 10]
        if empty_exercises:
            self.warnings.append(f"Empty exercises: {empty_exercises[:5]}")

    def _validate_examples(self, data: dict):
        """Validate example extraction."""
        sections = data.get("sections", [])
        total_examples = sum(len(s.get("examples", [])) for s in sections)

        if total_examples == 0:
            self.warnings.append("No examples extracted")
            return

        # Check examples have problems and solutions
        for s in sections:
            for ex in s.get("examples", []):
                if not ex.get("problem"):
                    self.warnings.append(f"Example {ex.get('number')} has no problem text")
                if not ex.get("solution"):
                    self.warnings.append(f"Example {ex.get('number')} has no solution")

    def _validate_equations(self, data: dict):
        """Validate equation extraction."""
        stats = data.get("statistics", {})
        eq_count = stats.get("equation_count", 0)

        # Chemistry/Physics chapters should have equations
        unit_title = data.get("unit_title", "").lower()
        if any(kw in unit_title for kw in ["solution", "kinetics", "electro", "thermo"]):
            if eq_count == 0:
                self.errors.append(f"No equations extracted for '{unit_title}' (expected many)")
            elif eq_count < 5:
                self.warnings.append(f"Only {eq_count} equations extracted (expected more)")

    def _validate_figures(self, data: dict):
        """Validate figure extraction."""
        diagrams = data.get("diagrams", [])
        figures_dir = self.base_dir / "figures"
        diagrams_dir = self.base_dir / "diagrams"

        # Check figure files exist
        if diagrams:
            for d in diagrams:
                path = Path(d.get("path", ""))
                if not path.exists():
                    self.warnings.append(f"Missing diagram file: {d.get('figure')}")

        # Check figures folder
        if figures_dir.exists():
            figure_count = len(list(figures_dir.glob("*.png"))) + len(list(figures_dir.glob("*.jpg")))
            if figure_count == 0:
                self.warnings.append("No figures extracted")

    def _validate_text_quality(self, data: dict):
        """Validate text extraction quality."""
        pages = data.get("pages", [])

        for p in pages:
            text = p.get("text", "")

            # Check for garbled text (consecutive special chars)
            if re.search(r'[^\w\s]{5,}', text):
                self.warnings.append(f"Possible garbled text on page {p.get('page')}")

            # Check for reading order issues (common patterns)
            if re.search(r'Objectives.*1\.\d.*After studying', text[:500]):
                self.warnings.append(f"Possible reading order issue on page {p.get('page')}")

            # Check for truncated formulas
            if re.search(r'[A-Za-z]=\s*$', text) or re.search(r'[A-Za-z]=\s*\n', text):
                self.warnings.append(f"Possible truncated formula on page {p.get('page')}")

    def _report(self) -> dict:
        """Generate validation report."""
        report = {
            "book_code": self.book_code,
            "status": "PASS" if not self.errors else "FAIL",
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings[:20]  # Limit warnings
        }

        return report


def validate_extraction(book_code: str) -> dict:
    """Validate an extraction and print report."""
    validator = ExtractionValidator(book_code)
    report = validator.validate()

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
        if len(report['warnings']) > 10:
            print(f"  ... and {len(report['warnings'])-10} more")

    # Save report
    report_file = Path("extracted") / book_code / "validation_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nReport saved: {report_file}")

    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validate_extraction.py <book_code>")
        sys.exit(1)

    book_code = sys.argv[1]
    validate_extraction(book_code)
