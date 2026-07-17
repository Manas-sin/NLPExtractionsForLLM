#!/usr/bin/env python3
"""
Structure parser for Physics Class 11 NCERT.
Optimized for vision-extracted markdown (chapter_complete.md).

Extracts:
- Sections and subsections
- Equations (LaTeX)
- Examples with solutions
- Exercises
- Intext questions
- Tables
- Figures

Usage:
    python structure_physics.py <book_code>
    python structure_physics.py all

Examples:
    python structure_physics.py keph101
    python structure_physics.py all
"""

import json
import re
import sys
from pathlib import Path

from ncert_subjects import detect_subject, get_chapter_titles

OUTPUT_DIR = Path("extracted_physics")


def extract_unit_info(book_code: str) -> dict:
    """Get unit info from book_code mapping."""
    subject_info = detect_subject(book_code)
    unit_num = subject_info.get("chapter")
    unit_title = None

    if subject_info["subject"] != "unknown" and subject_info["chapter"] and subject_info["class"]:
        titles = get_chapter_titles(subject_info["subject"], subject_info["class"])
        if 0 < subject_info["chapter"] <= len(titles):
            unit_title = titles[subject_info["chapter"] - 1]

    return {"unit_number": unit_num, "unit_title": unit_title}


def extract_objectives(text: str) -> list:
    """Extract learning objectives from chapter start."""
    objectives = []

    # Look for objectives after "After studying this" or bullet points at start
    patterns = [
        r'After studying.*?you will be able to[:\s]*(.*?)(?=\n\n|\n---|\n##)',
        r'Objectives[:\s]*(.*?)(?=\n\n|\n---|\n##)',
    ]

    for pattern in patterns:
        m = re.search(pattern, text[:5000], re.DOTALL | re.IGNORECASE)
        if m:
            obj_text = m.group(1)
            # Split by bullet points or newlines
            items = re.split(r'\n[-•*]\s*|\n\d+\.\s*', obj_text)
            for item in items:
                item = item.strip()
                item = re.sub(r'\s+', ' ', item)
                if item and len(item) > 10 and not item.startswith('#'):
                    objectives.append(item.rstrip(';.'))
            break

    return objectives[:15]  # Limit


def extract_sections(text: str) -> list:
    """Extract sections from markdown-formatted text."""
    sections = []
    seen_sections = set()  # Track seen section numbers to avoid duplicates

    # Only parse sections BEFORE the EXERCISES section
    # This prevents exercise numbers (1.1, 1.2) being parsed as sections
    # Look for EXERCISES header that's NOT in table of contents (has actual questions after it)
    exercises_pattern = re.compile(r'^#{1,3}\s*EXERCISES\s*$', re.MULTILINE | re.IGNORECASE)
    for match in exercises_pattern.finditer(text):
        # Check if this is followed by actual exercise content (numbered questions)
        after = text[match.end():match.end()+500]
        if re.search(r'\*\*\d+\.\d+\*\*|#{1,4}\s*\d+\.\d+\s|\n\d+\.\d+\s', after):
            text = text[:match.start()]
            break

    # Pattern for markdown headers with section numbers
    # Matches: ### 1.1 Introduction, ## 1.2 The International System
    section_pattern = re.compile(
        r'^(#{2,4})\s*(\d{1,2})\.(\d{1,2})(?:\.(\d{1,2}))?\s+(.+?)$',
        re.MULTILINE
    )

    matches = list(section_pattern.finditer(text))

    for i, match in enumerate(matches):
        header_level = len(match.group(1))
        major = int(match.group(2))
        minor = int(match.group(3))
        sub = match.group(4)  # May be None
        title = match.group(5).strip()

        # Validate section numbers
        if major < 1 or major > 20 or minor < 1 or minor > 20:
            continue

        # Skip table/figure headers
        if title.lower().startswith(('table', 'figure', 'fig.')):
            continue

        # Get section number
        if sub:
            section_num = f"{major}.{minor}.{sub}"
        else:
            section_num = f"{major}.{minor}"

        # Skip duplicates - keep only first occurrence
        if section_num in seen_sections:
            continue
        seen_sections.add(section_num)

        # Extract content until next section
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)

        content = text[start_pos:end_pos].strip()

        # Extract components from section content
        examples = extract_examples(content)
        equations = extract_equations(content)
        intext_questions = extract_intext_questions(content)
        tables = extract_tables(content)
        figures = extract_figures(content)

        sections.append({
            "number": section_num,
            "title": title,
            "level": header_level - 1,  # ## = level 1, ### = level 2
            "content_preview": content[:500] if content else "",
            "examples": examples,
            "equations": equations,
            "intext_questions": intext_questions,
            "tables": tables,
            "figures": figures,
        })

    return sections


