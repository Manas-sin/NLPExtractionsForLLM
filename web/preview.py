"""
NCERT Book Preview - Renders extracted JSON as NCERT-styled HTML
"""

import json
import os
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI(title="NCERT Preview", version="1.0.0")

DATA_DIR = Path(__file__).parent.parent / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"
CONFIG_DIR = Path(__file__).parent.parent / "config"

# Book codes are alphanumeric with dashes/underscores only (e.g. lech101, keph101)
BOOK_CODE_RE = re.compile(r"[A-Za-z0-9_-]+")


def resolve_book_dir(book_code: str) -> Path:
    """Validate book_code and return its extraction dir, guarding against path traversal."""
    if not BOOK_CODE_RE.fullmatch(book_code):
        raise HTTPException(400, "invalid book code")
    resolved = (EXTRACTED_DIR / book_code).resolve()
    base = EXTRACTED_DIR.resolve()
    if not str(resolved).startswith(str(base) + os.sep):
        raise HTTPException(404, "book not found")
    return resolved


def e(value) -> str:
    """HTML-escape any interpolated value."""
    return escape(str(value if value is not None else ""))


def load_structure_config():
    """Load NCERT structure config for styling."""
    config_file = CONFIG_DIR / "ncert_structure.json"
    if config_file.exists():
        return json.loads(config_file.read_text())
    return {}


