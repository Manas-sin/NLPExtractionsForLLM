"""
NCERT PDF Extractor - Web UI
Extracts text, page renders, and figures with captions.
"""

import json
import re
from pathlib import Path

from flask import Flask, render_template_string, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import fitz

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
EXTRACTED_DIR = Path("extracted")
UPLOAD_DIR.mkdir(exist_ok=True)
EXTRACTED_DIR.mkdir(exist_ok=True)


def clean_text(text: str) -> str:
    text = text.replace("­", "")
    text = re.sub(r"^\s*Reprint\s+\d{4}-\d{2}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = text.split('\n')
    deduped = []
    prev = None
    for line in lines:
        if line.strip() != prev:
            deduped.append(line)
            prev = line.strip()
    return '\n'.join(deduped).strip()


BOOK_PAGE_RE = re.compile(r"^(\d{1,3})\n")
FIG_CAPTION_RE = re.compile(r"(Fig\.|Figure)\s*(\d+\.?\d*)\s*[:\.]?\s*(.+)", re.IGNORECASE)


def extract_figures(page, page_num, figures_dir, scale=2):
    figures = []
    blocks = page.get_text("dict", sort=True)["blocks"]
    page_height = page.rect.height
    page_width = page.rect.width
    seen = set()

    for block in blocks:
        if block["type"] != 0:
            continue
        block_text = ""
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span.get("text", "") + " "
        block_text = block_text.strip()
        match = FIG_CAPTION_RE.search(block_text)

        if match:
            fig_num = match.group(2)
            if fig_num in seen:
                continue
            seen.add(fig_num)
            caption = match.group(3).strip()[:200]

            bbox = block["bbox"]
            fig_top = max(0, bbox[1] - 300)
            fig_bottom = bbox[3] + 20
            fig_left = max(0, bbox[0] - 50)
            fig_right = min(page_width, bbox[2] + 50)

            clip = fitz.Rect(fig_left, fig_top, fig_right, fig_bottom)
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, clip=clip)

            fig_name = f"page{page_num:03d}_fig{fig_num.replace('.', '_')}.png"
            pix.save(figures_dir / fig_name)

            figures.append({
                "page": page_num,
                "figure": fig_num,
                "caption": caption,
                "image": fig_name
            })
    return figures


