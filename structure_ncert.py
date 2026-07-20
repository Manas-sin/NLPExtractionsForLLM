#!/usr/bin/env python3
"""
NCERT Structure Extractor - converts raw page text to structured JSON.

Usage:
    python structure_ncert.py <book_code>

Example:
    python structure_ncert.py lech101

Input:
    extracted/<book_code>/pages.json (raw text per page)

Output:
    extracted/<book_code>/structured.json (structured chapter data)
"""

import json
import re
import sys
from pathlib import Path


# Unicode to LaTeX mappings
SUBSCRIPTS = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
    '₊': '+', '₋': '-', '₌': '=', '₍': '(', '₎': ')',
    'ₐ': 'a', 'ₑ': 'e', 'ₒ': 'o', 'ₓ': 'x', 'ₙ': 'n',
}

SUPERSCRIPTS = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
    '⁺': '+', '⁻': '-', '⁼': '=', '⁽': '(', '⁾': ')',
    'ⁿ': 'n', 'ⁱ': 'i',
}

GREEK_LETTERS = {
    'Δ': r'\Delta', 'δ': r'\delta',
    'π': r'\pi', 'Π': r'\Pi',
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma',
    'κ': r'\kappa', 'λ': r'\lambda', 'Λ': r'\Lambda',
    'ρ': r'\rho', 'σ': r'\sigma', 'Σ': r'\Sigma',
    'Ω': r'\Omega', 'ω': r'\omega',
    'χ': r'\chi', 'μ': r'\mu', 'η': r'\eta',
    'θ': r'\theta', 'Θ': r'\Theta',
    'ε': r'\epsilon', 'φ': r'\phi', 'Φ': r'\Phi',
}

ARROWS = {
    '→': r'\rightarrow',
    '⇌': r'\rightleftharpoons',
    '⟶': r'\longrightarrow',
    '↔': r'\leftrightarrow',
    '⇋': r'\leftrightharpoons',
}


def to_latex(text: str) -> str:
    """Convert chemical formulas, Greek letters, units to LaTeX."""
    if not text:
        return text

    result = text

    # Convert plain-text chemical formulas like H2O, CO2, NaCl, C6H12O6
    # Pattern: Capital letter, optional lowercase, then number(s), repeating
    def convert_plain_chemical(match):
        formula = match.group(0)
        # Convert numbers to subscripts: H2O -> H_{2}O
        latex_formula = re.sub(r'(\d+)', r'_{\1}', formula)
        return f'$\\ce{{{latex_formula}}}$'

    # Match chemical formulas: start with element, have numbers
    # Examples: H2O, CO2, NaCl, C6H12O6, CH3COOH, Ca(OH)2
    chemical_pattern = r'\b([A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*)\b'

    def smart_chemical_convert(match):
        formula = match.group(1)
        # Only convert if it has numbers (actual chemical formula)
        if re.search(r'\d', formula) and len(formula) >= 2:
            # Convert numbers to subscripts
            latex_formula = re.sub(r'(\d+)', r'_{\1}', formula)
            return f'$\\mathrm{{{latex_formula}}}$'
        return formula

    result = re.sub(chemical_pattern, smart_chemical_convert, result)

    # Convert Unicode subscripts/superscripts
    for uni, num in SUBSCRIPTS.items():
        result = result.replace(uni, f'$_{{{num}}}$')

    for uni, num in SUPERSCRIPTS.items():
        result = result.replace(uni, f'^{{{num}}}$')

    # Convert Greek letters
    for greek, latex in GREEK_LETTERS.items():
        if greek in result:
            result = result.replace(greek, f'${latex}$')

    # Convert arrows
    for arrow, latex in ARROWS.items():
        if arrow in result:
            result = result.replace(arrow, f'${latex}$')

    # Convert ion charges: Cu2+, Cl-, Na+
    result = re.sub(r'\$\\mathrm\{([A-Za-z]+)_\{(\d*)\}\}\$(\d*)([+-])',
                    r'$\\mathrm{\1_{\2}}^{\3\4}$', result)

    # Clean up adjacent math modes
    result = re.sub(r'\$\s*\$', ' ', result)

    # Convert common units to LaTeX
    result = re.sub(r'mol\s*L[-–]1', r'$\\text{mol L}^{-1}$', result)
    result = re.sub(r'g\s*mol[-–]1', r'$\\text{g mol}^{-1}$', result)
    result = re.sub(r'kg\s*mol[-–]1', r'$\\text{kg mol}^{-1}$', result)
    result = re.sub(r'K\s*kg\s*mol[-–]1', r'$\\text{K kg mol}^{-1}$', result)
    result = re.sub(r'(\d+)\s*mm\s*Hg', r'\1 $\\text{mm Hg}$', result)
    result = re.sub(r'(\d+)\s*kPa', r'\1 $\\text{kPa}$', result)
    result = re.sub(r'(\d+)\s*bar', r'\1 $\\text{bar}$', result)
    result = re.sub(r'(\d+)\s*K\b', r'\1 $\\text{K}$', result)

    return result


