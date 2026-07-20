"""Content cleaning and markdown normalization."""

from pathlib import Path

from ..utils.text import normalize_markdown, remove_watermark_text, convert_chemical_formula


def clean_marker_output(book_code: str, base_dir: Path = None) -> str:
    """Clean marker-extracted content.md and create chapter_complete.md."""
    if base_dir is None:
        base_dir = Path("extracted") / book_code

    content_file = base_dir / "content.md"
    if not content_file.exists():
        return ""

    text = content_file.read_text(encoding="utf-8")
    text = remove_watermark_text(text)
    text = normalize_markdown(text)
    text = convert_chemical_formula(text)

    output_file = base_dir / "chapter_complete.md"
    output_file.write_text(text.strip(), encoding="utf-8")

    return text
