# NCERT PDF Extraction Rules

> How to identify and extract each element from raw PDF text

---

## 1. UNIT OPENING PAGE ELEMENTS

### 1.1 Unit Number
```
PATTERN:    "Unit" followed by a number (1-16)
REGEX:      /Unit\s*(\d{1,2})/i
EXAMPLE:    "Unit 1" → extract "1"
LOCATION:   First page of chapter, top-right area
```

### 1.2 Unit Title
```
PATTERN:    Title text immediately after unit number
            Usually a single word or phrase (no punctuation)
REGEX:      /Unit\s*\d{1,2}\s*([A-Za-z\s]+)/
EXAMPLE:    "Unit 1 Solutions" → extract "Solutions"
            "Unit 2 Electrochemistry" → extract "Electrochemistry"
LOCATION:   Below unit number on first page
```

### 1.3 QR Code Reference
```
PATTERN:    Alphanumeric code format XXXXXCHYY
REGEX:      /(\d{5}CH\d{2})/
EXAMPLE:    "12085CH02" → Class 12, Chemistry, Chapter 02
LOCATION:   Below QR code image, top-left
```

### 1.4 Objectives Section
```
START MARKER:   "Objectives"
LEAD-IN:        "After studying this Unit, you will be able to"
BULLET PATTERN: Lines starting with "•" or "describe", "explain", "define", etc.
END MARKER:     First section header (e.g., "1.1") OR end of bullet list

EXTRACTION:
- Find "After studying this Unit, you will be able to"
- Collect all lines until next section starts
- Each objective is separated by ";" or new line with "•"

EXAMPLE INPUT:
"After studying this Unit, you will be able to
• describe the formation of different types of solutions;
• express concentration of solution in different units;
• state and explain Henry's law and Raoult's law;"

EXAMPLE OUTPUT:
[
  "describe the formation of different types of solutions",
  "express concentration of solution in different units",
  "state and explain Henry's law and Raoult's law"
]
```

### 1.5 Hook/Quote (Italicized intro)
```
PATTERN:    Italicized text on first page, usually about real-world relevance
LOCATION:   Between objectives and first section
IDENTIFIER: Text that connects topic to everyday life
            Often contains phrases like "In normal life...", "Almost all..."

EXAMPLE:
"Almost all processes in body occur in some kind of liquid solutions."
"Chemical reactions can be used to produce electrical energy..."
```

---

## 2. SECTION HEADERS

### 2.1 Main Section (X.Y)
```
PATTERN:    Number.Number followed by title text
REGEX:      /^(\d+\.\d+)\s+([A-Za-z\s]+)/m
EXAMPLES:
  "1.1 Types of Solutions" → section: "1.1", title: "Types of Solutions"
  "2.3 Nernst Equation" → section: "2.3", title: "Nernst Equation"

IDENTIFICATION:
- Starts with digit.digit pattern
- Title may span multiple lines (wrap)
- No period at end of title
```

### 2.2 Subsection (X.Y.Z)
```
PATTERN:    Number.Number.Number followed by bold title
REGEX:      /^(\d+\.\d+\.\d+)\s+([A-Za-z\s]+)/m
EXAMPLES:
  "1.3.1 Solubility of a Solid in a Liquid"
  "2.2.1 Measurement of Electrode Potential"

IDENTIFICATION:
- Starts with digit.digit.digit pattern
- Title is typically bold in source
```

### 2.3 Sub-subsection (No number, italic)
```
PATTERN:    Italicized text acting as mini-header
EXAMPLES:
  "Effect of temperature"
  "Effect of pressure"

IDENTIFICATION:
- No numbering
- Followed by paragraph of explanation
- Short phrase (2-5 words)
```

---

## 3. BODY TEXT ELEMENTS

### 3.1 Key Terms (Bold on first use)
```
PATTERN:    Word/phrase in bold when first introduced
REGEX:      /\*\*([^*]+)\*\*/ (if markdown)
            Look for terms followed by definition

IDENTIFICATION PHRASES:
- "is called **term**"
- "is known as **term**"
- "are called **term**"
- "Such a device is called a **term**"

EXAMPLES:
"component that is present in the largest quantity is known as **solvent**"
"are called **solutes**"
"Such a device is called a **galvanic** or a **voltaic** cell"

EXTRACTION:
Input: "is known as solvent. Solvent determines..."
Output: { term: "solvent", definition: "component present in largest quantity" }
```

