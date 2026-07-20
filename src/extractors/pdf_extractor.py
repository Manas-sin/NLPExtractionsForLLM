"""PDF-based extractor using PyMuPDF."""

import json
import re
from pathlib import Path

import fitz

from .base import BaseExtractor
from ..utils.pdf import extract_page_text, render_page, find_figure_captions


class PDFExtractor(BaseExtractor):
    """Extracts text, renders, and figures from PDF using PyMuPDF."""

    def __init__(self, output_dir: Path, render_scale: float = 2.0, figure_scale: float = 3.0):
        super().__init__(output_dir)
        self.render_scale = render_scale
        self.figure_scale = figure_scale

    def extract(self, pdf_path: Path) -> dict:
        """Extract all content from a PDF."""
        self.setup_directories()

        doc = fitz.open(pdf_path)
        pages_data = []
        all_figures = []
        all_text = []

        for page_num, page in enumerate(doc, start=1):
            result = self.extract_page(page_num, page)
            pages_data.append(result["page_data"])
            all_figures.extend(result["figures"])
            all_text.append(result["markdown"])

        doc.close()

        self._save_outputs(pages_data, all_figures, all_text)

        return {
            "pages": len(pages_data),
            "figures": len(all_figures),
            "total_chars": sum(p["char_count"] for p in pages_data),
            "output_dir": str(self.output_dir)
        }

    def extract_page(self, page_num: int, page: fitz.Page) -> dict:
        """Extract content from a single page."""
        text, book_page = extract_page_text(page)

        page_data = {
            "page": page_num,
            "book_page": book_page,
            "char_count": len(text),
            "text": text
        }

        (self.pages_dir / f"page_{page_num:03d}.txt").write_text(text, encoding="utf-8")

        pix = render_page(page, self.render_scale)
        pix.save(self.renders_dir / f"page_{page_num:03d}.png")

        figures = self._extract_figures(page, page_num)

        if book_page:
            markdown = f"\n---\n## Page {book_page}\n{text}"
        else:
            markdown = f"\n---\n## Page {page_num} (unnumbered)\n{text}"

        return {"page_data": page_data, "figures": figures, "markdown": markdown}

    def _extract_figures(self, page: fitz.Page, page_num: int) -> list[dict]:
        """Extract figures by rendering page regions around captions."""
        figures = []
        page_width = page.rect.width
        page_height = page.rect.height

        captions = find_figure_captions(page)
        content_images = self._find_content_images(page, page_width, page_height)

        for cap in captions:
            region = self._find_figure_region(cap, content_images, page, page_width, page_height)
            if region is None:
                continue

            clip = fitz.Rect(*region)
            mat = fitz.Matrix(self.figure_scale, self.figure_scale)
            pix = page.get_pixmap(matrix=mat, clip=clip)

            fig_name = f"fig{cap['fig_num'].replace('.', '_')}.png"
            pix.save(self.figures_dir / fig_name)

            figures.append({
                "page": page_num,
                "figure": cap["fig_num"],
                "caption": cap["caption"],
                "image": fig_name
            })

        return figures

    def _find_content_images(self, page: fitz.Page, page_width: float, page_height: float) -> list:
        """Find non-background images that might be figures."""
        content_images = []
        for img in page.get_image_info():
            bbox = img["bbox"]
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if width < 80 or height < 80:
                continue
            if width > page_width * 0.9 and height > page_height * 0.9:
                continue
            content_images.append(bbox)
        return content_images

    def _find_figure_region(self, caption: dict, content_images: list,
                            page: fitz.Page, page_width: float, page_height: float) -> tuple | None:
        """Find the region containing a figure based on its caption."""
        caption_y = caption["y"]
        caption_x0 = caption["x0"]
        caption_x1 = caption["x1"]

        for img_bbox in content_images:
            img_bottom = img_bbox[3]
            if 0 < caption_y - img_bottom < 100:
                x0 = max(0, img_bbox[0] - 10)
                y0 = max(0, img_bbox[1] - 10)
                x1 = min(page_width, img_bbox[2] + 10)
                y1 = min(page_height, img_bbox[3] + 10)
                return (x0, y0, x1, y1)

        fig_height = self._estimate_figure_height(page, caption_y, caption_x0, caption_x1)
        x0 = max(0, caption_x0 - 20)
        x1 = min(page_width, caption_x1 + 20)
        y0 = max(0, caption_y - fig_height)
        y1 = caption_y - 5

        if y1 - y0 < 30 or x1 - x0 < 30:
            return None

        return (x0, y0, x1, y1)

    def _estimate_figure_height(self, page: fitz.Page, caption_y: float,
                                 caption_x0: float, caption_x1: float) -> float:
        """Estimate figure height by analyzing page content."""
        drawings = page.get_drawings()
        drawing_tops = []

        for d in drawings:
            if "rect" not in d:
                continue
            r = d["rect"]
            if r.y1 < caption_y and r.y0 > 20:
                if r.x0 < caption_x1 + 50 and r.x1 > caption_x0 - 50:
                    drawing_tops.append(r.y0)

        if drawing_tops:
            top_y = min(drawing_tops)
            height = caption_y - top_y + 10
            return max(80, min(height, 500))

        blocks = page.get_text("dict", sort=True)["blocks"]
        text_blocks_above = []

        for block in blocks:
            if block["type"] == 0:
                bbox = block["bbox"]
                if bbox[3] < caption_y - 20:
                    if bbox[0] < caption_x1 and bbox[2] > caption_x0:
                        text_blocks_above.append(bbox[3])

        if text_blocks_above:
            last_text_y = max(text_blocks_above)
            height = caption_y - last_text_y - 15
            return max(80, min(height, 400))

        return 250

    def _save_outputs(self, pages_data: list, all_figures: list, all_text: list):
        """Save extraction outputs."""
        (self.output_dir / "content.md").write_text("\n".join(all_text), encoding="utf-8")
        (self.output_dir / "pages.json").write_text(
            json.dumps(pages_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (self.output_dir / "figures.json").write_text(
            json.dumps(all_figures, ensure_ascii=False, indent=2), encoding="utf-8"
        )
