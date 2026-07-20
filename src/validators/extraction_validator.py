"""Validation for NCERT extractions."""

import json
import re
from pathlib import Path

from ..subjects import detect_subject, get_chapter_titles


class ExtractionValidator:
    """Validates extracted NCERT content."""

    def __init__(self, book_code: str, base_dir: Path = None):
        self.book_code = book_code
        self.base_dir = base_dir or Path("extracted") / book_code
        self.errors = []
        self.warnings = []
        self.expected_title = self._get_expected_title()

    def _get_expected_title(self) -> str | None:
        subject_info = detect_subject(self.book_code)
        if subject_info["subject"] == "unknown":
            return None
        if not subject_info["chapter"] or not subject_info["class"]:
            return None

        titles = get_chapter_titles(subject_info["subject"], subject_info["class"])
        if 0 < subject_info["chapter"] <= len(titles):
            return titles[subject_info["chapter"] - 1]
        return None

    def validate(self) -> dict:
        """Run all validations and return report."""
        self.errors = []
        self.warnings = []

        final_output = self.base_dir / "final_output.json"
        if not final_output.exists():
            self.errors.append("final_output.json not found")
            return self._report()

        data = json.loads(final_output.read_text())

        self._validate_unit_title(data)
        self._validate_sections(data)
        self._validate_exercises(data)
        self._validate_examples(data)
        self._validate_equations(data)
        self._validate_figures(data)
        self._validate_text_quality(data)

        return self._report()

    def _validate_unit_title(self, data: dict):
        actual_title = data.get("unit_title", "")
        if not actual_title:
            self.errors.append("No unit_title extracted")
            return

        if self.expected_title and actual_title != self.expected_title:
            self.errors.append(f"Wrong unit_title: '{actual_title}' (expected '{self.expected_title}')")
        elif len(actual_title) > 100:
            self.warnings.append(f"unit_title too long ({len(actual_title)} chars)")

    def _validate_sections(self, data: dict):
        sections = data.get("sections", [])
        if not sections:
            self.errors.append("No sections extracted")
            return

        empty_sections = []
        for s in sections:
            content = s.get("content_preview", "") or s.get("content", "")
            if len(content) < 50:
                empty_sections.append(s.get("number"))

        if empty_sections:
            self.errors.append(f"Empty sections: {empty_sections}")

    def _validate_exercises(self, data: dict):
        exercises = data.get("exercises", [])
        if not exercises:
            self.warnings.append("No exercises extracted")
            return

        garbage_nums = []
        for ex in exercises:
            num_str = ex.get("number", "")
            try:
                parts = num_str.split('.')
                if len(parts) == 2:
                    major, minor = map(float, parts)
                    if major == 0 or major > 10 or minor > 50 or minor != int(minor):
                        garbage_nums.append(num_str)
            except ValueError:
                garbage_nums.append(num_str)

        if garbage_nums:
            self.errors.append(f"Garbage exercise numbers: {garbage_nums[:10]}")

    def _validate_examples(self, data: dict):
        sections = data.get("sections", [])
        total_examples = sum(len(s.get("examples", [])) for s in sections)
        if total_examples == 0:
            self.warnings.append("No examples extracted")

    def _validate_equations(self, data: dict):
        stats = data.get("statistics", {})
        eq_count = stats.get("equation_count", 0)

        unit_title = data.get("unit_title", "").lower()
        if any(kw in unit_title for kw in ["solution", "kinetics", "electro", "thermo"]):
            if eq_count == 0:
                self.errors.append(f"No equations extracted for '{unit_title}'")

    def _validate_figures(self, data: dict):
        figures_dir = self.base_dir / "figures"
        if figures_dir.exists():
            figure_count = len(list(figures_dir.glob("*.png"))) + len(list(figures_dir.glob("*.jpg")))
            if figure_count == 0:
                self.warnings.append("No figures extracted")

    def _validate_text_quality(self, data: dict):
        for p in data.get("pages", []):
            text = p.get("text", "")
            if re.search(r'[^\w\s]{5,}', text):
                self.warnings.append(f"Possible garbled text on page {p.get('page')}")

    def _report(self) -> dict:
        return {
            "book_code": self.book_code,
            "status": "PASS" if not self.errors else "FAIL",
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings[:20]
        }


def validate_extraction(book_code: str, base_dir: Path = None) -> dict:
    """Validate an extraction and return report."""
    validator = ExtractionValidator(book_code, base_dir)
    return validator.validate()
