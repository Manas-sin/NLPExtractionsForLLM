"""Ensemble PDF Extractor - combines multiple tools for best accuracy.

Runs PyMuPDF, Docling, and Gemini Vision in parallel, then uses an
LLM agent to merge the best parts and validate against the original.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import fitz
from google import genai
from google.genai import types


@dataclass
class ExtractionResult:
    """Result from one extraction technique."""
    technique: str
    text: str
    time_seconds: float
    char_count: int
    word_count: int
    has_equations: bool
    error: Optional[str] = None


@dataclass
class EnsembleResult:
    """Final merged result from ensemble extraction."""
    merged_text: str
    confidence_score: float
    sources_used: list[str]
    watermarks_removed: list[str]
    validation_notes: str
    individual_results: list[ExtractionResult]


class EnsembleExtractor:
    """Extracts text using multiple tools and merges results."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.client = None

    def _get_client(self):
        """Lazy load Genai client."""
        if self.client is None:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def extract_pymupdf(self, pdf_path: Path, page_num: int) -> ExtractionResult:
        """Fast text extraction with PyMuPDF."""
        start = time.time()
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            text = page.get_text("text")
            doc.close()

            return ExtractionResult(
                technique="PyMuPDF",
                text=text,
                time_seconds=round(time.time() - start, 3),
                char_count=len(text),
                word_count=len(text.split()),
                has_equations=False,
            )
        except Exception as e:
            return ExtractionResult(
                technique="PyMuPDF", text="", time_seconds=0,
                char_count=0, word_count=0, has_equations=False, error=str(e)
            )

    def extract_docling(self, pdf_path: Path, page_num: int) -> ExtractionResult:
        """ML-based extraction with Docling."""
        start = time.time()
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions

            opts = PdfPipelineOptions()
            opts.do_ocr = False
            opts.do_table_structure = True

            conv = DocumentConverter(
                format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
            )
            result = conv.convert(str(pdf_path))
            doc = result.document

            text_parts = []
            has_equations = False

            for item, _ in doc.iterate_items():
                prov = getattr(item, "prov", None)
                item_page = 0
                if prov:
                    try:
                        item_page = int(prov[0].page_no)
                    except:
                        pass

                if item_page == page_num:
                    label = str(getattr(item, "label", "")).lower()
                    text = getattr(item, "text", "") or ""
                    if text:
                        text_parts.append(text)
                    if "formula" in label or "equation" in label:
                        has_equations = True

            full_text = "\n".join(text_parts)

            return ExtractionResult(
                technique="Docling",
                text=full_text,
                time_seconds=round(time.time() - start, 3),
                char_count=len(full_text),
                word_count=len(full_text.split()),
                has_equations=has_equations,
            )
        except Exception as e:
            return ExtractionResult(
                technique="Docling", text="", time_seconds=0,
                char_count=0, word_count=0, has_equations=False, error=str(e)
            )

    def extract_vision(self, pdf_path: Path, page_num: int) -> ExtractionResult:
        """Vision-based extraction with Gemini."""
        start = time.time()
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            doc.close()

            client = self._get_client()
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                            types.Part.from_text(text="""Extract ALL text from this NCERT textbook page exactly as written.

Rules:
1. Convert mathematical equations to LaTeX format (use $...$ for inline, $$...$$ for display)
2. Preserve section numbers and headings exactly
3. For tables, use markdown table format
4. Ignore watermarks, page numbers, and "Reprint 2026-27" type text
5. Keep paragraph structure intact

Output ONLY the extracted content, no commentary."""),
                        ]
                    )
                ]
            )

            text = response.text
            has_equations = "$" in text or "\\frac" in text or "\\int" in text

            return ExtractionResult(
                technique="Gemini Vision",
                text=text,
                time_seconds=round(time.time() - start, 3),
                char_count=len(text),
                word_count=len(text.split()),
                has_equations=has_equations,
            )
        except Exception as e:
            return ExtractionResult(
                technique="Gemini Vision", text="", time_seconds=0,
                char_count=0, word_count=0, has_equations=False, error=str(e)
            )

    def extract_all_parallel(self, pdf_path: Path, page_num: int) -> list[ExtractionResult]:
        """Run all extractors in parallel."""
        results = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.extract_pymupdf, pdf_path, page_num): "pymupdf",
                executor.submit(self.extract_docling, pdf_path, page_num): "docling",
                executor.submit(self.extract_vision, pdf_path, page_num): "vision",
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  {result.technique}: {result.char_count} chars in {result.time_seconds}s")
                except Exception as e:
                    print(f"  {name}: ERROR - {e}")

        return results

    def merge_and_validate(self, pdf_path: Path, page_num: int,
                           results: list[ExtractionResult]) -> EnsembleResult:
        """Use LLM to merge best parts from all extractions."""

        # Get page image for validation
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        doc.close()

        # Build prompt with all extractions
        valid_results = [r for r in results if not r.error and r.text]

        if not valid_results:
            return EnsembleResult(
                merged_text="",
                confidence_score=0.0,
                sources_used=[],
                watermarks_removed=[],
                validation_notes="All extractors failed",
                individual_results=results,
            )

        prompt = """You are comparing multiple text extractions of the same NCERT textbook page.
Your job is to create the BEST possible merged extraction.

Here are the extractions from different tools:

"""
        for r in valid_results:
            prompt += f"\n=== {r.technique} ({r.char_count} chars) ===\n"
            prompt += r.text[:3000]  # Limit to avoid token overflow
            prompt += "\n"

        prompt += """

Now look at the ORIGINAL page image above and create the BEST merged extraction:

1. Use the most accurate text from each source
2. Keep proper LaTeX for equations (from Gemini Vision if available)
3. Remove any watermarks, "Reprint 20XX", page numbers
4. Fix any obvious OCR errors by checking the image
5. Preserve exact section numbers, headings, formatting

Return JSON:
{
  "merged_text": "The final best extraction...",
  "confidence_score": 0.0-1.0,
  "sources_used": ["Gemini Vision for equations", "Docling for structure", ...],
  "watermarks_removed": ["Reprint 2026-27", ...],
  "validation_notes": "Any issues found..."
}"""

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        types.Part.from_text(text=prompt),
                    ]
                )
            ]
        )

        text = response.text

        # Parse JSON response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
                return EnsembleResult(
                    merged_text=data.get("merged_text", ""),
                    confidence_score=data.get("confidence_score", 0.0),
                    sources_used=data.get("sources_used", []),
                    watermarks_removed=data.get("watermarks_removed", []),
                    validation_notes=data.get("validation_notes", ""),
                    individual_results=results,
                )
            except json.JSONDecodeError:
                pass

        # Fallback: use Gemini Vision result if available
        vision_result = next((r for r in valid_results if "Vision" in r.technique), None)
        best_result = vision_result or valid_results[0]

        return EnsembleResult(
            merged_text=best_result.text,
            confidence_score=0.7,
            sources_used=[best_result.technique],
            watermarks_removed=[],
            validation_notes="Fallback to single best source",
            individual_results=results,
        )

    def extract_page(self, pdf_path: Path, page_num: int = 1) -> EnsembleResult:
        """Full ensemble extraction for a single page."""
        pdf_path = Path(pdf_path)
        print(f"Extracting page {page_num} from {pdf_path.name}...")

        # Run all extractors
        print("Running extractors in parallel...")
        results = self.extract_all_parallel(pdf_path, page_num)

        # Merge and validate
        print("Merging and validating...")
        ensemble = self.merge_and_validate(pdf_path, page_num, results)

        print(f"Done! Confidence: {ensemble.confidence_score:.0%}")
        return ensemble

    def extract_chapter(self, pdf_path: Path, start_page: int = 1,
                        end_page: int = None) -> list[EnsembleResult]:
        """Extract multiple pages from a chapter."""
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()

        if end_page is None:
            end_page = total_pages

        results = []
        for page_num in range(start_page, end_page + 1):
            print(f"\n--- Page {page_num}/{end_page} ---")
            result = self.extract_page(pdf_path, page_num)
            results.append(result)

        return results


def extract_ensemble(pdf_path: str, page: int = 1, output_dir: str = "data/extracted") -> dict:
    """Convenience function for ensemble extraction."""
    extractor = EnsembleExtractor()
    result = extractor.extract_page(Path(pdf_path), page)

    # Save result
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_name = Path(pdf_path).stem
    output_file = output_path / f"{pdf_name}_page{page}_ensemble.json"

    result_dict = {
        "pdf": str(pdf_path),
        "page": page,
        "merged_text": result.merged_text,
        "confidence_score": result.confidence_score,
        "sources_used": result.sources_used,
        "watermarks_removed": result.watermarks_removed,
        "validation_notes": result.validation_notes,
        "individual_results": [asdict(r) for r in result.individual_results],
    }

    output_file.write_text(json.dumps(result_dict, ensure_ascii=False, indent=2))
    print(f"Saved to {output_file}")

    return result_dict