def extract_equations(text: str) -> list:
    """Extract LaTeX equations from text."""
    equations = []
    seen = set()

    # Display equations: $$...$$
    display_pattern = re.compile(r'\$\$\s*(.+?)\s*\$\$', re.DOTALL)
    for match in display_pattern.finditer(text):
        eq = match.group(1).strip()
        eq = re.sub(r'\s+', ' ', eq)
        if eq and len(eq) > 3 and eq not in seen:
            seen.add(eq)
            equations.append({
                "type": "display",
                "latex": eq
            })

    # Inline equations: $...$  (but not $$)
    inline_pattern = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)')
    for match in inline_pattern.finditer(text):
        eq = match.group(1).strip()
        # Filter out simple variables and very short expressions
        if eq and len(eq) > 5 and '=' in eq and eq not in seen:
            seen.add(eq)
            equations.append({
                "type": "inline",
                "latex": eq
            })

    # Also look for numbered equations: (1.1), (1.2), etc.
    numbered_pattern = re.compile(r'(.{10,200}?)\s*\((\d+\.\d+)\)\s*$', re.MULTILINE)
    for match in numbered_pattern.finditer(text):
        eq_text = match.group(1).strip()
        eq_num = match.group(2)

        # Must contain = or mathematical content
        if '=' in eq_text or '∝' in eq_text or '$' in eq_text:
            eq_key = f"eq_{eq_num}"
            if eq_key not in seen:
                seen.add(eq_key)
                equations.append({
                    "type": "numbered",
                    "number": eq_num,
                    "expression": eq_text[:200]
                })

    return equations


def extract_examples(text: str) -> list:
    """Extract examples with problems and solutions."""
    examples = []

    # Pattern for examples: ### Example 1.1, **Example 1.2**, Example 1.3
    example_pattern = re.compile(
        r'(?:#{2,4}\s*)?(?:\*\*)?Example\s+(\d+\.\d+)(?:\*\*)?\s*(.*?)(?=(?:#{2,4}\s*)?(?:\*\*)?Example\s+\d+\.\d+|#{2,4}\s*\d+\.\d+|$)',
        re.DOTALL | re.IGNORECASE
    )

    for match in example_pattern.finditer(text):
        example_num = match.group(1)
        content = match.group(2).strip()

        # Split into problem and solution
        solution_match = re.search(r'\*\*Solution\*\*|\bSolution[:\s]', content, re.IGNORECASE)

        if solution_match:
            problem = content[:solution_match.start()].strip()
            solution = content[solution_match.end():].strip()
        else:
            problem = content[:500]
            solution = ""

        # Clean up
        problem = re.sub(r'\s+', ' ', problem)[:1000]
        solution = re.sub(r'\s+', ' ', solution)[:2000]

        if problem and len(problem) > 10:
            examples.append({
                "number": example_num,
                "problem": problem,
                "solution": solution
            })

    return examples


def extract_intext_questions(text: str) -> list:
    """Extract intext questions."""
    questions = []

    # Look for ALL Intext Questions sections (can appear multiple times in chapter)
    intext_pattern = re.compile(
        r'(?:#{2,4}\s*)?Intext Questions?\s*(.*?)(?=#{2,3}\s*\d+\.\d+|#{2,3}\s*Summary|#{2,3}\s*EXERCISES|$)',
        re.DOTALL | re.IGNORECASE
    )

    for intext_match in intext_pattern.finditer(text):
        q_text = intext_match.group(1)

        # Intext questions can be numbered as:
        # 1. Question text  (simple numbering)
        # 1.1 Question text (chapter.question format)
        # **1.1** Question text

        # Pattern 1: Simple numbering (1., 2., 3.)
        simple_pattern = re.compile(r'(?:^|\n)\s*(\d{1,2})\.\s+(.+?)(?=(?:^|\n)\s*\d{1,2}\.|$)', re.DOTALL)

        for qm in simple_pattern.finditer(q_text):
            q_num = qm.group(1)
            q_body = qm.group(2).strip()
            q_body = re.sub(r'\s+', ' ', q_body)[:500]

            if q_body and len(q_body) > 10:
                questions.append({
                    "number": q_num,
                    "text": q_body
                })

        # Pattern 2: Chapter.question format (1.1, 1.2)
        chapter_pattern = re.compile(r'(?:\*\*)?(\d{1,2})\.(\d{1,2})(?:\*\*)?\s+(.+?)(?=(?:\*\*)?\d{1,2}\.\d{1,2}|$)', re.DOTALL)

        for qm in chapter_pattern.finditer(q_text):
            major = int(qm.group(1))
            minor = int(qm.group(2))

            if major < 1 or major > 20 or minor < 1 or minor > 30:
                continue

            q_num = f"{major}.{minor}"
            q_body = qm.group(3).strip()
            q_body = re.sub(r'\s+', ' ', q_body)[:500]

            if q_body and len(q_body) > 10:
                questions.append({
                    "number": q_num,
                    "text": q_body
                })

    return questions


