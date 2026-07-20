# NCERT Physics Textbook Structure (Class XI, Part I)

> Layout & design spec for implementing NCERT-style physics content.
> Companion to `NCERT_STRUCTURE.md` (chemistry). **Physics is structurally different — do not reuse the chemistry spec.**

**Source book:** `11086 – Physics (Part I)`, Textbook for Class XI, NCERT.
All values below were **measured from the source PDFs** (PyMuPDF), not estimated.

---

## Table of Contents

0. [⚠ Extraction Traps — Read First](#0--extraction-traps--read-first)
1. [Physics vs Chemistry — Key Differences](#1-physics-vs-chemistry--key-differences)
2. [File Naming & Book Assembly](#2-file-naming--book-assembly)
3. [Page Geometry](#3-page-geometry)
4. [Color Palette](#4-color-palette)
5. [Typography](#5-typography)
6. [Chapter Opening Page](#6-chapter-opening-page)
7. [Body Pages (Two-Column Grid)](#7-body-pages-two-column-grid)
8. [Running Headers & Footers](#8-running-headers--footers)
9. [Section Headers](#9-section-headers)
10. [Example Boxes](#10-example-boxes)
11. [Figures](#11-figures)
12. [Tables](#12-tables)
13. [Summary Box](#13-summary-box)
14. [Points to Ponder Box](#14-points-to-ponder-box)
15. [Exercises](#15-exercises)
16. [Answers (Separate File)](#16-answers-separate-file)
17. [Chapter Inventory](#17-chapter-inventory)

---

## 0. ⚠ Extraction Traps — Read First

Four defects in the source PDFs will silently corrupt any naive extraction. All four are **measured**, not theoretical.

### Trap 1 — PUA font corruption (worst)

Some pages use a subsetted font whose `ToUnicode` CMap maps into the **Unicode Private Use Area** (`U+F000`–`U+F0FF`). `pdftotext` and PyMuPDF return unusable glyphs; the text *looks* absent or garbled.

`` → subtract `0xF000` → `CHAPTER`

**Measured scope:**

| File | Pages affected | Severity |
|------|---------------|----------|
| `keph107` (Gravitation) | **10 / 17** | 🔴 majority |
| `keph1ps` (prelims) | **13 / 16** | 🔴 majority |
| `keph102` | 1 / 14 | 🟡 |
| `keph103` | 1 / 22 | 🟡 |
| `keph101`, `keph104`, `keph105`, `keph106`, `keph1an`, `keph1a1` | 0 | ✅ clean |

**Fix (one line):**

```python
def fix_pua(s: str) -> str:
    return ''.join(chr(ord(c) - 0xF000) if 0xF000 <= ord(c) <= 0xF0FF else c for c in s)
```

> This alone is why chapter 7's title and the whole front matter appeared "empty" on first extraction.

### Trap 2 — Page geometry is **not** uniform across files

| File | MediaBox | CropBox origin |
|------|----------|----------------|
| `keph101`, `keph106`, `keph107`, `keph1an`, `keph1a1` | `657.35 × 847.45` | `(27, 27)` — except ⬇ |
| `keph107` | `657.35 × 847.45` | **`(0, 0)`** ⚠ |
| `keph102` – `keph105` | `657.00 × 847.80` | `(27, 27)` |
| `keph1ps` | **`648.00 × 864.00`** ⚠ | **`(20, 40)`** ⚠ |

Consequence — `keph107` content sits **+27 pt** from `keph101`:

| File | Odd-page `x0` | Even-page `x0` |
|------|--------------|---------------|
| `keph101` | `46.7` | `82.7` |
| `keph107` | `73.7` | `109.7` |

> **Rule:** never hard-code absolute x-coordinates across files. Derive column boundaries
> **per page** by clustering block `x0` values. The coordinates in §3 are *reference values for `keph101`*, not universal constants.

### Trap 3 — Margin parity ≠ PDF page index

Margins are mirrored, but parity follows the **printed book page number**, not the PDF page index. Chapter files are cut from the full book, so chapter 7 does not start on an odd book page.

| File | PDF page 1 | Parity by `x0` | Parity by PDF index | Match? |
|------|-----------|---------------|--------------------|--------|
| `keph101` | opener | odd | odd | ✅ |
| `keph107` | opener | **even** | odd | ❌ **wrong** |

> **Rule:** infer parity from measured `x0`, or from the printed page number in the running header — never from `page_index % 2`.

### Trap 4 — Vector figures are invisible to `pdfimages`

Physics figures are overwhelmingly **vector line art** (free-body diagrams, vector triangles), not embedded bitmaps. `pdfimages -png` returns almost nothing. This matters far more in physics than chemistry.

**Consequence:** figure extraction requires either page rendering + crop, or vector-bbox detection. See `PHYSICS_EXTRACTION_RULES.md`.

---

## 1. Physics vs Chemistry — Key Differences

**Read this first.** These are the traps if you carry chemistry assumptions over.

| Aspect | Chemistry (`lech1xx`) | Physics (`keph1xx`) |
|--------|----------------------|---------------------|
| Unit label | `Unit 1` | `CHAPTER ONE` (spelled out, small caps) |
| Accent colour | Pink/magenta | **Cyan `#00AEEF`** |
| Opener sidebar | **Objectives** box (learning goals) | **Section TOC** box (list of section titles) |
| Reflection block | none | **Points to Ponder** box (ch 2–7, *not* ch 1) |
| Body columns | Sidebar + single column | **True two-column** on all body pages |
| Solved example | `Example 1.1` margin label + `Solution` margin label | **Filled cyan box** with `Example 1.3` + `Answer` *below, outside* the box |
| Intext questions | Yes (9–12 per unit) | **None — physics has zero intext questions** |
| Answers | At end of same chapter file | **Separate file** (`keph1an.pdf`) |
| Appendices | Inline | **Separate file** (`keph1a1.pdf`) |
| Front matter | Inline | **Separate file** (`keph1ps.pdf`) |
| Body font | — | **Bookman** family throughout |
| Margins | — | **Mirrored** (odd/even differ by 36 pt) |

> **Critical:** any parser that looks for `Intext Questions` in physics will find nothing.
> Any parser that looks for `Solution` will find nothing — physics uses `Answer`.

---

## 2. File Naming & Book Assembly

The book ships as **10 separate PDFs**. Naming pattern: `keph1` + `<part>`.

| File | Role | Pages | Notes |
|------|------|-------|-------|
| `keph1ps.pdf` | **Prelims** / front matter | 16 | Cover, copyright, ISBN, foreword, preface, contents. Pages 1, 4, 6 are **image-only** (near-zero text). |
| `keph101.pdf` | Chapter 1 — Units and Measurement | 12 | |
| `keph102.pdf` | Chapter 2 — Motion in a Straight Line | 14 | |
| `keph103.pdf` | Chapter 3 — Motion in a Plane | 22 | |
| `keph104.pdf` | Chapter 4 — Laws of Motion | 22 | |
| `keph105.pdf` | Chapter 5 — Work, Energy and Power | 21 | |
| `keph106.pdf` | Chapter 6 — Systems of Particles and Rotational Motion | 35 | |
| `keph107.pdf` | Chapter 7 — Gravitation | 17 | |
| `keph1an.pdf` | **Answers** to all chapter exercises | 9 | Grouped by `Chapter N` heading |
| `keph1a1.pdf` | **Appendices** A1–A… | 16 | Greek alphabet, SI prefixes, constants |

**Decoding the code:**

```
keph1 01
│││││ └┴─ 01–07 = chapter number
││││└──── 1     = Part I
└┴┴┴───── keph  = Class XI (k) + physics (eph)

Special suffixes:  ps = prelims   an = answers   a1 = appendices
```

**Book code:** `11086` (appears in the QR code as `11086CH02` on the chapter opener).

---

## 3. Page Geometry

### 3.1 Boxes

| Box | Value | Notes |
|-----|-------|-------|
| MediaBox | `657.35 × 847.45 pt` | Includes crop marks / bleed — **not** the visible page |
| CropBox | `(27, 27, 630.35, 820.45)` → `603.35 × 793.45 pt` | The trim page ≈ **212.9 × 279.9 mm** |

> When rendering with `pdftoppm`, the **MediaBox** is used by default, so crop marks appear in the raster.
> Use `-cropbox` if you want the trim page only.

### 3.2 Text area — mirrored margins ⚠

Text width is **474 pt on every page**, but the whole block **shifts 36 pt** between odd and even pages:

| Parity | Text x-range | Column 1 | Gutter | Column 2 |
|--------|--------------|----------|--------|----------|
| **Odd** (recto) | `46.7 → 520.7` | `46.7 – 274.0` | `274.0 – 293.4` | `293.4 – 520.7` |
| **Even** (verso) | `82.7 → 556.7` | `82.7 – 310.0` | `310.0 – 329.4` | `329.4 – 556.7` |

| Property | Value |
|----------|-------|
| Column width | `227.3 pt` |
| Gutter width | `19.4 pt` |
| Total text width | `474.0 pt` |
| Odd→even shift | `+36.0 pt` |

> **Why this matters for extraction:** a hard-coded column split at `x = 283` works on odd pages and
> silently corrupts every even page. Derive the split from page parity, or cluster block `x0` values per page.

### 3.3 Vertical

| Element | y (approx) |
|---------|-----------|
| Running header text | `59 – 67` |
| Header rule | `~70` |
| Body top | `~150` |
| Body bottom | `~1010` (varies) |
| Footer `Reprint 2026-27` | `770.6 – 781.6` |

---

## 4. Color Palette

| Role | Hex | Used for |
|------|-----|----------|
| **Primary cyan** | `#00AEEF` | Section headers, running headers, labels, rules |
| Gradient range | `#00AEEF → #00BCF2` | Opener bars (12+ interpolated stops measured) |
| **Pale fill** | `#C7EAFB` | Opener sidebar TOC box, Summary box |
| **Example fill** | `#D4EFFC` | Example box background (lighter than pale fill) |
| Example body text | `#00BDF2` | Text *inside* example boxes |
| **Body text** | `#231F20` | All black body copy (rich black, **not** `#000000`) |
| Footer text | `#000000` | `Reprint 2026-27` only |
| Watermark | `#000000` @ low alpha | `not to be republished` diagonal |

> Note two distinct near-identical blues: `#C7EAFB` (sidebar/summary) vs `#D4EFFC` (example box). They are **not** the same value.

---

## 5. Typography

**Family:** `Bookman` throughout. Weights observed: `Bookman-Light`, `Bookman-Demi`, `Bookman-DemiItalic`, `Bookman,Bold`, `Bookman,Italic`. `Symbol` for glyphs; `Arial` for the footer only.

| Element | Font | Size | Color | Style |
|---------|------|------|-------|-------|
| `CHAPTER ONE` | Bookman Bold | 14 pt | `#231F20` | Small caps, centered |
| Chapter title | Bookman Bold | 20 pt | `#231F20` | Small caps, centered |
| Section **number** (`1.1 `) | Bookman,Bold | 10 pt | **`#231F20`** | see ⚠ below |
| Section **title** (`INTRODUCTION`) | Bookman,Bold | 10 pt | `#00AEEF` | **ALL CAPS** |
| Subsection **number** (`1.3.2 `) | Bookman,Bold / Bookman-Demi | 10 pt | **`#231F20`** | see ⚠ below |
| Subsection **title** (`Rounding off the …`) | Bookman,Bold / Bookman-Demi | 10 pt | `#00AEEF` | Title Case |
| Body text | Bookman-Light | 10 pt | `#231F20` | Justified |
| Sidebar TOC entries | Bookman-Light | 9 pt | `#00AEEF` | |
| Example label | Bookman-DemiItalic | 10 pt | `#00AEEF` | Preceded by ▶ marker |
| Example body | Bookman-Light | 10 pt | `#00BDF2` | Inside filled box |
| `Answer` label | Bookman-DemiItalic | 10 pt | `#00AEEF` | Outside box |
| Answer body | Bookman-Light | 10 pt | `#231F20` | |
| `SUMMARY` / `EXERCISES` | Bookman-Demi | 9 pt | `#00AEEF` | Centered, caps |
| Summary list text | Bookman-Light | 9 pt | `#231F20` | Note: **9 pt**, not 10 |
| Running header | Bookman-Light | 8 pt | `#00AEEF` | |
| Footer | Arial | 8 pt | `#000000` | |

---

## 6. Chapter Opening Page

Page 1 of every chapter file. **Single wide column + sidebar** — *not* two-column.

```
┌────────────────────────────────────────────────────────────┐
│                                              ┌─────────┐   │
│                  CHAPTER ONE                 │ QR CODE │   │
│                  (14pt, centered)            │11086CH02│   │
│                                              └─────────┘   │
│  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  cyan gradient bar        │
│                                                            │
│            UNITS AND MEASUREMENT   (20pt, centered)        │
│                                                            │
│  ▬▬▬▬▬▬▬▬  ▬▬▬▬▬▬▬▬  ▬▬▬▬▬▬▬▬   3-segment gradient bar    │
│                                                            │
│  ┌──────────────┐   1.1  INTRODUCTION                      │
│  │ #C7EAFB      │   Measurement of any physical quantity   │
│  │              │   involves comparison with a certain     │
│  │ 1.1 Introduc.│   basic, arbitrarily chosen ...          │
│  │ 1.2 The int… │                                          │
│  │ 1.3 Signific.│   1.2  THE INTERNATIONAL SYSTEM OF UNITS │
│  │ 1.4 Dimensi… │   In earlier time scientists of ...      │
│  │ 1.5 Dimensi… │                                          │
│  │ 1.6 Dimensi… │   • In CGS system they were ...          │
│  │              │   • In FPS system they were ...          │
│  │   Summary    │                                          │
│  │   Exercises  │                                          │
│  └──────────────┘                                          │
│                     Reprint 2026-27                        │
└────────────────────────────────────────────────────────────┘
```

### Measured coordinates (page 1, odd)

| Element | Rect `(x0, y0, x1, y1)` | Notes |
|---------|------------------------|-------|
| `CHAPTER ONE` | `(235.3, 107.1, 332.0, 123.1)` | center x = 283.6 |
| Chapter title | `(174.8, 178.4, 392.5, 198.4)` | center x = 283.6 |
| Sidebar box fill | `(47.2, 264.1, 212.9, 704.8)` | `#C7EAFB`, w = 165.7, h = 440.7 |
| Sidebar TOC text | `(51.2, 308.2, 208.0, 435.1)` | 9 pt `#00AEEF` |
| `Summary` / `Exercises` | `(76.7, 443.1, 119.4, 464.9)` | indented, end of TOC list. **Ch 2–7 also list `Points to ponder` between them.** |
| Body column | `(230.8, 264.5, 520.7, 710.6)` | **w = 289.9** (single wide column) |
| Footer | `(273.0, 770.6, 330.3, 781.6)` | |

> The opener body column (289.9 pt) is **wider** than a normal body column (227.3 pt). The opener does not use the two-column grid.

### QR code

| Property | Value |
|----------|-------|
| Position | Top-right |
| Format | `11086CH02` = book code `11086` + `CH` + sequence |
| Purpose | Links to NCERT digital resources |

---

## 7. Body Pages (Two-Column Grid)

Pages 2 → end of chapter. Text flows **column 1 → column 2**, then next page.

```
┌────────────────────────────────────────────────────────────┐
│  4                                              PHYSICS    │  ← running header
│ ─────────────────────────────────────────────────────────  │  ← cyan rule
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ column 1             │  │ column 2             │        │
│  │ 227.3 pt             │  │ 227.3 pt             │        │
│  │                      │  │                      │        │
│  │ 1.3.1 Rules for …    │  │ ┌──────────────────┐ │        │
│  │ body text justified  │  │ │▶ Example 1.3     │ │ ← box  │
│  │ …                    │  │ │  #D4EFFC fill    │ │        │
│  │                      │  │ └──────────────────┘ │        │
│  │                      │  │  Answer  (outside)   │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                    Reprint 2026-27                         │
└────────────────────────────────────────────────────────────┘
      ↑ 19.4 pt gutter ↑
```

**Full-width breakouts.** These elements ignore the column grid and span all 474 pt:

- Summary box
- Exercises section
- Wide tables (e.g. Table 1.1 SI Base Quantities)
- Wide figures

---

## 8. Running Headers & Footers

| Parity | Left | Right |
|--------|------|-------|
| **Even** | Page number | `PHYSICS` |
| **Odd** | Chapter title (e.g. `UNITS AND MEASUREMENT`) | Page number |

- Font: Bookman-Light 8 pt `#00AEEF`
- A **cyan rule** sits immediately below the header text
- Header is **absent** on the chapter opening page (page 1)

**Footer:** `Reprint 2026-27`, Arial 8 pt `#000000`, centered, on **every** page including the opener.

**Watermark:** `not to be republished` + `© NCERT` diagonal, `#000000` at low alpha, rect `(57.4, 194.6, 530.2, 666.3)`. Present on every page. **Must be stripped during extraction.**

---

## 9. Section Headers

| Level | Pattern | Case | Example |
|-------|---------|------|---------|
| Section | `N.M` + 2 spaces + TITLE | **ALL CAPS** | `1.1  INTRODUCTION` |
| Subsection | `N.M.P` + 2 spaces + Title | Title Case | `1.3.1  Rules for Arithmetic Operations with Significant Figures` |

### ⚠ Headers are **two-colour** — the number is NOT cyan

Measured, span by span:

```
'1.1  '        color=#231F20  ← BLACK    (the number)
'INTRODUCTION' color=#00AEEF  ← CYAN     (the title)

'1.3.2   '                          color=#231F20  ← BLACK
'Rounding off the Uncertain Digits' color=#00AEEF  ← CYAN
```

> **Trap:** filtering headers by `color == 0x00AEEF` matches the **title only** and silently drops the number.
> Detect the header by the *line*, then read number and title from separate spans.

**Font varies** between `Bookman,Bold` and `Bookman-Demi` for the same role (`1.3.2` uses `Bookman,Bold`, `1.6.1` uses `Bookman-Demi`). Match on **size + colour**, not font name.

**Depth:** physics goes to **3 levels max** (`N.M.P`). No 4th level observed.

> **Extraction trap:** section titles wrap across lines in the source. Raw `pdftotext` yields
> `1.2 The international system of` / `units` as two lines. The title **must** be rejoined —
> this is the same bug that produced chemistry's truncated `"Solubility of"`.

---

## 10. Example Boxes

The single biggest structural difference from chemistry.

```
┌─────────────────────────────────────┐
│ ▶ Example 1.3  Let us consider an   │   ← #D4EFFC fill
│                equation             │      label: DemiItalic #00AEEF
│        ½ m v² = m g h               │      body:  Light #00BDF2
│   where m is the mass of the body,  │
│   v its velocity … Check whether    │
│   this equation is dimensionally    │
│   correct.                          │
└─────────────────────────────────────┘
  Answer  The dimensions of LHS are      ← OUTSIDE the box
     [M] [L T⁻¹]² = [M] [L²T⁻²]             label: DemiItalic #00AEEF
                 = [M L² T⁻²]               body:  Light #231F20
```

| Property | Value |
|----------|-------|
| Box fill | `#D4EFFC` |
| Box width | `226.4 pt` (≈ one column) |
| Marker | `▶` triangle, cyan, before label |
| Label | `Example N.M`, Bookman-DemiItalic 10 pt `#00AEEF` |
| Question text | Bookman-Light 10 pt `#00BDF2` — **inside** box |
| Answer label | `Answer`, Bookman-DemiItalic 10 pt `#00AEEF` — **outside/below** box |
| Answer text | Bookman-Light 10 pt `#231F20` — **outside** box |

**Measured example (p8, ch1):** box rect `(329.8, 547.8, 556.2, 657.8)`, w = 226.4, h = 110.0 — sits in column 2 of an even page (col 2 = `329.4 – 556.7`). ✓ aligns.

> **Extraction rule:** the example is the box; the answer is *not* in the box. Colour is the
> most reliable separator — question text is `#00BDF2`, answer text is `#231F20`.

---

## 11. Figures

| Property | Value |
|----------|-------|
| Caption pattern | `Fig. N.M` **or** `Fig N.M` — ⚠ **inconsistent in source** |
| Sub-labels | `(a)`, `(b)`, `(c)` — sometimes `Fig 3.13a` |
| Placement | Within a column, or full-width breakout |
| Type | Mostly **vector line art** (not raster) |

> `pdfimages` will **miss most physics figures** — they are drawn as vector graphics, not embedded bitmaps.
> Physics is diagram-heavy (mechanics vectors, free-body diagrams), so this matters more than in chemistry.

**Caption regex must tolerate both forms:**

```regex
Fig\.?\s*(\d+)\.(\d+)([a-z])?
```

---

## 12. Tables

| Property | Value |
|----------|-------|
| Caption pattern | `Table N.M <Title>` — **no colon** after the number |
| Footnote marker | Trailing `*` on the caption, footnote below table |
| Placement | Usually **full-width breakout** |

**Example:** `Table 1.1 SI Base Quantities and Units*`

> Contrast with chemistry, which uses `Table 1.2: Values of Henry's Law Constant …` (**with** colon).
> A shared regex across both books must make the colon optional.

**Chapter 1 tables:** `Table 1.1`, `Table 1.2`. Chapter 3 has **none** — table presence varies widely by chapter.

---

## 13. Summary Box

| Property | Value |
|----------|-------|
| Heading | `SUMMARY`, Bookman-Demi 9 pt `#00AEEF`, **centered** |
| Box fill | `#C7EAFB` |
| Layout | **Full-width breakout** (single column) |
| Content | **Numbered list** `1.` … `N.` |
| Body font | Bookman-Light **9 pt** `#231F20` (smaller than body copy) |

**Measured (ch1, p10):** box rect `(106.7, 82.5, 532.7, 522.9)`, w = 426.0, h = 440.5. Heading at `(295, 93, 344, 102)` — centered on the box.

**Chapter 1 summary:** 11 numbered points.

---

## 14. Points to Ponder Box

**Present in chapters 2–7. Absent from chapter 1.**

> ⚠ This element does not exist in chapter 1 — the chapter most people use as a template.
> Deriving the spec from `keph101` alone **will miss it entirely**.

A **third, distinct box style** — do not conflate with Summary or Exercises:

| | Summary | Points to Ponder | Exercises |
|---|---------|------------------|-----------|
| Box | **Filled** `#C7EAFB` | **Outlined**, no fill | **None** |
| Border | none | `#00AEEF`, `0.96 pt` | — |
| Heading align | **centered** | **left** | **centered** |
| Body text colour | `#231F20` (black) | **`#00AEEF` (all cyan)** | `#231F20` |

```
┌──────────────────────────────────────────────────────────┐  ← #00AEEF stroke, 0.96pt
│  POINTS TO PONDER            ← left-aligned, cyan bold   │     NO fill
│   1.  The origin and the positive direction of an axis   │
│       are a matter of choice. You should first specify   │  ← ALL body text cyan
│   2.  If a particle is speeding up, acceleration is in   │
│       the direction of velocity; if its speed is …       │
│   …                                                      │
└──────────────────────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Heading | `POINTS TO PONDER`, Bookman,Bold 9 pt `#00AEEF`, **left-aligned** |
| Box | stroke `#00AEEF`, width `0.96 pt`, **fill `None`** |
| Body | Bookman 9 pt **`#00AEEF`** — *all cyan, unlike every other body text* |
| List numbers | Bookman 9 pt `#00AEEF` |
| Layout | full-width breakout |

**Measured (ch2, p11):** box rect `(62.7, 323.4, 504.7, 630.0)`, w = 442.0, h = 306.5. Heading bbox `(85, 340, 183, 349)` — left-aligned at x = 85, **not** centered.

### Location per chapter

| Ch | File | PtP present | PDF page |
|----|------|-------------|----------|
| 1 | `keph101` | ❌ **no** | — |
| 2 | `keph102` | ✅ | 11 |
| 3 | `keph103` | ✅ | 20 |
| 4 | `keph104` | ✅ | 19 |
| 5 | `keph105` | ✅ | 17 |
| 6 | `keph106` | ✅ | 33 |
| 7 | `keph107` | ✅ | 15 |

**Order within a chapter:** `… body → Summary → Points to Ponder → Exercises`
(Chapter 1: `… body → Summary → Exercises`)

The opener sidebar TOC reflects this — ch1 lists `Summary / Exercises`; ch2–7 list `Summary / Points to ponder / Exercises`.

---

## 15. Exercises

| Property | Value |
|----------|-------|
| Heading | `EXERCISES`, Bookman-Demi 9 pt `#00AEEF`, **centered** |
| Box | **None** — no fill, unlike Summary |
| Layout | **Full-width breakout** (single column) |
| Numbering | `N.M` in **cyan bold**, continuous from `N.1` |
| Sub-parts | `(a)` `(b)` `(c)` `(d)` — indented under the parent |
| Preamble | Optional bold note, e.g. `Note : In stating numerical answers, take care of significant figures.` |

**Measured (ch1, p10):** heading at `(303, 559, 360, 568)`.

> **Numbering is strictly sequential `N.1 → N.max` with no gaps.** This is the strongest
> validation invariant available — see `PHYSICS_EXTRACTION_RULES.md`.

---

## 16. Answers (Separate File)

`keph1an.pdf` — 9 pages, covers **all 7 chapters**.

```
Chapter 1
1.1   (a) 10–6 ; (b) 1.5 × 104 ; (c) 5 ; (d) 11.3, 1.13 × 104.
1.2   (a) 107 ; (b) 10–16 ; (c) 3.9 × 104 ; (d) 6.67 × 10–8.
1.5   500
1.6   (c)
…
```

| Property | Value |
|----------|-------|
| Grouping | `Chapter N` heading, then answers |
| Numbering | Matches exercise numbers |
| **Coverage** | **Partial — not every exercise has an answer** |

**Chapter 1:** answers exist for `1.1, 1.2, 1.4, 1.5, 1.6, 1.7, 1.9 – 1.17`.
**Missing:** `1.3`, `1.8` — these are descriptive/explain questions with no numeric answer.

> Do **not** validate answers as `1.1 → N.max` contiguous. Gaps are legitimate.
> Validate instead: `set(answer_numbers) ⊆ set(exercise_numbers)`.

---

## 17. Chapter Inventory

Ground-truth counts, measured from source. Use these as extraction test fixtures.

| Ch | File | Title | Pages | Exercises | Examples | Intext Q | PtP | PUA |
|----|------|-------|-------|-----------|----------|----------|-----|-----|
| 1 | `keph101` | Units and Measurement | 12 | **1.1 – 1.17** (17) | 1.1 – 1.5 (5) | 0 | ❌ | clean |
| 2 | `keph102` | Motion in a Straight Line | 14 | **→ 2.18** (18) | 7 | 0 | ✅ p11 | 1 pg |
| 3 | `keph103` | Motion in a Plane | 22 | **→ 3.22** (22) | 9 | 0 | ✅ p20 | 1 pg |
| 4 | `keph104` | Laws of Motion | 22 | **→ 4.23** (23) | 12 | 0 | ✅ p19 | clean |
| 5 | `keph105` | Work, Energy and Power | 21 | **→ 5.23** (23) | 16 | 0 | ✅ p17 | clean |
| 6 | `keph106` | Systems of Particles and Rotational Motion | 35 | **→ 6.17** (17) | 13 | 0 | ✅ p33 | clean |
| 7 | `keph107` | Gravitation | 17 | **→ 7.21** (21) | 5 | 0 | ✅ p15 | 🔴 10 pg |

**Chapter 2 sections** (verified — confirms the sidebar TOC pattern):

| Section | Title |
|---------|-------|
| 2.1 | Introduction |
| 2.2 | Instantaneous velocity and speed |
| 2.3 | Acceleration |
| 2.4 | Kinematic equations for uniformly accelerated motion |
| 2.5 | Relative velocity |
| — | Summary |
| — | **Points to ponder** |
| — | Exercises |

**Chapter 1 detail:**

| Section | Title |
|---------|-------|
| 1.1 | Introduction |
| 1.2 | The International System of Units |
| 1.3 | Significant Figures |
| 1.3.1 | Rules for Arithmetic Operations with Significant Figures |
| 1.3.2 | Rounding off the Uncertain Digits |
| 1.3.3 | Rules for Determining the Uncertainty in the Results of Arithmetic Calculations |
| 1.4 | Dimensions of Physical Quantities |
| 1.5 | Dimensional Formulae and Dimensional Equations |
| 1.6 | Dimensional Analysis and its Applications |
| 1.6.1 | Checking the Dimensional Consistency of Equations |
| **1.6.2** | **Deducing Relation among the Physical Quantities** |
| — | Summary |
| — | Exercises |

> **Intext Q = 0 across all 7 chapters** — verified by grep. This is a structural property of the physics book, not an extraction gap.

---

## Provenance

Every measurement above came from the source PDFs via PyMuPDF (`get_drawings`, `get_text('dict')`,
`get_text('blocks')`) and `pdftotext`. Colours are exact fill/span values. Coordinates are in
MediaBox space unless noted. Nothing in this document is estimated or inferred from the chemistry spec.
