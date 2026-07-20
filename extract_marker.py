
import json
import sys
from pathlib import Path

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered


def extract_with_marker(pdf_path: Path):
    out_dir = Path("extracted") / pdf_path.stem
    images_dir = out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(exist_ok=True)

    print(f"Loading models (first run downloads them)...")
    models = create_model_dict()

    print(f"Converting {pdf_path.name}...")
    converter = PdfConverter(artifact_dict=models)
    rendered = converter(str(pdf_path))

    # Get markdown text
    text, _, images = text_from_rendered(rendered)

    # Save markdown
    (out_dir / "content.md").write_text(text, encoding="utf-8")

    # Save images
    image_data = []
    for img_name, img in images.items():
        img_path = images_dir / img_name
        img.save(img_path)
        image_data.append({
            "name": img_name,
            "width": img.width,
            "height": img.height
        })

    # Save structured JSON
    json_output = {
        "source": pdf_path.name,
        "markdown": text,
        "images": image_data,
        "char_count": len(text),
        "image_count": len(images)
    }
    (out_dir / "content.json").write_text(
        json.dumps(json_output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\nExtracted:")
    print(f"  Chars: {len(text):,}")
    print(f"  Images: {len(images)}")
    print(f"  Output: {out_dir}/")

    return json_output


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_marker.py <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    extract_with_marker(pdf_path)
