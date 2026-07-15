# Agent Implementation Guide

Step-by-step guide for implementing and validating the NCERT text extractor.

## Prerequisites

```bash
# Ensure Python 3.10+
python --version

# Install PyMuPDF
pip install pymupdf
```

## Implementation Steps

### Step 1: Create the Extractor

Create `extract_ncert.py` with these components:

1. **`extract_book_page(text)`** - Parse first line for printed page number
2. **`clean_text(text)`** - Normalize whitespace, collapse blank lines
3. **`extract_pdf(pdf_path, output_dir)`** - Main extraction loop
4. **`main()`** - CLI argument handling

### Step 2: Test with a Sample PDF

Download a test PDF:
```bash
curl -O https://ncert.nic.in/textbook/pdf/lech101.pdf
```

Run extraction:
```bash
python extract_ncert.py lech101.pdf
```

Expected output structure:
```
extracted/lech101/
├── pages.json
└── pages/
    ├── page_001.txt
    ├── page_002.txt
    └── ...
```

### Step 3: Validate Output

#### Check 1: JSON Structure

```python
import json
data = json.load(open('extracted/lech101/pages.json'))

# Every entry has required fields
for entry in data:
    assert 'page' in entry
    assert 'book_page' in entry  # can be None
    assert 'char_count' in entry
    assert 'text' in entry

# Pages are sequential
pages = [e['page'] for e in data]
assert pages == list(range(1, len(data) + 1))
```

#### Check 2: Character Counts

```python
# No completely empty pages (unless PDF has blank pages)
for entry in data:
    if entry['char_count'] < 50:
        print(f"Warning: page {entry['page']} has only {entry['char_count']} chars")
```

#### Check 3: Book Page Detection

```python
# Most pages should have book_page detected
detected = sum(1 for e in data if e['book_page'] is not None)
total = len(data)
print(f"Book page detected: {detected}/{total} ({100*detected/total:.0f}%)")
# Expect > 90% for typical chapters
```

#### Check 4: Content Sanity

```python
# Chemistry chapter should mention key terms
all_text = ' '.join(e['text'] for e in data).lower()
expected_terms = ['electrochemical', 'cell', 'electrode', 'oxidation']
for term in expected_terms:
    assert term in all_text, f"Missing expected term: {term}"
```

### Step 4: Test Edge Cases

1. **Chapter opener page** - Should have `book_page: null`
2. **Image-heavy page** - Low char_count but shouldn't crash
3. **Table page** - Text may be jumbled but should extract
4. **Last page** - Often has exercises, should extract normally

## Common Issues and Fixes

### Issue: UnicodeDecodeError

**Cause**: PDF has non-UTF8 characters in metadata
**Fix**: Already handled by PyMuPDF, but if you modify text handling,
ensure you're using `encoding='utf-8'` consistently.

### Issue: book_page is always null

**Cause**: First line extraction regex doesn't match NCERT format
**Fix**: Check the actual first line content. Some chapters have different
formatting. Adjust regex in `extract_book_page()`.

### Issue: Garbled text

**Cause**: PDF uses custom fonts without Unicode mapping
**Fix**: This is rare for official NCERT PDFs. If it happens, the PDF
itself is problematic. Try a different chapter.

### Issue: Out of memory on large PDF

**Cause**: Loading entire PDF into memory
**Fix**: PyMuPDF streams pages, so this shouldn't happen for typical
NCERT chapters (< 50 pages). If it does, process pages one at a time
and close each before opening next.

## Performance Notes

- Typical NCERT chapter (30 pages): < 2 seconds
- Memory usage: ~50MB peak for typical chapter
- Output size: JSON is ~100-200KB for typical chapter

## Integration Points

The output `pages.json` is designed for downstream consumption:

```python
# Load extracted pages
pages = json.load(open('extracted/lech101/pages.json'))

# Find page by book page number
def get_by_book_page(book_page: int):
    return next((p for p in pages if p['book_page'] == book_page), None)

# Get all text as single string
full_text = '\n\n'.join(p['text'] for p in pages)

# Filter to high-content pages
content_pages = [p for p in pages if p['char_count'] > 500]
```