NCERT_STYLE = """
<style>
:root {
    /* Actual NCERT Chemistry colors - softer, muted tones */
    --unit-banner: linear-gradient(180deg, #F5C6AA 0%, #EAAA87 50%, #D4896A 100%);
    --unit-banner-solid: #EAAA87;
    --section-underline: #8B4513;
    --section-title-color: #8B4513;
    --example-border: #4DB6C5;
    --example-label: #4DB6C5;
    --intext-bg: #FFF5F5;
    --intext-border: #CD5C5C;
    --intext-header: #8B0000;
    --exercise-sidebar: #CD5C5C;
    --table-header: #F5D5C8;
    --table-header-text: #8B4513;
    --objectives-color: #8B4513;
    --hook-quote: #8B4513;
    --summary-border: #1976D2;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Times New Roman', Georgia, serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
    background: #f5f5f5;
    padding: 0;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 0;
    min-height: 100vh;
}

/* Sidebar */
.sidebar {
    background: #fff;
    border-right: 1px solid #e0e0e0;
    padding: 1rem;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
}

.sidebar h2 {
    font-size: 14px;
    color: #666;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.book-list {
    list-style: none;
}

.book-list li {
    margin-bottom: 0.5rem;
}

.book-list a {
    display: block;
    padding: 0.75rem 1rem;
    background: #f8f8f8;
    border-radius: 6px;
    text-decoration: none;
    color: #333;
    font-size: 13px;
    transition: all 0.2s;
}

.book-list a:hover {
    background: #e3f2fd;
    color: var(--unit-banner);
}

.book-list a.active {
    background: var(--unit-banner);
    color: #fff;
}

.book-subject {
    font-size: 10px;
    color: #888;
    text-transform: uppercase;
}

.book-title {
    font-weight: 600;
    margin-top: 2px;
}

.stats-badge {
    display: inline-block;
    background: #e0e0e0;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 10px;
    margin-top: 4px;
}

/* Main content - NCERT styled page */
.main-content {
    background: #fff;
    padding: 0;
}

.ncert-page {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 60px;
    background: #fff;
    min-height: 100vh;
}

/* Unit Opening */
.unit-header {
    position: relative;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
}

.unit-banner {
    background: var(--unit-banner);
    color: #fff;
    padding: 1.5rem 2rem;
    border-radius: 0 0 0 40px;
    margin: -40px -60px 1.5rem -60px;
    padding-left: 60px;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.unit-label {
    font-family: 'Brush Script MT', cursive;
    font-size: 18px;
    opacity: 0.9;
}

.unit-number {
    font-size: 48px;
    font-weight: 300;
    line-height: 1;
    margin: 0.25rem 0;
}

.unit-title {
    font-family: 'Brush Script MT', cursive;
    font-size: 32px;
    color: #1a1a1a;
    margin-top: 1rem;
}

/* QR Code box */
.qr-box {
    position: absolute;
    top: 10px;
    left: 10px;
    background: #fff;
    padding: 8px;
    border: 1px solid #ddd;
    font-size: 10px;
    color: #666;
}

/* Objectives - matching NCERT maroon style */
.objectives-box {
    border-left: 4px solid var(--objectives-color);
    padding: 1rem 1.5rem;
    margin: 1.5rem 0;
    background: #fff;
}

.objectives-header {
    font-family: 'Brush Script MT', cursive;
    font-size: 22px;
    color: var(--objectives-color);
    margin-bottom: 0.5rem;
}

.objectives-intro {
    font-style: italic;
    margin-bottom: 0.75rem;
    color: #555;
}

.objectives-list {
    list-style: disc;
    margin-left: 1.5rem;
}

.objectives-list li {
    margin-bottom: 0.5rem;
    line-height: 1.5;
}

/* Hook Quote */
.hook-quote {
    font-style: italic;
    color: #8B4513;
    font-size: 13px;
    padding: 1rem;
    background: linear-gradient(90deg, var(--hook-quote) 0%, transparent 100%);
    border-radius: 4px;
    margin: 1.5rem 0;
}

/* Introduction */
.introduction {
    font-size: 11pt;
    line-height: 1.8;
    margin-bottom: 2rem;
    text-align: justify;
}

.introduction p {
    margin-bottom: 0.9rem;
}

/* Section Headers - NCERT maroon italic style */
.section {
    margin: 2rem 0;
}

.section-header {
    display: flex;
    align-items: baseline;
    margin-bottom: 1rem;
    border-bottom: 2px solid var(--section-underline);
    padding-bottom: 0.25rem;
}

.section-number {
    font-size: 13pt;
    font-weight: normal;
    margin-right: 0.5rem;
    color: var(--section-title-color);
    font-style: italic;
}

.section-title {
    font-family: 'Brush Script MT', 'Lucida Calligraphy', cursive;
    font-size: 16pt;
    color: var(--section-title-color);
    font-style: italic;
}

.section-content {
    text-align: justify;
    line-height: 1.8;
}

.subsection {
    margin: 1.5rem 0 1rem 0;
}

.subsection-header {
    font-weight: bold;
    font-size: 12pt;
    margin-bottom: 0.5rem;
}

/* Example Box - NCERT style: cyan left border only, white background */
.example-box {
    background: #fff;
    border-left: 4px solid var(--example-border);
    padding: 1rem 1.5rem;
    margin: 1.5rem 0;
    color: #1a1a1a;
}

.example-header {
    display: flex;
    align-items: baseline;
    margin-bottom: 0.5rem;
}

.example-label {
    font-family: 'Brush Script MT', cursive;
    font-size: 16px;
    margin-right: 0.5rem;
    color: var(--example-label);
}

.example-number {
    font-size: 14px;
    color: var(--example-label);
}

.example-problem {
    padding: 0.5rem 0;
    margin-bottom: 0.5rem;
    line-height: 1.6;
}

.solution-label {
    font-family: 'Brush Script MT', cursive;
    font-size: 14px;
    margin-bottom: 0.5rem;
    color: var(--example-label);
}

.example-solution {
    font-size: 10pt;
    line-height: 1.6;
}

/* Intext Questions - NCERT style: light pink bg, thin red border */
.intext-questions {
    background: var(--intext-bg);
    border: 1px solid var(--intext-border);
    padding: 1rem 1.5rem;
    margin: 1.5rem 0;
    border-radius: 0;
}

.intext-header {
    font-family: 'Brush Script MT', cursive;
    font-size: 16px;
    text-decoration: underline;
    text-align: right;
    margin-bottom: 0.75rem;
    color: var(--intext-header);
}

.intext-list {
    list-style: none;
}

.intext-item {
    display: flex;
    margin-bottom: 0.5rem;
    font-size: 10pt;
}

.intext-number {
    font-weight: bold;
    margin-right: 0.75rem;
    min-width: 30px;
}

/* Tables */
.table-container {
    margin: 1.5rem 0;
    overflow-x: auto;
}

.table-caption {
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.ncert-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 10pt;
}

.ncert-table th {
    background: var(--table-header);
    color: var(--table-header-text);
    padding: 0.5rem;
    text-align: left;
    font-weight: bold;
}

.ncert-table td {
    padding: 0.5rem;
    border: 1px solid #ddd;
}

.ncert-table tr:nth-child(even) {
    background: #f9f9f9;
}

/* Figures */
.figure-container {
    margin: 1.5rem 0;
    text-align: center;
}

.figure-placeholder {
    background: #f0f0f0;
    border: 2px dashed #ccc;
    padding: 2rem;
    color: #888;
    font-style: italic;
}

.figure-image {
    max-width: 100%;
    height: auto;
    border: 1px solid #e5ded7;
    border-radius: 4px;
    background: #fff;
    display: block;
    margin: 0 auto;
}

.figure-caption {
    font-size: 10pt;
    color: #555;
    margin-top: 0.5rem;
}

.figure-caption strong {
    color: var(--section-title-color);
}

.fig-count {
    font-size: 11px;
    font-style: normal;
    color: #888;
    font-family: 'Times New Roman', serif;
}

.page-badge {
    display: inline-block;
    font-family: -apple-system, Helvetica, Arial, sans-serif;
    font-size: 9px;
    font-style: normal;
    font-weight: 600;
    color: #8B4513;
    background: #f5e9df;
    border: 1px solid #e5d3c3;
    border-radius: 3px;
    padding: 0 5px;
    margin-left: 6px;
    vertical-align: middle;
    letter-spacing: 0.3px;
    white-space: nowrap;
}

/* Page-by-page view */
.pages-view {
    max-width: 1150px;
    margin: 0 auto;
    padding: 1.5rem;
}

.pg-row {
    margin-bottom: 2rem;
    background: #fff;
    border: 1px solid #e5ded7;
    border-radius: 8px;
    overflow: hidden;
}

.pg-num {
    background: var(--section-title-color);
    color: #fff;
    font-family: -apple-system, Helvetica, Arial, sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 6px 14px;
}

.pg-body {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
}

.pg-image {
    background: #ece7e2;
    padding: 12px;
    border-right: 1px solid #e5ded7;
}

.pg-image img {
    width: 100%;
    display: block;
    box-shadow: 0 1px 6px rgba(0,0,0,0.12);
}

.pg-extracted {
    padding: 14px 16px;
}

.pg-elements {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.pg-el {
    border-left: 3px solid #cfc3b8;
    padding: 5px 10px;
    background: #faf7f3;
    border-radius: 0 4px 4px 0;
}

.pg-el-section { border-left-color: #8B4513; }
.pg-el-example { border-left-color: #4DB6C5; }
.pg-el-figure  { border-left-color: #C77D3A; }
.pg-el-table   { border-left-color: #6A8D3A; }
.pg-el-exercise { border-left-color: #CD5C5C; }
.pg-el-intext_question { border-left-color: #B0729E; }

.pg-el-type {
    display: block;
    font-family: -apple-system, Helvetica, Arial, sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #333;
}

.pg-el-label {
    font-size: 12px;
    color: #666;
}

.pg-none, .pg-elements:empty::after {
    color: #aaa;
    font-style: italic;
    font-size: 12px;
}

@media (max-width: 900px) {
    .pg-body { grid-template-columns: 1fr; }
}

/* Summary Box */
.summary-box {
    border: 2px solid var(--summary-border);
    padding: 1.5rem;
    margin: 2rem 0;
    border-radius: 8px;
}

.summary-header {
    font-family: 'Brush Script MT', cursive;
    font-size: 24px;
    text-align: center;
    margin-bottom: 1rem;
    color: var(--summary-border);
}

.summary-list {
    list-style: disc;
    margin-left: 1.5rem;
}

.summary-list li {
    margin-bottom: 0.75rem;
    line-height: 1.6;
}

/* Exercises */
.exercises-section {
    margin: 2rem 0;
    border-left: 4px solid var(--exercise-sidebar);
    padding-left: 1.5rem;
}

.exercises-header {
    font-family: 'Brush Script MT', cursive;
    font-size: 24px;
    color: var(--exercise-sidebar);
    margin-bottom: 1rem;
}

.exercise-item {
    margin-bottom: 1rem;
}

.exercise-number {
    font-weight: bold;
    color: #333;
}

.exercise-text {
    margin-top: 0.25rem;
    line-height: 1.6;
}

.exercise-parts {
    margin-left: 1.5rem;
    margin-top: 0.5rem;
}

.exercise-part {
    margin-bottom: 0.25rem;
}

/* Key Terms */
.key-term {
    font-weight: bold;
}

/* Laws */
.law-name {
    font-weight: bold;
    color: #1565C0;
}

/* Statistics Panel */
.stats-panel {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
}

.stats-title {
    font-size: 12px;
    color: #666;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
}

.stat-item {
    text-align: center;
    padding: 0.5rem;
    background: #fff;
    border-radius: 4px;
}

.stat-value {
    font-size: 24px;
    font-weight: bold;
    color: var(--unit-banner);
}

.stat-label {
    font-size: 10px;
    color: #888;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #888;
}

.empty-state h2 {
    color: #666;
    margin-bottom: 0.5rem;
}

/* Answers */
.answers-section {
    margin: 2rem 0;
    padding: 1rem;
    background: #f5f5f5;
    border-radius: 8px;
}

.answers-header {
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 0.75rem;
}

.answer-item {
    display: flex;
    font-size: 10pt;
    margin-bottom: 0.25rem;
}

.answer-num {
    font-weight: bold;
    margin-right: 0.5rem;
    min-width: 30px;
}

.unit-subject {
    font-size: 11px;
    color: #8B4513;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.4rem;
}

.block-heading {
    margin: 2rem 0 1rem;
    color: var(--section-title-color);
    font-family: 'Brush Script MT', cursive;
    font-size: 18pt;
    font-style: italic;
}

/* View toolbar with tabs */
.view-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    position: sticky;
    top: 0;
    z-index: 10;
}

.view-tabs {
    display: flex;
    gap: 0.5rem;
}

.view-tab {
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
    text-decoration: none;
    color: #555;
    font-size: 13px;
    background: #f2f2f2;
    transition: all 0.15s;
}

.view-tab:hover { background: #e8e8e8; }

.view-tab.active {
    background: var(--section-title-color);
    color: #fff;
}

.view-title {
    font-family: 'Brush Script MT', cursive;
    font-style: italic;
    font-size: 18px;
    color: var(--section-title-color);
}

/* Side-by-side compare grid */
.compare-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
    height: calc(100vh - 55px);
}

.compare-col {
    display: flex;
    flex-direction: column;
    min-width: 0;
    border-right: 1px solid #e0e0e0;
}

.compare-col-header {
    padding: 0.5rem 1rem;
    background: #faf6f2;
    border-bottom: 1px solid #eadfd5;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #8B4513;
    text-align: center;
}

.compare-scroll {
    overflow-y: auto;
    flex: 1;
    background: #ece7e2;
    padding: 1rem;
}

.compare-right .compare-scroll {
    background: #fff;
    padding: 0;
}

.compare-right .ncert-page {
    max-width: 100%;
    padding: 30px 40px;
}

/* Original page images */
.orig-page {
    margin-bottom: 1.25rem;
    background: #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.orig-page-num {
    font-size: 10px;
    color: #888;
    padding: 4px 8px;
    background: #f5f5f5;
    border-bottom: 1px solid #eee;
}

.orig-page img {
    width: 100%;
    display: block;
}

.original-single {
    max-width: 850px;
    margin: 0 auto;
    padding: 1.5rem;
    background: #ece7e2;
    min-height: calc(100vh - 55px);
}

.original-single .orig-page {
    margin-bottom: 1.5rem;
}

.no-pages, .no-pages {
    padding: 2rem;
    color: #888;
    text-align: center;
}

@media (max-width: 900px) {
    .compare-grid { grid-template-columns: 1fr; }
}
</style>
"""


