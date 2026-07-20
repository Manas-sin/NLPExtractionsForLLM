# NCERT PDF Extraction for LLM

Extract structured JSON from NCERT textbooks (Class 11 & 12) for LLM training.

## Project Structure

```
ncert_extractor/
├── src/                    # Core library
│   ├── extractors/         # PDF & Vision extraction
│   ├── processors/         # Watermark removal, cleaning
│   ├── validators/         # Extraction quality checks
│   ├── subjects/           # Subject configs (chapters, prefixes)
│   └── utils/              # Shared utilities
│
├── scripts/                # CLI entry points
│   ├── extract.py          # Single PDF extraction
│   ├── batch_extract.py    # Batch processing
│   └── validate.py         # Validation CLI
│
├── web/                    # Web interface
│   └── app.py              # Flask app
│
├── config/                 # Configuration files
│   ├── ncert_extraction_rules.json
│   └── ncert_structure.json
│
├── data/                   # Output (gitignored)
│   ├── uploads/
│   └── extracted/
│
└── docs/                   # Documentation
```

## Supported Subjects

| Subject | Prefix | Example |
|---------|--------|---------|
| Chemistry | `lech` | `lech101.pdf` |
| Biology | `kebo` | `kebo101.pdf` |
| Physics | `keph` | `keph101.pdf` |
| Maths | `kemh` | `kemh101.pdf` |

## Installation

```bash
pip install -r requirements.txt
brew install poppler  # For PDF rendering (macOS)
```

## Usage

### CLI Extraction

```bash
# Single PDF
python scripts/extract.py /path/to/kebo101.pdf

# With vision enhancement (requires ANTHROPIC_API_KEY)
python scripts/extract.py /path/to/kebo101.pdf --vision

# Batch processing
python scripts/batch_extract.py /path/to/pdfs/ --subject biology
```

### Web Interface (FastAPI)

```bash
python web/app.py
# Open http://localhost:8080
# API docs: http://localhost:8080/docs
```

### Validation

```bash
python scripts/validate.py kebo101
```

## Output Structure

Output: `data/extracted/<book_code>/`

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

## Features

- Raw text extraction with LaTeX formula conversion
- Vision-based extraction using Claude API
- Structured sections, examples, exercises
- Figure extraction with watermark removal
- Validation and quality checks
