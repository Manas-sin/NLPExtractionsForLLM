#!/usr/bin/env python3
"""
Save extracted JSON to PostgreSQL.

Usage:
    python scripts/save_to_db.py <book_code>
    python scripts/save_to_db.py --all
    python scripts/save_to_db.py --init  # Initialize database schema
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db, ChapterRepository


def save_chapter(book_code: str, base_dir: Path = None) -> bool:
    """Save a single chapter to database."""
    # Try different locations
    search_paths = [
        Path("data/extracted_physics") / book_code / "structured_physics.json",
        Path("data/extracted") / book_code / "structured.json",
        Path("data/extracted") / book_code / "final_output.json",
    ]

    if base_dir:
        search_paths.insert(0, base_dir / "structured_physics.json")
        search_paths.insert(1, base_dir / "structured.json")

    json_file = None
    for path in search_paths:
        if path.exists():
            json_file = path
            break

    if not json_file:
        print(f"  No JSON found for {book_code}")
        return False

    data = json.loads(json_file.read_text(encoding="utf-8"))
    repo = ChapterRepository()
    chapter_id = repo.save_from_json(data)

    print(f"  Saved {book_code} (ID: {chapter_id})")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/save_to_db.py <book_code>")
        print("       python scripts/save_to_db.py --all")
        print("       python scripts/save_to_db.py --init")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--init":
        print("Initializing database...")
        init_db()
        return

    if arg == "--all":
        print("Saving all chapters to database...")

        # Physics
        physics_dir = Path("data/extracted_physics")
        if physics_dir.exists():
            for chapter_dir in sorted(physics_dir.iterdir()):
                if chapter_dir.is_dir():
                    save_chapter(chapter_dir.name, chapter_dir)

        # Other subjects
        extracted_dir = Path("data/extracted")
        if extracted_dir.exists():
            for chapter_dir in sorted(extracted_dir.iterdir()):
                if chapter_dir.is_dir():
                    save_chapter(chapter_dir.name, chapter_dir)

        # Print stats
        repo = ChapterRepository()
        stats = repo.get_statistics()
        print(f"\nDatabase stats:")
        print(f"  Chapters: {stats['total_chapters']}")
        print(f"  Sections: {stats['total_sections']}")
        print(f"  Examples: {stats['total_examples']}")
        print(f"  Exercises: {stats['total_exercises']}")
    else:
        save_chapter(arg)

    print("\nDone!")


if __name__ == "__main__":
    main()
