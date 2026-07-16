#!/usr/bin/env python3
"""
PYQ Extractor - Extract Previous Year Questions from sample papers.
Maps questions to chapters and adds them to final output.
"""

import json
import re
from pathlib import Path
import fitz


# Chapter keywords for mapping questions
CHAPTER_KEYWORDS = {
    "chemistry": {
        "Solutions": ["solution", "molality", "molarity", "colligative", "osmotic", "vapour pressure",
                     "raoult", "henry's law", "boiling point elevation", "freezing point depression"],
        "Electrochemistry": ["electrochemical", "electrolysis", "electrode", "galvanic", "nernst",
                            "conductivity", "molar conductivity", "faraday", "emf", "cell potential"],
        "Chemical Kinetics": ["rate", "order", "molecularity", "activation energy", "arrhenius",
                             "half-life", "rate constant", "rate law", "first order", "zero order"],
        "Surface Chemistry": ["adsorption", "colloid", "emulsion", "catalyst", "enzyme", "micelle",
                             "tyndall", "brownian", "coagulation", "peptization"],
        "Coordination Compounds": ["coordination", "ligand", "isomerism", "crystal field", "chelate",
                                  "werner", "cfse", "magnetic moment", "spectrochemical"],
        "Haloalkanes and Haloarenes": ["halogen", "alkyl halide", "sn1", "sn2", "elimination",
                                       "nucleophilic substitution", "grignard", "wurtz"],
        "Alcohols, Phenols and Ethers": ["alcohol", "phenol", "ether", "williamson", "dehydration",
                                         "oxidation of alcohol", "lucas test", "hydroxyl"],
        "Aldehydes, Ketones and Carboxylic Acids": ["aldehyde", "ketone", "carboxylic", "aldol",
                                                     "cannizzaro", "tollens", "fehling", "benedict"],
        "Amines": ["amine", "diazo", "hofmann", "gabriel", "carbylamine", "nitrosation", "basicity"],
        "Biomolecules": ["carbohydrate", "protein", "amino acid", "glucose", "fructose", "dna", "rna",
                        "enzyme", "vitamin", "nucleotide", "peptide", "starch", "cellulose"],
        "Polymers": ["polymer", "monomer", "polymerization", "nylon", "bakelite", "teflon", "rubber",
                    "addition polymer", "condensation polymer"],
        "Chemistry in Everyday Life": ["drug", "medicine", "antibiotic", "analgesic", "antiseptic",
                                       "detergent", "soap", "food additive", "preservative"],
        "The Solid State": ["crystal", "unit cell", "lattice", "packing", "defect", "schottky",
                           "frenkel", "band theory", "semiconductor"],
        "The p-Block Elements": ["halogen", "noble gas", "oxygen family", "nitrogen family",
                                "interhalogen", "oxyacid", "phosphorus", "sulphur"],
        "The d- and f-Block Elements": ["transition", "lanthanoid", "actinoid", "magnetic",
                                        "catalytic", "oxidation state", "interstitial"]
    }
}


def extract_questions_from_pdf(pdf_path: Path) -> list:
    """Extract all questions from a sample paper PDF."""
    questions = []

    doc = fitz.open(pdf_path)
    all_text = ""
    for page in doc:
        all_text += page.get_text() + "\n"
    doc.close()

    # Clean text
    all_text = re.sub(r'\s+', ' ', all_text)

    # Pattern for questions: number followed by question text
    # Match patterns like "1.", "1)", "Q1.", "Q.1", etc.
    q_pattern = re.compile(
        r'(?:^|\s)(\d{1,2})\s*[.\)]\s*(.+?)(?=(?:\s\d{1,2}\s*[.\)])|Section\s+[A-E]|$)',
        re.MULTILINE | re.DOTALL
    )

    # Also match section-based questions
    sections = re.split(r'Section\s+[A-E]', all_text, flags=re.IGNORECASE)

    for section in sections:
        # Find questions in each section
        matches = q_pattern.findall(section)
        for num, text in matches:
            text = text.strip()
            # Clean up the question text
            text = re.sub(r'\[[\d\s]+\]', '', text)  # Remove marks like [1], [2]
            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) > 20 and len(text) < 2000:  # Valid question length
                questions.append({
                    "number": num,
                    "text": text[:500],  # Limit length
                    "source": pdf_path.stem
                })

    return questions


