#!/usr/bin/env python3
"""
Image Enhancement using Mistral Pixtral API.
Generates better captions and descriptions for extracted figures.
"""

import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral

# Load .env file
load_dotenv()


def encode_image(image_path: Path) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_mime(image_path: Path) -> str:
    """Get MIME type from extension."""
    ext = image_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    return mime_types.get(ext, "image/png")


def analyze_figure(client: Mistral, image_path: Path, caption: str = "") -> dict:
    """
    Analyze a figure using Mistral Pixtral.
    Returns enhanced description and identified diagram type.
    """
    image_data = encode_image(image_path)
    mime_type = get_image_mime(image_path)

    prompt = f"""Analyze this NCERT textbook figure.
Original caption: {caption if caption else 'Not provided'}

Provide:
1. A clear, concise description of what the diagram shows (2-3 sentences)
2. The type of diagram (e.g., graph, flowchart, cell diagram, circuit, experimental setup, etc.)
3. Key labels or components visible
4. Subject area (Chemistry, Physics, Biology, Maths)

Respond in JSON format:
{{"description": "...", "diagram_type": "...", "components": [...], "subject": "..."}}"""

    try:
        response = client.chat.complete(
            model="pixtral-12b-2409",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:{mime_type};base64,{image_data}"}
                    ]
                }
            ]
        )

        result_text = response.choices[0].message.content

        # Parse JSON from response
        try:
            # Find JSON in response
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result_text[start:end])
        except json.JSONDecodeError:
            pass

        return {"description": result_text, "diagram_type": "unknown", "components": [], "subject": "unknown"}

    except Exception as e:
        print(f"Error analyzing {image_path.name}: {e}")
        return None


def enhance_figures(book_code: str, api_key: str = None):
    """Enhance all figures for a book using Mistral API."""

    if not api_key:
        api_key = os.environ.get("MISTRAL_API_KEY")

    if not api_key:
        print("Error: No Mistral API key provided")
        return

    client = Mistral(api_key=api_key)

    base_dir = Path("extracted") / book_code
    figures_json = base_dir / "figures.json"
    figures_dir = base_dir / "figures"

    if not figures_json.exists():
        print(f"No figures.json found for {book_code}")
        return

    figures = json.loads(figures_json.read_text())
    enhanced = []

    print(f"Enhancing {len(figures)} figures with Mistral Pixtral...")

    for fig in figures:
        image_path = figures_dir / fig["image"]
        if not image_path.exists():
            enhanced.append(fig)
            continue

        print(f"  Analyzing {fig['image']}...")

        analysis = analyze_figure(client, image_path, fig.get("caption", ""))

        if analysis:
            fig["enhanced_description"] = analysis.get("description", "")
            fig["diagram_type"] = analysis.get("diagram_type", "")
            fig["components"] = analysis.get("components", [])
            fig["detected_subject"] = analysis.get("subject", "")

        enhanced.append(fig)

    # Save enhanced figures
    output_file = base_dir / "figures_enhanced.json"
    output_file.write_text(json.dumps(enhanced, ensure_ascii=False, indent=2))
    print(f"\nSaved enhanced figures to: {output_file}")

    # Also update final_output.json if exists
    final_output = base_dir / "final_output.json"
    if final_output.exists():
        final_data = json.loads(final_output.read_text())
        final_data["figures_enhanced"] = enhanced
        final_output.write_text(json.dumps(final_data, ensure_ascii=False, indent=2))
        print(f"Updated: {final_output}")

    return enhanced


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_enhance.py <book_code> [mistral_api_key]")
        print("Example: python image_enhance.py lech101")
        print("(API key loaded from .env if not provided)")
        sys.exit(1)

    book_code = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None

    enhance_figures(book_code, api_key)
