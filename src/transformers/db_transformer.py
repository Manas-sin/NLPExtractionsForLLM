"""Transform structured.json to unified DB format with content_blocks."""

import json
import uuid
from pathlib import Path
from typing import Any


def generate_id() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def transform_to_db_format(structured_data: dict) -> dict:
    """Transform structured.json to unified DB format."""

    chapter_id = generate_id()

    result = {
        "id": chapter_id,
        "book_code": structured_data.get("book_code", ""),
        "subject": structured_data.get("subject", ""),
        "class": structured_data.get("class", 0),
        "chapter_number": structured_data.get("unit_number", 0),
        "chapter_title": structured_data.get("unit_title", ""),
        "objectives": structured_data.get("objectives", []),
        "sections": [],
        "content_blocks": []
    }

    section_id_map = {}
    block_order = 1

    for idx, section in enumerate(structured_data.get("sections", [])):
        section_id = generate_id()
        section_id_map[section["number"]] = section_id

        parent_id = None
        if "." in section["number"]:
            parts = section["number"].rsplit(".", 1)
            if len(parts) == 2 and parts[0] in section_id_map:
                parent_id = section_id_map[parts[0]]

        result["sections"].append({
            "id": section_id,
            "chapter_id": chapter_id,
            "number": section["number"],
            "title": section["title"],
            "parent_section_id": parent_id,
            "order": idx + 1
        })

        if section.get("content"):
            result["content_blocks"].append({
                "id": generate_id(),
                "chapter_id": chapter_id,
                "section_id": section_id,
                "type": "paragraph",
                "order": block_order,
                "data": {
                    "text": section["content"]
                }
            })
            block_order += 1

    for term in structured_data.get("key_terms", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "definition",
            "order": block_order,
            "data": {
                "term": term["term"],
                "definition": term.get("context", ""),
                "pattern_type": term.get("pattern_type", "")
            }
        })
        block_order += 1

    for law in structured_data.get("laws_principles", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "law",
            "order": block_order,
            "data": {
                "name": law["name"],
                "statement": law.get("statement", ""),
                "context": law.get("context", "")
            }
        })
        block_order += 1

    for eq in structured_data.get("equations", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "equation",
            "order": block_order,
            "data": {
                "equation_type": eq.get("type", ""),
                "number": eq.get("number", ""),
                "expression": eq.get("full", eq.get("latex", eq.get("expression", ""))),
                "reactants": eq.get("reactants", ""),
                "products": eq.get("products", ""),
                "reversible": eq.get("reversible", False)
            }
        })
        block_order += 1

    for table in structured_data.get("tables", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "table",
            "order": block_order,
            "data": {
                "number": table.get("number", ""),
                "title": table.get("title", ""),
                "headers": table.get("headers", []),
                "rows": table.get("rows", []),
                "raw_content": table.get("raw_content", ""),
                "format": table.get("format", "structured")
            }
        })
        block_order += 1

    for fig in structured_data.get("figures", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "figure",
            "order": block_order,
            "data": {
                "number": fig.get("number", ""),
                "caption": fig.get("caption", ""),
                "image_path": fig.get("image", "")
            }
        })
        block_order += 1

    for ex in structured_data.get("examples", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "example",
            "order": block_order,
            "data": {
                "number": ex.get("number", ""),
                "problem": ex.get("problem", ""),
                "solution": ex.get("solution", "")
            }
        })
        block_order += 1

    for q in structured_data.get("intext_questions", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "question",
            "order": block_order,
            "data": {
                "number": q.get("number", ""),
                "text": q.get("text", ""),
                "question_type": "intext"
            }
        })
        block_order += 1

    for ex in structured_data.get("exercises", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "question",
            "order": block_order,
            "data": {
                "number": ex.get("number", ""),
                "text": ex.get("text", ""),
                "sub_parts": ex.get("sub_parts", []),
                "question_type": "exercise"
            }
        })
        block_order += 1

    for point in structured_data.get("summary", []):
        result["content_blocks"].append({
            "id": generate_id(),
            "chapter_id": chapter_id,
            "section_id": None,
            "type": "summary_point",
            "order": block_order,
            "data": {
                "text": point
            }
        })
        block_order += 1

    result["statistics"] = {
        "section_count": len(result["sections"]),
        "content_block_count": len(result["content_blocks"]),
        "block_types": {}
    }

    for block in result["content_blocks"]:
        block_type = block["type"]
        result["statistics"]["block_types"][block_type] = \
            result["statistics"]["block_types"].get(block_type, 0) + 1

    return result


def transform_file(input_path: Path, output_path: Path = None) -> dict:
    """Transform a structured.json file to DB format."""
    data = json.loads(input_path.read_text(encoding="utf-8"))
    result = transform_to_db_format(data)

    if output_path is None:
        output_path = input_path.parent / "db_format.json"

    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return result


def transform_all_chapters(base_dir: Path = None) -> list:
    """Transform all structured.json files in data/extracted."""
    if base_dir is None:
        base_dir = Path("data/extracted")

    results = []

    for chapter_dir in base_dir.iterdir():
        if not chapter_dir.is_dir():
            continue

        structured_file = chapter_dir / "structured.json"
        if not structured_file.exists():
            continue

        result = transform_file(structured_file)
        results.append({
            "book_code": result["book_code"],
            "chapter_title": result["chapter_title"],
            "sections": result["statistics"]["section_count"],
            "content_blocks": result["statistics"]["content_block_count"],
            "output": str(chapter_dir / "db_format.json")
        })
        print(f"Transformed: {result['book_code']} - {result['chapter_title']}")

    return results


if __name__ == "__main__":
    results = transform_all_chapters()
    print(f"\nTransformed {len(results)} chapters")