def extract_pdf(pdf_path: Path):
    doc = fitz.open(pdf_path)
    out_dir = EXTRACTED_DIR / pdf_path.stem
    pages_dir = out_dir / "pages"
    renders_dir = out_dir / "renders"
    figures_dir = out_dir / "figures"

    for d in [pages_dir, renders_dir, figures_dir]:
        d.mkdir(parents=True, exist_ok=True)

    pages_data = []
    all_figures = []

    for page_num, page in enumerate(doc, start=1):
        raw = page.get_text("text", sort=False)
        text = clean_text(raw)
        m = BOOK_PAGE_RE.match(text)
        book_page = int(m.group(1)) if m else None

        pages_data.append({
            "page": page_num,
            "book_page": book_page,
            "char_count": len(text),
            "text": text
        })
        (pages_dir / f"page_{page_num:03d}.txt").write_text(text, encoding="utf-8")

        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        pix.save(renders_dir / f"page_{page_num:03d}.png")

        figures = extract_figures(page, page_num, figures_dir)
        all_figures.extend(figures)

    doc.close()

    (out_dir / "pages.json").write_text(json.dumps(pages_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "figures.json").write_text(json.dumps(all_figures, ensure_ascii=False, indent=2), encoding="utf-8")

    return pages_data, all_figures, str(out_dir.name)


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
        .upload { background: #fff; border: 2px dashed #ccc; padding: 2rem; text-align: center; cursor: pointer; margin-bottom: 1rem; }
        .upload:hover { border-color: #1e40af; }
        .btn { background: #1e40af; color: #fff; border: none; padding: 0.75rem 1.5rem; cursor: pointer; width: 100%; margin-bottom: 1rem; }
        .btn:disabled { opacity: 0.5; }

        .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .panel { background: #fff; border: 1px solid #ddd; height: 80vh; overflow: auto; }
        .panel-header { padding: 0.75rem; border-bottom: 1px solid #ddd; font-weight: bold; background: #f9f9f9; position: sticky; top: 0; z-index: 10; }

        .tabs { display: flex; border-bottom: 1px solid #ddd; background: #fff; position: sticky; top: 40px; z-index: 9; }
        .tab { padding: 0.5rem 1rem; cursor: pointer; border: none; background: none; }
        .tab.active { border-bottom: 2px solid #1e40af; color: #1e40af; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .page-list { padding: 0.5rem; }
        .page-item { padding: 0.5rem; cursor: pointer; border-bottom: 1px solid #eee; font-size: 0.875rem; }
        .page-item:hover { background: #f0f7ff; }
        .page-item.active { background: #dbeafe; }

        .text-content { padding: 1rem; white-space: pre-wrap; font-family: monospace; font-size: 0.8rem; line-height: 1.6; }
        .json-view { padding: 1rem; font-family: monospace; font-size: 0.75rem; white-space: pre; }

        .figures-grid { display: grid; grid-template-columns: 1fr; gap: 1rem; padding: 1rem; }
        .figure-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
        .figure-card img { width: 100%; height: auto; border-bottom: 1px solid #ddd; }
        .figure-info { padding: 0.75rem; }
        .figure-num { font-weight: bold; color: #1e40af; margin-bottom: 0.25rem; }
        .figure-caption { font-size: 0.8rem; color: #444; line-height: 1.4; }
        .figure-page { font-size: 0.75rem; color: #888; margin-top: 0.5rem; }

        #fileInput { display: none; }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <h1>NCERT PDF Extractor</h1>
    <div class="upload" onclick="document.getElementById('fileInput').click()">
        Drop PDF here or click to upload
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
            document.querySelector('.upload').textContent = currentFile.name;
            document.getElementById('extractBtn').disabled = false;
        }
    };

    document.getElementById('extractBtn').onclick = async () => {
        if (!currentFile) return;
        document.getElementById('extractBtn').disabled = true;
        document.getElementById('extractBtn').textContent = 'Extracting...';

        const form = new FormData();
        form.append('pdf', currentFile);

        const res = await fetch('/extract', { method: 'POST', body: form });
        const data = await res.json();

        pagesData = data.pages;
        figuresData = data.figures;
        outputDir = data.output_dir;

        showResults();
        document.getElementById('extractBtn').textContent = 'Extract';
        document.getElementById('extractBtn').disabled = false;
    };

    function showResults() {
        document.getElementById('results').classList.remove('hidden');

        // Pages list
        document.getElementById('pageList').innerHTML = pagesData.map((p, i) =>
            `<div class="page-item" onclick="showPage(${i})">Page ${p.page} (book: ${p.book_page ?? '-'}) - ${p.char_count} chars</div>`
        ).join('');

        // JSON
        document.getElementById('jsonView').textContent = JSON.stringify(pagesData, null, 2);

        // Figures
        document.getElementById('figCount').textContent = figuresData.length;
        document.getElementById('figuresGrid').innerHTML = figuresData.map(f =>
            `<div class="figure-card">
                <img src="/file/${outputDir}/figures/${f.image}" alt="Fig ${f.figure}">
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


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/extract', methods=['POST'])
def extract():
    pdf = request.files.get('pdf')
    if not pdf:
        return jsonify({"error": "No PDF"}), 400

    # Sanitize filename to prevent path traversal
    filename = secure_filename(pdf.filename)
    if not filename or not filename.lower().endswith('.pdf'):
        return jsonify({"error": "Invalid filename"}), 400

    pdf_path = UPLOAD_DIR / filename
    pdf.save(pdf_path)
    pages, figures, out_dir = extract_pdf(pdf_path)
    return jsonify({"pages": pages, "figures": figures, "output_dir": out_dir})


@app.route('/file/<path:filepath>')
def serve_file(filepath):
    parts = filepath.split('/')
    if len(parts) < 2:
        abort(404)

    # Validate directory name to prevent path traversal
    dir_name = parts[0]
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', dir_name) or dir_name in ('.', '..'):
        abort(404)

    base_dir = (EXTRACTED_DIR / dir_name).resolve()
    if not str(base_dir).startswith(str(EXTRACTED_DIR.resolve())):
        abort(404)

    return send_from_directory(base_dir, '/'.join(parts[1:]))


if __name__ == '__main__':
    print("Open http://localhost:8080")
    app.run(debug=True, port=8080)
