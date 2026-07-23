"""Docling-based extractor for ML-powered PDF parsing."""

import json
from pathlib import Path
from typing import Optional

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

from .base import BaseExtractor


class DoclingExtractor(BaseExtractor):
    """Extract structured content from PDFs using IBM Docling."""

    def __init__(self, output_dir: Path, ocr_enabled: bool = True):
        super().__init__(output_dir)
        self.ocr_enabled = ocr_enabled
        self._converter = None

    @property
    def converter(self) -> DocumentConverter:
        """Lazy-load converter (heavy initialization)."""
        if self._converter is None:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = self.ocr_enabled
            pipeline_options.do_table_structure = True

            self._converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                format_options={
                    InputFormat.PDF: {
                        "pipeline_options": pipeline_options,
                        "backend": PyPdfiumDocumentBackend,
                    }
                }
            )
        return self._converter

    def extract(self, pdf_path: Path) -> dict:
        """Extract structured content from PDF."""
        self.setup_directories()

        result = self.converter.convert(pdf_path)
        doc = result.document

        sections = self._extract_sections(doc)
        tables = self._extract_tables(doc)
        equations = self._extract_equations(doc)
        figures = self._extract_figures(doc)

        markdown = doc.export_to_markdown()
        (self.output_dir / "content.md").write_text(markdown, encoding="utf-8")

        structured = {
            "sections": sections,
            "tables": tables,
            "equations": equations,
            "figures": figures,
            "statistics": {
                "section_count": len(sections),
                "table_count": len(tables),
                "equation_count": len(equations),
                "figure_count": len(figures),
            }
        }

        (self.output_dir / "docling_output.json").write_text(
            json.dumps(structured, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return structured

    def _extract_sections(self, doc) -> list[dict]:
        """Extract sections with hierarchy."""
        sections = []
        current_section = None

        for item in doc.iterate_items():
            if hasattr(item, 'label') and 'heading' in str(item.label).lower():
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "title": item.text if hasattr(item, 'text') else str(item),
                    "level": self._get_heading_level(item),
                    "content": []
                }
            elif current_section and hasattr(item, 'text'):
                current_section["content"].append(item.text)

        if current_section:
            sections.append(current_section)

        for section in sections:
            section["content"] = "\n".join(section["content"])

        return sections

    def _get_heading_level(self, item) -> int:
        """Determine heading level from item."""
        label = str(item.label).lower() if hasattr(item, 'label') else ""
        if 'h1' in label or 'title' in label:
            return 1
        elif 'h2' in label:
            return 2
        elif 'h3' in label:
            return 3
        return 2

    def _extract_tables(self, doc) -> list[dict]:
        """Extract tables with structure."""
        tables = []
        table_num = 0

        for item in doc.iterate_items():
            if hasattr(item, 'label') and 'table' in str(item.label).lower():
                table_num += 1
                table_data = {
                    "number": str(table_num),
                    "headers": [],
                    "rows": []
                }

                if hasattr(item, 'data') and item.data:
                    data = item.data
                    if hasattr(data, 'grid') and data.grid:
                        grid = data.grid
                        if len(grid) > 0:
                            table_data["headers"] = [str(cell) for cell in grid[0]]
                            for row in grid[1:]:
                                table_data["rows"].append([str(cell) for cell in row])

                tables.append(table_data)

        return tables

    def _extract_equations(self, doc) -> list[dict]:
        """Extract equations."""
        equations = []

        for item in doc.iterate_items():
            if hasattr(item, 'label'):
                label = str(item.label).lower()
                if 'formula' in label or 'equation' in label or 'math' in label:
                    text = item.text if hasattr(item, 'text') else str(item)
                    equations.append({
                        "type": "display",
                        "latex": text,
                        "raw": text
                    })

        return equations

    def _extract_figures(self, doc) -> list[dict]:
        """Extract figure references."""
        figures = []
        fig_num = 0

        for item in doc.iterate_items():
            if hasattr(item, 'label'):
                label = str(item.label).lower()
                if 'figure' in label or 'picture' in label or 'image' in label:
                    fig_num += 1
                    caption = item.text if hasattr(item, 'text') else ""
                    figures.append({
                        "number": str(fig_num),
                        "caption": caption
                    })

        return figures

    def extract_to_chunks(self, pdf_path: Path, chunk_size: int = 1000) -> list[dict]:
        """Extract and chunk for RAG/embeddings."""
        from docling.chunking import HybridChunker

        result = self.converter.convert(pdf_path)
        chunker = HybridChunker(
            tokenizer="sentence-transformers/all-MiniLM-L6-v2",
            max_tokens=chunk_size
        )

        chunks = []
        for chunk in chunker.chunk(result.document):
            chunks.append({
                "text": chunk.text,
                "metadata": {
                    "headings": [h.text for h in chunk.meta.headings] if chunk.meta.headings else [],
                    "page": chunk.meta.doc_items[0].prov[0].page_no if chunk.meta.doc_items else None
                }
            })

        return chunks