### 3.2 Important Laws/Principles
```
PATTERN:    Named law/principle in bold
REGEX:      /\*\*([A-Z][a-z]+'s\s+law)\*\*/
            /\*\*([A-Z][a-z]+\s+equation)\*\*/

EXAMPLES:
- "**Henry's law**"
- "**Raoult's law**"
- "**Nernst equation**"
- "**Dalton's law of partial pressures**"

EXTRACTION: Collect law name and following statement
```

### 3.3 Definitions (Full sentence bold)
```
PATTERN:    Entire statement in bold - indicates key concept

EXAMPLE:
"**the solubility of a gas in a liquid is directly proportional to the partial pressure of the gas present above the surface of liquid or solution.**"

IDENTIFICATION:
- Long bold text (more than 5 words)
- Usually contains "is", "are", describing a relationship
```

---

## 4. EQUATIONS

### 4.1 Chemical Equations
```
PATTERN:    Reactants → Products with state symbols and equation number

REGEX FOR NUMBER: /\((\d+\.\d+)\)$/
REGEX FOR ARROW:  /→|⇌|->|<->|<=>/ 

EXAMPLES:
"Zn(s) + Cu²⁺(aq) → Zn²⁺(aq) + Cu(s)                    (2.1)"

EXTRACTION:
{
  "equation_number": "2.1",
  "reactants": "Zn(s) + Cu²⁺(aq)",
  "products": "Zn²⁺(aq) + Cu(s)",
  "type": "forward",
  "states": ["s", "aq", "aq", "s"]
}
```

### 4.2 Mathematical Equations
```
PATTERN:    Variable = Expression followed by equation number

EXAMPLES:
"Molarity = Moles of solute / Volume of solution in litre    (1.8)"
"p = KH x                                                     (1.11)"
"E(cell) = E°(cell) - (RT/nF) ln Q                           (2.8)"

EXTRACTION:
{
  "equation_number": "1.8",
  "left_side": "Molarity",
  "right_side": "Moles of solute / Volume of solution in litre",
  "type": "definition"
}
```

### 4.3 Half-Cell Reactions
```
PATTERN:    (i) or (ii) prefix with reaction type label

EXAMPLES:
"(i) Cu²⁺ + 2e⁻ → Cu(s)     (reduction half reaction)    (2.2)"
"(ii) Zn(s) → Zn²⁺ + 2e⁻    (oxidation half reaction)    (2.3)"

EXTRACTION:
{
  "sub_number": "i",
  "equation_number": "2.2",
  "reaction": "Cu²⁺ + 2e⁻ → Cu(s)",
  "type": "reduction half reaction"
}
```

---

## 5. TABLES

### 5.1 Table Detection
```
START MARKER:   "Table X.Y:" followed by title
HEADER ROW:     First row with column names
DATA ROWS:      Subsequent rows with aligned data
END MARKER:     Empty line OR next section/element

EXAMPLE INPUT:
"Table 1.1: Types of Solutions
Type of Solution    Solute    Solvent    Common Examples
Gaseous Solutions   Gas       Gas        Mixture of oxygen and nitrogen gases
                    Liquid    Gas        Chloroform mixed with nitrogen gas
Liquid Solutions    Gas       Liquid     Oxygen dissolved in water"

EXTRACTION:
{
  "table_number": "1.1",
  "title": "Types of Solutions",
  "headers": ["Type of Solution", "Solute", "Solvent", "Common Examples"],
  "rows": [
    ["Gaseous Solutions", "Gas", "Gas", "Mixture of oxygen and nitrogen gases"],
    ["", "Liquid", "Gas", "Chloroform mixed with nitrogen gas"],
    ["Liquid Solutions", "Gas", "Liquid", "Oxygen dissolved in water"]
  ]
}
```

### 5.2 Table Footnotes
```
PATTERN:    Line starting with "*" below table
EXAMPLE:    "* represent i values for incomplete dissociation."
```

---

## 6. FIGURES

### 6.1 Figure Detection
```
MARKER:     "Fig. X.Y:" followed by caption
REGEX:      /Fig\.\s*(\d+\.\d+):\s*(.+)/

EXAMPLE:
"Fig. 1.1: Effect of pressure on the solubility of a gas. The concentration of dissolved gas is proportional to the pressure on the gas above the solution."

EXTRACTION:
{
  "figure_number": "1.1",
  "caption": "Effect of pressure on the solubility of a gas. The concentration of dissolved gas is proportional to the pressure on the gas above the solution."
}
```