def identify_chapter(question_text: str, subject: str = "chemistry") -> str:
    """Identify which chapter a question belongs to."""
    text_lower = question_text.lower()

    keywords = CHAPTER_KEYWORDS.get(subject, {})

    best_match = None
    best_score = 0

    for chapter, kws in keywords.items():
        score = sum(1 for kw in kws if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = chapter

    return best_match if best_score > 0 else "General"


def extract_pyqs(pyq_folder: Path, subject: str = "chemistry") -> dict:
    """Extract PYQs from all PDFs and organize by chapter."""

    chapter_questions = {}

    # Process all PDFs in folder
    pdf_files = list(pyq_folder.glob("*.pdf"))
    print(f"Found {len(pdf_files)} sample papers")

    all_questions = []

    for pdf_path in pdf_files:
        print(f"  Processing {pdf_path.name}...")
        questions = extract_questions_from_pdf(pdf_path)
        all_questions.extend(questions)

    print(f"Extracted {len(all_questions)} total questions")

    # Organize by chapter
    for q in all_questions:
        chapter = identify_chapter(q["text"], subject)
        if chapter not in chapter_questions:
            chapter_questions[chapter] = []
        chapter_questions[chapter].append(q)

    # Limit to 15 per chapter and remove duplicates
    for chapter in chapter_questions:
        # Simple dedup by checking first 50 chars
        seen = set()
        unique = []
        for q in chapter_questions[chapter]:
            key = q["text"][:50].lower()
            if key not in seen:
                seen.add(key)
                unique.append(q)
        chapter_questions[chapter] = unique[:15]  # Limit to 15

    return chapter_questions


def add_pyqs_to_output(book_code: str, pyq_folder: Path, subject: str = "chemistry"):
    """Add PYQs to the final_output.json of a book."""

    base_dir = Path("extracted") / book_code
    final_output = base_dir / "final_output.json"

    if not final_output.exists():
        print(f"Error: {final_output} not found")
        return

    # Extract PYQs
    print(f"Extracting PYQs from {pyq_folder}...")
    chapter_pyqs = extract_pyqs(pyq_folder, subject)

    # Load existing output
    data = json.loads(final_output.read_text())

    # Get unit title to match with PYQs
    unit_title = data.get("unit_title", "")

    # Find matching PYQs
    matched_pyqs = []
    for chapter, questions in chapter_pyqs.items():
        if chapter.lower() in unit_title.lower() or unit_title.lower() in chapter.lower():
            matched_pyqs = questions
            break

    # If no direct match, try keyword matching from sections
    if not matched_pyqs:
        section_titles = " ".join(s.get("title", "") for s in data.get("sections", []))
        for chapter, questions in chapter_pyqs.items():
            if any(kw in section_titles.lower() for kw in CHAPTER_KEYWORDS.get(subject, {}).get(chapter, [])):
                matched_pyqs.extend(questions)
        matched_pyqs = matched_pyqs[:15]

    # Add PYQs to output
    data["previous_year_questions"] = matched_pyqs
    data["pyq_count"] = len(matched_pyqs)

    # Save updated output
    final_output.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Added {len(matched_pyqs)} PYQs to {final_output}")

    # Also save all PYQs separately
    pyq_file = base_dir / "pyqs.json"
    pyq_file.write_text(json.dumps(chapter_pyqs, ensure_ascii=False, indent=2))
    print(f"Saved all PYQs to {pyq_file}")

    return chapter_pyqs


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python extract_pyq.py <book_code> <pyq_folder>")
        print("Example: python extract_pyq.py lech101 '/path/to/sample papers'")
        sys.exit(1)

    book_code = sys.argv[1]
    pyq_folder = Path(sys.argv[2])

    if not pyq_folder.exists():
        print(f"Error: {pyq_folder} not found")
        sys.exit(1)

    add_pyqs_to_output(book_code, pyq_folder, "chemistry")