def _clip(text, limit):
    """Escape text and clip to limit with ellipsis."""
    text = str(text or "")
    clipped = text[:limit] + ("..." if len(text) > limit else "")
    return e(clipped)


def _page_badge(obj) -> str:
    """Render a 'p.N' badge showing the source page, when known."""
    page = obj.get("page", 0) if isinstance(obj, dict) else 0
    if page and int(page) > 0:
        return f'<span class="page-badge">p.{e(page)}</span>'
    return ""


def render_book_html(data: dict, book_code: str = "", figures_map: dict = None) -> str:
    """Render extracted JSON as NCERT-styled HTML. All values are HTML-escaped."""
    figures_map = figures_map or {}
    html_parts = []

    subject = e(data.get("subject", "")).title()
    chapter_no = data.get("unit_number", "")

    # Chapter Header - prominent NCERT-style banner with chapter number + name
    html_parts.append(f'''
    <div class="unit-header">
        <div class="unit-banner">
            <div class="unit-label">Chapter {e(chapter_no)}</div>
            <div class="unit-number">{e(chapter_no)}</div>
        </div>
        <div class="unit-title">{e(data.get("unit_title", "Unknown"))}</div>
        <div class="unit-subject">{subject} · Class {e(data.get("class", ""))}</div>
        {f'<div class="qr-box">{e(data.get("qr_code", ""))}</div>' if data.get("qr_code") else ""}
    </div>
    ''')

    # Statistics Panel
    stats = data.get("statistics", {})
    html_parts.append(f'''
    <div class="stats-panel">
        <div class="stats-title">Extraction Coverage</div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{e(stats.get("section_count", 0))}</div>
                <div class="stat-label">Sections</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{e(stats.get("example_count", 0))}</div>
                <div class="stat-label">Examples</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{e(stats.get("intext_question_count", 0))}</div>
                <div class="stat-label">Intext Qs</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{e(stats.get("exercise_count", 0))}</div>
                <div class="stat-label">Exercises</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{e(stats.get("table_count", 0))}</div>
                <div class="stat-label">Tables</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{e(stats.get("figure_count", 0))}</div>
                <div class="stat-label">Figures</div>
            </div>
        </div>
    </div>
    ''')

    # Objectives
    objectives = data.get("objectives", [])
    if objectives:
        obj_items = "".join(f"<li>{e(obj)}</li>" for obj in objectives)
        html_parts.append(f'''
        <div class="objectives-box">
            <div class="objectives-header">Objectives</div>
            <div class="objectives-intro">After studying this Unit, you will be able to</div>
            <ul class="objectives-list">{obj_items}</ul>
        </div>
        ''')

    # Hook Quote
    if data.get("hook_quote"):
        html_parts.append(f'<div class="hook-quote">"{e(data["hook_quote"])}"</div>')

    # Introduction (may hold several paragraphs joined by blank lines)
    if data.get("introduction"):
        paras = "".join(
            f"<p>{e(p.strip())}</p>" for p in str(data["introduction"]).split("\n\n") if p.strip()
        )
        html_parts.append(f'<div class="introduction">{paras}</div>')

    # Sections
    for section in data.get("sections", []):
        subsections_html = ""
        for sub in section.get("subsections", []):
            subsections_html += f'''
            <div class="subsection">
                <div class="subsection-header">{e(sub["number"])} {e(sub["title"])}</div>
            </div>
            '''

        examples_html = ""
        for ex in section.get("examples", []):
            solution_html = ""
            if ex.get("solution"):
                solution_html = f'<div class="solution-label">Solution</div><div class="example-solution">{_clip(ex["solution"], 400)}</div>'
            examples_html += f'''
            <div class="example-box">
                <div class="example-header">
                    <span class="example-label">Example</span>
                    <span class="example-number">{e(ex["number"])}</span>
                </div>
                <div class="example-problem">{_clip(ex.get("problem", ""), 300)}</div>
                {solution_html}
            </div>
            '''

        html_parts.append(f'''
        <div class="section">
            <div class="section-header">
                <span class="section-number">{e(section["number"])}</span>
                <span class="section-title">{e(section["title"])}</span>
                {_page_badge(section)}
            </div>
            <div class="section-content">{_clip(section.get("content", ""), 1600)}</div>
            {subsections_html}
            {examples_html}
        </div>
        ''')

    # All Examples (if not in sections)
    examples = data.get("examples", [])
    if examples and not any(s.get("examples") for s in data.get("sections", [])):
        html_parts.append('<h3 class="block-heading">Solved Examples</h3>')
        for ex in examples:
            solution_html = ""
            if ex.get("solution"):
                solution_html = f'<div class="solution-label">Solution</div><div class="example-solution">{_clip(ex["solution"], 400)}</div>'
            html_parts.append(f'''
            <div class="example-box">
                <div class="example-header">
                    <span class="example-label">Example</span>
                    <span class="example-number">{e(ex["number"])}</span>
                    {_page_badge(ex)}
                </div>
                <div class="example-problem">{_clip(ex.get("problem", ""), 300)}</div>
                {solution_html}
            </div>
            ''')

    # Intext Questions
    intext = data.get("intext_questions", [])
    if intext:
        items = "".join(
            f'<li class="intext-item"><span class="intext-number">{e(q["number"])}</span>'
            f'<span>{_clip(q.get("text", ""), 200)} {_page_badge(q)}</span></li>'
            for q in intext
        )
        html_parts.append(f'''
        <div class="intext-questions">
            <div class="intext-header">Intext Questions</div>
            <ul class="intext-list">{items}</ul>
        </div>
        ''')

    # Tables
    tables = data.get("tables", [])
    if tables:
        html_parts.append('<h3 class="block-heading">Tables</h3>')
        for table in tables:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            if headers:
                th_html = "".join(f"<th>{e(h)}</th>" for h in headers)
                tr_html = ""
                for row in rows:
                    if isinstance(row, dict):
                        td_html = "".join(f"<td>{e(row.get(h, ''))}</td>" for h in headers)
                    else:
                        td_html = f"<td colspan='{len(headers)}'>{e(row)}</td>"
                    tr_html += f"<tr>{td_html}</tr>"
                html_parts.append(f'''
                <div class="table-container">
                    <div class="table-caption">Table {e(table["number"])}: {e(table.get("title", ""))} {_page_badge(table)}</div>
                    <table class="ncert-table">
                        <thead><tr>{th_html}</tr></thead>
                        <tbody>{tr_html}</tbody>
                    </table>
                </div>
                ''')

    # Figures — show the actual cropped image when available
    figures = data.get("figures", [])
    if figures:
        extracted = sum(1 for f in figures if f["number"] in figures_map)
        html_parts.append(
            f'<h3 class="block-heading">Figures '
            f'<span class="fig-count">({extracted}/{len(figures)} images extracted)</span></h3>'
        )
        for fig in figures:
            num = fig["number"]
            fname = figures_map.get(num)
            if fname and book_code:
                visual = (f'<img class="figure-image" loading="lazy" '
                          f'src="/figures/{e(book_code)}/{e(fname)}" alt="Figure {e(num)}">')
            else:
                visual = f'<div class="figure-placeholder">[Figure {e(num)} — image not captured]</div>'
            html_parts.append(f'''
            <div class="figure-container">
                {visual}
                <div class="figure-caption"><strong>Fig. {e(num)}:</strong> {_clip(fig.get("caption", ""), 150)} {_page_badge(fig)}</div>
            </div>
            ''')

    # Summary
    summary = data.get("summary", [])
    if summary:
        items = "".join(f"<li>{_clip(point, 200)}</li>" for point in summary)
        html_parts.append(f'''
        <div class="summary-box">
            <div class="summary-header">Summary</div>
            <ul class="summary-list">{items}</ul>
        </div>
        ''')

    # Exercises
    exercises = data.get("exercises", [])
    if exercises:
        exercise_items = ""
        for ex in exercises:
            parts_html = ""
            if ex.get("sub_parts"):
                parts_html = '<div class="exercise-parts">' + "".join(
                    f'<div class="exercise-part">({e(p["label"])}) {_clip(p.get("text", ""), 100)}</div>'
                    for p in ex["sub_parts"]
                ) + '</div>'
            exercise_items += f'''
            <div class="exercise-item">
                <span class="exercise-number">{e(ex["number"])}</span>
                <div class="exercise-text">{_clip(ex.get("text", ""), 200)} {_page_badge(ex)}</div>
                {parts_html}
            </div>
            '''
        html_parts.append(f'''
        <div class="exercises-section">
            <div class="exercises-header">Exercises</div>
            {exercise_items}
        </div>
        ''')

    # Answers
    answers = data.get("answers", {})
    if answers:
        answer_items = "".join(
            f'<div class="answer-item"><span class="answer-num">{e(k)}</span><span>{_clip(v, 100)}</span></div>'
            for k, v in answers.items()
        )
        html_parts.append(f'''
        <div class="answers-section">
            <div class="answers-header">Answers to Some Intext Questions</div>
            {answer_items}
        </div>
        ''')

    return "".join(html_parts)


