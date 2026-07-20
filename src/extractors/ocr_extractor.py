"""OCR-based extractor using Tesseract (no API key required)."""

import json
import re
from pathlib import Path

import pytesseract
from PIL import Image

from .base import BaseExtractor


class OCRExtractor(BaseExtractor):
    """Extracts text from image-based PDFs using Tesseract OCR."""

    def __init__(self, output_dir: Path, lang: str = "eng"):
        super().__init__(output_dir)
        self.lang = lang

    def extract(self, source: Path) -> dict:
        """Extract from a directory of page renders."""
        renders_dir = source if source.is_dir() else self.renders_dir

        if not renders_dir.exists():
            raise FileNotFoundError(f"No renders at {renders_dir}")

        page_images = sorted(renders_dir.glob("page_*.png"))
        results = []
        all_text = []

        print(f"  OCR extracting {len(page_images)} pages...")

        for img_path in page_images:
            match = re.search(r'page_(\d+)', img_path.stem)
            page_num = int(match.group(1)) if match else 0

            result = self.extract_page(page_num, img_path)
            results.append(result)

            if result.get("text"):
                all_text.append(f"\n---\n## Page {page_num}\n\n{result['text']}")

        full_text = "\n".join(all_text)
        output_file = self.output_dir / "ocr_content.md"
        output_file.write_text(full_text, encoding="utf-8")

        pages_ocr = self.output_dir / "pages_ocr.json"
        pages_ocr.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

        total_chars = sum(len(r.get("text", "")) for r in results)
        print(f"  OCR complete: {total_chars:,} chars extracted")

        return {
            "pages": len(results),
            "total_chars": total_chars,
            "output_file": str(output_file)
        }

    def extract_page(self, page_num: int, image_path: Path) -> dict:
        """Extract text from a single page image using OCR."""
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=self.lang)
            text = text.strip()

            return {
                "page": page_num,
                "text": text,
                "char_count": len(text)
            }
        except Exception as e:
            print(f"    Page {page_num} OCR error: {e}")
            return {"page": page_num, "text": "", "error": str(e)}