def extract_exercises(text: str) -> list:
    """Extract end-of-chapter exercises."""
    exercises = []

    # Find the LAST EXERCISES section (to skip any in table of contents)
    # It should be followed by actual numbered exercises like **6.1** or 6.1
    exercises_match = None
    exercises_pattern = re.compile(r'#{1,3}\s*EXERCISES\s*\n', re.IGNORECASE)

    for match in exercises_pattern.finditer(text):
        # Check if this section has actual exercise content
        after = text[match.end():match.end()+500]
        if re.search(r'\*\*\d+\.\d+\*\*|#{1,4}\s*\d+\.\d+\s|\n\d+\.\d+\s', after):
            # This looks like real exercises - extract until end or Answers section
            remaining = text[match.end():]
            end_match = re.search(r'#{1,3}\s*(?:Answers|Additional|Appendix)', remaining, re.IGNORECASE)
            if end_match:
                ex_text = remaining[:end_match.start()]
            else:
                ex_text = remaining
            exercises_match = type('obj', (object,), {'group': lambda s, n: ex_text})()
            break

    if exercises_match:
        ex_text = exercises_match.group(1)

        # Find exercises: ### 1.1 or **1.1** or 1.1 at line start
        # Pattern: ### X.Y Title or ### X.Y\n or just X.Y at line start
        ex_pattern = re.compile(
            r'(?:^|\n)(?:#{2,4}\s*)?(\d{1,2})\.(\d{1,2})\s*([^\n]*(?:\n(?!(?:#{2,4}\s*)?\d{1,2}\.\d{1,2}).*?)*)',
            re.MULTILINE
        )

        for em in ex_pattern.finditer(ex_text):
            major = int(em.group(1))
            minor = int(em.group(2))

            if major < 1 or major > 20 or minor < 1 or minor > 50:
                continue

            ex_num = f"{major}.{minor}"
            ex_body = em.group(3).strip() if em.group(3) else ""

            # Clean up - remove markdown headers, extra whitespace
            ex_body = re.sub(r'^#+\s*', '', ex_body)
            ex_body = re.sub(r'\s+', ' ', ex_body)[:800]

            if ex_body and len(ex_body) > 5:
                exercises.append({
                    "number": ex_num,
                    "text": ex_body
                })

    return exercises


def extract_tables(text: str) -> list:
    """Extract table references."""
    tables = []

    # Pattern for table headers
    table_pattern = re.compile(r'(?:#{2,4}\s*)?Table\s+(\d+\.\d+)[:\s]*(.+?)(?=\n|$)', re.IGNORECASE)

    for match in table_pattern.finditer(text):
        tables.append({
            "number": match.group(1),
            "title": match.group(2).strip()[:200]
        })

    return tables


def extract_figures(text: str) -> list:
    """Extract figure references."""
    figures = []

    # Pattern for figures: [Figure 1.1: description], Fig. 1.1, Figure 1.1
    fig_patterns = [
        r'\[(?:Figure|Fig\.?)\s+(\d+\.\d+)[:\s]*([^\]]+)\]',
        r'(?:Figure|Fig\.?)\s+(\d+\.\d+)[:\s]*(.+?)(?=\n|$)',
    ]

    seen = set()
    for pattern in fig_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            fig_num = match.group(1)
            if fig_num not in seen:
                seen.add(fig_num)
                caption = match.group(2).strip()[:200] if match.group(2) else ""
                figures.append({
                    "number": fig_num,
                    "caption": caption
                })

    return figures


