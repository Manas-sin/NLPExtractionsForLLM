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

---

## Why These Technologies?

### API Layer: FastAPI

| Why FastAPI? | Alternatives Considered |
|--------------|------------------------|
| **Async support** - handles concurrent PDF uploads | Flask (sync only) |
| **Auto API docs** - Swagger UI at `/docs` | Django (overkill) |
| **Pydantic validation** - type-safe requests | Express.js (not Python) |
| **Performance** - one of the fastest Python frameworks | - |

### PDF Processing: PyMuPDF (fitz)

| Why PyMuPDF? | Alternatives Considered |
|--------------|------------------------|
| **Fast** - C-based, handles large PDFs | PyPDF2 (slower, less features) |
| **Full extraction** - text, images, renders | pdfplumber (text only) |
| **Page rendering** - converts to PNG for OCR/Vision | pdf2image (needs Poppler) |
| **Figure detection** - finds images with captions | - |

### OCR: Tesseract

| Why Tesseract? | Alternatives Considered |
|----------------|------------------------|
| **Free & open source** - no API costs | Google Cloud Vision (paid) |
| **Offline** - no internet needed | AWS Textract (paid) |
| **Good accuracy** - 95%+ for clean text | EasyOCR (slower) |
| **Multi-language** - supports Hindi, Sanskrit | - |

### AI/Vision: Claude API (Anthropic)