### 6.2 Multi-part Figures
```
PATTERN:    Caption mentions (a), (b), (c)

EXAMPLE:
"Fig. 2.2: Functioning of Daniell cell when external voltage Eext opposing the cell potential is applied."
With sub-labels: (a), (b), (c) in figure

EXTRACTION:
{
  "figure_number": "2.2",
  "caption": "Functioning of Daniell cell...",
  "parts": ["a", "b", "c"]
}
```

---

## 7. SOLVED EXAMPLES

### 7.1 Example Detection
```
START MARKER:   "Example X.Y" or "Example X.Y:"
SOLUTION MARKER: "Solution"
END MARKER:     Next "Example" OR next section OR "Intext Questions"

REGEX:          /Example\s+(\d+\.\d+)/

EXAMPLE INPUT:
"Example 1.1  Calculate the mole fraction of ethylene glycol (C₂H₆O₂) in a solution containing 20% of C₂H₆O₂ by mass.

Solution  Assume that we have 100 g of solution (one can start with any amount of solution because the results obtained will be the same). Solution will contain 20 g of ethylene glycol and 80 g of water.
Molar mass of C₂H₆O₂ = 12 × 2 + 1 × 6 + 16 × 2 = 62 g mol⁻¹
Moles of C₂H₆O₂ = 20 g / 62 g mol⁻¹ = 0.322 mol"

EXTRACTION:
{
  "example_number": "1.1",
  "problem": "Calculate the mole fraction of ethylene glycol (C₂H₆O₂) in a solution containing 20% of C₂H₆O₂ by mass.",
  "solution": {
    "steps": [
      "Assume that we have 100 g of solution...",
      "Molar mass of C₂H₆O₂ = 62 g mol⁻¹",
      "Moles of C₂H₆O₂ = 0.322 mol"
    ],
    "answer": "0.322 mol"
  }
}
```

---

## 8. INTEXT QUESTIONS

### 8.1 Detection
```
START MARKER:   "Intext Questions"
QUESTION PATTERN: "X.Y" followed by question text
END MARKER:     Next section header (X.Y format with title)

EXAMPLE INPUT:
"Intext Questions
1.1 Calculate the mass percentage of benzene (C₆H₆) and carbon tetrachloride (CCl₄) if 22 g of benzene is dissolved in 122 g of carbon tetrachloride.
1.2 Calculate the mole fraction of benzene in solution containing 30% by mass in carbon tetrachloride.
1.3 Calculate the molarity of each of the following solutions: (a) 30 g of Co(NO₃)₂. 6H₂O in 4.3 L of solution (b) 30 mL of 0.5 M H₂SO₄ diluted to 500 mL."

EXTRACTION:
{
  "type": "intext_questions",
  "questions": [
    {
      "number": "1.1",
      "question": "Calculate the mass percentage of benzene (C₆H₆) and carbon tetrachloride (CCl₄) if 22 g of benzene is dissolved in 122 g of carbon tetrachloride."
    },
    {
      "number": "1.2",
      "question": "Calculate the mole fraction of benzene in solution containing 30% by mass in carbon tetrachloride."
    },
    {
      "number": "1.3",
      "question": "Calculate the molarity of each of the following solutions:",
      "parts": [
        "(a) 30 g of Co(NO₃)₂. 6H₂O in 4.3 L of solution",
        "(b) 30 mL of 0.5 M H₂SO₄ diluted to 500 mL"
      ]
    }
  ]
}
```

---

## 9. END-OF-CHAPTER ELEMENTS

### 9.1 Summary
```
START MARKER:   "Summary"
END MARKER:     "Exercises"

CONTENT:        Paragraph(s) summarizing key concepts
                Key terms remain bold

EXTRACTION:
{
  "type": "summary",
  "content": "A solution is a homogeneous mixture of two or more substances...",
  "key_terms": ["mole fraction", "molarity", "molality", "Henry's law", "Raoult's law"]
}
```

