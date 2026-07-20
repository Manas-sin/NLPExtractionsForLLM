#!/usr/bin/env python3
"""
Validation for NCERT extractions.
Checks for common issues and ensures extraction quality.
"""

import json
import re
from pathlib import Path

from ncert_subjects import detect_subject, get_chapter_titles


class ExtractionValidator:
    """Validates extracted NCERT content."""

    def __init__(self, book_code: str, physics_mode: bool = False):
        self.book_code = book_code
        if physics_mode:
            self.base_dir = Path("extracted_physics") / book_code
        else:
            self.base_dir = Path("extracted") / book_code
        self.errors = []
        self.warnings = []

        # Get expected title from book_code
        subject_info = detect_subject(book_code)
        self.expected_title = None
        if subject_info["subject"] != "unknown" and subject_info["chapter"] and subject_info["class"]:
            titles = get_chapter_titles(subject_info["subject"], subject_info["class"])
            if 0 < subject_info["chapter"] <= len(titles):
                self.expected_title = titles[subject_info["chapter"] - 1]

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
        self._validate_unit_title(data)
        self._validate_sections(data)
        self._validate_exercises(data)
        self._validate_examples(data)
        self._validate_equations(data)
        self._validate_figures(data)
        self._validate_text_quality(data)

        return self._report()

    def _validate_unit_title(self, data: dict):
        """Validate unit_title matches expected from book_code."""
        actual_title = data.get("unit_title", "")

        if not actual_title:
            self.errors.append("No unit_title extracted")
            return

        if self.expected_title:
            if actual_title != self.expected_title:
                self.errors.append(f"Wrong unit_title: '{actual_title}' (expected '{self.expected_title}')")
        else:
            # Can't validate without expected title, just check it's reasonable
            if len(actual_title) > 100:
                self.warnings.append(f"unit_title too long ({len(actual_title)} chars) - may be text fragment")

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
                    # Valid: X.Y where X is chapter (1-10), Y is exercise (1-50)
                    if major == 0 or major > 10 or minor > 50:
                        garbage_nums.append(num_str)
                    elif minor != int(minor):  # Decimal like 2.54
                        garbage_nums.append(num_str)
                    else:
                        exercise_nums.append((int(major), int(minor)))
            except:
                garbage_nums.append(num_str)

        if garbage_nums:
            self.errors.append(f"Garbage exercise numbers: {garbage_nums[:10]}")

        # Check monotonic ordering within exercises (NOT starting from 1.1)
        # NCERT books have Intext Questions (1.1-1.N) separate from Exercises (1.M-1.K)
        # Exercises often start at a higher number like 1.5 or 1.14 - this is NOT a bug
        if exercise_nums:
            sorted_nums = sorted(exercise_nums)
            # Just check for gaps within the exercise sequence
            for i in range(1, len(sorted_nums)):
                prev_major, prev_minor = sorted_nums[i-1]
                curr_major, curr_minor = sorted_nums[i]
                if prev_major == curr_major and curr_minor - prev_minor > 1:
                    self.warnings.append(f"Gap in exercises: {prev_major}.{prev_minor} to {curr_major}.{curr_minor}")

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

        # Check if chapter_complete.md has LaTeX equations (vision extraction)
        chapter_md = self.base_dir / "chapter_complete.md"
        has_vision_latex = False
        if chapter_md.exists():
            content = chapter_md.read_text(encoding="utf-8")
            latex_count = content.count("$$") + content.count("$\\")
            if latex_count > 10:
                has_vision_latex = True

        # Chemistry/Physics chapters should have equations
        unit_title = data.get("unit_title", "").lower()
        if any(kw in unit_title for kw in ["solution", "kinetics", "electro", "thermo"]):
            if eq_count == 0:
                if has_vision_latex:
                    # Equations exist in vision output but not in structured.json (from raw OCR)
                    self.warnings.append(f"Equations in chapter_complete.md but not structured.json (raw OCR issue)")
                else:
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


def validate_extraction(book_code: str, physics_mode: bool = False) -> dict:
    """Validate an extraction and print report."""
    validator = ExtractionValidator(book_code, physics_mode)
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
        print("Usage: python validate_extraction.py <book_code> [--physics]")
        print("Examples:")
        print("  python validate_extraction.py lech101           # Chemistry")
        print("  python validate_extraction.py keph101 --physics # Physics")
        sys.exit(1)

    book_code = sys.argv[1]
    physics_mode = "--physics" in sys.argv
    validate_extraction(book_code, physics_mode)