| Why Claude Vision? | Alternatives Considered |
|--------------------|------------------------|
| **Best for complex layouts** - two-column, equations | GPT-4 Vision (similar cost) |
| **LaTeX conversion** - converts formulas accurately | Google Gemini (less accurate) |
| **Table understanding** - extracts rows/columns | Tesseract (can't do this) |
| **Context-aware** - understands physics/chemistry | - |

**When to use which:**
```
Simple PDF (text-based)     → PyMuPDF (free, instant)
Scanned PDF                 → Tesseract OCR (free, 2-3 sec/page)
Complex layout/equations    → Claude Vision (paid, best quality)
```

### Image Processing: OpenCV

| Why OpenCV? | Alternatives Considered |
|-------------|------------------------|
| **Watermark removal** - HSV color masking | Pillow (basic only) |
| **Fast** - C++ based | scikit-image (slower) |
| **Industry standard** - well documented | - |

### Document Parsing: Docling (IBM)

| Why Docling? | Alternatives Considered |
|--------------|------------------------|
| **ML-based PDF parsing** - understands document structure | PyMuPDF (basic extraction) |
| **Table extraction** - accurate row/column detection | Tabula (rule-based, brittle) |
| **Equation detection** - finds and extracts formulas | Regex (misses complex layouts) |
| **Scientific documents** - built for research papers/textbooks | pdf2image + OCR (manual) |
| **Structured output** - JSON with hierarchy | - |

**What Docling extracts:**
```
Input: NCERT Physics PDF page

Docling Output:
├── sections (with hierarchy)
├── tables (rows, columns, headers)
├── equations (LaTeX-ready)
├── figures (with captions)
└── reading order (correct sequence)
```

**Docling vs PyMuPDF vs Claude Vision:**
```
Docling                     PyMuPDF                   Claude Vision
├── ML-based structure      ├── Rule-based            ├── AI-based
├── Free & local            ├── Free & local          ├── Paid API
├── Table-aware             ├── Basic tables          ├── Best tables
├── Equation detection      ├── No equation support   ├── LaTeX conversion
├── Fast (local ML)         ├── Very fast             ├── Slow (API call)
└── Good for batch          └── Good for simple PDFs  └── Good for complex
```

**Use cases in our system:**
- Extract tables with proper structure
- Detect equation regions
- Understand two-column layouts
- Batch process without API costs

### Database: PostgreSQL

| Why PostgreSQL? | Alternatives Considered |
|-----------------|------------------------|
| **JSONB support** - store structured JSON natively | MongoDB (no relations) |
| **pgvector extension** - semantic search with embeddings | Pinecone (paid, separate service) |
| **Relational + JSON** - best of both worlds | MySQL (no JSONB) |
| **Full-text search** - built-in `ts_vector` | Elasticsearch (overkill) |
| **Free & scalable** - production ready | SQLite (not scalable) |

**PostgreSQL vs MongoDB:**
```
PostgreSQL                          MongoDB
├── JSONB (flexible schema)         ├── Native JSON
├── Relations (chapters→sections)   ├── No joins (denormalized)
├── pgvector (embeddings)           ├── Needs Atlas Vector Search
├── Full-text search built-in       ├── Needs Atlas Search
└── Single database for everything  └── May need multiple services
```

---

## AI Role in the System

| Stage | AI Component | What It Does |
|-------|--------------|--------------|
| **Text Extraction** | Claude Vision | Reads page images → structured markdown |
| **Layout Understanding** | Claude Vision | Handles two-column, equations, tables |
| **LaTeX Conversion** | Claude Vision | Converts `∫f(x)dx` → `$\int f(x)dx$` |
| **Table Parsing** | Claude Vision | Extracts rows/columns correctly |
| **Future: Search** | OpenAI Embeddings | Semantic search with pgvector |
| **Future: Q&A** | RAG with Claude | Answer questions from textbook |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API** | FastAPI, Uvicorn, Pydantic | REST API, async server, validation |
| **PDF Processing** | Docling (IBM) + PyMuPDF | ML-based document parsing, page rendering |
| **OCR** | Tesseract | Scanned PDF text extraction |
| **AI/Vision** | Claude API (Anthropic) | Complex layout extraction |
| **Image Processing** | OpenCV | Watermark removal, figure extraction |
| **Database** | DuckDB | Embedded analytics database (JSON, Parquet) |
| **Future: Search** | DuckDB + embeddings | Vector similarity search |

---

## Data Flow Pipeline

```
1. PDF Ingestion      →  Upload via API or batch directory
2. Page Rendering     →  Convert pages to PNG (PyMuPDF)
3. Text Extraction    →  OCR (Tesseract) or Vision API (Claude)
4. Content Structuring →  Parse into sections, examples, exercises
5. Image Processing   →  Extract figures, remove watermarks
6. Database Storage   →  Save to PostgreSQL with JSONB
7. [Future] Embeddings →  Generate vectors for semantic search
```

---

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
│   ├── database/               # Database layer
│   │   ├── connection.py       # PostgreSQL connection
│   │   ├── models.py           # Pydantic models
│   │   └── repository.py       # CRUD operations
│   ├── validators/             # Quality checks
│   ├── subjects/               # Subject configs
│   └── utils/                  # Shared utilities
│
├── scripts/                    # CLI entry points
│   ├── extract.py              # Single PDF extraction
│   ├── batch_extract.py        # Batch processing
│   ├── structure_physics.py    # Physics structurer
│   ├── save_to_db.py           # Save to PostgreSQL
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

---

## Database Schema

```sql
-- Enable vector search
CREATE EXTENSION IF NOT EXISTS vector;

-- chapters table
CREATE TABLE chapters (
    id SERIAL PRIMARY KEY,
    book_code VARCHAR(20) UNIQUE NOT NULL,
    subject VARCHAR(50),
    class INTEGER,
    chapter_number INTEGER,
    title TEXT,
    content JSONB,              -- Full structured content
    embedding vector(1536),     -- For semantic search
    created_at TIMESTAMP DEFAULT NOW()
);

-- sections table
CREATE TABLE sections (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id),
    section_number VARCHAR(10),
    title TEXT,
    content TEXT,
    equations JSONB,
    embedding vector(1536)
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

-- Full-text search index
CREATE INDEX idx_sections_fts ON sections 
USING GIN(to_tsvector('english', content));
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/extract` | Upload and extract PDF |
| `GET` | `/api/books` | List all extracted books |
| `GET` | `/api/books/{book_code}` | Get chapter content |
| `GET` | `/api/files/{book}/{type}/{file}` | Serve renders/figures |
| `GET` | `/api/search?q={query}` | Full-text search |
| `DELETE` | `/api/books/{book_code}` | Delete extraction |

---

## Future Improvements

| Feature | Technology | Benefit |
|---------|------------|---------|
| **Semantic Search** | pgvector + OpenAI embeddings | "Find Newton's laws" returns relevant sections |
| **RAG Chatbot** | LangChain + Claude | Students ask questions, get answers with citations |
| **Exercise Solutions** | Claude API | Auto-generate step-by-step solutions |
| **Diagram Recreation** | AI image generation | Clean diagrams without watermarks |
| **Hindi Support** | Tesseract + multilingual models | Extract Hindi NCERT books |

---

## Supported Subjects

| Subject | Prefix | Example |
|---------|--------|---------|
| Chemistry | `lech` | `lech101.pdf` |
| Biology | `kebo` | `kebo101.pdf` |
| Physics | `keph` | `keph101.pdf` |
| Maths | `kemh` | `kemh101.pdf` |

---

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract (macOS)
brew install tesseract

# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15
createdb ncert_extractor

# Initialize database
python scripts/save_to_db.py --init
```

---

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
python scripts/structure_physics.py --all

# Save to database
python scripts/save_to_db.py --all
```

### Web Interface

```bash
python web/app.py
# Open http://localhost:8080
# API docs: http://localhost:8080/docs
```

---

## Output Format

```json
{
  "book_code": "keph101",
  "subject": "physics",
  "class": 11,
  "chapter_title": "Units and Measurement",
  "sections": [
    {"number": "1.1", "title": "INTRODUCTION", "content": "..."}
  ],
  "tables": [
    {"number": "1.1", "headers": ["Name", "Symbol"], "rows": [...]}
  ],
  "examples": [
    {"number": "1.1", "problem": "...", "solution": "..."}
  ],
  "exercises": [
    {"number": "1.4", "text": "...", "sub_parts": [{"label": "a", "text": "..."}]}
  ],
  "equations": [
    {"type": "display", "latex": "F = ma"}
  ],
  "statistics": {
    "section_count": 11,
    "example_count": 5,
    "exercise_count": 15,
    "equation_count": 64
  }
}
```

---

## Cost Analysis

| Method | Cost | Speed | Accuracy |
|--------|------|-------|----------|
| PyMuPDF | Free | Instant | 100% (text PDFs) |
| Tesseract OCR | Free | 2-3 sec/page | 95% |
| Claude Vision | ~$0.003/page | 3-5 sec/page | 98%+ |

**Recommendation:**
- Use PyMuPDF for text-based PDFs (free)
- Use Tesseract for scanned PDFs (free)
- Use Claude Vision only for complex layouts with equations/tables
