"""Compare extraction quality across different techniques.

Runs multiple extractors on the same PDF, then uses Claude to evaluate
and score each approach. Outputs a comparison report.
"""

import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import fitz
import anthropic

from .pdf_extractor import PDFExtractor
from .ocr_extractor import OCRExtractor


@dataclass
class ExtractionResult:
    """Result from one extraction technique."""
    technique: str
    text: str
    time_seconds: float
    char_count: int
    word_count: int
    has_tables: bool
    has_equations: bool
    error: Optional[str] = None


@dataclass
class ComparisonScore:
    """AI evaluation scores for an extraction."""
    technique: str
    accuracy: int  # 1-10
    completeness: int  # 1-10
    structure: int  # 1-10
    readability: int  # 1-10
    equation_quality: int  # 1-10
    table_quality: int  # 1-10
    overall: int  # 1-10
    strengths: list[str]
    weaknesses: list[str]
    best_for: str


class ExtractionComparator:
    """Compare extraction techniques on the same PDF."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = None

    def _get_client(self):
        """Lazy load Anthropic client."""
        if self.client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = anthropic.Anthropic(api_key=api_key)
        return self.client

    def extract_with_pymupdf(self, pdf_path: Path, page_num: int = 1) -> ExtractionResult:
        """Extract using PyMuPDF (basic text extraction)."""
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
                has_tables=False,
                has_equations=False,
            )
        except Exception as e:
            return ExtractionResult(
                technique="PyMuPDF", text="", time_seconds=0,
                char_count=0, word_count=0, has_tables=False,
                has_equations=False, error=str(e)
            )

    def extract_with_docling(self, pdf_path: Path, page_num: int = 1) -> ExtractionResult:
        """Extract using Docling (ML-based structure detection)."""
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

            # Get text from specific page
            text_parts = []
            has_tables = False
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
                    if "table" in label:
                        has_tables = True
                    if "formula" in label or "equation" in label:
                        has_equations = True

            full_text = "\n".join(text_parts)

            return ExtractionResult(
                technique="Docling",
                text=full_text,
                time_seconds=round(time.time() - start, 3),
                char_count=len(full_text),
                word_count=len(full_text.split()),
                has_tables=has_tables,
                has_equations=has_equations,
            )
        except Exception as e:
            return ExtractionResult(
                technique="Docling", text="", time_seconds=0,
                char_count=0, word_count=0, has_tables=False,
                has_equations=False, error=str(e)
            )

    def extract_with_ocr(self, pdf_path: Path, page_num: int = 1) -> ExtractionResult:
        """Extract using Tesseract OCR."""
        start = time.time()
        try:
            import pytesseract
            from PIL import Image
            import io

            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            doc.close()

            text = pytesseract.image_to_string(img)

            return ExtractionResult(
                technique="Tesseract OCR",
                text=text,
                time_seconds=round(time.time() - start, 3),
                char_count=len(text),
                word_count=len(text.split()),
                has_tables=False,
                has_equations=False,
            )
        except Exception as e:
            return ExtractionResult(
                technique="Tesseract OCR", text="", time_seconds=0,
                char_count=0, word_count=0, has_tables=False,
                has_equations=False, error=str(e)
            )

    def extract_with_vision(self, pdf_path: Path, page_num: int = 1) -> ExtractionResult:
        """Extract using Gemini Vision API."""
        start = time.time()
        try:
            from google import genai
            from google.genai import types

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set")

            client = genai.Client(api_key=api_key)

            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            doc.close()

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                            types.Part.from_text(text="""Extract ALL text from this textbook page exactly as written.
For equations, convert to LaTeX format.
For tables, use markdown table format.
Preserve section numbers and headings.
Output only the extracted content, no commentary."""),
                        ]
                    )
                ]
            )

            text = response.text
            has_tables = "|" in text and "---" in text
            has_equations = "$" in text or "\\frac" in text or "\\int" in text or "\\(" in text

            return ExtractionResult(
                technique="Gemini Vision (ADK)",
                text=text,
                time_seconds=round(time.time() - start, 3),
                char_count=len(text),
                word_count=len(text.split()),
                has_tables=has_tables,
                has_equations=has_equations,
            )
        except Exception as e:
            return ExtractionResult(
                technique="Gemini Vision (ADK)", text="", time_seconds=0,
                char_count=0, word_count=0, has_tables=False,
                has_equations=False, error=str(e)
            )

    def compare_page(self, pdf_path: Path, page_num: int = 1,
                     techniques: list[str] = None) -> dict:
        """Run all techniques on a single page and compare."""
        if techniques is None:
            techniques = ["pymupdf", "docling", "ocr", "vision"]

        results = []

        if "pymupdf" in techniques:
            print("  Running PyMuPDF...")
            results.append(self.extract_with_pymupdf(pdf_path, page_num))

        if "docling" in techniques:
            print("  Running Docling...")
            results.append(self.extract_with_docling(pdf_path, page_num))

        if "ocr" in techniques:
            print("  Running Tesseract OCR...")
            results.append(self.extract_with_ocr(pdf_path, page_num))

        if "vision" in techniques:
            print("  Running Claude Vision...")
            results.append(self.extract_with_vision(pdf_path, page_num))

        return {
            "pdf": str(pdf_path),
            "page": page_num,
            "results": [asdict(r) for r in results],
        }

    def evaluate_with_ai(self, comparison: dict) -> list[ComparisonScore]:
        """Use Claude to evaluate and score each extraction."""
        results = comparison["results"]
        valid_results = [r for r in results if not r.get("error")]

        if not valid_results:
            return []

        prompt = f"""You are evaluating text extraction quality from a PDF page.
