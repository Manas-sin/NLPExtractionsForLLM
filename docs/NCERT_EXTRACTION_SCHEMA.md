# NCERT Content Extraction Schema

## Overview

This document describes how we extract and structure content from NCERT textbooks for the enhanced reading experience feature. The extraction pipeline converts PDF textbooks into structured JSON that supports:

- Highlighting
- Notes (text and voice)
- Viewing toppers' highlights and notes
- PYQ questions associated with text blocks
- Alternate explanations and clarifications

---

## Content Hierarchy

NCERT textbooks follow a consistent hierarchical structure:

```
Book
└── Unit/Chapter
    ├── Unit Opening Page
    │   ├── QR Code
    │   ├── Unit Banner (number + title)
    │   ├── Objectives ("After studying this Unit, you will be able to...")
    │   ├── Hook Quote (motivational/real-world connection)
    │   └── Introduction
    │
    ├── Sections (1.1, 1.2, 1.3, ...)
    │   ├── Section Header
    │   ├── Body Text (paragraphs)
    │   ├── Key Terms (bold, first introduction)
    │   ├── Laws/Principles (Henry's law, Raoult's law, etc.)
    │   ├── Equations
    │   │   ├── Chemical (with → or ⇌ arrows)
    │   │   └── Mathematical (numbered, e.g., (1.5))
    │   ├── Tables
    │   ├── Figures (diagrams, graphs, molecular structures)
    │   ├── Subsections (1.1.1, 1.1.2, ...)
    │   ├── Solved Examples
    │   │   ├── Problem
    │   │   └── Solution
    │   └── Intext Questions
    │
    ├── Summary (bordered box, key points)
    │
    ├── Exercises (end-of-chapter questions)
    │   ├── Main questions (1.1, 1.2, ...)
    │   └── Sub-parts ((a), (b), (c), ...)
    │
    └── Answers to Intext Questions
```

---

## Extraction Pipeline

### Step 1: PDF Extraction

```
PDF File (e.g., lech101.pdf)
        │
        ▼
┌─────────────────────────────────┐
│     PDFExtractor                │
│  (src/extractors/pdf_extractor.py)  │
│                                 │
│  - Extract text per page        │
│  - Render page images           │
│  - Extract figure regions       │
└─────────────────────────────────┘
        │
        ▼
    Outputs:
    ├── content.md (raw text)
    ├── pages.json (per-page data)
    ├── figures.json (figure metadata)
    ├── figures/ (extracted images)
    └── renders/ (page renders)
```

### Step 2: Content Structuring

```
content.md (raw extracted text)
        │
        ▼
┌─────────────────────────────────┐
│     NCERTStructurer             │
│  (src/extractors/ncert_structurer.py) │
│                                 │
│  - Parse objectives             │
│  - Extract sections hierarchy   │
│  - Identify key terms           │
│  - Extract laws/principles      │
│  - Parse equations              │
│  - Extract tables               │
│  - Parse examples               │
│  - Extract exercises            │
└─────────────────────────────────┘
        │
        ▼
    Output:
    └── structured.json
```

---

## JSON Output Schema

### Root Structure

```json
{
  "book_code": "lech101",
  "subject": "chemistry",
  "class": 11,
  "unit_number": 1,
  "unit_title": "Solutions",
  "qr_code": "12085CH01",
  "objectives": [...],
  "hook_quote": "...",
  "introduction": "...",
  "sections": [...],
  "key_terms": [...],
  "laws_principles": [...],
  "equations": [...],
  "tables": [...],
  "figures": [...],
  "examples": [...],
  "intext_questions": [...],
  "summary": [...],
  "exercises": [...],
  "answers": {...},
  "statistics": {...}
}
```

### Objectives

Learning objectives from the unit opening page.

```json
"objectives": [
  "describe the formation of different types of solutions",
  "express concentration of solution in different units",
  "state and explain Henry's law and Raoult's law"
]
```

### Sections

Hierarchical sections with content and subsections.

```json
"sections": [
  {
    "number": "1.1",
    "title": "Types of Solutions",
    "content": "Solutions are homogeneous mixtures of two or more...",
    "content_truncated": false,
    "subsections": [
      {
        "number": "1.1.1",
        "title": "Gaseous Solutions"
      }
    ]
  }
]
```

### Key Terms

Terms defined in the text (identified by patterns like "is called", "is known as").

```json
"key_terms": [
  {
    "term": "solvent",
    "context": "the component that is present in the largest quantity is known as solvent",
    "pattern_type": "known_as"
  }
]
```

### Laws and Principles

Named laws, equations, principles, and rules.

```json
"laws_principles": [
  {
    "name": "Raoult's law",
    "statement": "the partial vapour pressure of each component is directly proportional to its mole fraction",
    "context": "..."
  }
]
```

### Equations

Chemical and mathematical equations.

```json
"equations": [
  {
    "type": "chemical",
    "number": "",
    "reactants": "2 CH3COOH",
    "products": "(CH3COOH)2",
    "reversible": true,
    "full": "2 CH3COOH ⇌ (CH3COOH)2"
  },
  {
    "type": "mathematical",
    "number": "1.5",
    "expression": "p = xA × p°A",
    "display": true
  }
]
```

### Tables

Structured tables with headers and rows.

```json
"tables": [
  {
    "number": "1.1",
    "title": "Types of Solutions",
    "headers": ["Type of Solution", "Solute", "Solvent", "Common Examples"],
    "rows": [
      {
        "Type of Solution": "Gaseous Solutions",
        "Solute": "Gas",
        "Solvent": "Gas",
        "Common Examples": "Mixture of oxygen and nitrogen"
      }
    ],
    "row_count": 9,
    "format": "structured"
  }
]
```

