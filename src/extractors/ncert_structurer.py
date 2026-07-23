"""NCERT content structurer - extracts structured data from raw text using schema rules."""

import json
import re
from pathlib import Path


class NCERTStructurer:
    """Structures NCERT chapter content into clean JSON following the schema."""

    def __init__(self, book_code: str, subject: str, base_dir: Path = None):
        self.book_code = book_code
        self.subject = subject.lower()
        self.base_dir = base_dir or Path("data/extracted") / book_code
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        """Load extraction rules from config."""
        rules_file = Path("config/ncert_extraction_rules.json")
        if rules_file.exists():
            return json.loads(rules_file.read_text(encoding="utf-8"))
        return {}

    def structure(self) -> dict:
        """Parse content.md into structured JSON."""
        md_file = self.base_dir / "content.md"
        if not md_file.exists():
            raise FileNotFoundError(f"No content.md at {md_file}")

        content = md_file.read_text(encoding="utf-8")
        content = self._clean_content(content)

        result = {
            "book_code": self.book_code,
            "subject": self.subject,
            "class": self._detect_class(),
            "unit_number": self._extract_unit_number(content),
            "unit_title": self._extract_unit_title(content),
            "qr_code": self._extract_qr_code(content),
            "objectives": self._extract_objectives(content),
            "hook_quote": self._extract_hook_quote(content),
            "introduction": self._extract_introduction(content),
            "sections": self._extract_sections(content),
            "key_terms": self._extract_key_terms(content),
            "laws_principles": self._extract_laws_principles(content),
            "equations": self._extract_equations(content),
            "tables": self._extract_tables(content),
            "figures": self._extract_figures(content),
            "examples": self._extract_examples(content),
            "intext_questions": self._extract_intext_questions(content),
            "summary": self._extract_summary(content),
            "exercises": self._extract_exercises(content),
            "answers": self._extract_answers(content),
        }

        result["statistics"] = {
            "section_count": len(result["sections"]),
            "key_term_count": len(result["key_terms"]),
            "law_count": len(result["laws_principles"]),
            "equation_count": len(result["equations"]),
            "table_count": len(result["tables"]),
            "figure_count": len(result["figures"]),
            "example_count": len(result["examples"]),
            "intext_question_count": len(result["intext_questions"]),
            "exercise_count": len(result["exercises"]),
        }

        return result

    def _clean_content(self, content: str) -> str:
        """Clean raw extracted content."""
        content = re.sub(r'^```markdown\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        content = re.sub(r'\n---\n## Page \d+.*?\n', '\n', content)
        content = re.sub(r'\n---\n## Page \d+ \(unnumbered\)\n', '\n', content)

        content = re.sub(
            r'^(\d+\.\d+)\n\1\s+([A-Z][A-Za-z\s\-]+?)\n\2\n([a-z][a-z\s]+)',
            r'\1 \2\3',
            content,
            flags=re.MULTILINE
        )

        content = re.sub(
            r'^(\d+\.\d+)\n([A-Z][A-Za-z]+(?:\s+(?:of|and|the|in|a))?)\n([A-Z][A-Za-z]+)',
            r'\1 \2 \3',
            content,
            flags=re.MULTILINE
        )

        content = re.sub(
            r'^(\d+\.\d+\s+[A-Z][A-Za-z\s]+)-\n([a-z][a-z\s]+)',
            r'\1-\2',
            content,
            flags=re.MULTILINE
        )

        content = re.sub(
            r'^(\d+\.\d+)\n([A-Z][A-Za-z\s\-]+?)$',
            r'\1 \2',
            content,
            flags=re.MULTILINE
        )

        return content.strip()

    def _detect_class(self) -> int:
        """Detect class from book code."""
        if 'lech1' in self.book_code or 'keph1' in self.book_code:
            return 11 if '11' in self.book_code or self.book_code[4] == '1' else 12
        if '11' in self.book_code:
            return 11
        if '12' in self.book_code:
            return 12
        return 12

    def _extract_unit_number(self, content: str) -> int:
        """Extract unit/chapter number."""
        word_to_num = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15
        }

        patterns = [
            (r'Chapter\s+(\w+)', True),
            (r'Unit\s*(\d{1,2})', False),
            (r'Chapter\s*(\d{1,2})', False),
        ]
        for pattern, is_word in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                val = match.group(1).lower()
                if is_word and val in word_to_num:
                    return word_to_num[val]
                try:
                    return int(val)
                except ValueError:
                    continue
        try:
            return int(self.book_code[-2:])
        except ValueError:
            return 1

    def _extract_unit_title(self, content: str) -> str:
        """Extract unit/chapter title."""
        specific_titles = {
            'lech101': 'Solutions',
            'lech102': 'Electrochemistry',
            'lech103': 'Chemical Kinetics',
            'lech104': 'The d- and f-Block Elements',
            'lech105': 'Coordination Compounds',
            'keph101': 'Units and Measurement',
        }
        if self.book_code in specific_titles:
            return specific_titles[self.book_code]

        patterns = [
            r'CHAPTER\s+\w+\s*\n+([A-Z][A-Z\s]+?)(?:\n|$)',
            r'(The\s+d-\s*and\s*f-\s*Block\s+Elements)',
            r'\n(Coordination\s+Compounds)',
            r'\n(Haloalkanes\s+and\s+Haloarenes)',
            r'\n(Chemical\s+Kinetics)',
            r'\n(Electrochemistry)',
            r'\n(Solutions)\s*\n',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'\s+', ' ', title)
                title = title.title()
                if 3 < len(title) < 60 and not title.startswith('After'):
                    return title

        return "Unknown"

    def _extract_qr_code(self, content: str) -> str:
        """Extract QR code reference."""
        pattern = r'(\d{5}[A-Z]{2}\d{2})'
        match = re.search(pattern, content)
        return match.group(1) if match else ""

    def _extract_objectives(self, content: str) -> list:
        """Extract learning objectives."""
        objectives = []

        start_match = re.search(
            r'After studying this (?:Unit|chapter),?\s*you will be\s*able to',
            content,
            re.IGNORECASE
        )
        if not start_match:
            return objectives

        start_idx = start_match.end()
        end_patterns = [r'In normal', r'In this Unit', r'In this chapter', r'Solutions\s*\n', r'Almost all']

        end_idx = len(content)
        for pattern in end_patterns:
            match = re.search(pattern, content[start_idx:])
            if match:
                end_idx = min(end_idx, start_idx + match.start())

        objectives_text = content[start_idx:end_idx]
        lines = objectives_text.split('\n')
        current_obj = []

        for line in lines:
            line_stripped = line.strip()

            if line_stripped in ('·**', '•**', '·', '•'):
                if current_obj:
                    obj = ' '.join(current_obj).strip()
                    obj = re.sub(r"['']\*\*\s*s", "'s", obj)
                    obj = obj.rstrip(';.')
                    if len(obj) > 10:
                        objectives.append(obj)
                    current_obj = []
            elif line_stripped:
                clean = re.sub(r'^[•·\-\*]+\s*', '', line_stripped)
                clean = re.sub(r'\*\*', '', clean)
                if clean:
                    current_obj.append(clean)

        if current_obj:
            obj = ' '.join(current_obj).strip()
            obj = re.sub(r"['']\*\*\s*s", "'s", obj)
            obj = obj.rstrip(';.')
            if len(obj) > 10:
                objectives.append(obj)

        return objectives

    def _extract_hook_quote(self, content: str) -> str:
        """Extract motivational/hook quote."""
        patterns = [
            r'"([^"]{20,200})"',
            r'"([^"]{20,200})"',
        ]
        for pattern in patterns:
            match = re.search(pattern, content[:2000])
            if match:
                return match.group(1).strip()
        return ""

    def _extract_introduction(self, content: str) -> str:
        """Extract introduction paragraph."""
        section_match = re.search(r'\d+\.\d+\s+[A-Z]', content)
        if section_match:
            intro_end = section_match.start()
            intro_text = content[:intro_end]
            intro_text = re.sub(r'^.*?(After studying|In normal|In this)', '', intro_text, flags=re.DOTALL)
            lines = [l.strip() for l in intro_text.split('\n') if l.strip()]
            for line in reversed(lines):
                if len(line) > 100 and not line.startswith('•'):
                    return line
        return ""

    def _extract_sections(self, content: str) -> list:
        """Extract sections with hierarchy."""
        sections = []

        exercise_match = re.search(r'(?:^|\n)(?:##\s+)?EXERCISES?\s*(?:\n|$)', content, re.IGNORECASE)
        summary_match = re.search(r'(?:^|\n)(?:##\s+)?SUMMARY\s*(?:\n|$)', content, re.IGNORECASE)

        end_idx = len(content)
        if summary_match:
            end_idx = min(end_idx, summary_match.start())
        if exercise_match:
            end_idx = min(end_idx, exercise_match.start())

        main_content = content[:end_idx]

        main_pattern = re.compile(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s\-,]+?)(?:\n|$)', re.MULTILINE)
        sub_pattern = re.compile(r'^(\d+\.\d+\.\d+)\s+([A-Z][A-Za-z][A-Za-z\s\-,]+?)(?:\n|$)', re.MULTILINE)

        chapter_num = self._extract_unit_number(content)

        valid_main_matches = []
        for match in main_pattern.finditer(main_content):
            number = match.group(1)
            title = match.group(2).strip()

            parts = number.split('.')
            if len(parts) == 2:
                try:
                    major = int(parts[0])
                    minor = int(parts[1])
                    if major != chapter_num:
                        continue
                    if minor > 15:
                        continue
                except ValueError:
                    continue

            if len(title) < 3 or len(title) > 80:
                continue

            if re.match(r'^(Calculate|Find|What|How|Why|When|Where|Which|Determine|An?\s|The\s|If\s)', title):
                continue

            if len(title.split()) > 10:
                continue

            valid_main_matches.append(match)

        main_matches = valid_main_matches
        sub_matches = list(sub_pattern.finditer(main_content))

        for i, match in enumerate(main_matches):
            number = match.group(1)
            title = match.group(2).strip()

            start = match.end()
            end = main_matches[i + 1].start() if i + 1 < len(main_matches) else len(main_content)
            section_content = main_content[start:end].strip()

            subsections = []
            for sub in sub_matches:
                if sub.start() > match.start() and sub.start() < end:
                    sub_num = sub.group(1)
                    if sub_num.startswith(number + '.'):
                        subsections.append({
                            "number": sub_num,
                            "title": sub.group(2).strip()
                        })

            section_content = re.sub(r'^\d+\.\d+\.\d+\s+[A-Z].*$', '', section_content, flags=re.MULTILINE)
            section_content = section_content.strip()

            sections.append({
                "number": number,
                "title": title,
                "content": section_content[:3000] if len(section_content) > 3000 else section_content,
                "content_truncated": len(section_content) > 3000,
                "subsections": subsections
            })

        return sections

    def _extract_key_terms(self, content: str) -> list:
        """Extract key terms and their definitions."""
        key_terms = []
        seen = set()

        patterns = [
            (r'is called\s+([a-z][a-z\s]+)', 'called'),
            (r'is known as\s+([a-z][a-z\s]+)', 'known_as'),
            (r'are called\s+([a-z][a-z\s]+)', 'called'),
            (r'termed as\s+([a-z][a-z\s]+)', 'termed'),
            (r'referred to as\s+([a-z][a-z\s]+)', 'referred'),
        ]

        for pattern, pattern_type in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                term = match.group(1).strip()
                term = re.sub(r'\s+', ' ', term)
                term = term.rstrip('.,;')

                if len(term) < 3 or len(term) > 50:
                    continue
                if term.lower() in seen:
                    continue

                seen.add(term.lower())

                context_start = max(0, match.start() - 150)
                context_end = min(len(content), match.end() + 50)
                context = content[context_start:context_end]
                context = re.sub(r'\s+', ' ', context).strip()

                key_terms.append({
                    "term": term,
                    "context": context,
                    "pattern_type": pattern_type
                })

        return key_terms

    def _extract_laws_principles(self, content: str) -> list:
        """Extract laws, principles, and named equations."""
        laws = []
        seen = set()

        skip_words = {'the', 'this', 'that', 'using', 'above', 'following', 'same', 'general', 'basic'}

        patterns = [
            r"([A-Z][a-z]+'s\s+law)",
            r"([A-Z][a-z]+\s+law)",
            r"([A-Z][a-z]+'s\s+equation)",
            r"([A-Z][a-z]+\s+equation)",
            r"([A-Z][a-z]+'s\s+principle)",
            r"([A-Z][a-z]+\s+principle)",
            r"([A-Z][a-z]+'s\s+rule)",
            r"([A-Z][a-z]+\s+rule)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                law = match.group(1).strip()

                first_word = law.split()[0].lower().rstrip("'s")
                if first_word in skip_words:
                    continue

                if law.lower() in seen:
                    continue
                seen.add(law.lower())

                context_start = max(0, match.start() - 200)
                context_end = min(len(content), match.end() + 300)
                context = content[context_start:context_end]

                statement = ""
                stmt_patterns = [
                    rf'{re.escape(law)}[:\s]+([^.]+\.)',
                    rf'{re.escape(law)}.*?states that[:\s]+([^.]+\.)',
                ]
                for sp in stmt_patterns:
                    stmt_match = re.search(sp, context, re.IGNORECASE)
                    if stmt_match:
                        statement = stmt_match.group(1).strip()
                        break

                laws.append({
                    "name": law,
                    "statement": statement,
                    "context": re.sub(r'\s+', ' ', context).strip()
                })

        return laws

    def _extract_equations(self, content: str) -> list:
        """Extract chemical and mathematical equations."""
        equations = []
        seen = set()

        chem_pattern = re.compile(r'([^\n→⇌]+?)\s*(→|⇌)\s*([^\n]+)')

        for match in chem_pattern.finditer(content):
            reactants = match.group(1).strip()
            arrow = match.group(2)
            products = match.group(3).strip()

            if len(reactants) < 2 or len(products) < 2:
                continue
            if len(reactants) > 100 or len(products) > 100:
                continue

            full_eq = f"{reactants} {arrow} {products}"
            if full_eq in seen:
                continue

            has_chem_notation = any(c in full_eq for c in ['₂', '₃', '₄', '⁺', '⁻', '(s)', '(l)', '(g)', '(aq)', 'CH', 'OH', 'CO', 'NH', 'Solute', 'Solvent'])
            has_elements = bool(re.search(r'[A-Z][a-z]?\d|[A-Z][a-z]?[₀-₉]|[A-Z]{2,}', full_eq))

            if has_chem_notation or has_elements:
                seen.add(full_eq)

                eq_num_match = re.search(r'\((\d+\.\d+)\)\s*$', products)
                eq_num = eq_num_match.group(1) if eq_num_match else ""
                if eq_num_match:
                    products = products[:eq_num_match.start()].strip()

                equations.append({
                    "type": "chemical",
                    "number": eq_num,
                    "reactants": reactants,
                    "products": products,
                    "reversible": arrow == '⇌',
                    "full": f"{reactants} {arrow} {products}"
                })

        numbered_eq = re.compile(r'([A-Za-z₀₁₂₃₄₅₆₇₈₉\s\+\-\=\(\)\/\*×÷]+?)\s*[\.…]+\s*\((\d+\.\d+)\)')
        for match in numbered_eq.finditer(content):
            eq_text = match.group(1).strip()
            eq_num = match.group(2)
            if '=' in eq_text and len(eq_text) > 5:
                equations.append({
                    "type": "mathematical",
                    "number": eq_num,
                    "expression": eq_text,
                    "display": True
                })

        math_pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        for match in math_pattern.finditer(content):
            equations.append({
                "type": "mathematical_latex",
                "latex": match.group(1).strip(),
                "display": True
            })

        inline_pattern = re.compile(r'(?<!\$)\$([^\$]+?)\$(?!\$)')
        for match in inline_pattern.finditer(content):
            latex = match.group(1).strip()
            if len(latex) > 3 and '=' in latex:
                equations.append({
                    "type": "mathematical_latex",
                    "latex": latex,
                    "display": False
                })

        return equations

    def _extract_tables(self, content: str) -> list:
        """Extract tables with headers and rows."""
        tables = []
        seen = set()

        table_pattern = re.compile(
            r'Table\s+(\d+\.\d+):\s*([A-Z][^\n]+)',
            re.IGNORECASE
        )

        for match in table_pattern.finditer(content):
            table_num = match.group(1)
            if table_num in seen:
                continue
            seen.add(table_num)

            table_title = match.group(2).strip()
            table_title = re.sub(r'^[:\s]+', '', table_title)

            start = match.end()
            table_content = content[start:start + 3000]

            headers = []
            rows = []
            in_table = False

            lines = table_content.split('\n')
            for line in lines:
                line = line.strip()

                if line.startswith('|') and '|' in line[1:]:
                    in_table = True
                    cells = [c.strip() for c in line.split('|')[1:-1] if c.strip()]

                    if not headers:
                        headers = cells
                    elif all(set(c) <= {'-', ':', ' '} for c in cells):
                        continue
                    else:
                        row = {}
                        for j, cell in enumerate(cells):
                            key = headers[j] if j < len(headers) else f"col_{j}"
                            row[key] = cell
                        if any(row.values()):
                            rows.append(row)

                elif in_table and line and not line.startswith('|'):
                    if re.match(r'^[A-Z]', line) or line.startswith('#'):
                        break

            if not headers and not rows:
                raw_lines = []
                for line in lines[:50]:
                    line = line.strip()
                    if not line:
                        if raw_lines:
                            break
                        continue
                    if re.match(r'^\d+\.\d+\s+[A-Z]', line):
                        break
                    if line.startswith('Fig.') or line.startswith('Example'):
                        break
                    raw_lines.append(line)

                if raw_lines:
                    tables.append({
                        "number": table_num,
                        "title": table_title[:150] if table_title else f"Table {table_num}",
                        "raw_content": '\n'.join(raw_lines),
                        "format": "unstructured"
                    })
                    continue

            if headers:
                tables.append({
                    "number": table_num,
                    "title": table_title[:150] if table_title else f"Table {table_num}",
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows),
                    "format": "structured"
                })

        return tables

    def _extract_figures(self, content: str) -> list:
        """Extract figure references with captions."""
        figures = []
        seen = set()

        patterns = [
            r'Fig\.?\s*(\d+\.\d+)[:\s]*([^\n]+)',
            r'Figure\s*(\d+\.\d+)[:\s]*([^\n]+)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                fig_num = match.group(1)
                if fig_num in seen:
                    continue
                seen.add(fig_num)

                caption = match.group(2).strip()
                caption = re.sub(r'\s+', ' ', caption)
                caption = caption[:200] if len(caption) > 200 else caption

                figures.append({
                    "number": fig_num,
                    "caption": caption
                })

        return sorted(figures, key=lambda x: [int(p) for p in x["number"].split('.')])

    def _extract_examples(self, content: str) -> list:
        """Extract solved examples with problem and solution."""
        examples = []

        example_pattern = re.compile(
            r'Example\s+(\d+\.\d+)\s*\n(.+?)(?=Example\s+\d+\.\d+|##\s+SUMMARY|##\s+EXERCISES|Intext Questions|$)',
            re.DOTALL | re.IGNORECASE
        )

        for match in example_pattern.finditer(content):
            num = match.group(1)
            full_content = match.group(2).strip()

            solution_patterns = [
                r'Solution[:\s]*\n(.+)',
                r'\*\*Solution\*\*[:\s]*\n(.+)',
                r'Answer[:\s]*\n(.+)',
            ]

            problem = full_content
            solution = ""

            for sp in solution_patterns:
                sol_match = re.search(sp, full_content, re.DOTALL | re.IGNORECASE)
                if sol_match:
                    problem = full_content[:sol_match.start()].strip()
                    solution = sol_match.group(1).strip()
                    break

            problem = re.sub(r'\s+', ' ', problem)
            solution = re.sub(r'\s+', ' ', solution)

            examples.append({
                "number": num,
                "problem": problem[:1000] if len(problem) > 1000 else problem,
                "solution": solution[:2000] if len(solution) > 2000 else solution,
            })

        return examples

    def _extract_intext_questions(self, content: str) -> list:
        """Extract intext questions."""
        questions = []

        intext_pattern = re.compile(
            r'Intext Questions?\s*\n(.+?)(?=\d+\.\d+\s+[A-Z][a-z]+\s+[A-Z]|##|Example|$)',
            re.DOTALL | re.IGNORECASE
        )

        for block_match in intext_pattern.finditer(content):
            block = block_match.group(1)

            q_pattern = re.compile(r'(\d+\.\d+)\s+(.+?)(?=\d+\.\d+\s+|$)', re.DOTALL)
            for match in q_pattern.finditer(block):
                num = match.group(1)
                text = match.group(2).strip()
                text = re.sub(r'\s+', ' ', text)

                if len(text) > 10:
                    questions.append({
                        "number": num,
                        "text": text[:500] if len(text) > 500 else text
                    })

        return questions

    def _extract_summary(self, content: str) -> list:
        """Extract summary points."""
        points = []

        summary_match = re.search(
            r'(?:##\s+)?SUMMARY\s*\n(.+?)(?=##\s+EXERCISES|##\s+POINTS|$)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not summary_match:
            return points

        summary_text = summary_match.group(1)

        bullet_pattern = re.compile(r'[•·\-\*]\s*(.+?)(?=[•·\-\*]|\n\n|$)', re.DOTALL)
        for match in bullet_pattern.finditer(summary_text):
            point = match.group(1).strip()
            point = re.sub(r'\s+', ' ', point)
            if len(point) > 20:
                points.append(point)

        if not points:
            for line in summary_text.split('\n'):
                line = line.strip()
                line = re.sub(r'^\d+\.\s*', '', line)
                if len(line) > 20:
                    points.append(line)

        return points

    def _extract_exercises(self, content: str) -> list:
        """Extract end-of-chapter exercises."""
        exercises = []

        exercise_match = re.search(
            r'(?:##\s+)?EXERCISES?\s*\n(.+?)(?=##\s+ADDITIONAL|##\s+ANSWERS|Answers to|$)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not exercise_match:
            return exercises

        exercise_content = exercise_match.group(1)

        q_pattern = re.compile(r'(\d+\.\d+)\s+(.+?)(?=\d+\.\d+\s+|$)', re.DOTALL)

        for match in q_pattern.finditer(exercise_content):
            num = match.group(1)
            text = match.group(2).strip()

            sub_parts = []
            sub_pattern = re.compile(r'\(([a-z])\)\s*(.+?)(?=\([a-z]\)|$)', re.DOTALL)
            for sub in sub_pattern.finditer(text):
                sub_parts.append({
                    "label": sub.group(1),
                    "text": re.sub(r'\s+', ' ', sub.group(2).strip())
                })

            if sub_parts:
                main_match = re.match(r'^(.+?)(?=\([a-z]\))', text, re.DOTALL)
                main_text = main_match.group(1).strip() if main_match else ""
            else:
                main_text = text

            main_text = re.sub(r'\s+', ' ', main_text)

            exercises.append({
                "number": num,
                "text": main_text[:1000] if len(main_text) > 1000 else main_text,
                "sub_parts": sub_parts
            })

        return exercises

    def _extract_answers(self, content: str) -> dict:
        """Extract answers to intext questions."""
        answers = {}

        answer_match = re.search(
            r'Answers?\s+to\s+(?:Some\s+)?Intext\s+Questions?\s*\n(.+?)$',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not answer_match:
            return answers

        answer_content = answer_match.group(1)

        ans_pattern = re.compile(r'(\d+\.\d+)\s+(.+?)(?=\d+\.\d+\s+|$)', re.DOTALL)
        for match in ans_pattern.finditer(answer_content):
            num = match.group(1)
            ans = match.group(2).strip()
            ans = re.sub(r'\s+', ' ', ans)
            answers[num] = ans

        return answers

    def save(self, output_file: Path = None) -> Path:
        """Structure and save to JSON."""
        result = self.structure()

        if output_file is None:
            output_file = self.base_dir / "structured.json"

        output_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return output_file


def structure_ncert_chapter(book_code: str, subject: str, base_dir: Path = None) -> dict:
    """Structure an NCERT chapter and save JSON."""
    structurer = NCERTStructurer(book_code, subject, base_dir)
    output_file = structurer.save()
    print(f"Structured: {output_file}")
    return structurer.structure()
