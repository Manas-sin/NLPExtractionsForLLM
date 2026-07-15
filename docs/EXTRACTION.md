# How the Extractor Works

## Overview

The extractor uses PyMuPDF (fitz) to read PDF pages sequentially and extract
their text content. It's deliberately simple: no OCR, no table parsing, no
equation rendering — just raw text extraction with minimal cleanup.

## Processing Pipeline

```
PDF page → PyMuPDF get_text() → clean_text() → extract_book_page() → JSON + .txt
```

### 1. Text Extraction

PyMuPDF's `page.get_text()` returns the page's text in reading order. This
works well for NCERT PDFs because they're digitally generated (not scanned),
so the text layer is clean.

### 2. Text Cleaning

The `clean_text()` function:
- Normalizes line endings (CRLF/CR → LF)
- Strips trailing whitespace from each line
- Collapses 3+ consecutive blank lines to 2 (preserves paragraph structure)
- Strips leading/trailing whitespace from the whole page

We intentionally preserve:
- Line breaks (they often indicate structure)
- Indentation (for code blocks, lists)
- Multiple spaces within lines (may be intentional formatting)

### 3. Book Page Detection

NCERT pages typically have the printed page number on the first line by itself.
We detect this with a regex: `^(\d{1,3})$`

This returns `null` for:
- Chapter opener pages (no page number, just title)
- Pages where the first line is content, not a number
- Blank or near-empty pages

## NCERT-Specific Gotchas

### Chapter Openers

First page of each chapter often has:
- No printed page number
- Large decorative text
- Chapter number in a different format ("Chapter 2" vs "2")

Solution: `book_page` is `null` for these. Downstream consumers should handle
this gracefully.

### Two-Column Layout

Some NCERT pages use two-column layout. PyMuPDF extracts left column first,
then right column. This is usually correct reading order but may cause issues
with:
- Tables spanning columns
- Figures with captions
- Equations continuing across columns

### Equations and Formulas

PyMuPDF extracts equations as Unicode where possible, but complex LaTeX-style
formulas often extract poorly. Examples:
- Subscripts/superscripts may be on wrong lines
- Fraction bars disappear
- Greek letters usually extract correctly (Δ, θ, etc.)

This is a known limitation. For chemistry/physics chapters, downstream
consumers should expect some formula garbling.

### Headers and Footers

NCERT PDFs have:
- Subject name in header (e.g., "Chemistry")
- Page number (we extract this)
- Chapter name sometimes in footer

These are extracted inline with content. No special handling.

### Figures and Images

Images extract as nothing (blank space). Figure captions extract normally.
The `char_count` field helps detect image-heavy pages (low char count).

## File Naming Convention

```
page_001.txt  ← PDF page 1 (always starts at 001)
page_002.txt  ← PDF page 2
...
```

The filename uses PDF page number (`page` field), not book page number
(`book_page` field). This is intentional:
- File names are predictable (always sequential from 001)
- No gaps or collisions from `null` book pages
- Easy to iterate programmatically

## Validation Heuristics

To check extraction quality:

1. **char_count sanity**: Pages with < 100 chars are suspicious (maybe
   image-only or extraction failed)

2. **book_page continuity**: In a well-extracted chapter, book pages should
   be mostly sequential (gaps okay for chapter openers)

3. **Common words**: Chemistry chapters should contain "atom", "molecule",
   etc. Absence suggests extraction issues.

## Limitations

This extractor does NOT:
- Parse tables into structured data
- Render equations to LaTeX
- Extract images or diagrams
- Handle scanned PDFs (no OCR)
- Parse hierarchical structure (sections, subsections)

These are all intentional. This stage produces raw, lossless text. Structure
extraction is a separate downstream concern.
