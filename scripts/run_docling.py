"""Run the Docling structurer on a book and promote it to final_output.json.

Backs up any existing regex output to final_output.regex.json so you can compare.

Usage:
    python scripts/run_docling.py <book_code> <pdf_path>
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.docling_structurer import DoclingStructurer


def main(book_code: str, pdf_path: str):
    base = Path("data/extracted") / book_code
    base.mkdir(parents=True, exist_ok=True)

    final = base / "final_output.json"
    if final.exists() and not (base / "final_output.regex.json").exists():
        shutil.copy(final, base / "final_output.regex.json")
        print(f"Backed up regex output -> {base/'final_output.regex.json'}")

    structurer = DoclingStructurer(book_code, pdf_path, base)
    structurer.save(final)
    print(f"Wrote Docling output -> {final}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
