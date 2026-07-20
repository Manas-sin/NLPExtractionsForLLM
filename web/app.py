"""
NCERT PDF Extractor - FastAPI Web UI
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.extractors import PDFExtractor

app = FastAPI(title="NCERT Extractor", version="1.0.0")

DATA_DIR = Path(__file__).parent.parent / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXTRACTED_DIR = DATA_DIR / "extracted"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NCERT Extractor</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #f5f5f5; padding: 1rem; }
        h1 { margin-bottom: 1rem; }
        .upload { background: #fff; border: 2px dashed #ccc; padding: 2rem; text-align: center; cursor: pointer; margin-bottom: 1rem; border-radius: 8px; }
        .upload:hover { border-color: #1e40af; background: #f8fafc; }
        .btn { background: #1e40af; color: #fff; border: none; padding: 0.75rem 1.5rem; cursor: pointer; width: 100%; margin-bottom: 1rem; border-radius: 6px; font-size: 1rem; }
        .btn:hover { background: #1e3a8a; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .panel { background: #fff; border: 1px solid #ddd; height: 80vh; overflow: auto; border-radius: 8px; }
        .panel-header { padding: 0.75rem 1rem; border-bottom: 1px solid #ddd; font-weight: 600; background: #f9fafb; position: sticky; top: 0; z-index: 10; }
        .tabs { display: flex; border-bottom: 1px solid #ddd; background: #fff; position: sticky; top: 45px; z-index: 9; }
        .tab { padding: 0.5rem 1rem; cursor: pointer; border: none; background: none; font-size: 0.875rem; }
        .tab.active { border-bottom: 2px solid #1e40af; color: #1e40af; font-weight: 500; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .page-list { padding: 0.5rem; }
        .page-item { padding: 0.5rem 0.75rem; cursor: pointer; border-bottom: 1px solid #f3f4f6; font-size: 0.875rem; }
        .page-item:hover { background: #eff6ff; }
        .page-item.active { background: #dbeafe; }
        .text-content { padding: 1rem; white-space: pre-wrap; font-family: 'SF Mono', Consolas, monospace; font-size: 0.8rem; line-height: 1.6; }
        .json-view { padding: 1rem; font-family: 'SF Mono', Consolas, monospace; font-size: 0.75rem; white-space: pre; overflow-x: auto; }
        .figures-grid { display: grid; grid-template-columns: 1fr; gap: 1rem; padding: 1rem; }
        .figure-card { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
        .figure-card img { width: 100%; height: auto; border-bottom: 1px solid #e5e7eb; }
        .figure-info { padding: 0.75rem; }
        .figure-num { font-weight: 600; color: #1e40af; margin-bottom: 0.25rem; }
        .figure-caption { font-size: 0.8rem; color: #4b5563; line-height: 1.4; }
        .figure-page { font-size: 0.75rem; color: #9ca3af; margin-top: 0.5rem; }
        #fileInput { display: none; }
        .hidden { display: none !important; }
        .loading { display: inline-block; width: 16px; height: 16px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 8px; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>NCERT PDF Extractor</h1>
    <div class="upload" onclick="document.getElementById('fileInput').click()">
        <svg width="48" height="48" fill="none" stroke="#9ca3af" stroke-width="1.5" viewBox="0 0 24 24" style="margin-bottom: 0.5rem;">
            <path d="M12 16V4m0 0L8 8m4-4l4 4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/>
        </svg>
        <div id="uploadText">Drop PDF here or click to upload</div>
        <input type="file" id="fileInput" accept=".pdf">
    </div>
    <button class="btn" id="extractBtn" disabled>Extract</button>
    <div class="layout hidden" id="results">
        <div class="panel">
            <div class="panel-header">Text Extraction</div>
            <div class="tabs">
                <button class="tab active" data-tab="pages">Pages</button>
                <button class="tab" data-tab="json">JSON</button>
            </div>
            <div class="tab-content active" id="tab-pages">
                <div class="page-list" id="pageList"></div>
            </div>
            <div class="tab-content" id="tab-json">
                <div class="json-view" id="jsonView"></div>
            </div>
            <div class="text-content hidden" id="textView"></div>
        </div>
        <div class="panel">
            <div class="panel-header">Figures (<span id="figCount">0</span>)</div>
            <div class="figures-grid" id="figuresGrid"></div>
        </div>
    </div>
<script>
    let currentFile = null;
    let pagesData = null;
    let figuresData = null;
    let outputDir = null;

    document.getElementById('fileInput').onchange = e => {
        if (e.target.files[0]) {
            currentFile = e.target.files[0];
            document.getElementById('uploadText').textContent = currentFile.name;
            document.getElementById('extractBtn').disabled = false;
        }
    };

    document.getElementById('extractBtn').onclick = async () => {
        if (!currentFile) return;
        const btn = document.getElementById('extractBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span>Extracting...';

        const form = new FormData();
        form.append('file', currentFile);

        try {
            const res = await fetch('/api/extract', { method: 'POST', body: form });
            const data = await res.json();
            pagesData = data.pages;
            figuresData = data.figures;
            outputDir = data.output_dir;
            showResults();
        } catch (err) {
            alert('Extraction failed: ' + err.message);
        }

        btn.textContent = 'Extract';
        btn.disabled = false;
    };

    function showResults() {
        document.getElementById('results').classList.remove('hidden');
        document.getElementById('pageList').innerHTML = pagesData.map((p, i) =>
            `<div class="page-item" onclick="showPage(${i})">Page ${p.page} (book: ${p.book_page ?? '-'}) - ${p.char_count} chars</div>`
        ).join('');
        document.getElementById('jsonView').textContent = JSON.stringify(pagesData, null, 2);
        document.getElementById('figCount').textContent = figuresData.length;
        document.getElementById('figuresGrid').innerHTML = figuresData.map(f =>
            `<div class="figure-card">
                <img src="/api/files/${outputDir}/figures/${f.image}" alt="Fig ${f.figure}" loading="lazy">
                <div class="figure-info">
                    <div class="figure-num">Fig. ${f.figure}</div>
                    <div class="figure-caption">${f.caption}</div>
                    <div class="figure-page">Page ${f.page}</div>
                </div>
            </div>`
        ).join('');
    }

    function showPage(idx) {
        document.querySelectorAll('.page-item').forEach((el, i) => el.classList.toggle('active', i === idx));
        document.getElementById('tab-pages').classList.remove('active');
        document.getElementById('textView').classList.remove('hidden');
        document.getElementById('textView').textContent = pagesData[idx].text;
    }

    document.querySelectorAll('.tab').forEach(tab => {
        tab.onclick = () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
            document.getElementById('textView').classList.add('hidden');
        };
    });
</script>
</body>
</html>
'''


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.post("/api/extract")
async def extract(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Invalid file. Please upload a PDF.")

    filename = re.sub(r'[^\w\-.]', '_', file.filename)
    pdf_path = UPLOAD_DIR / filename

    content = await file.read()
    pdf_path.write_bytes(content)

    book_code = pdf_path.stem
    output_dir = EXTRACTED_DIR / book_code

    extractor = PDFExtractor(output_dir)
    result = extractor.extract(pdf_path)

    pages_data = json.loads((output_dir / "pages.json").read_text())
    figures_data = json.loads((output_dir / "figures.json").read_text())

    return {
        "pages": pages_data,
        "figures": figures_data,
        "output_dir": book_code,
        "stats": result
    }


@app.get("/api/files/{book_code}/{subdir}/{filename}")
async def serve_file(book_code: str, subdir: str, filename: str):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', book_code) or book_code in ('.', '..'):
        raise HTTPException(404, "Invalid path")
    if subdir not in ("figures", "renders", "pages"):
        raise HTTPException(404, "Invalid directory")
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', filename) or filename in ('.', '..'):
        raise HTTPException(404, "Invalid filename")

    base = EXTRACTED_DIR.resolve()
    file_path = (EXTRACTED_DIR / book_code / subdir / filename).resolve()
    try:
        file_path.relative_to(base)
    except ValueError:
        raise HTTPException(404, "Invalid path")

    if not file_path.is_file():
        raise HTTPException(404, "File not found")

    return FileResponse(file_path)


@app.get("/api/books")
async def list_books():
    """List all extracted books."""
    books = []
    for d in EXTRACTED_DIR.iterdir():
        if d.is_dir() and (d / "pages.json").exists():
            pages = json.loads((d / "pages.json").read_text())
            figures = json.loads((d / "figures.json").read_text()) if (d / "figures.json").exists() else []
            books.append({
                "book_code": d.name,
                "pages": len(pages),
                "figures": len(figures),
                "total_chars": sum(p.get("char_count", 0) for p in pages)
            })
    return {"books": books}


if __name__ == '__main__':
    import uvicorn
    print("Open http://localhost:8080")
    print("API docs: http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