_ELEMENT_LABELS = {
    "section": "Section", "example": "Example", "intext_question": "Intext Q",
    "table": "Table", "figure": "Figure", "exercise": "Exercise",
}


def render_pages_view(book_code: str, data: dict) -> str:
    """Render the extraction laid out page by page: each page image beside the
    elements that were extracted from that page."""
    page_index = {p["page"]: p["elements"] for p in data.get("page_index", [])}
    pages = list_page_images(book_code)
    if not pages:
        return '<div class="no-pages">No rendered pages for this book.</div>'
    if not page_index:
        return ('<div class="no-pages">This book has no page index yet. '
                'Re-run it through the Docling engine to get page-by-page data.</div>')

    rows = []
    for i, fname in enumerate(pages):
        page_no = i + 1
        elements = page_index.get(page_no, [])
        if elements:
            chips = "".join(
                f'<div class="pg-el pg-el-{e(el["type"])}">'
                f'<span class="pg-el-type">{e(_ELEMENT_LABELS.get(el["type"], el["type"]))} {e(el["ref"])}</span>'
                f'<span class="pg-el-label">{e(el.get("label", ""))}</span></div>'
                for el in elements
            )
            extracted = f'<div class="pg-elements">{chips}</div>'
        else:
            extracted = '<div class="pg-none">No elements extracted from this page</div>'
        rows.append(f'''
        <div class="pg-row">
            <div class="pg-num">Page {page_no}</div>
            <div class="pg-body">
                <div class="pg-image"><img loading="lazy" src="/pages/{e(book_code)}/{e(fname)}" alt="Page {page_no}"></div>
                <div class="pg-extracted">{extracted}</div>
            </div>
        </div>
        ''')
    return f'<div class="pages-view">{"".join(rows)}</div>'


