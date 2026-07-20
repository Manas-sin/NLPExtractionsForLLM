#!/usr/bin/env python3
"""
Structure physics chapters into clean JSON.

Usage:
    python scripts/structure_physics.py <book_code>
    python scripts/structure_physics.py --all
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.physics_structurer import PhysicsStructurer


def structure_chapter(book_code: str):
    """Structure a single physics chapter."""
    base_dir = Path("data/extracted_physics") / book_code

    if not base_dir.exists():
        print(f"Error: {base_dir} not found")
        return None

    print(f"\nStructuring: {book_code}")
    print("=" * 50)

    structurer = PhysicsStructurer(book_code, base_dir)
    result = structurer.structure()
    output_file = structurer.save()

    print(f"Chapter: {result['chapter_title']}")
    print(f"Sections: {result['statistics']['section_count']}")
    print(f"Tables: {result['statistics']['table_count']}")
    print(f"Examples: {result['statistics']['example_count']}")
    print(f"Exercises: {result['statistics']['exercise_count']}")
    print(f"Equations: {result['statistics']['equation_count']}")
    print(f"Output: {output_file}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/structure_physics.py <book_code>")
        print("       python scripts/structure_physics.py --all")
        print("\nExample: python scripts/structure_physics.py keph101")
        sys.exit(1)

    if sys.argv[1] == "--all":
        physics_dir = Path("data/extracted_physics")
        if not physics_dir.exists():
            print(f"Error: {physics_dir} not found")
            sys.exit(1)

        for chapter_dir in sorted(physics_dir.iterdir()):
            if chapter_dir.is_dir() and (chapter_dir / "chapter_complete.md").exists():
                structure_chapter(chapter_dir.name)
    else:
        book_code = sys.argv[1]
        structure_chapter(book_code)

    print("\nDone!")


if __name__ == "__main__":
    main()