Below are extractions from {len(valid_results)} different techniques.

Rate each technique on a scale of 1-10 for:
1. accuracy - How accurately does it capture the original text?
2. completeness - Does it capture all content (text, equations, tables)?
3. structure - Does it preserve document structure (headings, paragraphs)?
4. readability - Is the output readable and well-formatted?
5. equation_quality - How well are mathematical equations captured? (1 if none expected)
6. table_quality - How well are tables captured? (1 if none expected)
7. overall - Overall quality score

Also provide:
- strengths: 2-3 bullet points
- weaknesses: 2-3 bullet points
- best_for: One sentence describing ideal use case

"""
        for r in valid_results:
            prompt += f"\n\n=== {r['technique']} ===\n"
            prompt += f"Time: {r['time_seconds']}s | Chars: {r['char_count']} | Words: {r['word_count']}\n"
            prompt += f"Text (first 2000 chars):\n{r['text'][:2000]}\n"

        prompt += """

Respond in JSON format:
{
  "evaluations": [
    {
      "technique": "...",
      "accuracy": 1-10,
      "completeness": 1-10,
      "structure": 1-10,
      "readability": 1-10,
      "equation_quality": 1-10,
      "table_quality": 1-10,
      "overall": 1-10,
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "best_for": "..."
    }
  ],
  "recommendation": "Which technique is best for this type of content and why",
  "summary_table": "Markdown table comparing all scores"
}"""

        try:
            client = self._get_client()
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text
            # Extract JSON from response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return data
        except Exception as e:
            return {"error": str(e)}

        return []

    def full_comparison(self, pdf_path: Path, page_num: int = 1,
                        techniques: list[str] = None) -> dict:
        """Run comparison and AI evaluation."""
        print(f"Comparing extraction techniques on {pdf_path} page {page_num}...")

        comparison = self.compare_page(pdf_path, page_num, techniques)

        print("  Evaluating with AI...")
        evaluation = self.evaluate_with_ai(comparison)

        result = {
            **comparison,
            "evaluation": evaluation,
        }

        # Save results
        output_file = self.output_dir / f"comparison_page{page_num}.json"
        output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"  Saved to {output_file}")

        return result

    def print_comparison(self, result: dict):
        """Print comparison results in readable format."""
        print("\n" + "=" * 60)
        print(f"EXTRACTION COMPARISON: {result['pdf']} (Page {result['page']})")
        print("=" * 60)

        print("\n--- Extraction Results ---")
        for r in result["results"]:
            status = "ERROR" if r.get("error") else "OK"
            print(f"\n{r['technique']}: [{status}]")
            if r.get("error"):
                print(f"  Error: {r['error']}")
            else:
                print(f"  Time: {r['time_seconds']}s")
                print(f"  Chars: {r['char_count']} | Words: {r['word_count']}")
                print(f"  Tables: {'Yes' if r['has_tables'] else 'No'} | Equations: {'Yes' if r['has_equations'] else 'No'}")

        if "evaluation" in result and not result["evaluation"].get("error"):
            eval_data = result["evaluation"]
            print("\n--- AI Evaluation ---")

            if "summary_table" in eval_data:
                print(f"\n{eval_data['summary_table']}")

            if "recommendation" in eval_data:
                print(f"\nRecommendation: {eval_data['recommendation']}")

            for e in eval_data.get("evaluations", []):
                print(f"\n{e['technique']}:")
                print(f"  Overall: {e['overall']}/10")
                print(f"  Strengths: {', '.join(e['strengths'])}")
                print(f"  Best for: {e['best_for']}")


def compare_extraction(pdf_path: str, page: int = 1,
                       techniques: list[str] = None,
                       output_dir: str = "data/comparisons") -> dict:
    """Convenience function to run comparison."""
    comparator = ExtractionComparator(Path(output_dir))
    result = comparator.full_comparison(Path(pdf_path), page, techniques)
    comparator.print_comparison(result)
    return result
