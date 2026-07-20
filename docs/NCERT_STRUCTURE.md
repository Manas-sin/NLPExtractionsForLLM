# NCERT Chemistry Textbook Structure (Class 11 & 12)

> Complete structural template for implementing NCERT-style educational content

---

## Table of Contents

1. [Unit Opening Page](#1-unit-opening-page)
2. [Section Headers](#2-section-headers)
3. [Text Formatting](#3-text-formatting)
4. [Equations](#4-equations)
5. [Tables](#5-tables)
6. [Figures & Diagrams](#6-figures--diagrams)
7. [Solved Examples](#7-solved-examples)
8. [Intext Questions](#8-intext-questions)
9. [Footnotes](#9-footnotes)
10. [End-of-Chapter Elements](#10-end-of-chapter-elements)
11. [Page Layout](#11-page-layout)
12. [Special Elements](#12-special-elements)
13. [Typography](#13-typography)
14. [Color Palette](#14-color-palette)

---

## 1. Unit Opening Page

### 1.1 Overall Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ┌─────────┐                        ┌─────────────────────┐     │
│  │ QR CODE │                        │       Unit          │     │
│  │         │                        │                     │     │
│  │12085CH02│                        │    2               │ PINK│
│  └─────────┘                        │                     │ BAR │
│                                     │ Electrochemistry    │     │
│                                     └─────────────────────┘     │
│                                                                  │
│  ┌─────────────────────┐    ┌────────────────────────────────┐  │
│  │ Objectives          │    │ Italicized Hook/Quote          │  │
│  │ (cursive, pink)     │    │ (yellow/gold color)            │  │
│  ├─────────────────────┤    │                                │  │
│  │After studying this  │    │ Chemical reactions can be used │  │
│  │Unit, you will be    │    │ to produce electrical energy...│  │
│  │able to              │    │                                │  │
│  │• objective 1;       │    ├────────────────────────────────┤  │
│  │• objective 2;       │    │                                │  │
│  │• objective 3;       │    │ Introduction paragraph         │  │
│  │• ...                │    │ (regular text)                 │  │
│  │                     │    │                                │  │
│  └─────────────────────┘    └────────────────────────────────┘  │
│  ↑ Red sidebar                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 QR Code

| Property | Value |
|----------|-------|
| Position | Top-left corner |
| Size | ~2cm × 2cm |
| Code Format | `XXXXXCHYY` (e.g., `12085CH02`) |
| Purpose | Links to digital resources |

### 1.3 Unit Banner

| Property | Value |
|----------|-------|
| Color | Pink/Magenta gradient |
| "Unit" text | Cursive/italic, white |
| Number | Large numeral (50-60pt), light pink |
| Title | Decorative cursive font |

### 1.4 Objectives Box

| Property | Value |
|----------|-------|
| Header | "Objectives" in cursive, pink/magenta |
| Left border | Red sidebar (3-4px wide) |
| Lead-in text | "After studying this Unit, you will be able to" |
| Bullet style | Solid black dots (•) |
| Punctuation | Semicolons (;) after each, period (.) after last |

### 1.5 Hook/Quote

| Property | Value |
|----------|-------|
| Style | Fully italicized |
| Color | Yellow/gold |
| Purpose | Real-world connection to topic |
| Position | Right side, below unit title |

---

## 2. Section Headers

### 2.1 Main Section (Format: X.Y)

```
2.1 Electrochemical    ← Number: regular font
    Cells              ← Title: cursive/decorative
    ─────              ← Red underline beneath title
```

| Property | Value |
|----------|-------|
| Number format | X.Y (Chapter.Section) |
| Title font | Decorative cursive |
| Decoration | Red/maroon underline |
| Position | Left margin |

### 2.2 Subsection (Format: X.Y.Z)

```
2.2.1 Measurement      ← All bold text
      of Electrode     ← Multi-line allowed
      Potential        ← No underline
```

| Property | Value |
|----------|-------|
| Number format | X.Y.Z (Chapter.Section.Subsection) |
| Font | Bold, regular serif |
| Decoration | None |

### 2.3 Sub-subsection (No number)

```
Effect of temperature  ← Italicized text
─────────────────────  ← Underlined
```

| Property | Value |
|----------|-------|
| Number | None |
| Font | Italic |
| Decoration | Underlined |

---

## 3. Text Formatting

### 3.1 Key Terms (First Introduction)

| Context | Format | Example |
|---------|--------|---------|
| Definition | **bold** | "is called **electrode potential**" |
| New concept | **bold** | "called a **galvanic** or **voltaic** cell" |
| With abbreviation | **bold (abbrev)** | "**cell electromotive force (emf)**" |

### 3.2 Important Laws/Principles

| Type | Format | Example |
|------|--------|---------|
| Law name | **bold** | "**Henry's law**" |
| Possessive | **bold** | "**Dalton's law of partial pressures**" |
| Equation name | **bold** | "**Nernst equation**" |

### 3.3 Important Statements

- Entire sentence in **bold** for crucial definitions
- Example: "**the solubility of a gas in a liquid is directly proportional to the partial pressure of the gas**"

### 3.4 Scientific Notation

| Type | Examples |
|------|----------|
| Subscripts | H₂O, CO₂, Cu²⁺, Zn²⁺ |
| Superscripts | mol⁻¹, cm², 10⁻⁵, E° |
| Greek letters | Δ, π, α, χ, κ, Λ, ρ, Ω |

---

## 4. Equations

### 4.1 Chemical Equations

```
Zn(s) + Cu²⁺(aq) → Zn²⁺(aq) + Cu(s)                          (2.1)
```

| Property | Value |
|----------|-------|
| Numbering | Right margin, format `(X.Y)` |
| State symbols | (s), (l), (g), (aq) |
| Forward arrow | → |
| Reversible arrow | ⇌ |

### 4.2 Half-Cell Reactions

```
(i)  Cu²⁺ + 2e⁻  → Cu(s)     (reduction half reaction)       (2.2)
(ii) Zn(s) → Zn²⁺ + 2e⁻      (oxidation half reaction)       (2.3)
```

### 4.3 Mathematical Equations

```
E(cell) = E°(cell) - (RT/nF) ln Q                            (2.8)

Molarity = Moles of solute / Volume of solution in litre     (1.8)
```

### 4.4 Cell Notation

```
Cu(s) | Cu²⁺(aq) || Ag⁺(aq) | Ag(s)
      ↑          ↑↑         ↑
   single     double     single
   line       line       line
   (phase)    (salt      (phase)
              bridge)
```

---

## 5. Tables

### 5.1 Standard Table Format

```
          Table 2.1: Standard Electrode Potentials at 298 K

┌───────────────────────────────────────┬────────────────────────┐
│ Reaction (Oxidised form + ne⁻        │        E°/V            │
│            → Reduced form)            │                        │
├───────────────────────────────────────┼────────────────────────┤
│ F₂(g) + 2e⁻ → 2F⁻                    │         2.87           │
│ Co³⁺ + e⁻ → Co²⁺                     │         1.81           │
│ ...                                   │         ...            │
└───────────────────────────────────────┴────────────────────────┘
         ↑ PINK HEADER ROW (white text)
```

### 5.2 Table Features

| Feature | Description |
|---------|-------------|
| Caption | Bold "Table X.Y:" above table |
| Header row | Pink/coral background, white text |
| Borders | Full grid lines |
| Footnotes | Below table with asterisk (*) |

### 5.3 Tables with Side Annotations

```
│ ↑ Increasing strength   │         │   ↑ Increasing strength │
│   of oxidising agent    │         │     of reducing agent   │
│ ↓                       │         │   ↓                     │
```

---

## 6. Figures & Diagrams

### 6.1 Figure Structure

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│     [DIAGRAM - colored illustration]                         │
│                                                              │
│            (a)                    (b)                        │
└──────────────────────────────────────────────────────────────┘

Fig. 2.1: Daniell cell having electrodes of zinc and copper 
          dipping in the solutions of their respective salts.
          ↑                        ↑
       Bold "Fig. X.Y:"        Italic caption
```

### 6.2 Figure Properties

| Property | Value |
|----------|-------|
| Label | "Fig. X.Y:" in bold |
| Caption | Italicized, can be multi-line |
| Sub-figures | Labeled (a), (b), (c) |
| Position | Left, right, or centered |

### 6.3 Multi-part Figures

```
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│               │  │               │  │               │
│      (a)      │  │      (b)      │  │      (c)      │
│  Eext < 1.1V  │  │  Eext = 1.1V  │  │  Eext > 1.1V  │
└───────────────┘  └───────────────┘  └───────────────┘
```

### 6.4 Graph Features

| Feature | Description |
|---------|-------------|
| Axes | Labeled with units |
| Y-axis label | Rotated 90° counterclockwise |
| Grid lines | When applicable |
| Data points | Circles or dots |
| Legend | If multiple lines |

---

## 7. Solved Examples

### 7.1 Type A: Full Box (Cyan background)

```
┌─────────────────────────────────────────────────────────────────┐
│ Example 2.1                                                     │
│ ───────────  ← Cyan header bar                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [Problem statement here]                                        │
│                                                                 │
│ Solution                                                        │
│ ────────  ← Cyan text                                           │
│                                                                 │
│ [Step-by-step solution here]                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Type B: Side Label Style

```
┌────────────────────────────────────────────────┬───────────────┐
│ [Problem statement here]                       │ Example 1.1   │
│                                                │  (cyan box)   │
├────────────────────────────────────────────────┤               │
│ [Solution content here]                        │ Solution      │
│                                                │  (cyan text)  │
└────────────────────────────────────────────────┴───────────────┘
```

### 7.3 Example Components

| Component | Style |
|-----------|-------|
| Header "Example X.Y" | Cursive "Example", regular number |
| Problem statement | Regular text |
| "Solution" label | Cursive, cyan/teal color |
| Working | Step-by-step with equations |
| Final answer | May be underlined or highlighted |

---

## 8. Intext Questions

### 8.1 Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                                     Intext Questions            │
│                                     ────────────────            │
│ ← Light pink/coral                  (cursive, underlined)       │
│   background                                                    │
│                                                                 │
│ 2.1  How would you determine the standard electrode potential   │
│      of the system Mg²⁺|Mg?                                     │
│                                                                 │
│ 2.2  Can you store copper sulphate solutions in a zinc pot?    │
│                                                                 │
│ 2.3  Consult the table of standard electrode potentials and    │
│      suggest three substances that can oxidise ferrous ions    │
│      under suitable conditions.                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Properties

| Property | Value |
|----------|-------|
| Background | Light pink/coral shading |
| Header | "Intext Questions" in cursive, underlined |
| Header position | Right-aligned |
| Numbering | X.Y format (matches chapter) |
| Placement | After completing a major topic |
| Purpose | Practice before next topic |

---

## 9. Footnotes

### 9.1 Page Footnotes

```
─────────────────────────────────────────────────────────────────
* Strictly speaking activity should be used instead of 
  concentration. It is directly proportional to concentration. 
  In dilute solutions, it is equal to concentration. You will 
  study more about it in higher classes.
```

### 9.2 Footnote Properties

| Property | Value |
|----------|-------|
| Marker | Asterisk (*) in text |
| Position | Bottom of page |
| Separator | Horizontal line above |
| Font | Smaller, italic |
| Purpose | Additional info, clarifications, historical notes |

---

## 10. End-of-Chapter Elements

### 10.1 Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                           Summary                               │
│                           ───────                               │
│                        (cursive, centered, bordered box)        │
│                                                                 │
│ A solution is a homogeneous mixture of two or more substances. │
│ Solutions are classified as solid, liquid and gaseous          │
│ solutions. The concentration of a solution is expressed in     │
│ terms of mole fraction, molarity, molality and in percentages. │
│                                                                 │
│ [Key terms remain **bold** within summary]                      │
│                                                                 │
│ [Laws stated in their key form with bold names]                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Exercises

```
                                                      Exercises
                                                      ─────────
│ ← Red sidebar                                    (cursive, red)
│
│ 1.1  Define the term solution. How many types of solutions are
│      formed? Write briefly about each type with an example.
│
│ 1.2  Give an example of a solid solution in which the solute 
│      is a gas.
│
│ 1.3  Define the following terms:
│      (i) Mole fraction  (ii) Molality  (iii) Molarity
│      (iv) Mass percentage.
│
│ ...
│
│ 1.41 Determine the osmotic pressure of a solution prepared by
│      dissolving 25 mg of K₂SO₄ in 2 litre of water at 25° C,
│      assuming that it is completely dissociated.
```

### 10.3 Exercise Properties

| Property | Value |
|----------|-------|
| Sidebar | Red, left edge |
| Header | "Exercises" in cursive, red |
| Numbering | X.Y format continuing from chapter |
| Question types | Conceptual, numerical, application-based |
| Multi-part format | (a), (b), (c) or (i), (ii), (iii) |

### 10.4 Answers to Intext Questions

```
              Answers to Some Intext Questions
              ─────────────────────────────────

1.1   C₆H₆ = 15.28%, CCl₄ = 84.72%
1.2   0.459, 0.541
1.3   0.024 M, 0.03 M
1.4   36.946 g
...
```

| Property | Value |
|----------|-------|
| Content | Brief numerical answers only |
| Explanations | None |
| Position | Last page of chapter |

---

## 11. Page Layout

### 11.1 Footer Format

```
Even pages (left-aligned):          Odd pages (right-aligned):
Chemistry ▌ 32 ▌                              ▌ 33 ▌ Electrochemistry

─────────────────────────────────────────────────────────────────────
                           Reprint 2026-27
```

### 11.2 Margins

| Margin | Size | Notes |
|--------|------|-------|
| Left | ~2.5 cm | Binding margin |
| Right | ~2 cm | |
| Top | ~2 cm | |
| Bottom | ~2.5 cm | Footer space |

### 11.3 Two-Column Layout (when used)

```
┌─────────────────────┬─────────────────────┐
│ Text content        │ Figure/Diagram      │
│ flows here          │ positioned here     │
│ alongside the       │ with caption        │
│ illustration        │ below it            │
└─────────────────────┴─────────────────────┘
```

---

## 12. Special Elements

### 12.1 Chemical Structures

```
         H₃C       Cl
            \     /
             C=O···H—C
            /     \
         CH₃       Cl
                    \
                     Cl
```

| Feature | Description |
|---------|-------------|
| Bonds | Single (-), double (=), triple (≡) |
| Lone pairs | Two dots (:) |
| Hydrogen bonding | Dotted lines (···) |

### 12.2 Electrode/Cell Diagrams

| Feature | Description |
|---------|-------------|
| Electrode colors | Zn: gray, Cu: brown/copper |
| Electron flow | Arrows with e⁻ label |
| Labels | anode (-ve), cathode (+ve) |
| Salt bridge | Clearly marked U-tube shape |
| Solutions | Labeled (ZnSO₄, CuSO₄) |

### 12.3 Graphs with Trends

| Feature | Description |
|---------|-------------|
| Trend arrows | On sides indicating "Increasing X" |
| Axis labels | With units (e.g., "Pressure / atm") |
| Data points | Connected with lines |
| Legend | If multiple datasets |

---

## 13. Typography

### 13.1 Font Specifications

| Element | Font Type | Size | Style | Color |
|---------|-----------|------|-------|-------|
| Unit Title | Decorative cursive | ~28pt | Regular | Black |
| Section (X.Y) | Cursive | ~14pt | Underlined | Black + Red line |
| Subsection (X.Y.Z) | Serif | ~12pt | Bold | Black |
| Body text | Serif | ~11pt | Regular | Black |
| Key terms | Serif | ~11pt | Bold | Black |
| Equations | Math font | ~11pt | Italic variables | Black |
| Example header | Cursive | ~12pt | Regular | Cyan/Teal |
| Solution label | Cursive | ~11pt | Regular | Cyan/Teal |
| Intext Q header | Cursive | ~12pt | Underlined | Pink/Coral |
| Table header text | Sans-serif | ~10pt | Bold | White |
| Figure caption | Serif | ~10pt | Italic | Black |
| Footnote | Serif | ~9pt | Italic | Black |
| Footer | Serif | ~10pt | Regular | Black |

---

## 14. Color Palette

### 14.1 Primary Colors

| Element | Color Name | Hex Code | RGB |
|---------|------------|----------|-----|
| Unit banner | Pink/Magenta | #E91E63 | 233, 30, 99 |
| Section underline | Red/Maroon | #8B0000 | 139, 0, 0 |
| Example boxes | Cyan/Teal | #00BCD4 | 0, 188, 212 |
| Intext Q background | Light Coral | #FFB6C1 | 255, 182, 193 |
| Exercise sidebar | Red | #D32F2F | 211, 47, 47 |
| Table headers | Coral/Pink | #FF6B6B | 255, 107, 107 |
| Objectives sidebar | Red | #C62828 | 198, 40, 40 |
| Hook/Quote text | Gold/Yellow | #FFD700 | 255, 215, 0 |

### 14.2 Secondary Colors

| Element | Color Name | Hex Code |
|---------|------------|----------|
| Page number box (even) | Pink | #F48FB1 |
| Page number box (odd) | Cyan | #4DD0E1 |
| Light background | Light Gray | #F5F5F5 |
| Highlight | Yellow | #FFEB3B |

---

## 15. Content Flow Summary

### 15.1 Chapter Structure (In Order)

1. **Unit Opening Page**
   - QR Code
   - Unit banner (number + title)
   - Objectives box
   - Hook/Quote
   - Introduction paragraph

2. **Main Content**
   - Sections (X.Y) with content
   - Subsections (X.Y.Z) as needed
   - Figures & Tables interspersed
   - Solved Examples after relevant concepts
   - Intext Questions after major topics

3. **End Matter**
   - Summary box
   - Exercises section
   - Answers to Intext Questions

### 15.2 Typical Page Flow

```
┌─────────────────────────────────────────────────────────────┐
│ [Header area - empty or running head]                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Main content area]                                         │
│                                                             │
│   - Section headers                                         │
│   - Body text with bold key terms                          │
│   - Equations (numbered)                                    │
│   - Figures with captions                                   │
│   - Tables with headers                                     │
│   - Example boxes                                           │
│   - Intext question boxes                                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Footnotes if any]                                          │
├─────────────────────────────────────────────────────────────┤
│ Chemistry ▌ 42 ▌                         Reprint 2026-27    │
└─────────────────────────────────────────────────────────────┘
```

---

## 16. Implementation Notes

### 16.1 Key Design Principles

1. **Consistency**: Same formatting throughout all chapters
2. **Hierarchy**: Clear visual distinction between section levels
3. **Accessibility**: Bold terms, numbered equations for reference
4. **Engagement**: Colored boxes, real-world connections
5. **Practice**: Intext questions for self-assessment

### 16.2 Critical Elements

| Element | Purpose |
|---------|---------|
| Objectives | Learning outcomes preview |
| Bold terms | Vocabulary building |
| Solved Examples | Step-by-step problem solving |
| Intext Questions | Concept reinforcement |
| Summary | Quick revision |
| Exercises | Practice and assessment |

### 16.3 File Naming Convention

```
lech1XX.pdf  →  Class 11/12 Chemistry Part 1, Unit XX
lech2XX.pdf  →  Class 11/12 Chemistry Part 2, Unit XX

Examples:
lech101.pdf  →  Unit 1 (Solutions)
lech102.pdf  →  Unit 2 (Electrochemistry)
```

---

*Document Version: 1.0*
*Based on: NCERT Chemistry Class 12 (Reprint 2026-27)*