### 9.2 Exercises
```
START MARKER:   "Exercises"
QUESTION PATTERN: "X.Y" or "X.YY" followed by question
END MARKER:     "Answers to Some Intext Questions" OR end of chapter

EXAMPLE INPUT:
"Exercises
1.1 Define the term solution. How many types of solutions are formed? Write briefly about each type with an example.
1.2 Give an example of a solid solution in which the solute is a gas.
1.3 Define the following terms:
    (i) Mole fraction  (ii) Molality  (iii) Molarity  (iv) Mass percentage."

EXTRACTION:
{
  "type": "exercises",
  "questions": [
    {
      "number": "1.1",
      "question": "Define the term solution. How many types of solutions are formed? Write briefly about each type with an example.",
      "type": "conceptual"
    },
    {
      "number": "1.2",
      "question": "Give an example of a solid solution in which the solute is a gas.",
      "type": "conceptual"
    },
    {
      "number": "1.3",
      "question": "Define the following terms:",
      "parts": ["(i) Mole fraction", "(ii) Molality", "(iii) Molarity", "(iv) Mass percentage"],
      "type": "definition"
    }
  ]
}
```

### 9.3 Answers to Intext Questions
```
START MARKER:   "Answers to Some Intext Questions"
PATTERN:        "X.Y" followed by answer value(s)

EXAMPLE INPUT:
"Answers to Some Intext Questions
1.1  C₆H₆ = 15.28%, CCl₄ = 84.72%
1.2  0.459, 0.541
1.3  0.024 M, 0.03 M
1.4  36.946 g"

EXTRACTION:
{
  "type": "answers",
  "answers": {
    "1.1": "C₆H₆ = 15.28%, CCl₄ = 84.72%",
    "1.2": "0.459, 0.541",
    "1.3": "0.024 M, 0.03 M",
    "1.4": "36.946 g"
  }
}
```

---

## 10. PAGE ELEMENTS

### 10.1 Footer Detection
```
PATTERN:    "Chemistry" + page number OR page number + chapter name
REGEX:      /Chemistry\s+(\d+)|(\d+)\s+([A-Za-z]+)/
REPRINT:    "Reprint YYYY-YY"

EXAMPLES:
"Chemistry  2"        → page 2
"33  Electrochemistry" → page 33
"Reprint 2026-27"
```

### 10.2 Footnotes
```
MARKER:     "*" at start of line at page bottom
SEPARATOR:  Horizontal line above footnote

EXAMPLE:
"* Strictly speaking activity should be used instead of concentration."
```

---

## 11. EXTRACTION WORKFLOW

### Step 1: Page Classification
```
FOR each page:
  IF contains "Unit" + number + title at top:
    → UNIT_OPENING_PAGE
  ELSE IF contains "Summary" header:
    → SUMMARY_PAGE
  ELSE IF contains "Exercises" header:
    → EXERCISES_PAGE
  ELSE IF contains "Answers to Some Intext Questions":
    → ANSWERS_PAGE
  ELSE:
    → CONTENT_PAGE
```

### Step 2: Element Extraction Order
```
FOR UNIT_OPENING_PAGE:
  1. Extract unit_number
  2. Extract unit_title
  3. Extract qr_code_reference
  4. Extract objectives[]
  5. Extract hook_quote
  6. Extract introduction_paragraph

FOR CONTENT_PAGE:
  1. Extract section_headers[]
  2. Extract body_paragraphs[]
  3. Extract key_terms[] (from bold text)
  4. Extract equations[]
  5. Extract tables[]
  6. Extract figures[]
  7. Extract examples[]
  8. Extract intext_questions[]
  9. Extract footnotes[]
```

### Step 3: Content Parsing
```python
# Pseudocode for parsing body text

def parse_body_text(text):
    elements = []
    
    # Split by section markers
    sections = re.split(r'(\d+\.\d+\s+[A-Z])', text)
    
    for section in sections:
        # Check for key terms
        terms = re.findall(r'is (?:called|known as) \*\*(.+?)\*\*', section)
        
        # Check for equations
        equations = re.findall(r'(.+?)\s+\((\d+\.\d+)\)$', section, re.MULTILINE)
        
        # Check for examples
        if 'Example' in section:
            example = parse_example(section)
            elements.append(example)
        
        elements.extend(terms)
        elements.extend(equations)
    
    return elements
```

---

## 12. SAMPLE FULL PAGE EXTRACTION