def latex_equation(expr: str) -> str:
    """Convert a mathematical expression to LaTeX equation format."""
    if not expr:
        return expr

    result = expr

    # Convert fractions: a/b -> \frac{a}{b}
    result = re.sub(r'(\w+)\s*/\s*(\w+)', r'\\frac{\1}{\2}', result)

    # Convert subscripts
    for uni, num in SUBSCRIPTS.items():
        result = result.replace(uni, f'_{{{num}}}')

    # Convert superscripts
    for uni, num in SUPERSCRIPTS.items():
        result = result.replace(uni, f'^{{{num}}}')

    # Convert Greek letters
    for greek, latex in GREEK_LETTERS.items():
        result = result.replace(greek, latex)

    # Convert arrows
    for arrow, latex in ARROWS.items():
        result = result.replace(arrow, latex)

    # Common chemistry notation
    result = re.sub(r'\(s\)', r'_{(s)}', result)
    result = re.sub(r'\(l\)', r'_{(l)}', result)
    result = re.sub(r'\(g\)', r'_{(g)}', result)
    result = re.sub(r'\(aq\)', r'_{(aq)}', result)

    return f'$${result}$$'


def extract_unit_info(text: str, book_code: str = None) -> dict:
    """Extract unit number and title from opening page."""
    from ncert_subjects import detect_subject, get_chapter_titles

    unit_num = None
    unit_title = None

    # Unit number: "Unit 1" or "Unit1" or "Chapter 1"
    m = re.search(r'(?:Unit|Chapter)\s*(\d{1,2})', text, re.IGNORECASE)
    if m:
        unit_num = int(m.group(1))

    # FIXED: Use book_code to get exact title instead of substring matching
    if book_code:
        subject_info = detect_subject(book_code)
        if subject_info["subject"] != "unknown":
            chapter_idx = subject_info["chapter"]
            class_num = subject_info["class"]
            if chapter_idx and class_num:
                titles = get_chapter_titles(subject_info["subject"], class_num)
                if 0 < chapter_idx <= len(titles):
                    unit_title = titles[chapter_idx - 1]

    # Fallback: search in text (only for subject-specific titles)
    if not unit_title and book_code:
        subject_info = detect_subject(book_code)
        if subject_info["class"]:
            titles = get_chapter_titles(subject_info["subject"], subject_info["class"])
            for title in titles:
                if title.lower() in text.lower():
                    unit_title = title
                    break

    # Last fallback: try regex
    if not unit_title:
        m = re.search(r'\n([A-Z][a-z]+(?:\s+[A-Za-z-]+)*)\n', text)
        if m:
            unit_title = m.group(1).strip()

    return {"unit_number": unit_num, "unit_title": unit_title}


def extract_objectives(text: str) -> list:
    """Extract learning objectives from opening page."""
    objectives = []

    # Find objectives section
    m = re.search(
        r'After studying this Unit,? you will be\s*able to\s*(.*?)(?=In normal life|In this Unit|\d+\.\d+\s+[A-Z])',
        text, re.DOTALL | re.IGNORECASE
    )

    if m:
        obj_text = m.group(1)
        # Split by bullet markers or semicolons
        items = re.split(r'[·•]\s*|;\s*(?=[a-z])', obj_text)
        for item in items:
            item = item.strip()
            item = re.sub(r'\s+', ' ', item)
            item = item.rstrip(';.')
            if item and len(item) > 10:
                objectives.append(item)

    return objectives


