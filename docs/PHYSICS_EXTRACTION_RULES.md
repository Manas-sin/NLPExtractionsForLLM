# NCERT Physics — Extraction Rules & Validation

> How to pull structured content **out of** `keph1*.pdf`.
> Companion to `PHYSICS_STRUCTURE.md` (which describes how to render it back in).
> Machine-readable form: `physics_extraction_rules.json`.

---

## Table of Contents

1. [Pre-flight — Non-negotiable](#1-pre-flight--non-negotiable)
2. [Target Schema](#2-target-schema)
3. [Parsing Rules](#3-parsing-rules)
4. [Validation Constraints](#4-validation-constraints)
5. [Ground-Truth Fixtures](#5-ground-truth-fixtures)
6. [Recommended Pipeline](#6-recommended-pipeline)

---

## 1. Pre-flight — Non-negotiable

Run these **before** any parsing. Each one corresponds to a measured defect (see `PHYSICS_STRUCTURE.md` §0).

### 1.1 Repair PUA text

```python
def fix_pua(s: str) -> str:
    """Undo Private-Use-Area font mapping. MUST run before any regex."""
    return ''.join(chr(ord(c) - 0xF000) if 0xF000 <= ord(c) <= 0xF0FF else c for c in s)
```

**Apply to every string** from `get_text()` / `pdftotext`. Without it, `keph107` (10/17 pages) and `keph1ps` (13/16 pages) yield garbage.

**Self-check:** after repair, `assert 'CHAPTER' in fix_pua(page1_text).upper()`

### 1.2 Derive column split per page — never hard-code

```python
def column_split(page) -> float:
    """Cluster block x0 values; return the x that separates col1 from col2."""
    xs = sorted(b[0] for b in page.get_text('blocks') if b[4].strip())
    if not xs:
        return None
    left = xs[0]                     # column 1 starts here
    # column 2 starts at the first x0 more than ~200pt right of column 1
    right = next((x for x in xs if x > left + 200), None)
    return (left + right) / 2 if right else None
```

Hard-coding `x = 283` works on `keph101` odd pages and **silently corrupts** every even page and all of `keph107`.

### 1.3 Determine parity from geometry, not index

```python
parity = 'odd' if min_x0 < (page.rect.width / 2 - 240) else 'even'
```

Or read the printed page number from the running header. **Never** `page_index % 2` — that is wrong for `keph107`.

### 1.4 Strip boilerplate

| Pattern | Action |
|---------|--------|
| `not to be republished` | remove (watermark) |
| `©\s*NCERT` | remove (watermark) |
| `Reprint \d{4}-\d{2}` | remove (footer) |
| `^\s*PHYSICS\s*$` | remove (running header) |
| `^\s*\d{1,3}\s*$` | remove (page number) |
| chapter title alone on a line at y < 75 | remove (running header) |

---

## 2. Target Schema

```jsonc
{
  "book_code": "11086",
  "chapter_number": 1,
  "chapter_title": "Units and Measurement",
  "source_file": "keph101.pdf",
  "total_pages": 12,

  "sidebar_toc": ["1.1 Introduction", "...", "Summary", "Exercises"],

  "sections": [
    {
      "number": "1.3",
      "title": "Significant Figures",     // MUST be non-empty, MUST NOT be truncated
      "text": "…",                        // MUST be non-empty
      "subsections": [
        { "number": "1.3.1", "title": "Rules for Arithmetic Operations with Significant Figures", "text": "…" }
      ]
    }
  ],

  "examples": [
    { "number": "1.3", "question": "…", "answer": "…" }   // note: "answer", NOT "solution"
  ],

  "figures": [
    { "number": "1.1", "caption": "…", "page": 7, "image": "figures/fig1_1.png" }
  ],

  "tables": [
    { "number": "1.1", "caption": "SI Base Quantities and Units", "footnote": "…", "rows": [[...]] }
  ],

  "summary": ["point 1", "point 2", "…"],          // numbered list -> array

  "points_to_ponder": ["point 1", "…"],            // null for chapter 1

  "exercises": [
    { "number": "1.1", "text": "…", "parts": ["(a) …", "(b) …"] }
  ],

  "answers": { "1.1": "…", "1.2": "…" },            // from keph1an.pdf; PARTIAL by design

  "statistics": {
    "section_count": 6,
    "example_count": 5,
    "table_count": 2,
    "figure_count": 1,
    "equation_count": 0,
    "exercise_count": 17,
    "intext_question_count": 0                      // ALWAYS 0 in physics
  }
}
```

> **`intext_questions` is deliberately absent.** Physics has none — verified across all 7 chapters.
> A field that is always empty is a liability; omit it or pin it to `0`.

---

## 3. Parsing Rules

### 3.1 Sections

| Rule | Detail |
|------|--------|
| Detect by | **font + colour**, not regex: `Bookman-Demi` @ 10 pt, colour `#00AEEF` |
| Section | `^(\d+)\.(\d+)\s+([A-Z][A-Z\s,'-]+)$` — ALL CAPS |
| Subsection | `^(\d+)\.(\d+)\.(\d+)\s+(.+)$` — Title Case |
| Max depth | 3 (`N.M.P`) |

**⚠ Title rejoining — mandatory.**
Titles wrap across lines. Raw text gives:

```
1.2 The international system of
units
```

Rejoin **before** storing, or you reproduce chemistry's `"Solubility of"` bug. Rejoin rule: while the next line is same-font/same-colour and the current title has no terminal punctuation, append it.

> Prefer the **sidebar TOC on page 1** as the authoritative source for **section titles** — it is compact and reliable.
>
> ⚠ **But the TOC lists sections only (`1.1–1.6`), never subsections.** Chapter 1's `1.6.2 Deducing Relation
> among the Physical Quantities` exists in the body and is **absent from the TOC**. Subsections must be
> discovered from in-body headers; an extractor that trusts the TOC alone reports 0 subsections.

### 3.1a ⚠ Headers are two-colour — do not filter by `#00AEEF`

```
'1.1  '        color=#231F20   ← BLACK  (number)
'INTRODUCTION' color=#00AEEF   ← CYAN   (title)
```

Filtering header spans by `color == 0x00AEEF` matches the **title only** and drops the number.
Detect the *line*, then read number and title from separate spans. Also: font alternates between
`Bookman,Bold` and `Bookman-Demi` for the same role — match on **size + colour**, never font name.

### 3.2 Examples — colour is the separator

Physics examples are **not** delimited by keywords reliably. Use colour:

| Element | Colour | Location |
|---------|--------|----------|
| Label `Example N.M` | `#00AEEF`, Bookman-DemiItalic | inside box |
| **Question** | **`#00BDF2`** | **inside** box (`#D4EFFC` fill) |
| Label `Answer` | `#00AEEF`, Bookman-DemiItalic | outside box |
| **Answer** | **`#231F20`** | **outside** box |

```python
# question text is the ONLY body text in the book coloured #00BDF2
is_question = (span['color'] == 0x00BDF2)
```

> Do **not** search for `Solution` — physics uses `Answer`. Do not assume the answer is inside the box; it is not.

### 3.3 Figures

```regex
Fig\.?\s*(\d+)\.(\d+)([a-z])?
```

The period is **inconsistent** in the source (`Fig. 1.1` in ch1, `Fig 3.13` in ch3). Regex must tolerate both.

**Extraction:** `pdfimages` will miss these — they are vector. Use:
1. Render page at 300 DPI (`pdftoppm -r 300`)
2. Locate figure bbox via caption position + vector drawing cluster
3. Crop

### 3.4 Tables

```regex
Table\s+(\d+)\.(\d+)\s*:?\s*(.+?)(\*?)$
```

Colon is **optional** — physics omits it (`Table 1.1 SI Base Quantities and Units*`), chemistry includes it (`Table 1.2: Values of…`). Trailing `*` marks a footnote.

### 3.5 Summary / Points to Ponder / Exercises

All three are **full-width breakouts** — disable two-column logic once detected.

| Block | Heading | Box | Body colour | Detect by |
|-------|---------|-----|-------------|-----------|
| Summary | `SUMMARY`, centered | filled `#C7EAFB` | `#231F20` | fill colour |
| Points to Ponder | `POINTS TO PONDER`, **left** | **stroked** `#00AEEF`, no fill | **`#00AEEF`** | stroke + no fill |
| Exercises | `EXERCISES`, centered | none | `#231F20` | heading only |

**Points to Ponder is absent in chapter 1** — treat as `null`, not as a parse failure.

### 3.6 Exercises

```regex
^(\d+)\.(\d+)\s+(.+)
```

**⚠ The killer bug.** Values inside question text match this pattern. Chemistry's extraction produced exercise numbers `0.1`, `273.15`, `2.3`, `120.7` because it regexed blindly.

**Guard — all three required:**

1. **Expect the next number only.** Track `expected = (chapter, last_n + 1)`. Reject any match that isn't it.
2. **Chapter must match.** `int(m[1]) == chapter_number` — kills `273.15`, `0.15`.
3. **Colour check.** Exercise numbers are **cyan bold**; numbers in prose are `#231F20`.

```python
def is_exercise_number(m, chapter, last_n, span_color):
    return (int(m[1]) == chapter
            and int(m[2]) == last_n + 1
            and span_color == 0x00AEEF)
```

### 3.7 Answers

Parse `keph1an.pdf`, grouped by `Chapter N`. **Coverage is partial by design** — ch1 has no answer for `1.3` or `1.8` (descriptive questions).

---

## 4. Validation Constraints

Run after every extraction. **Fail loudly** — a silent bad extraction is worse than a crash.

### 4.1 Hard constraints (must pass)

| # | Constraint | Rationale |
|---|-----------|-----------|
| V1 | Exercise numbers form **exactly** `{c}.1 … {c}.max`, contiguous, no gaps, no duplicates | strongest invariant available |
| V2 | Every exercise number has `chapter == c` | kills `273.15`-type garbage |
| V3 | Every section `title` is non-empty | catches truncation |
| V4 | Every section `text` is non-empty | chemistry shipped 7 sections with `text_len == 0` |
| V5 | No section title ends with a preposition/article (`of`, `the`, `in`, `a`, `and`, `for`, `with`) | catches `"Solubility of"` |
| V6 | Example numbers contiguous `{c}.1 … {c}.max` | |
| V7 | `set(answers) ⊆ set(exercises)` | answers are partial; subset, not equality |
| V8 | `intext_question_count == 0` | physics has none |
| V9 | No text contains PUA chars `U+F000–U+F0FF` | proves `fix_pua` ran |
| V10 | No text contains `not to be republished` / `Reprint 20` | proves boilerplate stripped |

### 4.2 Soft constraints (warn)

| # | Constraint |
|---|-----------|
| W1 | `points_to_ponder` present for ch 2–7, `null` for ch 1 |
| W2 | `figure_count > 0` for mechanics chapters (2–6) |
| W3 | Section count matches sidebar TOC length |
| W4 | Mean section `text` length > 200 chars |

### 4.3 Reference implementation

```python
PREPOSITIONS = {'of', 'the', 'in', 'a', 'an', 'and', 'for', 'with', 'to', 'on', 'its'}

def validate(doc: dict) -> list[str]:
    errs, c = [], doc['chapter_number']

    # V1/V2 — exercises contiguous and chapter-correct
    nums = [e['number'] for e in doc['exercises']]
    parsed = [tuple(map(int, n.split('.'))) for n in nums]
    for ch, _ in parsed:
        if ch != c:
            errs.append(f'V2: exercise chapter {ch} != {c}')
    got = sorted(n for ch, n in parsed if ch == c)
    if got != list(range(1, len(got) + 1)):
        missing = set(range(1, (max(got) if got else 0) + 1)) - set(got)
        errs.append(f'V1: exercises not contiguous; missing {sorted(missing)}')

    # V3/V4/V5 — sections
    for s in doc['sections']:
        if not s.get('title', '').strip():
            errs.append(f"V3: section {s['number']} has empty title")
        if not s.get('text', '').strip():
            errs.append(f"V4: section {s['number']} has empty text")
        if s.get('title', '').split() and s['title'].split()[-1].lower() in PREPOSITIONS:
            errs.append(f"V5: section {s['number']} title truncated: {s['title']!r}")

    # V6 — examples contiguous
    ex = sorted(int(e['number'].split('.')[1]) for e in doc.get('examples', []))
    if ex and ex != list(range(1, len(ex) + 1)):
        errs.append(f'V6: examples not contiguous: {ex}')

    # V7 — answers subset of exercises
    extra = set(doc.get('answers', {})) - set(nums)
    if extra:
        errs.append(f'V7: answers reference non-existent exercises: {sorted(extra)}')

    # V8 — no intext questions in physics
    if doc['statistics'].get('intext_question_count', 0) != 0:
        errs.append('V8: physics must have 0 intext questions')

    # V9/V10 — cleanliness
    blob = json.dumps(doc)
    if any(0xF000 <= ord(ch) <= 0xF0FF for ch in blob):
        errs.append('V9: unrepaired PUA characters — fix_pua did not run')
    for bad in ('not to be republished', 'Reprint 20'):
        if bad in blob:
            errs.append(f'V10: boilerplate not stripped: {bad!r}')

    return errs
```

---

## 5. Ground-Truth Fixtures

Assert against these. They are measured from source, not assumed.

```python
GROUND_TRUTH = {
    1: dict(title='Units and Measurement', pages=12, exercises=17, examples=5,
            intext=0, ptp=None,  pua_pages=0,  tables=2),
    2: dict(title='Motion in a Straight Line', pages=14, exercises=18, examples=7,
            intext=0, ptp=11,    pua_pages=1),
    3: dict(title='Motion in a Plane', pages=22, exercises=22, examples=9,
            intext=0, ptp=20,    pua_pages=1,  tables=0),
    4: dict(title='Laws of Motion', pages=22, exercises=23, examples=12,
            intext=0, ptp=19,    pua_pages=0),
    5: dict(title='Work, Energy and Power', pages=21, exercises=23, examples=16,
            intext=0, ptp=17,    pua_pages=0),
    6: dict(title='Systems of Particles and Rotational Motion', pages=35, exercises=17,
            examples=13, intext=0, ptp=33, pua_pages=0),
    7: dict(title='Gravitation', pages=17, exercises=21, examples=5,
            intext=0, ptp=15,    pua_pages=10),
}

CH1_ANSWERS_PRESENT = {'1.1','1.2','1.4','1.5','1.6','1.7',
                       '1.9','1.10','1.11','1.12','1.13','1.14','1.15','1.16','1.17'}
CH1_ANSWERS_MISSING = {'1.3', '1.8'}   # descriptive questions — legitimately absent
```

**Regression test order.** Extract in this sequence — it surfaces bugs earliest:

1. `keph101` — clean baseline, no PtP, no PUA
2. `keph107` — **worst case**: PUA (10 pg) + CropBox `(0,0)` + parity anomaly
3. `keph102` — first PtP chapter
4. Remainder

> If `keph107` passes, the pipeline is sound. Testing only `keph101` proves almost nothing —
> it is the single least representative chapter in the book.

---

## 6. Recommended Pipeline

Tiered by concern. Do not solve everything with one tool.

| Tier | Content | Tool | Cost |
|------|---------|------|------|
| 1 | Text + structure | PyMuPDF `get_text('dict')` + `fix_pua` + per-page column split | free |
| 2 | Colour-tagged elements (examples, PtP, exercise numbers) | PyMuPDF span colours | free |
| 3 | Vector figures | `pdftoppm -r 300` + bbox crop | free |
| 4 | Verification only | Claude vision on rendered page | ~$0.01/pg |

**Why not `pdftotext`:** it discards colour and font, which are the *only* reliable separators for examples (`#00BDF2` vs `#231F20`) and exercise numbers (cyan vs black). It also mangles two-column reading order. Use PyMuPDF's `dict` mode.

**Where vision earns its cost:** not bulk text — use it to spot-check pages that fail validation, and to read figure content. Running vision on all 184 pages is ~$2 and unnecessary if V1–V10 pass.

---

## Provenance

Every rule traces to a measured defect or a verified invariant in the source PDFs.
The validation constraints are derived from **actual failures** observed in the chemistry
extraction (`extracted/lech101/`): truncated titles, empty section text, and exercise
numbers `0.1` / `273.15` / `2.3` / `120.7` parsed out of question prose.