def get_books_list() -> list:
    """Get list of extracted books."""
    books = []
    for d in sorted(EXTRACTED_DIR.iterdir()):
        if d.is_dir():
            final_output = d / "final_output.json"
            if final_output.exists():
                try:
                    data = json.loads(final_output.read_text())
                    books.append({
                        "code": d.name,
                        "subject": data.get("subject", "unknown"),
                        "title": data.get("unit_title", "Unknown"),
                        "stats": data.get("statistics", {})
                    })
                except:
                    pass
    return books


def render_sidebar(books: list, active_code: str = "") -> str:
    """Render the book list sidebar with escaping."""
    items = ""
    for book in books:
        stats = book["stats"]
        total = sum(stats.values()) if stats else 0
        active = "active" if book["code"] == active_code else ""
        items += f'''
        <li>
            <a href="/preview/{e(book["code"])}" class="{active}">
                <div class="book-subject">{e(book["subject"])}</div>
                <div class="book-title">{e(book["title"])}</div>
                <span class="stats-badge">{e(total)} elements</span>
            </a>
        </li>
        '''
    if not items:
        items = '<li style="color:#888;padding:1rem;">No books extracted yet. Run the extractor first.</li>'
    return f'<h2>Extracted Books</h2><ul class="book-list">{items}</ul>'