def extract_sections(pages: list, book_code: str = None) -> list:
    """Extract main sections (X.Y) and their content."""
    sections = []
    current_section = None

    # Combine all text
    all_text = "\n".join(p["text"] for p in pages)

    # Known main section titles for NCERT books (to avoid matching examples/exercises)
    known_section_keywords = [
        "Types", "Expressing", "Concentration", "Solubility", "Vapour", "Pressure",
        "Ideal", "Non-ideal", "Colligative", "Properties", "Abnormal", "Molar",
        "Introduction", "Structure", "Classification", "Bonding", "Reactions",
        "Laws", "Motion", "Energy", "Work", "Power", "Gravitation", "Waves",
        "Electric", "Magnetic", "Current", "Optics", "Atoms", "Nuclei",
        "Cell", "Tissue", "Organ", "System", "Reproduction", "Genetics",
        "Evolution", "Ecology", "Ecosystem", "Biodiversity",
        "Sets", "Relations", "Functions", "Trigonometric", "Complex", "Linear",
        "Matrices", "Determinants", "Continuity", "Derivatives", "Integrals",
        "Vectors", "Probability", "Statistics"
    ]

    # Find section headers: "1.1 Types of Solutions"
    section_pattern = re.compile(r'^(\d{1,2}\.\d{1,2})\s+([A-Z][a-z]+(?:\s+[a-zA-Z\-]+)*)', re.MULTILINE)

    matches = list(section_pattern.finditer(all_text))
    valid_matches = []

    for match in matches:
        section_num = match.group(1)
        section_title = match.group(2).strip()

        # Skip invalid section numbers
        try:
            major, minor = map(int, section_num.split('.'))
            if major == 0 or major > 20 or minor > 15:
                continue
        except:
            continue

        # Skip if it looks like an example, question, or calculation
        skip_words = [
            'Example', 'Calculate', 'Define', 'Give', 'What', 'Why', 'How', 'State',
            'An ', 'The ', 'Suggest', 'Write', 'Draw', 'Explain', 'Find', 'Determine',
            'Prove', 'Show', 'If ', 'A ', 'In ', 'For ', 'Which', 'When', 'Where'
        ]
        if any(section_title.startswith(w) for w in skip_words):
            continue

        # Only accept if title contains a known section keyword
        if not any(kw.lower() in section_title.lower() for kw in known_section_keywords):
            continue

        if len(section_title) < 4:
            continue

        valid_matches.append(match)

    matches = valid_matches

    for i, match in enumerate(matches):
        section_num = match.group(1)
        section_title = match.group(2).strip()

        # Clean up title - remove newlines, duplicates, and extra spaces
        section_title = re.sub(r'\s+', ' ', section_title).strip()

        # Clean up hyphenation issues first
        section_title = re.sub(r'-\s+', '-', section_title)  # "Non- ideal" -> "Non-ideal"

        # Remove duplicate phrases (handles "Ideal and Non-Ideal and Non-ideal")
        section_title = re.sub(r'(Ideal and Non-ideal)\s+(Ideal and Non-ideal|and Non-ideal)', r'\1', section_title, flags=re.IGNORECASE)
        section_title = re.sub(r'(\b[\w-]+(?:\s+[\w-]+){0,2})\s+\1', r'\1', section_title, flags=re.IGNORECASE)

        # Remove duplicate consecutive words
        words = section_title.split()
        cleaned_words = []
        for w in words:
            if not cleaned_words or w.lower() != cleaned_words[-1].lower():
                cleaned_words.append(w)
        section_title = ' '.join(cleaned_words)

        # Truncate at common stop words that indicate content start
        stop_patterns = ['We have', 'In this', 'You have', 'After studying', 'Intext', 'Calculate', 'is a']
        for stop in stop_patterns:
            if stop in section_title:
                section_title = section_title.split(stop)[0].strip()

        # Skip if title still looks like a question/example
        if any(section_title.startswith(w) for w in ['Vapour pressure of', 'Concentrated', 'Calculate']):
            continue

        # Get content until next section
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(all_text)
        content = all_text[start:end].strip()

        # Extract subsections (X.Y.Z)
        subsections = extract_subsections(content, section_num)

        # Extract examples in this section
        examples = extract_examples(content)

        # Extract intext questions
        intext_qs = extract_intext_questions(content)

        # Extract tables
        tables = extract_tables(content)

        # Extract figures
        figures = extract_figures(content, book_code)

        # Extract equations
        equations = extract_equations(content)

        # Extract key terms
        key_terms = extract_key_terms(content)

        sections.append({
            "number": section_num,
            "title": section_title,
            "subsections": subsections,
            "examples": examples,
            "intext_questions": intext_qs,
            "tables": tables,
            "figures": figures,
            "equations": equations,
            "key_terms": key_terms,
            "content_preview": to_latex(content[:500] + "..." if len(content) > 500 else content)
        })

    return sections


