"""Text processing utilities."""

import re


def clean_text(text: str) -> str:
    """Clean extracted text by removing artifacts and normalizing whitespace."""
    text = text.replace("­", "")
    text = re.sub(r"^\s*Reprint\s+\d{4}-\d{2}\s*$", "", text, flags=re.MULTILINE)
    text = remove_watermark_text(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = text.split('\n')
    deduped = []
    prev = None
    for line in lines:
        if line.strip() != prev:
            deduped.append(line)
            prev = line.strip()
    return '\n'.join(deduped).strip()


def remove_watermark_text(text: str) -> str:
    """Remove NCERT watermark text patterns."""
    text = re.sub(r"not\s+to\s+be\s+republished", "", text, flags=re.IGNORECASE)
    text = re.sub(r"©\s*NCERT", "", text, flags=re.IGNORECASE)
    return text


def convert_chemical_formula(text: str) -> str:
    """Convert chemical formulas to LaTeX notation."""
    def convert_match(match):
        formula = match.group(0)
        if re.search(r'\d', formula):
            return '$\\mathrm{' + re.sub(r'(\d+)', r'_{\1}', formula) + '}$'
        return formula

    return re.sub(r'\b([A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+)\b', convert_match, text)


def normalize_markdown(text: str) -> str:
    """Normalize markdown formatting."""
    text = re.sub(r'^---\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^## Page \d+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[·•]\s*', '- ', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s\-]+)$', r'## \1 \2', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+\.\d+\.\d+)\s+([A-Z][A-Za-z\s\-]+)$', r'### \1 \2', text, flags=re.MULTILINE)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()