def extract_summary(text: str) -> str:
    """Extract chapter summary."""
    summary_match = re.search(r'(?:#{2,3}\s*)?Summary\s*(.*?)(?=#{2,3}\s*Exercises|#{2,3}\s*Points to Ponder|$)', text, re.DOTALL | re.IGNORECASE)

    if summary_match:
        summary = summary_match.group(1).strip()
        summary = re.sub(r'\s+', ' ', summary)
        return summary[:3000]

    return ""


def structure_physics_chapter(book_code: str):
    """Main function to structure a physics chapter."""
    base_dir = OUTPUT_DIR / book_code
    chapter_file = base_dir / "chapter_complete.md"
    pages_file = base_dir / "pages.json"

    if not chapter_file.exists():
        print(f"Error: {chapter_file} not found")
        print("Run extract_physics.py first.")
        sys.exit(1)

    # Load vision-extracted markdown
    text = chapter_file.read_text(encoding="utf-8")
    print(f"Loaded {len(text):,} chars from {chapter_file.name}")

    # Get page count from pages.json if exists
    page_count = 0
    if pages_file.exists():
        pages = json.loads(pages_file.read_text(encoding="utf-8"))
        page_count = len(pages)

    # Extract structured data
    unit_info = extract_unit_info(book_code)
    objectives = extract_objectives(text)
    sections = extract_sections(text)
    summary = extract_summary(text)
    exercises = extract_exercises(text)

    # Also extract top-level equations (not in sections)
    all_equations = extract_equations(text)

    # Calculate stats
    section_equations = sum(len(s.get("equations", [])) for s in sections)
    section_examples = sum(len(s.get("examples", [])) for s in sections)
    section_intext = sum(len(s.get("intext_questions", [])) for s in sections)
    section_tables = sum(len(s.get("tables", [])) for s in sections)
    section_figures = sum(len(s.get("figures", [])) for s in sections)

    # Build structured output
    structured = {
        "book_code": book_code,
        "unit_number": unit_info["unit_number"],
        "unit_title": unit_info["unit_title"],
        "total_pages": page_count,
        "objectives": objectives,
        "sections": sections,
        "all_equations": all_equations,  # All equations in chapter
        "summary": summary,
        "exercises": exercises,
        "statistics": {
            "section_count": len(sections),
            "example_count": section_examples,
            "table_count": section_tables,
            "figure_count": section_figures,
            "equation_count": len(all_equations),
            "exercise_count": len(exercises),
            "intext_question_count": section_intext
        }
    }

    # Save structured output
    output_file = base_dir / "structured.json"
    output_file.write_text(
        json.dumps(structured, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Print summary
    print(f"\nUnit {structured['unit_number']}: {structured['unit_title']}")
    print(f"  Sections: {structured['statistics']['section_count']}")
    print(f"  Examples: {structured['statistics']['example_count']}")
    print(f"  Tables: {structured['statistics']['table_count']}")
    print(f"  Figures: {structured['statistics']['figure_count']}")
    print(f"  Equations: {structured['statistics']['equation_count']}")
    print(f"  Exercises: {structured['statistics']['exercise_count']}")
    print(f"  Intext Questions: {structured['statistics']['intext_question_count']}")
    print(f"\nSaved: {output_file}")

    return structured


def batch_structure():
    """Structure all physics chapters."""
    chapters = ["keph101", "keph102", "keph103", "keph104", "keph105", "keph106", "keph107"]

    print("="*60)
    print("STRUCTURING ALL PHYSICS CHAPTERS")
    print("="*60)

    results = []
    for book_code in chapters:
        print(f"\n{'='*40}")
        print(f"Processing: {book_code}")
        print(f"{'='*40}")

        try:
            result = structure_physics_chapter(book_code)
            results.append((book_code, "SUCCESS", result['statistics']))
        except Exception as e:
            print(f"Error: {e}")
            results.append((book_code, f"FAILED: {e}", {}))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for code, status, stats in results:
        if stats:
            print(f"  {code}: {status} - {stats.get('section_count', 0)} sections, {stats.get('equation_count', 0)} equations")
        else:
            print(f"  {code}: {status}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python structure_physics.py <book_code>")
        print("  python structure_physics.py all")
        print("")
        print("Examples:")
        print("  python structure_physics.py keph101")
        print("  python structure_physics.py all")
        sys.exit(0)

    if sys.argv[1] == "all":
        batch_structure()
    else:
        book_code = sys.argv[1]
        structure_physics_chapter(book_code)