def extract_subsections(text: str, parent_num: str) -> list:
    """Extract subsections (X.Y.Z) within a section."""
    subsections = []

    # NCERT PDFs often have multi-line subsection titles like:
    # "1.3.1 Solubility of\na Solid in a\nLiquid"
    # We need to capture these properly

    # First, find all subsection numbers
    num_pattern = re.compile(rf'^({re.escape(parent_num)}\.\d+)\s+(\S+)', re.MULTILINE)
    matches = list(num_pattern.finditer(text))

    for i, match in enumerate(matches):
        sub_num = match.group(1)
        first_word = match.group(2)
        start = match.end()

        # Find end: next subsection number
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = start + 300

        # Extract title - collect words from the multiline title
        title_text = first_word + " " + text[start:end]
        lines = title_text.split('\n')

        title_words = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Stop conditions - body text indicators
            if re.match(r'^(Every|When|Let |The [a-z]|In [a-z]|At [a-z]|For [a-z]|It [a-z]|We [a-z]|This [a-z]|These|According|Consider|Assume|Many [a-z]|If [a-z]|A [a-z]|An [a-z]|Liquid solutions|Liquid-liquid)', line):
                break
            if re.match(r'^Fig\.?\s*\d', line):
                break
            if re.match(r'^\d+$', line) or re.match(r'^(Chemistry|Solutions|Physics)\s*\d*$', line):
                break
            # Stop if line has long lowercase text (body paragraph)
            if len(line) > 30:
                break
            # Check if next subsection number appears
            if re.match(rf'{re.escape(parent_num)}\.\d+\s+', line):
                break

            # Add words from this line
            words = line.split()
            for word in words:
                # Stop at obvious body text words
                if word.lower() in ['every', 'when', 'the', 'in', 'at', 'for', 'it', 'we', 'this', 'these', 'according', 'consider']:
                    if len(title_words) > 2:
                        break
                title_words.append(word)

            # Stop after getting enough words for a title
            if len(title_words) >= 8:
                break

        title = ' '.join(title_words)

        # Clean up
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'\s+(Fig\.?|Intext|Example|Calculate)\b.*$', '', title, flags=re.IGNORECASE)
        title = title.rstrip('.:,;')

        # Fix hyphenation issues
        title = re.sub(r'-\s+', '-', title)  # "Liquid- Liquid" -> "Liquid-Liquid"

        # Fix known truncated/malformed titles
        known_fixes = {
            "Raoult": "Raoult's Law as a special case of Henry's Law",
            "Raoult's Law as a special case of Henry's": "Raoult's Law as a special case of Henry's Law",
            "Raoult's Law as a special case of Henry's Law Law": "Raoult's Law as a special case of Henry's Law",
            "Vapour Pressure of Liquid- Liquid": "Vapour Pressure of Liquid-Liquid Solutions",
            "Vapour Pressure of Liquid-Liquid": "Vapour Pressure of Liquid-Liquid Solutions",
            "Osmosis and Osmotic": "Osmosis and Osmotic Pressure",
            "Solubility of a Solid Liquid": "Solubility of a Solid in a Liquid",
            "Solubility of a Gas Liquid": "Solubility of a Gas in a Liquid",
            "Vapour Pressure of Solutions of Solids Liquids": "Vapour Pressure of Solutions of Solids in Liquids",
            "Ideal": "Ideal Solutions",
            "Non-ideal": "Non-ideal Solutions",
            "Elevation of Boiling Point Solution": "Elevation of Boiling Point",
        }
        if title in known_fixes:
            title = known_fixes[title]

        # Generic fix: "X of a Y Z" -> "X of a Y in a Z" for solubility patterns
        title = re.sub(r'Solubility of a (\w+) (\w+)$', r'Solubility of a \1 in a \2', title)

        if title and len(title) > 3:
            subsections.append({
                "number": sub_num,
                "title": title
            })

    return subsections