### Figures

Figure references with captions.

```json
"figures": [
  {
    "number": "1.1",
    "caption": "Effect of pressure on the solubility of a gas"
  }
]
```

### Examples

Solved examples with problem and solution.

```json
"examples": [
  {
    "number": "1.1",
    "problem": "Calculate the mole fraction of benzene in solution containing 30% by mass...",
    "solution": "Molar mass of C6H6 = 78 g/mol. If total mass = 100g..."
  }
]
```

### Intext Questions

Questions embedded within sections.

```json
"intext_questions": [
  {
    "number": "1.1",
    "text": "Calculate the mass percentage of benzene (C6H6) and carbon tetrachloride..."
  }
]
```

### Exercises

End-of-chapter exercises with sub-parts.

```json
"exercises": [
  {
    "number": "1.1",
    "text": "Define the term solution. How many types of solutions are formed?",
    "sub_parts": []
  },
  {
    "number": "1.10",
    "text": "The vapour pressure of water is 12.3 kPa at 300 K.",
    "sub_parts": [
      {"label": "a", "text": "Calculate the molality of the solution"},
      {"label": "b", "text": "Calculate the boiling point elevation"}
    ]
  }
]
```

### Statistics

Summary counts for validation.

```json
"statistics": {
  "section_count": 7,
  "key_term_count": 20,
  "law_count": 1,
  "equation_count": 3,
  "table_count": 4,
  "figure_count": 11,
  "example_count": 12,
  "intext_question_count": 7,
  "exercise_count": 97
}
```

---

## Book Code Convention

| Code | Subject | Class | Description |
|------|---------|-------|-------------|
| `lech1XX` | Chemistry | 11/12 | Part 1 Chemistry |
| `lech2XX` | Chemistry | 11/12 | Part 2 Chemistry |
| `keph1XX` | Physics | 11 | Class 11 Physics |
| `keph2XX` | Physics | 12 | Class 12 Physics |
| `lebo1XX` | Biology | 11/12 | Biology |

Example: `lech101` = Chemistry Part 1, Unit 01 (Solutions)

---

## Visual Elements in NCERT

### Color Coding (Chemistry)

| Element | Color | Hex |
|---------|-------|-----|
| Unit Banner | Pink/Magenta | #E91E63 |
| Section Underline | Red/Maroon | #8B0000 |
| Example Boxes | Cyan/Teal | #00BCD4 |
| Intext Questions | Light Coral | #FFB6C1 |
| Exercise Sidebar | Red | #D32F2F |
| Table Headers | Coral/Pink | #FF6B6B |

### Special Notations

| Notation | Meaning |
|----------|---------|
| `→` | Forward reaction |
| `⇌` | Reversible reaction |
| `(s)` | Solid state |
| `(l)` | Liquid state |
| `(g)` | Gaseous state |
| `(aq)` | Aqueous solution |
| `₂`, `₃` | Subscripts |
| `⁺`, `⁻` | Superscripts (charges) |

---

## Usage

### Extract and Structure a Chapter

```python
from src.extractors.ncert_structurer import structure_ncert_chapter
from pathlib import Path

# Structure a chemistry chapter
result = structure_ncert_chapter(
    book_code='lech101',
    subject='chemistry',
    base_dir=Path('data/extracted/lech101')
)

# Output saved to: data/extracted/lech101/structured.json
```

### Access Structured Data

```python
import json
from pathlib import Path

data = json.loads(Path('data/extracted/lech101/structured.json').read_text())

# Get all sections
for section in data['sections']:
    print(f"{section['number']}: {section['title']}")

# Get all key terms
for term in data['key_terms']:
    print(f"- {term['term']}: {term['context']}")

# Get exercises
for ex in data['exercises']:
    print(f"Q{ex['number']}: {ex['text']}")
```

---

## Linking Content to PYQs

The structured content enables linking Previous Year Questions (PYQs) to specific content blocks:

```
Section 1.3 (Solubility)
    │
    ├── Concept: Henry's Law
    │   └── Related PYQs:
    │       ├── NEET 2023 Q42
    │       ├── NEET 2021 Q38
    │       └── NEET 2019 Q55
    │
    └── Concept: Effect of Temperature
        └── Related PYQs:
            ├── NEET 2022 Q41
            └── NEET 2020 Q36
```

This enables the "Ask for questions associated with blocks of text" feature.

---

## Current Extraction Coverage

| Book | Title | Sections | Tables | Examples | Exercises |
|------|-------|----------|--------|----------|-----------|
| lech101 | Solutions | 7 | 4 | 12 | 97 |
| lech102 | Electrochemistry | 10 | 4 | 10 | 0 |
| lech103 | Chemical Kinetics | 5 | 4 | 9 | 61 |
| lech104 | d- and f-Block Elements | 8 | 11 | 10 | 18 |
| lech105 | Coordination Compounds | 6 | 3 | 7 | 28 |
| keph101 | Units and Measurement | 7 | 0 | 0 | 145 |

---

## Files Reference

```
ytlcExperiment/
├── config/
│   ├── ncert_structure.json        # Visual layout rules
│   └── ncert_extraction_rules.json # Regex patterns
│
├── src/extractors/
│   ├── pdf_extractor.py            # PDF to raw text
│   ├── ncert_structurer.py         # Raw text to structured JSON
│   └── vision_extractor.py         # Claude Vision for complex pages
│
├── data/extracted/
│   └── {book_code}/
│       ├── content.md              # Raw extracted text
│       ├── structured.json         # Structured output
│       ├── figures.json            # Figure metadata
│       ├── figures/                # Extracted figure images
│       └── renders/                # Page renders
│
└── docs/
    └── NCERT_EXTRACTION_SCHEMA.md  # This document
```