def render_original_pages(book_code: str) -> str:
    """Render the original PDF page images as the 'book replica' column."""
    pages = list_page_images(book_code)
    if not pages:
        return '<div class="no-pages">No rendered pages. Run the page renderer for this book.</div>'
    imgs = "".join(
        f'<div class="orig-page"><div class="orig-page-num">Page {i + 1}</div>'
        f'<img loading="lazy" src="/pages/{e(book_code)}/{e(fname)}" alt="Page {i + 1}"></div>'
        for i, fname in enumerate(pages)
    )
    return imgs


@app.get("/", response_class=HTMLResponse)
async def index():
    """Main preview page."""
    books = get_books_list()
    sidebar = render_sidebar(books)

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NCERT Preview</title>
        {NCERT_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="sidebar">{sidebar}</div>
            <div class="main-content">
                <div class="empty-state">
                    <h2>Select a Book</h2>
                    <p>Choose a book from the sidebar to compare the original NCERT pages with the extraction.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''


@app.get("/preview/{book_code}", response_class=HTMLResponse)
async def preview_book(book_code: str, view: str = "compare"):
    """Preview a specific book. view = compare | extracted | original."""
    books = get_books_list()

    final_output = resolve_book_dir(book_code) / "final_output.json"
    if not final_output.exists():
        raise HTTPException(404, f"Book {book_code} not found")

    data = json.loads(final_output.read_text())
    sidebar = render_sidebar(books, book_code)
    figures_map = load_figures_map(book_code)
    extracted_html = render_book_html(data, book_code, figures_map)
    original_html = render_original_pages(book_code)
    title = e(data.get("unit_title", book_code))

    def tab(name, label):
        cls = "view-tab active" if view == name else "view-tab"
        return f'<a class="{cls}" href="/preview/{e(book_code)}?view={name}">{label}</a>'

    tabs = f'''
    <div class="view-toolbar">
        <div class="view-tabs">
            {tab("compare", "⇄ Side by Side")}
            {tab("pages", "▦ Page by Page")}
            {tab("original", "📖 Original Book")}
            {tab("extracted", "✓ Extracted")}
        </div>
        <div class="view-title">{title}</div>
    </div>
    '''

    if view == "original":
        body = f'<div class="original-single">{original_html}</div>'
    elif view == "extracted":
        body = f'<div class="ncert-page">{extracted_html}</div>'
    elif view == "pages":
        body = render_pages_view(book_code, data)
    else:  # compare
        body = f'''
        <div class="compare-grid">
            <div class="compare-col compare-left">
                <div class="compare-col-header">Original NCERT Book</div>
                <div class="compare-scroll">{original_html}</div>
            </div>
            <div class="compare-col compare-right">
                <div class="compare-col-header">Our Extraction</div>
                <div class="compare-scroll"><div class="ncert-page">{extracted_html}</div></div>
            </div>
        </div>
        '''

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title} - NCERT Preview</title>
        {NCERT_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="sidebar">{sidebar}</div>
            <div class="main-content">
                {tabs}
                {body}
            </div>
        </div>
    </body>
    </html>
    '''


@app.get("/api/book/{book_code}")
async def get_book_data(book_code: str):
    """Get raw JSON data for a book."""
    final_output = resolve_book_dir(book_code) / "final_output.json"
    if not final_output.exists():
        raise HTTPException(404, f"Book {book_code} not found")
    return json.loads(final_output.read_text())


@app.get("/pages/{book_code}/{filename}")
async def get_page_image(book_code: str, filename: str):
    """Serve a rendered PDF page image."""
    if not re.fullmatch(r"page_\d{3}\.png", filename):
        raise HTTPException(400, "invalid page filename")
    image_path = (resolve_book_dir(book_code) / "pages" / filename).resolve()
    base = resolve_book_dir(book_code).resolve()
    if not str(image_path).startswith(str(base) + os.sep) or not image_path.exists():
        raise HTTPException(404, "page not found")
    return FileResponse(image_path, media_type="image/png")


@app.get("/figures/{book_code}/{filename}")
async def get_figure_image(book_code: str, filename: str):
    """Serve an extracted figure image."""
    if not re.fullmatch(r"fig_\d+_\d+\.png", filename):
        raise HTTPException(400, "invalid figure filename")
    image_path = (resolve_book_dir(book_code) / "figures" / filename).resolve()
    base = resolve_book_dir(book_code).resolve()
    if not str(image_path).startswith(str(base) + os.sep) or not image_path.exists():
        raise HTTPException(404, "figure not found")
    return FileResponse(image_path, media_type="image/png")


def load_figures_map(book_code: str) -> dict:
    """Load the {figure_number: filename} map for a book, if present."""
    fmap = resolve_book_dir(book_code) / "figures_map.json"
    if fmap.exists():
        try:
            return json.loads(fmap.read_text())
        except (ValueError, OSError):
            return {}
    return {}


def list_page_images(book_code: str) -> list:
    """List rendered page image filenames for a book, in order."""
    pages_dir = resolve_book_dir(book_code) / "pages"
    if not pages_dir.exists():
        return []
    return sorted(f.name for f in pages_dir.glob("page_*.png"))


if __name__ == '__main__':
    import uvicorn
    print("NCERT Preview Server")
    print("Open http://localhost:8081")
    uvicorn.run(app, host="0.0.0.0", port=8081)