def extract_examples(text: str) -> list:
    """Extract solved examples."""
    examples = []

    # Better pattern: Find "Example X.Y" markers first, then extract content between them
    example_markers = list(re.finditer(r'Example\s+(\d+\.\d+)', text, re.IGNORECASE))

    for i, marker in enumerate(example_markers):
        example_num = marker.group(1)
        start = marker.end()

        # Find end: next example or end of relevant content
        if i + 1 < len(example_markers):
            end = example_markers[i + 1].start()
        else:
            # Look for section end markers
            end_match = re.search(r'(?:Intext Questions|\d+\.\d+\.\d+\s+[A-Z]|\d+\.\d+\s+[A-Z][a-z]+\s+[A-Z])', text[start:])
            end = start + end_match.start() if end_match else len(text)

        content = text[start:end].strip()

        # Split into problem and solution
        solution_match = re.search(r'\bSolution\b', content, re.IGNORECASE)

        if solution_match:
            problem = content[:solution_match.start()].strip()
            solution = content[solution_match.end():].strip()
        else:
            # No explicit "Solution" marker - take first part as problem
            problem = content[:500]
            solution = ""

        # Clean up
        problem = re.sub(r'\s+', ' ', problem)[:500]
        solution = re.sub(r'\s+', ' ', solution)[:1000]

        # Remove page numbers and headers from problem
        problem = re.sub(r'^\d+\s+(Chemistry|Solutions|Physics|Biology|Maths)\s*', '', problem)
        problem = re.sub(r'\s+\d+\s*$', '', problem)

        if problem and len(problem) > 10:
            examples.append({
                "number": example_num,
                "problem": to_latex(problem),
                "solution": to_latex(solution)
            })

    return examples


def extract_intext_questions(text: str) -> list:
    """Extract intext questions."""
    questions = []

    # Find intext questions section
    m = re.search(r'Intext Questions\s*(.*?)(?=\d+\.\d+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+[a-z]|$)', text, re.DOTALL)

    if m:
        q_text = m.group(1)

        # Better pattern: question numbers are at start of line or after previous question
        # Only match X.Y where X is the chapter number (1-20) and Y is question number (1-20)
        q_pattern = re.compile(r'(?:^|\n)\s*(\d{1,2})\.(\d{1,2})\s+([A-Z].+?)(?=(?:^|\n)\s*\d{1,2}\.\d{1,2}\s+[A-Z]|$)', re.DOTALL)

        for qm in q_pattern.finditer(q_text):
            major = int(qm.group(1))
            minor = int(qm.group(2))

            # Validate: chapter number should be 1-20, question number 1-20
            if major < 1 or major > 20 or minor < 1 or minor > 20:
                continue

            # Skip if it looks like a decimal in text (e.g., "4.3 L" or "0.5 M")
            q_body = qm.group(3).strip()

            # Check if this is actually part of a sentence (preceded by quantity)
            # These patterns indicate it's a decimal, not a question number
            if re.match(r'^[LMgm]\s', q_body) or re.match(r'^(of|in|to|at|for)\s', q_body, re.IGNORECASE):
                continue

            q_num = f"{major}.{minor}"
            q_body = re.sub(r'\s+', ' ', q_body)[:500]

            if q_body and len(q_body) > 10:
                questions.append({
                    "number": q_num,
                    "text": to_latex(q_body)
                })

    return questions


