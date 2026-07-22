# NCERT PDF Extraction for LLM

Extract structured JSON from NCERT textbooks (Class 11 & 12) for LLM training.

## System Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │     │  API LAYER  │     │ EXTRACTION  │     │ PROCESSING  │     │  STORAGE    │
├─────────────┤     ├─────────────┤     ├─────────────┤     ├─────────────┤     ├─────────────┤
│ PDF Upload  │────▶│  FastAPI    │────▶│ PDFExtractor│────▶│ Structurer  │────▶│ PostgreSQL  │
│ Batch Dir   │     │  Pydantic   │     │ OCR/Vision  │     │ Watermark   │     │ File Store  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API** | FastAPI, Uvicorn, Pydantic | REST API, async server, validation |
| **PDF Processing** | PyMuPDF (fitz) | Text extraction, page rendering |
| **OCR** | Tesseract | Scanned PDF text extraction |
| **AI/Vision** | Claude API (Anthropic) | Complex layout extraction |
| **Image Processing** | OpenCV | Watermark removal, figure extraction |
| **Database** | PostgreSQL, psycopg2 | Structured data storage (JSONB) |

## Data Flow Pipeline

```
1. PDF Ingestion      →  Upload via API or batch directory
2. Page Rendering     →  Convert pages to PNG (PyMuPDF)
3. Text Extraction    →  OCR (Tesseract) or Vision API (Claude)
4. Content Structuring →  Parse into sections, examples, exercises
5. Image Processing   →  Extract figures, remove watermarks
6. Database Storage   →  Save to PostgreSQL with JSONB
```

## Project Structure

```
ncert_extractor/
├── src/                        # Core library
│   ├── extractors/             # Extraction strategies
│   │   ├── pdf_extractor.py    # PyMuPDF-based extraction
│   │   ├── ocr_extractor.py    # Tesseract OCR
│   │   ├── vision_extractor.py # Claude Vision API
│   │   ├── physics_structurer.py
│   │   └── ncert_structurer.py
│   ├── processors/             # Post-processing
│   │   ├── watermark.py        # Watermark removal (OpenCV)
│   │   └── cleaner.py          # Markdown cleanup
│   ├── validators/             # Quality checks
│   ├── subjects/               # Subject configs
│   └── utils/                  # Shared utilities
│
├── scripts/                    # CLI entry points
│   ├── extract.py              # Single PDF extraction
│   ├── batch_extract.py        # Batch processing
│   ├── structure_physics.py    # Physics structurer
│   └── validate.py             # Validation CLI
│
├── web/                        # Web interface
│   └── app.py                  # FastAPI server
│
├── config/                     # Configuration files
│   └── ncert_extraction_rules.json
│
└── data/                       # Output (gitignored)
    ├── uploads/
    ├── extracted/
    └── extracted_physics/
```

## Database Schema

```sql
-- chapters table
CREATE TABLE chapters (
    id SERIAL PRIMARY KEY,
    book_code VARCHAR(20) UNIQUE NOT NULL,
    subject VARCHAR(50),
    class INTEGER,
    chapter_number INTEGER,
    title TEXT,
    content JSONB,              -- Full structured content
    created_at TIMESTAMP DEFAULT NOW()
);

-- sections table
CREATE TABLE sections (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id),
    section_number VARCHAR(10),
    title TEXT,
    content TEXT,
    equations JSONB
);

-- exercises table
CREATE TABLE exercises (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id),
    number VARCHAR(10),
    text TEXT,
    sub_parts JSONB,
    answer TEXT
);

-- figures table
CREATE TABLE figures (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id),
    figure_number VARCHAR(10),
    caption TEXT,
    image_path TEXT
);
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/extract` | Upload and extract PDF |
| `GET` | `/api/books` | List all extracted books |
| `GET` | `/api/books/{book_code}` | Get chapter content |
| `GET` | `/api/files/{book}/{type}/{file}` | Serve renders/figures |
| `GET` | `/api/search?q={query}` | Search across chapters |
| `DELETE` | `/api/books/{book_code}` | Delete extraction |

## Supported Subjects

| Subject | Prefix | Example |
|---------|--------|---------|
| Chemistry | `lech` | `lech101.pdf` |
| Biology | `kebo` | `kebo101.pdf` |
| Physics | `keph` | `keph101.pdf` |
| Maths | `kemh` | `kemh101.pdf` |

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract (macOS)
brew install tesseract

# Install Poppler for PDF rendering (macOS)
brew install poppler
```

## Usage

### CLI Extraction

```bash
# Single PDF with OCR
python scripts/extract.py /path/to/keph101.pdf --ocr

# With Claude Vision (requires ANTHROPIC_API_KEY in .env)
python scripts/extract.py /path/to/keph101.pdf --vision

# Batch processing
python scripts/batch_extract.py /path/to/pdfs/ --subject physics

# Structure physics chapters
python scripts/structure_physics.py keph101
python scripts/structure_physics.py --all
```

### Web Interface

```bash
python web/app.py
# Open http://localhost:8080
# API docs: http://localhost:8080/docs
```

### Validation

```bash
python scripts/validate.py keph101
```

## Output Format

Output: `data/extracted/<book_code>/structured_physics.json`

```json
{
  "book_code": "keph101",
  "subject": "physics",
  "class": 11,
  "chapter_number": 1,
  "chapter_title": "Units and Measurement",
  "sections": [
    {
      "number": "1.1",
      "title": "INTRODUCTION",
      "content": "Measurement of any physical quantity..."
    }
  ],
  "tables": [
    {
      "number": "1.1",
      "title": "SI Base Quantities and Units",
      "headers": ["Name", "Symbol", "Value"],
      "rows": [{"Name": "metre", "Symbol": "m", "Value": "..."}]
    }
  ],
  "examples": [
    {
      "number": "1.1",
      "problem": "Each side of a cube is measured...",
      "solution": "The number of significant figures..."
    }
  ],
  "exercises": [
    {
      "number": "1.4",
      "text": "Explain this statement...",
      "sub_parts": [
        {"label": "a", "text": "atoms are very small objects"},
        {"label": "b", "text": "a jet plane moves with great speed"}
      ]
    }
  ],
  "equations": [
    {"type": "display", "latex": "F = ma"},
    {"type": "inline", "latex": "v = \\frac{dx}{dt}"}
  ],
  "summary": [
    "Physics is a quantitative science...",
    "Each base quantity is defined..."
  ],
  "statistics": {
    "section_count": 11,
    "example_count": 5,
    "exercise_count": 15,
    "equation_count": 64
  }
}
```

## Features

- **Multi-strategy extraction**: PyMuPDF (text-based), Tesseract (OCR), Claude Vision (AI)
- **Structured output**: Sections, examples, exercises with sub-parts, tables with rows
- **LaTeX equations**: Display and inline math converted to LaTeX
- **Figure extraction**: Automatic figure detection with watermark removal
- **Validation**: Quality checks for extracted content
- **REST API**: FastAPI with Swagger docs
