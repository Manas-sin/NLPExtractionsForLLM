"""Batch: render watermark-free page images + run Docling for a set of chapters.

Usage:
    python scripts/batch_docling.py <code:pdf_path> [<code:pdf_path> ...]
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.page_renderer import render_book
from src.extractors.docling_structurer import DoclingStructurer


def process(book_code: str, pdf_path: str):
    base = Path("data/extracted") / book_code
    base.mkdir(parents=True, exist_ok=True)
    pdf = Path(pdf_path)

    # 1) Render page images (watermark removed) if missing
    pages_dir = base / "pages"
    if not (pages_dir.exists() and list(pages_dir.glob("page_*.png"))):
        n = len(render_book(book_code, pdf, base))
    else:
        n = len(list(pages_dir.glob("page_*.png")))

    # 2) Back up any regex output, then run Docling
    final = base / "final_output.json"
    if final.exists() and not (base / "final_output.regex.json").exists():
        shutil.copy(final, base / "final_output.regex.json")

    data = DoclingStructurer(book_code, pdf, base).save(final)
    d = __import__("json").loads(Path(data).read_text())
    s = d["statistics"]
    print(f"{book_code}: {d['unit_title']!r}  pages={n}  sec={s['section_count']} "
          f"tbl={s['table_count']} fig={s['figure_count']} ex={s['example_count']} "
          f"exr={s['exercise_count']}  page_index={len(d['page_index'])}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        code, _, path = arg.partition(":")
        try:
            process(code, path)
        except Exception as exc:  # keep going on failure
            print(f"{code}: FAILED - {exc}")