def extract_tables(text: str) -> list:
    """Extract table references."""
    tables = []

    pattern = re.compile(r'Table\s+(\d+\.\d+):\s*(.+?)(?=\n)', re.IGNORECASE)

    for match in pattern.finditer(text):
        tables.append({
            "number": match.group(1),
            "title": match.group(2).strip()
        })

    return tables


def extract_figures(text: str, book_code: str = None) -> list:
    """Extract figure references with diagram paths."""
    figures = []

    pattern = re.compile(r'Fig\.\s*(\d+\.\d+):\s*(.+?)(?=\n|Fig\.)', re.IGNORECASE)

    for match in pattern.finditer(text):
        fig_num = match.group(1)
        fig_data = {
            "number": fig_num,
            "caption": match.group(2).strip()
        }

        # Add diagram path if it exists
        if book_code:
            diagram_path = Path("extracted") / book_code / "diagrams" / f"fig{fig_num.replace('.', '_')}_clean.png"
            if diagram_path.exists():
                fig_data["diagram"] = str(diagram_path)

            # Also add original extract path
            original_path = Path("extracted") / book_code / "figures" / f"fig{fig_num.replace('.', '_')}.png"
            if original_path.exists():
                fig_data["original"] = str(original_path)

        figures.append(fig_data)

    return figures


def extract_equations(text: str) -> list:
    """Extract numbered equations."""
    equations = []

    # Pattern for equation numbers like (1.1), (1.2), (1.10) etc.
    # Can be at end of line or followed by text
    pattern = re.compile(r'(.{10,200}?)\s*\((\d+\.\d+)\)', re.MULTILINE)

    seen_nums = set()

    for match in pattern.finditer(text):
        eq_text = match.group(1).strip()
        eq_num = match.group(2)

        # Validate equation number: X.Y where X is 1-20, Y is 1-50
        try:
            major, minor = map(int, eq_num.split('.'))
            if major < 1 or major > 20 or minor < 1 or minor > 50:
                continue
        except:
            continue

        # Skip duplicates
        if eq_num in seen_nums:
            continue

        # Must contain = or mathematical content
        if not re.search(r'[=∝∞×÷+−]|\\frac|mol|pressure|fraction', eq_text, re.IGNORECASE):
            continue

        # Clean up: get just the equation part (last line if multiline)
        lines = eq_text.split('\n')
        eq_text = lines[-1].strip() if lines else eq_text

        # Remove leading text that's not equation
        eq_text = re.sub(r'^.*?(?=[A-Za-z]\s*=|\$)', '', eq_text)

        if eq_text and len(eq_text) > 5:
            seen_nums.add(eq_num)
            equations.append({
                "number": eq_num,
                "expression": eq_text[:200],
                "latex": latex_equation(eq_text[:200])
            })

    return equations