### Input (Raw PDF Text):
```
Unit
1
Solutions

Objectives
After studying this Unit, you will be able to
• describe the formation of different types of solutions;
• express concentration of solution in different units;
• state and explain Henry's law and Raoult's law;

Almost all processes in body occur in some kind of liquid solutions.

In normal life we rarely come across pure substances. Most of these are mixtures containing two or more pure substances.

1.1 Types of Solutions

Solutions are homogeneous mixtures of two or more than two components. By homogenous mixture we mean that its composition and properties are uniform throughout the mixture. Generally, the component that is present in the largest quantity is known as solvent. Solvent determines the physical state in which solution exists. One or more components present in the solution other than solvent are called solutes. In this Unit we shall consider only binary solutions (i.e., consisting of two components).

Table 1.1: Types of Solutions
Type of Solution    Solute    Solvent    Common Examples
Gaseous Solutions   Gas       Gas        Mixture of oxygen and nitrogen gases
```

### Output (Structured JSON):
```json
{
  "page_type": "UNIT_OPENING_PAGE",
  "unit": {
    "number": 1,
    "title": "Solutions"
  },
  "objectives": [
    "describe the formation of different types of solutions",
    "express concentration of solution in different units",
    "state and explain Henry's law and Raoult's law"
  ],
  "hook_quote": "Almost all processes in body occur in some kind of liquid solutions.",
  "introduction": "In normal life we rarely come across pure substances. Most of these are mixtures containing two or more pure substances.",
  "sections": [
    {
      "number": "1.1",
      "title": "Types of Solutions",
      "content": [
        {
          "type": "paragraph",
          "text": "Solutions are homogeneous mixtures of two or more than two components. By homogenous mixture we mean that its composition and properties are uniform throughout the mixture."
        },
        {
          "type": "key_term",
          "term": "solvent",
          "context": "the component that is present in the largest quantity is known as solvent"
        },
        {
          "type": "key_term",
          "term": "solutes",
          "context": "One or more components present in the solution other than solvent are called solutes"
        },
        {
          "type": "key_term",
          "term": "binary solutions",
          "context": "we shall consider only binary solutions (i.e., consisting of two components)"
        }
      ]
    }
  ],
  "tables": [
    {
      "number": "1.1",
      "title": "Types of Solutions",
      "headers": ["Type of Solution", "Solute", "Solvent", "Common Examples"],
      "rows": [
        ["Gaseous Solutions", "Gas", "Gas", "Mixture of oxygen and nitrogen gases"]
      ]
    }
  ]
}
```

---

## 13. REGEX PATTERNS SUMMARY

| Element | Regex Pattern |
|---------|---------------|
| Unit Number | `/Unit\s*(\d{1,2})/i` |
| Section Header | `/^(\d+\.\d+)\s+([A-Za-z\s]+)/m` |
| Subsection | `/^(\d+\.\d+\.\d+)\s+(.+)/m` |
| Equation Number | `/\((\d+\.\d+)\)\s*$/` |
| Table Marker | `/Table\s+(\d+\.\d+):\s*(.+)/` |
| Figure Marker | `/Fig\.\s*(\d+\.\d+):\s*(.+)/` |
| Example Marker | `/Example\s+(\d+\.\d+)/` |
| Key Term | `/(?:is|are)\s+(?:called|known as)\s+\*\*(.+?)\*\*/` |
| Intext Q | `/^(\d+\.\d+)\s+(.+\?)/m` |
| Chemical Equation | `/(.+?)\s*(→|⇌)\s*(.+?)\s+\((\d+\.\d+)\)/` |

---

## 14. ELEMENT HIERARCHY

```
CHAPTER
├── unit_number
├── unit_title
├── qr_code
├── objectives[]
├── hook_quote
├── introduction
│
├── SECTIONS[]
│   ├── section_number (X.Y)
│   ├── section_title
│   ├── content
│   │   ├── paragraphs[]
│   │   ├── key_terms[]
│   │   ├── equations[]
│   │   ├── tables[]
│   │   ├── figures[]
│   │   └── subsections[]
│   │       ├── subsection_number (X.Y.Z)
│   │       ├── subsection_title
│   │       └── content...
│   │
│   ├── examples[]
│   │   ├── example_number
│   │   ├── problem
│   │   └── solution
│   │
│   └── intext_questions[]
│       ├── question_number
│       ├── question_text
│       └── parts[] (if multi-part)
│
├── SUMMARY
│   ├── content
│   └── key_terms[]
│
├── EXERCISES[]
│   ├── question_number
│   ├── question_text
│   ├── parts[]
│   └── type (conceptual/numerical)
│
└── ANSWERS{}
    └── question_number: answer
```

---

*Document Version: 1.0*
*Purpose: PDF Text Extraction Rules for NCERT Chemistry*
