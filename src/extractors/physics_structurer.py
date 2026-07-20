"""Physics-specific structurer for NCERT content."""

import json
import re
from pathlib import Path


class PhysicsStructurer:
    """Structures physics chapter content into clean JSON."""

    def __init__(self, book_code: str, base_dir: Path = None):
        self.book_code = book_code
        self.base_dir = base_dir or Path("data/extracted_physics") / book_code

    def structure(self) -> dict:
        """Parse chapter_complete.md into structured JSON."""
        md_file = self.base_dir / "chapter_complete.md"
        if not md_file.exists():
            raise FileNotFoundError(f"No chapter_complete.md at {md_file}")

        content = md_file.read_text(encoding="utf-8")
        content = self._clean_markdown_wrapper(content)

        result = {
            "book_code": self.book_code,
            "subject": "physics",
            "class": 11 if self.book_code.startswith("keph1") else 12,
            "chapter_number": self._extract_chapter_number(),
            "chapter_title": self._extract_title(content),
            "sections": self._extract_sections(content),
            "tables": self._extract_tables(content),
            "examples": self._extract_examples(content),
            "exercises": self._extract_exercises(content),
            "intext_questions": self._extract_intext_questions(content),
            "summary": self._extract_summary(content),
            "equations": self._extract_all_equations(content),
            "figures": self._extract_figures(content),
        }

        result["statistics"] = {
            "section_count": len(result["sections"]),
            "table_count": len(result["tables"]),
            "example_count": len(result["examples"]),
            "exercise_count": len(result["exercises"]),
            "intext_question_count": len(result["intext_questions"]),
            "equation_count": len(result["equations"]),
            "figure_count": len(result["figures"]),
        }

        return result

    def _clean_markdown_wrapper(self, content: str) -> str:
        """Remove markdown code block wrappers."""
        content = re.sub(r'^```markdown\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        content = re.sub(r'^```\s*\n', '', content)
        return content.strip()

    def _extract_chapter_number(self) -> int:
        """Extract chapter number from book code."""
        try:
            return int(self.book_code[5:7])
        except (ValueError, IndexError):
            return 1

    def _extract_title(self, content: str) -> str:
        """Extract chapter title."""
        match = re.search(r'^##\s+(.+?)(?:\n|$)', content, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'^Chapter\s+\w+\s*', '', title, flags=re.IGNORECASE)
            return title.strip()

        match = re.search(r'^#\s+Chapter\s+\w+\s*\n+##\s+(.+)', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        return "Unknown"

    def _extract_sections(self, content: str) -> list:
        """Extract all sections with proper hierarchy."""
        sections = []
        section_pattern = re.compile(
            r'^(#{2,3})\s+(\d+\.\d+(?:\.\d+)?)\s+(.+?)(?:\n|$)',
            re.MULTILINE
        )

        matches = list(section_pattern.finditer(content))

        for i, match in enumerate(matches):
            level = len(match.group(1))
            number = match.group(2)
            title = match.group(3).strip()

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end].strip()

            section_content = re.sub(r'^##.*$', '', section_content, flags=re.MULTILINE)
            section_content = section_content.strip()

            sections.append({
                "number": number,
                "title": title,
                "level": level - 1,
                "content": section_content[:2000] if len(section_content) > 2000 else section_content,
                "has_more": len(section_content) > 2000
            })

        return sections

    def _extract_tables(self, content: str) -> list:
        """Extract tables with full content."""
        tables = []

        table_header_pattern = re.compile(
            r'(?:###?\s+)?Table\s+(\d+\.\d+)[:\s]+(.+?)(?:\n|$)',
            re.IGNORECASE
        )

        for match in table_header_pattern.finditer(content):
            table_num = match.group(1)
            table_title = match.group(2).strip()

            start = match.end()
            table_content = content[start:start + 2000]

            rows = []
            headers = []

            lines = table_content.split('\n')
            in_table = False

            for line in lines:
                line = line.strip()
                if line.startswith('|') and line.endswith('|'):
                    in_table = True
                    cells = [c.strip() for c in line.split('|')[1:-1]]

                    if not headers:
                        headers = cells
                    elif all(c.replace('-', '').replace(':', '') == '' for c in cells):
                        continue
                    else:
                        if len(cells) == len(headers):
                            rows.append(dict(zip(headers, cells)))
                        else:
                            rows.append({"values": cells})
                elif in_table and line and not line.startswith('|'):
                    break

            tables.append({
                "number": table_num,
                "title": table_title,
                "headers": headers,
                "rows": rows,
                "row_count": len(rows)
            })

        return tables

    def _extract_examples(self, content: str) -> list:
        """Extract examples with separate problem and solution."""
        examples = []

        example_pattern = re.compile(
            r'(?:###?\s+)?(?:\*\*)?Example\s+(\d+\.\d+)(?:\*\*)?[:\s]*\n(.+?)(?=(?:###?\s+)?(?:\*\*)?Example\s+\d+\.\d+|## SUMMARY|## EXERCISES|$)',
            re.DOTALL | re.IGNORECASE
        )

        for match in example_pattern.finditer(content):
            num = match.group(1)
            full_content = match.group(2).strip()

            answer_match = re.search(
                r'\*\*(?:Answer|Solution)\*\*[:\s]*\n?(.+)',
                full_content,
                re.DOTALL | re.IGNORECASE
            )

            if answer_match:
                problem = full_content[:answer_match.start()].strip()
                solution = answer_match.group(1).strip()
            else:
                parts = re.split(r'\n(?:Answer|Solution)[:\s]*\n', full_content, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    problem = parts[0].strip()
                    solution = parts[1].strip()
                else:
                    problem = full_content
                    solution = ""

            problem = re.sub(r'^\*\*Answer\*\*.*', '', problem, flags=re.DOTALL).strip()

            examples.append({
                "number": num,
                "problem": problem,
                "solution": solution,
                "equations": self._extract_equations_from_text(full_content)
            })

        return examples

    def _extract_exercises(self, content: str) -> list:
        """Extract exercises with sub-parts."""
        exercises = []

        exercise_section = re.search(
            r'##\s+EXERCISES?\s*\n(.+?)(?=##\s+ADDITIONAL|##\s+APPENDIX|$)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not exercise_section:
            return exercises

        exercise_content = exercise_section.group(1)

        exercise_pattern = re.compile(
            r'(?:###?\s+)?(\d+\.\d+)\s*\n(.+?)(?=(?:###?\s+)?\d+\.\d+\s*\n|$)',
            re.DOTALL
        )

        for match in exercise_pattern.finditer(exercise_content):
            num = match.group(1)
            text = match.group(2).strip()

            sub_parts = []
            sub_pattern = re.compile(r'\(([a-z])\)\s*(.+?)(?=\([a-z]\)|$)', re.DOTALL)

            for sub_match in sub_pattern.finditer(text):
                sub_parts.append({
                    "label": sub_match.group(1),
                    "text": sub_match.group(2).strip()
                })

            if sub_parts:
                main_text_match = re.match(r'^(.+?)(?=\([a-z]\))', text, re.DOTALL)
                main_text = main_text_match.group(1).strip() if main_text_match else ""
            else:
                main_text = text

            exercises.append({
                "number": num,
                "text": main_text,
                "sub_parts": sub_parts,
                "has_sub_parts": len(sub_parts) > 0
            })

        return exercises

    def _extract_intext_questions(self, content: str) -> list:
        """Extract intext/check questions."""
        questions = []

        patterns = [
            r'(?:###?\s+)?\*\*(?:Intext\s+)?Question\s+(\d+\.\d+)\*\*[:\s]*(.+?)(?=\*\*(?:Intext\s+)?Question|\n##|$)',
            r'(?:Check|Think)\s*[:\?]\s*(.+?)(?=\n\n|\n##|$)',
            r'\?\s+(.+?)(?=\n\n|\n##|$)',
        ]

        for i, pattern in enumerate(patterns):
            for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                if i == 0:
                    questions.append({
                        "number": match.group(1),
                        "text": match.group(2).strip()
                    })
                else:
                    questions.append({
                        "number": f"Q{len(questions) + 1}",
                        "text": match.group(1).strip()
                    })

        return questions

    def _extract_summary(self, content: str) -> list:
        """Extract summary as clean bullet points."""
        summary_match = re.search(
            r'##\s+SUMMARY\s*\n(.+?)(?=##\s+EXERCISES|##\s+POINTS|$)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not summary_match:
            return []

        summary_text = summary_match.group(1)
        points = []

        bullet_pattern = re.compile(r'^\s*[\d\.\-\*]+\s*(.+?)(?=^\s*[\d\.\-\*]|\Z)', re.MULTILINE | re.DOTALL)

        for match in bullet_pattern.finditer(summary_text):
            point = match.group(1).strip()
            point = re.sub(r'\s+', ' ', point)
            if len(point) > 20:
                points.append(point)

        return points

    def _extract_equations_from_text(self, text: str) -> list:
        """Extract equations from a text block."""
        equations = []

        display_pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        for match in display_pattern.finditer(text):
            equations.append({
                "type": "display",
                "latex": match.group(1).strip()
            })

        inline_pattern = re.compile(r'(?<!\$)\$([^\$]+?)\$(?!\$)')
        for match in inline_pattern.finditer(text):
            latex = match.group(1).strip()
            if len(latex) > 2:
                equations.append({
                    "type": "inline",
                    "latex": latex
                })

        return equations

    def _extract_all_equations(self, content: str) -> list:
        """Extract all equations from content."""
        return self._extract_equations_from_text(content)

    def _extract_figures(self, content: str) -> list:
        """Extract figure references."""
        figures = []

        patterns = [
            r'\[?Fig(?:ure)?\.?\s*(\d+\.\d+)[:\s]*([^\]]+)\]?',
            r'!\[Fig(?:ure)?\.?\s*(\d+\.\d+)[:\s]*([^\]]+)\]',
        ]

        seen = set()
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                num = match.group(1)
                if num not in seen:
                    seen.add(num)
                    figures.append({
                        "number": num,
                        "caption": match.group(2).strip()
                    })

        return sorted(figures, key=lambda x: x["number"])

    def save(self, output_file: Path = None) -> Path:
        """Structure and save to JSON."""
        result = self.structure()

        if output_file is None:
            output_file = self.base_dir / "structured_physics.json"

        output_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return output_file


def structure_physics_chapter(book_code: str, base_dir: Path = None) -> dict:
    """Structure a physics chapter and save JSON."""
    structurer = PhysicsStructurer(book_code, base_dir)
    output_file = structurer.save()
    print(f"Structured: {output_file}")
    return structurer.structure()