def extract_key_terms(text: str) -> list:
    """Extract key terms (bold definitions)."""
    terms = []

    patterns = [
        r'is called\s+([a-z][a-z\s]+)',
        r'is known as\s+([a-z][a-z\s]+)',
        r'are called\s+([a-z][a-z\s]+)',
        r"([A-Z][a-z]+'s\s+law)",
        r"([A-Z][a-z]+'s\s+principle)",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            term = match.group(1).strip()
            if term and len(term) > 2:
                terms.append(term)

    return list(set(terms))  # Remove duplicates


def extract_summary(pages: list) -> str:
    """Extract chapter summary."""
    all_text = "\n".join(p["text"] for p in pages)

    m = re.search(r'Summary\s*(.*?)(?=Exercises|$)', all_text, re.DOTALL | re.IGNORECASE)

    if m:
        summary = m.group(1).strip()
        summary = re.sub(r'\s+', ' ', summary)
        return summary

    return ""


def extract_exercises(pages: list) -> list:
    """Extract end-of-chapter exercises."""
    exercises = []
    all_text = "\n".join(p["text"] for p in pages)

    m = re.search(r'Exercises\s*(.*?)(?=Answers to Some Intext Questions|$)', all_text, re.DOTALL)

    if m:
        ex_text = m.group(1)

        # Better pattern: only match X.Y at line start where X is chapter (1-20), Y is exercise (1-50)
        pattern = re.compile(r'(?:^|\n)\s*(\d{1,2})\.(\d{1,2})\s+([A-Z].+?)(?=(?:^|\n)\s*\d{1,2}\.\d{1,2}\s+[A-Z]|$)', re.DOTALL)

        for match in pattern.finditer(ex_text):
            major = int(match.group(1))
            minor = int(match.group(2))

            # Validate: chapter 1-20, exercise 1-50
            if major < 1 or major > 20 or minor < 1 or minor > 50:
                continue

            ex_body = match.group(3).strip()

            # Skip if looks like a decimal in text (quantity before it)
            if re.match(r'^[LMgm%°]\s', ex_body) or re.match(r'^(of|in|to|at|for|and)\s', ex_body, re.IGNORECASE):
                continue

            # Skip pure numbers or very short text
            if re.match(r'^[\d\.\s]+$', ex_body) or len(ex_body) < 10:
                continue

            ex_num = f"{major}.{minor}"
            ex_body = re.sub(r'\s+', ' ', ex_body)[:500]

            # Clean trailing page numbers
            ex_body = re.sub(r'\s+\d+\s+(Chemistry|Solutions|Physics)\s*$', '', ex_body)

            if ex_body and len(ex_body) > 10:
                exercises.append({
                    "number": ex_num,
                    "text": to_latex(ex_body)
                })

    return exercises


def extract_answers(pages: list) -> dict:
    """Extract answers to intext questions."""
    answers = {}
    all_text = "\n".join(p["text"] for p in pages)

    m = re.search(r'Answers to Some Intext Questions\s*(.*?)$', all_text, re.DOTALL)

    if m:
        ans_text = m.group(1)
        # Find individual answers
        pattern = re.compile(r'(\d+\.\d+)\s+(.+?)(?=\d+\.\d+|$)', re.DOTALL)

        for match in pattern.finditer(ans_text):
            ans_num = match.group(1)
            ans_body = match.group(2).strip()
            ans_body = re.sub(r'\s+', ' ', ans_body)[:200]

            if ans_body:
                answers[ans_num] = to_latex(ans_body)

    return answers


def structure_book(book_code: str, physics_mode: bool = False):
    """Main function to structure a book."""
    if physics_mode:
        base_dir = Path("extracted_physics") / book_code
    else:
        base_dir = Path("extracted") / book_code

    pages_file = base_dir / "pages.json"
    chapter_complete_file = base_dir / "chapter_complete.md"

    if not pages_file.exists():
        print(f"Error: {pages_file} not found")
        print("Run extract_ncert.py (or extract_physics.py) first to extract raw pages.")
        sys.exit(1)

    # Load raw pages for page count and basic structure
    pages = json.loads(pages_file.read_text(encoding="utf-8"))
    print(f"Loaded {len(pages)} pages from {pages_file}")

    # PREFER chapter_complete.md (vision extraction) over pages.json (raw OCR)
    # Vision extraction has much better quality for equations, tables, sections
    use_vision = False
    if chapter_complete_file.exists():
        vision_text = chapter_complete_file.read_text(encoding="utf-8")
        if len(vision_text) > 1000:  # Valid vision output
            use_vision = True
            print(f"Using vision extraction from {chapter_complete_file.name} ({len(vision_text):,} chars)")
            # Create synthetic pages list from chapter_complete.md
            pages_for_parsing = [{"page": 1, "text": vision_text}]
        else:
            pages_for_parsing = pages
    else:
        pages_for_parsing = pages

    # Get first page/vision text for unit info
    if use_vision:
        first_page_text = vision_text[:5000]  # First part of vision text
    else:
        first_page_text = pages[0]["text"] if pages else ""

    # Extract structured data - use pages_for_parsing (vision or raw)
    unit_info = extract_unit_info(first_page_text, book_code)
    objectives = extract_objectives(first_page_text)
    sections = extract_sections(pages_for_parsing, book_code)
    summary = extract_summary(pages_for_parsing)
    exercises = extract_exercises(pages_for_parsing)
    answers = extract_answers(pages_for_parsing)

    # Build structured output
    structured = {
        "book_code": book_code,
        "unit_number": unit_info["unit_number"],
        "unit_title": unit_info["unit_title"],
        "total_pages": len(pages),
        "objectives": objectives,
        "sections": sections,
        "summary": summary[:2000] if summary else None,
        "exercises": exercises,
        "answers": answers,
        "statistics": {
            "section_count": len(sections),
            "example_count": sum(len(s.get("examples", [])) for s in sections),
            "table_count": sum(len(s.get("tables", [])) for s in sections),
            "figure_count": sum(len(s.get("figures", [])) for s in sections),
            "equation_count": sum(len(s.get("equations", [])) for s in sections),
            "exercise_count": len(exercises),
            "intext_question_count": sum(len(s.get("intext_questions", [])) for s in sections)
        }
    }

    # Save structured output
    output_file = base_dir / "structured.json"
    output_file.write_text(
        json.dumps(structured, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Create FINAL combined output with everything
    diagrams_dir = base_dir / "diagrams"

    # Get all diagram paths
    diagram_files = {}
    if diagrams_dir.exists():
        for f in diagrams_dir.glob("*.png"):
            # Extract figure number from filename like fig1_1_clean.png
            match = re.search(r'fig(\d+)_(\d+)', f.name)
            if match:
                fig_num = f"{match.group(1)}.{match.group(2)}"
                diagram_files[fig_num] = str(f)

    final_output = {
        "book_code": book_code,
        "unit_number": unit_info["unit_number"],
        "unit_title": unit_info["unit_title"],
        "total_pages": len(pages),
        "objectives": objectives,

        # Full page content
        "pages": [
            {
                "page": p["page"],
                "book_page": p.get("book_page"),
                "text": p["text"]
            }
            for p in pages
        ],

        # Structured sections with full content
        "sections": sections,

        # All diagrams with paths
        "diagrams": [
            {
                "figure": fig_num,
                "path": path,
                "filename": Path(path).name
            }
            for fig_num, path in sorted(diagram_files.items())
        ],

        "summary": summary[:2000] if summary else None,
        "exercises": exercises,
        "answers": answers,

        "statistics": {
            "section_count": len(sections),
            "example_count": sum(len(s.get("examples", [])) for s in sections),
            "table_count": sum(len(s.get("tables", [])) for s in sections),
            "figure_count": sum(len(s.get("figures", [])) for s in sections),
            "diagram_count": len(diagram_files),
            "equation_count": sum(len(s.get("equations", [])) for s in sections),
            "exercise_count": len(exercises),
            "intext_question_count": sum(len(s.get("intext_questions", [])) for s in sections)
        }
    }

    # Save final combined output
    final_file = base_dir / "final_output.json"
    final_file.write_text(
        json.dumps(final_output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Final combined output saved to: {final_file}")

    print(f"\nStructured output saved to: {output_file}")
    print(f"\nUnit {structured['unit_number']}: {structured['unit_title']}")
    print(f"  Sections: {structured['statistics']['section_count']}")
    print(f"  Examples: {structured['statistics']['example_count']}")
    print(f"  Tables: {structured['statistics']['table_count']}")
    print(f"  Figures: {structured['statistics']['figure_count']}")
    print(f"  Equations: {structured['statistics']['equation_count']}")
    print(f"  Exercises: {structured['statistics']['exercise_count']}")
    print(f"  Intext Questions: {structured['statistics']['intext_question_count']}")

    return structured


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python structure_ncert.py <book_code> [--physics]")
        print("Examples:")
        print("  python structure_ncert.py lech101           # Chemistry")
        print("  python structure_ncert.py keph101 --physics # Physics")
        sys.exit(1)

    book_code = sys.argv[1]
    physics_mode = "--physics" in sys.argv
    structure_book(book_code, physics_mode)
