"""Unified NCERT structurer - config-driven extraction for all subjects."""

import json
import re
from pathlib import Path
from typing import Optional


class UnifiedStructurer:
    """Config-driven structurer that works for all NCERT subjects."""

    def __init__(self, book_code: str, base_dir: Path = None):
        self.book_code = book_code
        self.subject = self._detect_subject()
        self.base_dir = base_dir or Path("data/extracted") / book_code
        self.config = self._load_config()
        self.chapter_num = self._extract_chapter_number()

    def _detect_subject(self) -> str:
        """Detect subject from book code prefix."""
        prefix = self.book_code[:4].lower()
        mapping = {
            "lech": "chemistry",
            "keph": "physics",
            "kebo": "biology",
            "kemh": "maths",
        }
        return mapping.get(prefix, "unknown")

    def _extract_chapter_number(self) -> int:
        """Extract chapter number from book code."""
        try:
            return int(self.book_code[-2:])
        except ValueError:
            return 1

    def _load_config(self) -> dict:
        """Load base config + subject-specific overrides."""
        config_dir = Path("config")

        base_config = {}
        base_file = config_dir / "ncert_extraction_rules.json"
        if base_file.exists():
            base_config = json.loads(base_file.read_text(encoding="utf-8"))

        subject_file = config_dir / f"{self.subject}_extraction_rules.json"
        if subject_file.exists():
            subject_config = json.loads(subject_file.read_text(encoding="utf-8"))
            base_config = self._merge_configs(base_config, subject_config)

        return base_config

    def _merge_configs(self, base: dict, override: dict) -> dict:
        """Deep merge override into base config."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def structure(self) -> dict:
        """Parse content into structured JSON."""
        content = self._load_content()
        content = self._clean_content(content)

        result = {
            "book_code": self.book_code,
            "subject": self.subject,
            "class": self._detect_class(),
            "unit_number": self.chapter_num,
            "unit_title": self._extract_title(content),
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

        result["statistics"] = self._compute_statistics(result)
        return result

    def _load_content(self) -> str:
        """Load content from markdown file."""
        possible_files = ["content.md", "chapter_complete.md"]
        for fname in possible_files:
            fpath = self.base_dir / fname
            if fpath.exists():
                return fpath.read_text(encoding="utf-8")
        raise FileNotFoundError(f"No content file found in {self.base_dir}")

    def _clean_content(self, content: str) -> str:
        """Clean raw extracted content."""
        content = re.sub(r'^```markdown\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        content = re.sub(r'^```\s*\n', '', content)

        content = re.sub(
            r'^(\d+\.\d+)\n\1\s+([A-Z][A-Za-z\s\-]+?)\n\2\n([a-z])',
            r'\1 \2\3',
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
        """Detect class (11 or 12) from book code."""
        if self.book_code[4] == '1':
            return 11
        elif self.book_code[4] == '2':
            return 12
        return 12

    def _get_section_titles(self) -> dict:
        """Get correct section titles for known books."""
        section_titles = {
            "lech102": {
                "2.1": "Electrochemical Cells",
                "2.2": "Galvanic Cells",
                "2.3": "Nernst Equation",
                "2.4": "Conductance of Electrolytic Solutions",
                "2.5": "Electrolytic Cells and Electrolysis",
                "2.6": "Batteries",
                "2.7": "Fuel Cells",
                "2.8": "Corrosion",
            },
            "lech101": {
                "1.1": "Types of Solutions",
                "1.2": "Expressing Concentration of Solutions",
                "1.3": "Solubility",
                "1.4": "Vapour Pressure of Liquid Solutions",
                "1.5": "Ideal and Non-ideal Solutions",
                "1.6": "Colligative Properties and Determination of Molar Mass",
                "1.7": "Abnormal Molar Masses",
            },
            "lech103": {
                "3.1": "Rate of a Chemical Reaction",
                "3.2": "Factors Influencing Rate of a Reaction",
                "3.3": "Integrated Rate Equations",
                "3.4": "Temperature Dependence of the Rate of a Reaction",
                "3.5": "Collision Theory of Chemical Reactions",
            },
        }
        return section_titles.get(self.book_code, {})

    def _extract_title(self, content: str) -> str:
        """Extract chapter/unit title."""
        titles = {
            "lech101": "Solutions",
            "lech102": "Electrochemistry",
            "lech103": "Chemical Kinetics",
            "lech104": "The d- and f-Block Elements",
            "lech105": "Coordination Compounds",
            "keph101": "Units and Measurement",
            "keph102": "Motion in a Straight Line",
            "keph103": "Motion in a Plane",
            "keph104": "Laws of Motion",
        }
        if self.book_code in titles:
            return titles[self.book_code]

        patterns = [
            r'CHAPTER\s+\w+\s*\n+([A-Z][A-Z\s]+?)(?:\n|$)',
            r'^#\s+([A-Z][A-Za-z\s,\-]+?)(?:\n|$)',
            r'^##\s+([A-Z][A-Za-z\s,\-]+?)(?:\n|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'^Chapter\s+\w+\s*', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s+', ' ', title).strip()
                if 3 < len(title) < 60:
                    return title.title()
        return "Unknown"

    def _extract_qr_code(self, content: str) -> str:
        """Extract QR code reference."""
        pattern = r'(\d{5}[A-Z]{2}\d{2})'
        match = re.search(pattern, content)
        return match.group(1) if match else ""

    def _extract_objectives(self, content: str) -> list:
        """Extract learning objectives."""
        objectives = []

        start_patterns = [
            r'After studying this (?:Unit|chapter),?\s*you will be\s*able to',
            r'After studying this Unit,\s*you will be\s*\nable to',
        ]

        start_idx = None
        for pattern in start_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                start_idx = match.end()
                break

        if start_idx is None:
            return objectives

        end_patterns = [
            r'\n\d+\.\d+\s+[A-Z]',
            r'In normal',
            r'In this Unit',
            r'In this chapter',
            r'\n[A-Z][a-z]+\s+is\s+the\s+study',
        ]

        end_idx = len(content)
        for pattern in end_patterns:
            match = re.search(pattern, content[start_idx:])
            if match:
                end_idx = min(end_idx, start_idx + match.start())

        objectives_text = content[start_idx:end_idx]

        bullet_pattern = re.compile(r'[·•]\s*(.+?)(?=[·•]|\Z)', re.DOTALL)
        for match in bullet_pattern.finditer(objectives_text):
            obj = match.group(1).strip()
            obj = re.sub(r'\s+', ' ', obj)
            obj = re.sub(r'\*\*', '', obj)
            obj = obj.rstrip(';.')
            if len(obj) > 10 and not obj.startswith('After'):
                objectives.append(obj)

        if not objectives:
            lines = objectives_text.split('\n')
            current = []
            for line in lines:
                line = line.strip()
                if line.startswith(('·', '•', '-')):
                    if current:
                        obj = ' '.join(current).strip()
                        obj = re.sub(r'\s+', ' ', obj).rstrip(';.')
                        if len(obj) > 10:
                            objectives.append(obj)
                    current = [re.sub(r'^[·•\-]\s*', '', line)]
                elif line and current:
                    current.append(line)
            if current:
                obj = ' '.join(current).strip()
                obj = re.sub(r'\s+', ' ', obj).rstrip(';.')
                if len(obj) > 10:
                    objectives.append(obj)

        return objectives

    def _extract_hook_quote(self, content: str) -> str:
        """Extract motivational/hook quote."""
        patterns = [r'"([^"]{20,200})"', r'"([^"]{20,200})"']
        for pattern in patterns:
            match = re.search(pattern, content[:2000])
            if match:
                return match.group(1).strip()
        return ""

    def _extract_introduction(self, content: str) -> str:
        """Extract introduction paragraph."""
        section_match = re.search(r'\d+\.\d+\s+[A-Z]', content)
        if section_match:
            intro_text = content[:section_match.start()]
            lines = [l.strip() for l in intro_text.split('\n') if l.strip()]
            for line in reversed(lines):
                if len(line) > 100 and not line.startswith(('·', '•', 'After')):
                    return line
        return ""

    def _extract_sections(self, content: str) -> list:
        """Extract sections with hierarchy."""
        sections = []

        # End markers - use word boundary patterns to avoid TOC matches
        # Physics uses ALL CAPS "SUMMARY" at end, not lowercase "Summary" in TOC
        end_idx = len(content)
        if self.subject == "physics":
            # For physics: match ALL CAPS only (no IGNORECASE flag)
            end_markers = [
                r'(?:^|\n)SUMMARY\s*(?:\n|$)',
                r'(?:^|\n)EXERCISES\s*(?:\n|$)',
            ]
            for marker in end_markers:
                match = re.search(marker, content)  # No IGNORECASE
                if match:
                    end_idx = min(end_idx, match.start())
        else:
            end_markers = [
                r'(?:^|\n)(?:##\s+)?SUMMARY\s*(?:\n|$)',
                r'(?:^|\n)(?:##\s+)?EXERCISES?\s*(?:\n|$)',
            ]
            for marker in end_markers:
                match = re.search(marker, content, re.IGNORECASE)
                if match:
                    end_idx = min(end_idx, match.start())

        main_content = content[:end_idx]

        # Physics: ALL CAPS titles, sometimes split across lines (1.3\nTITLE)
        # Biology: ALL CAPS major sections
        # Chemistry: Title Case
        if self.subject == "physics":
            # First try: title on same line
            section_pattern = re.compile(
                r'^(\d+\.\d+)\s+([A-Z][A-Z\s\-,]+?)(?:\n|$)',
                re.MULTILINE
            )
            # Second pass: title on next line (PDF fragmentation)
            split_line_pattern = re.compile(
                r'^(\d+\.\d+)\s*\n([A-Z][A-Z][A-Z\s\-,]+?)(?:\n|$)',
                re.MULTILINE
            )
        elif self.subject == "biology":
            section_pattern = re.compile(
                r'^(\d+\.\d+)\s+([A-Z][A-Z\s\-,]+?)(?:\n|$)',
                re.MULTILINE
            )
            split_line_pattern = None
        else:
            section_pattern = re.compile(
                r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s\-,]+?)(?:\n|$)',
                re.MULTILINE
            )
            split_line_pattern = None

        matches = []
        seen_sections = set()

        # Collect all patterns to search
        patterns_to_search = [section_pattern]
        if split_line_pattern:
            patterns_to_search.append(split_line_pattern)

        for pattern in patterns_to_search:
            for match in pattern.finditer(main_content):
                number = match.group(1)
                title = match.group(2).strip()

                parts = number.split('.')
                if len(parts) != 2:
                    continue
                try:
                    major, minor = int(parts[0]), int(parts[1])
                    if major != self.chapter_num or minor > 20:
                        continue
                    if minor > 10:
                        continue
                except ValueError:
                    continue

                if number in seen_sections:
                    continue

                if len(title) < 3 or len(title) > 50:
                    continue

                question_starters = (
                    'Calculate', 'Find', 'What', 'How', 'Why', 'When', 'Where',
                    'Which', 'Determine', 'Suggest', 'Consult', 'Write', 'Explain',
                    'Define', 'Describe', 'Compare', 'Give', 'Can', 'Is', 'Are',
                    'Do', 'Does', 'Will', 'Would', 'Should', 'Could', 'If', 'The',
                    'An', 'A', 'In', 'At', 'On', 'For', 'To', 'From', 'With'
                )
                if title.split()[0] in question_starters:
                    continue

                if len(title.split()) > 6:
                    continue

                # Physics/Biology: ALL CAPS titles; Chemistry: Title Case
                if self.subject in ("physics", "biology"):
                    if not re.match(r'^[A-Z][A-Z]', title):
                        continue
                else:
                    if not re.match(r'^[A-Z][a-z]', title):
                        continue

                seen_sections.add(number)
                matches.append(match)

        # Sort matches by position in document
        matches.sort(key=lambda m: m.start())

        for i, match in enumerate(matches):
            number = match.group(1)
            title = match.group(2).strip()

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(main_content)
            section_content = main_content[start:end].strip()

            # Join continuation lines for title (handles PDF fragmentation)
            lines = section_content.split('\n')
            for line in lines[:6]:  # Check up to 6 lines for physics multi-line titles
                line = line.strip()
                if not line:
                    continue
                # Physics: ALL CAPS words or multi-word ALL CAPS lines
                if self.subject == "physics":
                    # Check if line is ALL CAPS (title continuation)
                    if re.match(r'^[A-Z][A-Z\s]+$', line) and len(line) < 35:
                        title = title + ' ' + line
                    # Connector words
                    elif line in ('AND', 'OF', 'IN', 'THE', 'FOR', 'TO'):
                        title = title + ' ' + line
                    else:
                        break
                # Chemistry: Title Case continuation
                elif re.match(r'^[A-Z][a-z]+$', line) and len(line) < 20:
                    if line.lower() not in title.lower():
                        title = title + ' ' + line
                elif line and re.match(r'^(Cells|Equation|Solutions|Electrolysis)$', line):
                    if line.lower() not in title.lower():
                        title = title + ' ' + line
                else:
                    break

            # For physics, clean title - remove duplicate adjacent words
            if self.subject == "physics":
                words = title.split()
                clean_words = []
                for w in words:
                    if not clean_words or w != clean_words[-1]:
                        clean_words.append(w)
                title = ' '.join(clean_words)

            # Clean up duplicate words in title
            words = title.split()
            clean_words = []
            for w in words:
                if not clean_words or w.lower() != clean_words[-1].lower():
                    clean_words.append(w)
            title = ' '.join(clean_words)

            # Use known correct title if available
            known_titles = self._get_section_titles()
            if number in known_titles:
                title = known_titles[number]

            section_content = re.sub(r'^Intext Questions.*?(?=\d+\.\d+\s+[A-Z]|\Z)', '',
                                    section_content, flags=re.DOTALL | re.MULTILINE)

            subsections = self._extract_subsections(section_content, number)
            examples = self._extract_section_examples(section_content)

            sections.append({
                "number": number,
                "title": title,
                "content": section_content[:3000],
                "content_truncated": len(section_content) > 3000,
                "subsections": subsections,
                "examples": examples,
            })

        return sections

    def _extract_subsections(self, content: str, parent_number: str) -> list:
        """Extract subsections within a section."""
        subsections = []
        pattern = re.compile(
            rf'^({re.escape(parent_number)}\.\d+)\s+([A-Z][A-Za-z\s\-,]+?)(?:\n|$)',
            re.MULTILINE
        )
        for match in pattern.finditer(content):
            subsections.append({
                "number": match.group(1),
                "title": match.group(2).strip()
            })
        return subsections

    def _extract_section_examples(self, content: str) -> list:
        """Extract examples within a section."""
        examples = []
        pattern = re.compile(
            r'Example\s+(\d+\.\d+)\s*\n(.+?)(?=Example\s+\d+\.\d+|\Z)',
            re.DOTALL | re.IGNORECASE
        )
        for match in pattern.finditer(content):
            num = match.group(1)
            full = match.group(2).strip()
            problem, solution = self._split_problem_solution(full)
            examples.append({
                "number": num,
                "problem": problem[:1000],
                "solution": solution[:2000],
            })
        return examples

    def _split_problem_solution(self, text: str) -> tuple:
        """Split example text into problem and solution."""
        patterns = [
            r'Solution[:\s]*\n',
            r'\*\*Solution\*\*[:\s]*\n',
            r'Answer[:\s]*\n',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                problem = text[:match.start()].strip()
                solution = text[match.end():].strip()
                return re.sub(r'\s+', ' ', problem), re.sub(r'\s+', ' ', solution)
        return re.sub(r'\s+', ' ', text), ""

    def _extract_key_terms(self, content: str) -> list:
        """Extract key terms and definitions."""
        terms = []
        seen = set()

        patterns = [
            (r'is called\s+([a-z][a-z\s]+)', 'called'),
            (r'is known as\s+([a-z][a-z\s]+)', 'known_as'),
            (r'are called\s+([a-z][a-z\s]+)', 'called'),
            (r'termed as\s+([a-z][a-z\s]+)', 'termed'),
        ]

        for pattern, ptype in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                term = match.group(1).strip().rstrip('.,;')
                term = re.sub(r'\s+', ' ', term)
                if 3 <= len(term) <= 50 and term.lower() not in seen:
                    seen.add(term.lower())
                    ctx_start = max(0, match.start() - 100)
                    ctx_end = min(len(content), match.end() + 50)
                    terms.append({
                        "term": term,
                        "context": re.sub(r'\s+', ' ', content[ctx_start:ctx_end]).strip(),
                    })
        return terms

    def _extract_laws_principles(self, content: str) -> list:
        """Extract laws, principles, named equations."""
        laws = []
        seen = set()
        skip_words = {'the', 'this', 'that', 'using', 'above', 'following', 'same'}

        patterns = [
            r"([A-Z][a-z]+'s\s+law)",
            r"([A-Z][a-z]+\s+law)",
            r"([A-Z][a-z]+'s\s+equation)",
            r"([A-Z][a-z]+\s+equation)",
            r"([A-Z][a-z]+'s\s+principle)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                law = match.group(1).strip()
                first_word = law.split()[0].lower().rstrip("'s")
                if first_word in skip_words or law.lower() in seen:
                    continue
                seen.add(law.lower())

                ctx_start = max(0, match.start() - 200)
                ctx_end = min(len(content), match.end() + 300)
                laws.append({
                    "name": law,
                    "context": re.sub(r'\s+', ' ', content[ctx_start:ctx_end]).strip()
                })
        return laws

    def _extract_equations(self, content: str) -> list:
        """Extract chemical and mathematical equations."""
        equations = []
        seen = set()

        chem_pattern = re.compile(r'([^\n→⇌]{2,80})\s*(→|⇌)\s*([^\n]{2,80})')
        for match in chem_pattern.finditer(content):
            reactants = match.group(1).strip()
            arrow = match.group(2)
            products = match.group(3).strip()

            full_eq = f"{reactants} {arrow} {products}"
            if full_eq in seen:
                continue

            has_chem = any(c in full_eq for c in ['₂', '₃', '⁺', '⁻', '(s)', '(l)', '(g)', '(aq)'])
            has_elem = bool(re.search(r'[A-Z][a-z]?\d|[A-Z][a-z]?[₀-₉]', full_eq))

            if has_chem or has_elem:
                seen.add(full_eq)
                eq_num_match = re.search(r'\((\d+\.\d+)\)\s*$', products)
                eq_num = eq_num_match.group(1) if eq_num_match else ""
                equations.append({
                    "type": "chemical",
                    "number": eq_num,
                    "full": full_eq,
                    "reversible": arrow == '⇌',
                })

        math_pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        for match in math_pattern.finditer(content):
            equations.append({
                "type": "mathematical",
                "latex": match.group(1).strip(),
                "display": True,
            })

        return equations

    def _extract_tables(self, content: str) -> list:
        """Extract tables with headers and rows."""
        tables = []
        seen = set()

        pattern = re.compile(r'Table\s+(\d+\.\d+)[:\s]*([^\n]+)', re.IGNORECASE)
        for match in pattern.finditer(content):
            table_num = match.group(1)

            # Only include tables from current chapter
            parts = table_num.split('.')
            try:
                chapter = int(parts[0])
                if chapter != self.chapter_num:
                    continue
            except (ValueError, IndexError):
                continue

            if table_num in seen:
                continue
            seen.add(table_num)

            title = match.group(2).strip()[:150]
            start = match.end()
            table_content = content[start:start + 3000]

            headers, rows = self._parse_markdown_table(table_content)

            tables.append({
                "number": table_num,
                "title": title or f"Table {table_num}",
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
            })

        return tables

    def _parse_markdown_table(self, content: str) -> tuple:
        """Parse markdown table into headers and rows."""
        headers = []
        rows = []
        in_table = False

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('|') and '|' in line[1:]:
                in_table = True
                cells = [c.strip() for c in line.split('|')[1:-1] if c.strip()]
                if not headers:
                    headers = cells
                elif all(set(c) <= {'-', ':', ' '} for c in cells):
                    continue
                else:
                    row = {headers[j] if j < len(headers) else f"col_{j}": cell
                           for j, cell in enumerate(cells)}
                    if any(row.values()):
                        rows.append(row)
            elif in_table and line and not line.startswith('|'):
                break

        return headers, rows

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
                figures.append({
                    "number": fig_num,
                    "caption": re.sub(r'\s+', ' ', match.group(2).strip())[:200],
                })

        return sorted(figures, key=lambda x: [int(p) for p in x["number"].split('.')])

    def _extract_examples(self, content: str) -> list:
        """Extract all solved examples."""
        examples = []

        # Physics uses inline "Example 1.1 <problem> Answer <solution>"
        # Chemistry uses "Example 1.1\n<problem>\nSolution\n<solution>"
        if self.subject == "physics":
            pattern = re.compile(
                r'Example\s+(\d+\.\d+)\s+(.+?)(?=Example\s+\d+\.\d+|SUMMARY|EXERCISES|⊳|\n\d+\.\d+\.\d+\s|$)',
                re.DOTALL | re.IGNORECASE
            )
        else:
            pattern = re.compile(
                r'Example\s+(\d+\.\d+)\s*\n(.+?)(?=Example\s+\d+\.\d+|##\s+SUMMARY|##\s+EXERCISES|Intext Questions|$)',
                re.DOTALL | re.IGNORECASE
            )

        for match in pattern.finditer(content):
            num = match.group(1)
            full = match.group(2).strip()
            problem, solution = self._split_problem_solution(full)
            examples.append({
                "number": num,
                "problem": problem[:1000],
                "solution": solution[:2000],
            })

        return examples

    def _extract_intext_questions(self, content: str) -> list:
        """Extract intext questions."""
        questions = []
        seen = set()

        intext_starts = [m.end() for m in re.finditer(r'Intext Questions?\s*\n', content, re.IGNORECASE)]

        for start_idx in intext_starts:
            search_region = content[start_idx:start_idx + 1500]

            end_patterns = [
                rf'\n{self.chapter_num}\.\d+\s+[A-Z][a-z]+[a-z]+[a-z]+\s+[A-Z]',
                r'\n##',
                r'\nSummary\n',
                r'\nWe have assumed',
                r'\nThe potential',
                r'\n[A-Z][a-z]+ is the study',
            ]
            end_idx = len(search_region)
            for pattern in end_patterns:
                match = re.search(pattern, search_region)
                if match:
                    end_idx = min(end_idx, match.start())

            block = search_region[:end_idx]

            q_pattern = re.compile(
                rf'^({self.chapter_num}\.\d+)\s+(.+?)(?=^{self.chapter_num}\.\d+\s+|\Z)',
                re.MULTILINE | re.DOTALL
            )

            for match in q_pattern.finditer(block):
                num = match.group(1)
                text = match.group(2).strip()
                text = re.sub(r'\s+', ' ', text)

                if num in seen:
                    continue

                parts = num.split('.')
                try:
                    minor = int(parts[1])
                    if minor > 15:
                        continue
                except (ValueError, IndexError):
                    continue

                question_words = ('How', 'What', 'Why', 'Can', 'Calculate', 'Suggest',
                                  'Consult', 'Write', 'Explain', 'Define', 'If', 'The')
                if not any(text.startswith(w) for w in question_words):
                    continue

                if len(text) > 10 and len(text) < 400:
                    seen.add(num)
                    questions.append({
                        "number": num,
                        "text": text[:300],
                    })

        return questions

    def _extract_summary(self, content: str) -> list:
        """Extract summary points."""
        points = []

        match = re.search(
            r'(?:##\s+)?SUMMARY\s*\n(.+?)(?=##\s+EXERCISES|##\s+POINTS|$)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not match:
            return points

        summary_text = match.group(1)

        bullet_pattern = re.compile(r'[•·\-\*]\s*(.+?)(?=[•·\-\*]|\n\n|$)', re.DOTALL)
        for m in bullet_pattern.finditer(summary_text):
            point = re.sub(r'\s+', ' ', m.group(1).strip())
            if len(point) > 20:
                points.append(point)

        if not points:
            for line in summary_text.split('\n'):
                line = re.sub(r'^\d+\.\s*', '', line.strip())
                if len(line) > 20:
                    points.append(line)

        return points

    def _extract_exercises(self, content: str) -> list:
        """Extract end-of-chapter exercises."""
        exercises = []

        # Find EXERCISES section
        exercise_match = re.search(r'(?:^|\n)(?:##\s+)?E\s*XERCISES?\s*(?:\n|$)', content, re.IGNORECASE)
        if not exercise_match:
            exercise_match = re.search(r'(?:^|\n)(?:##\s+)?EXERCISES?\s*(?:\n|$)', content, re.IGNORECASE)

        if exercise_match:
            start_idx = exercise_match.end()
        else:
            # Fallback: search after Summary
            summary_match = re.search(r'(?:^|\n)(?:##\s+)?Summary\s*(?:\n|$)', content, re.IGNORECASE)
            if summary_match:
                start_idx = summary_match.end()
            else:
                last_section = None
                for m in re.finditer(rf'^{self.chapter_num}\.\d+\s+[A-Z]', content, re.MULTILINE):
                    last_section = m
                start_idx = last_section.end() if last_section else len(content) // 2

        end_idx = len(content)
        search_region = content[start_idx:end_idx]

        # Biology uses simple numbering (1, 2, 3...); Physics/Chemistry uses X.Y
        if self.subject == "biology":
            q_pattern = re.compile(
                r'^(\d+)\.\s+(.+?)(?=^\d+\.\s+|\Z)',
                re.MULTILINE | re.DOTALL
            )
        else:
            q_pattern = re.compile(
                rf'^({self.chapter_num}\.\d+)\s+(.+?)(?=^{self.chapter_num}\.\d+\s+|\Z)',
                re.MULTILINE | re.DOTALL
            )

        seen = set()
        for m in q_pattern.finditer(search_region):
            num = m.group(1)
            text = m.group(2).strip()

            if num in seen:
                continue

            if 'Intext Question' in text[:50]:
                continue

            if len(text) < 20:
                continue

            first_word = text.split()[0] if text.split() else ''
            question_starters = ('Arrange', 'Given', 'Depict', 'Calculate', 'Write', 'In',
                                 'The', 'A', 'How', 'Three', 'Using', 'Predict', 'Conductivity',
                                 'Why', 'What', 'Suggest', 'Consider', 'Define', 'Explain',
                                 'Can', 'Try', 'Illustrate', 'Fill', 'State', 'Note',
                                 'Which', 'One', 'Guess', 'Precise', 'Sun', 'Answer')
            if not any(text.startswith(w) for w in question_starters):
                continue

            sub_parts = []
            sub_pattern = re.compile(r'\(([ivx]+|[a-z])\)\s*(.+?)(?=\([ivx]+\)|\([a-z]\)|$)', re.DOTALL)
            for sub in sub_pattern.finditer(text):
                sub_parts.append({
                    "label": sub.group(1),
                    "text": re.sub(r'\s+', ' ', sub.group(2).strip())[:500]
                })

            if sub_parts:
                main_match = re.match(r'^(.+?)(?=\([ivx]+\)|\([a-z]\))', text, re.DOTALL)
                main_text = re.sub(r'\s+', ' ', main_match.group(1).strip()) if main_match else ""
            else:
                main_text = re.sub(r'\s+', ' ', text)

            if len(main_text) < 15:
                continue

            seen.add(num)
            exercises.append({
                "number": num,
                "text": main_text[:1000],
                "sub_parts": sub_parts,
            })

        return exercises

    def _extract_answers(self, content: str) -> dict:
        """Extract answers to intext questions."""
        answers = {}

        match = re.search(
            r'Answers?\s+to\s+(?:Some\s+)?Intext\s+Questions?\s*\n(.+?)$',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not match:
            return answers

        answer_content = match.group(1)
        pattern = re.compile(r'(\d+\.\d+)\s+(.+?)(?=\d+\.\d+\s+|$)', re.DOTALL)
        for m in pattern.finditer(answer_content):
            num = m.group(1)
            ans = re.sub(r'\s+', ' ', m.group(2).strip())
            answers[num] = ans

        return answers

    def _compute_statistics(self, result: dict) -> dict:
        """Compute extraction statistics."""
        return {
            "section_count": len(result["sections"]),
            "objective_count": len(result["objectives"]),
            "key_term_count": len(result["key_terms"]),
            "law_count": len(result["laws_principles"]),
            "equation_count": len(result["equations"]),
            "table_count": len(result["tables"]),
            "figure_count": len(result["figures"]),
            "example_count": len(result["examples"]),
            "intext_question_count": len(result["intext_questions"]),
            "exercise_count": len(result["exercises"]),
            "summary_point_count": len(result["summary"]),
        }

    def save(self, output_file: Path = None) -> Path:
        """Structure and save to JSON."""
        result = self.structure()

        if output_file is None:
            output_file = self.base_dir / "final_output.json"

        output_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return output_file


def structure_chapter(book_code: str, base_dir: Path = None) -> dict:
    """Structure any NCERT chapter using unified structurer."""
    structurer = UnifiedStructurer(book_code, base_dir)
    output_file = structurer.save()
    print(f"Structured: {output_file}")
    return structurer.structure()
