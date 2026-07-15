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
    from ncert_subjects import detect_subject, get_all_chapter_titles

    unit_num = None
    unit_title = None

    # Unit number: "Unit 1" or "Unit1" or "Chapter 1"
    m = re.search(r'(?:Unit|Chapter)\s*(\d{1,2})', text, re.IGNORECASE)
    if m:
        unit_num = int(m.group(1))

    # Get all known titles from all subjects
    known_titles = get_all_chapter_titles()

    for title in known_titles:
        if title.lower() in text.lower():
            unit_title = title
            break

    # Fallback: try regex
    if not unit_title:
        m = re.search(r'\n([A-Z][a-z]+)\n', text)
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

    # Find section headers: "1.1 Types of Solutions"
    section_pattern = re.compile(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s\-]+?)(?=\n)', re.MULTILINE)

    matches = list(section_pattern.finditer(all_text))

    for i, match in enumerate(matches):
        section_num = match.group(1)
        section_title = match.group(2).strip()

        # Skip if it looks like an example or question number
        if 'Example' in section_title or len(section_title) < 3:
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

    # Pattern for X.Y.Z headers
    pattern = re.compile(
        rf'^({re.escape(parent_num)}\.\d+)\s+([A-Z][A-Za-z\s\-]+?)(?=\n)',
        re.MULTILINE
    )

    for match in pattern.finditer(text):
        subsections.append({
            "number": match.group(1),
            "title": match.group(2).strip()
        })

    return subsections


def extract_examples(text: str) -> list:
    """Extract solved examples."""
    examples = []

    # Pattern: "Example 1.1" followed by problem and solution
    pattern = re.compile(
        r'Example\s+(\d+\.\d+)\s*(.*?)(?:Solution\s*)(.*?)(?=Example\s+\d+\.\d+|Intext Questions|$)',
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(text):
        example_num = match.group(1)
        problem = match.group(2).strip()
        solution = match.group(3).strip()

        # Clean up
        problem = re.sub(r'\s+', ' ', problem)[:500]
        solution = re.sub(r'\s+', ' ', solution)[:1000]

        if problem or solution:
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
    m = re.search(r'Intext Questions\s*(.*?)(?=\d+\.\d+\s+[A-Z][a-z]+\s+[A-Z]|$)', text, re.DOTALL)

    if m:
        q_text = m.group(1)
        # Find individual questions
        q_pattern = re.compile(r'(\d+\.\d+)\s+(.+?)(?=\d+\.\d+\s+[A-Z]|$)', re.DOTALL)

        for qm in q_pattern.finditer(q_text):
            q_num = qm.group(1)
            q_body = qm.group(2).strip()
            q_body = re.sub(r'\s+', ' ', q_body)[:500]

            if q_body:
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

    # Pattern for equation numbers like (1.1), (1.2)
    pattern = re.compile(r'\((\d+\.\d+)\)\s*$', re.MULTILINE)

    for match in pattern.finditer(text):
        eq_num = match.group(1)
        # Get the line before the equation number
        start = text.rfind('\n', 0, match.start()) + 1
        eq_text = text[start:match.start()].strip()

        if eq_text and '=' in eq_text:
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
        # Find individual exercises
        pattern = re.compile(r'(\d+\.\d+)\s+(.+?)(?=\d+\.\d+\s+[A-Z]|$)', re.DOTALL)

        for match in pattern.finditer(ex_text):
            ex_num = match.group(1)
            ex_body = match.group(2).strip()
            ex_body = re.sub(r'\s+', ' ', ex_body)[:500]

            if ex_body:
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


def structure_book(book_code: str):
    """Main function to structure a book."""
    base_dir = Path("extracted") / book_code
    pages_file = base_dir / "pages.json"

    if not pages_file.exists():
        print(f"Error: {pages_file} not found")
        print("Run extract_ncert.py first to extract raw pages.")
        sys.exit(1)

    # Load raw pages
    pages = json.loads(pages_file.read_text(encoding="utf-8"))
    print(f"Loaded {len(pages)} pages from {pages_file}")

    # Get first page for unit info
    first_page_text = pages[0]["text"] if pages else ""

    # Extract structured data
    unit_info = extract_unit_info(first_page_text)
    objectives = extract_objectives(first_page_text)
    sections = extract_sections(pages, book_code)
    summary = extract_summary(pages)
    exercises = extract_exercises(pages)
    answers = extract_answers(pages)

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
                "book_page": p["book_page"],
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
        print("Usage: python structure_ncert.py <book_code>")
        print("Example: python structure_ncert.py lech101")
        sys.exit(1)

    book_code = sys.argv[1]
    structure_book(book_code)
