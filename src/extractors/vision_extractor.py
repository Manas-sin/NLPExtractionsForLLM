"""Vision-based extractor using Claude API."""

import base64
import json
import os
import re
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from .base import BaseExtractor

load_dotenv()


EXTRACTION_PROMPT = """You are extracting content from an NCERT textbook page.
Analyze this page image and extract ALL content in structured markdown format.

Follow these rules:
1. **Reading Order**: Follow the natural reading order. Handle two-column layouts correctly - read left column fully before right column.
2. **Section Headers**: Mark as ## 1.1 Title, ### 1.1.1 Subtitle
3. **Equations**: Convert ALL equations and formulas to LaTeX ($$...$$ for display, $...$ for inline)
4. **Chemical Formulas**: Use LaTeX subscripts: H₂O → $\\mathrm{H_2O}$, CO₂ → $\\mathrm{CO_2}$
5. **Tables**: Convert to proper markdown tables with | headers |
6. **Examples**: Mark as **Example X.Y** followed by problem and solution
7. **Exercises**: Mark as **Exercise X.Y** with full question text
8. **Figures**: Note as [Figure X.Y: caption description]
9. **Margin Notes/Boxes**: Include but mark clearly as > blockquotes
10. **Intext Questions**: Mark as **Intext Question X.Y**

Extract EVERYTHING - don't summarize or skip content. Preserve all numbers, values, and formulas exactly.

Return ONLY the structured markdown, no explanations."""


class VisionExtractor(BaseExtractor):
    """Extracts content using Claude Vision API."""

    def __init__(self, output_dir: Path, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        super().__init__(output_dir)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.client = None

    def _get_client(self) -> Anthropic:
        """Get or create Anthropic client."""
        if not self.api_key:
            raise ValueError("No Anthropic API key. Set ANTHROPIC_API_KEY in .env")
        if self.client is None:
            self.client = Anthropic(api_key=self.api_key)
        return self.client

    def extract(self, source: Path) -> dict:
        """Extract from a directory of page renders."""
        renders_dir = source if source.is_dir() else self.renders_dir

        if not renders_dir.exists():
            raise FileNotFoundError(f"No renders at {renders_dir}")

        page_images = sorted(renders_dir.glob("page_*.png"))
        total_tokens = 0
        results = []

        for img_path in page_images:
            match = re.search(r'page_(\d+)', img_path.stem)
            page_num = int(match.group(1)) if match else 0

            vision_file = self.output_dir / f"vision_page_{page_num:03d}.md"
            if vision_file.exists() and vision_file.stat().st_size > 100:
                continue

            result = self.extract_page(page_num, img_path)
            results.append(result)
            total_tokens += result.get("tokens_used", 0)

            if result.get("markdown"):
                vision_file.write_text(result["markdown"], encoding="utf-8")

        self._merge_pages()

        return {
            "pages": len(results),
            "total_tokens": total_tokens,
            "estimated_cost": round(total_tokens * 0.000003, 4)
        }

    def extract_page(self, page_num: int, image_path: Path) -> dict:
        """Extract content from a single page image using Vision API."""
        client = self._get_client()
        image_data = self._encode_image(image_path)

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT}
                    ]
                }]
            )

            return {
                "page": page_num,
                "markdown": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except Exception as e:
            return {"page": page_num, "markdown": "", "error": str(e)}

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _merge_pages(self) -> str:
        """Merge all vision_page_*.md files into chapter_complete.md."""
        page_files = sorted(
            self.output_dir.glob("vision_page_*.md"),
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))
        )

        if not page_files:
            return ""

        merged_content = []

        for i, page_file in enumerate(page_files):
            content = page_file.read_text(encoding="utf-8").strip()
            if not content:
                continue

            if i == 0:
                merged_content.append(content)
                continue

            lines = content.split('\n')
            cleaned_lines = []

            for line in lines:
                if re.match(r'^(Chemistry\s+)?\d+(\s+Solutions)?$', line.strip()):
                    continue
                if re.match(r'^\d+\s+(Chemistry|Solutions|Electrochemistry|Chemical Kinetics)$', line.strip()):
                    continue
                if line.startswith('# Unit') and i > 0:
                    continue
                cleaned_lines.append(line)

            content = '\n'.join(cleaned_lines).strip()
            if content:
                merged_content.append('\n' + content)

        full_text = '\n'.join(merged_content)
        full_text = re.sub(r'\n{4,}', '\n\n\n', full_text)

        output_file = self.output_dir / "chapter_complete.md"
        output_file.write_text(full_text, encoding="utf-8")

        return full_text
