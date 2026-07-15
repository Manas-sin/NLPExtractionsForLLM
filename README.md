# NCERT PDF Extraction for LLM

Extract structured JSON from NCERT textbooks (Class 11 & 12) for LLM training.

## Supported Subjects

| Subject | Prefix | Example |
|---------|--------|---------|
| Chemistry | `lech` | `lech101.pdf` |
| Biology | `kebo` | `kebo101.pdf` |
| Physics | `keph` | `keph101.pdf` |
| Maths | `kemh` | `kemh101.pdf` |

## Features

- Raw text extraction with LaTeX formula conversion
- Structured sections, examples, exercises
- Figure extraction with watermark removal
- Clean diagram recreation (45+ diagram types)
- Combined `final_output.json` with everything

## Installation

```bash
pip install -r requirements.txt
brew install poppler  # For PDF rendering (macOS)
```

## Usage

```bash
python extract_ncert.py /path/to/kebo101.pdf
```

Output: `extracted/<book_code>/final_output.json`

## Output Structure

```json
{
  "book_code": "kebo101",
  "unit_title": "The Living World",
  "pages": [...],
  "sections": [...],
  "diagrams": [...],
  "exercises": [...],
  "statistics": {...}
}
```

## Files

- `extract_ncert.py` - Main extraction script
- `structure_ncert.py` - Converts raw text to structured JSON
- `ncert_subjects.py` - Subject config (chapters, prefixes)
- `recreate_*.py` - Diagram recreation for each subject
- `remove_watermark.py` - Watermark removal from figures
