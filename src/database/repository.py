"""Repository pattern for database operations."""

import json
from typing import Optional

from .connection import get_db
from .models import Chapter, Section, Example, Exercise, Figure, ContentTable


class ChapterRepository:
    """Repository for chapter operations."""

    def save_from_json(self, data: dict) -> int:
        """Save structured JSON to database. Returns chapter ID."""
        with get_db() as conn:
            with conn.cursor() as cur:
                # Insert or update chapter
                cur.execute("""
                    INSERT INTO chapters (
                        book_code, subject, class, chapter_number, title,
                        content, summary, statistics
                    ) VALUES (
                        %(book_code)s, %(subject)s, %(class)s, %(chapter_number)s,
                        %(title)s, %(content)s, %(summary)s, %(statistics)s
                    )
                    ON CONFLICT (book_code) DO UPDATE SET
                        subject = EXCLUDED.subject,
                        class = EXCLUDED.class,
                        chapter_number = EXCLUDED.chapter_number,
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        summary = EXCLUDED.summary,
                        statistics = EXCLUDED.statistics,
                        updated_at = NOW()
                    RETURNING id
                """, {
                    "book_code": data["book_code"],
                    "subject": data.get("subject", "unknown"),
                    "class": data.get("class", 0),
                    "chapter_number": data.get("chapter_number"),
                    "title": data.get("chapter_title") or data.get("unit_title", ""),
                    "content": json.dumps(data),
                    "summary": data.get("summary", []),
                    "statistics": json.dumps(data.get("statistics", {})),
                })

                chapter_id = cur.fetchone()["id"]

                # Delete existing related data
                for table in ["sections", "examples", "exercises", "figures", "content_tables"]:
                    cur.execute(f"DELETE FROM {table} WHERE chapter_id = %s", (chapter_id,))

                # Insert sections
                for section in data.get("sections", []):
                    cur.execute("""
                        INSERT INTO sections (chapter_id, section_number, title, content, equations)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        chapter_id,
                        section.get("number", ""),
                        section.get("title", ""),
                        section.get("content", ""),
                        json.dumps(section.get("equations", [])),
                    ))

                # Insert examples
                for example in data.get("examples", []):
                    cur.execute("""
                        INSERT INTO examples (chapter_id, number, problem, solution, equations)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        chapter_id,
                        example.get("number", ""),
                        example.get("problem", ""),
                        example.get("solution", ""),
                        json.dumps(example.get("equations", [])),
                    ))

                # Insert exercises
                for exercise in data.get("exercises", []):
                    cur.execute("""
                        INSERT INTO exercises (chapter_id, number, text, sub_parts, answer)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        chapter_id,
                        exercise.get("number", ""),
                        exercise.get("text", ""),
                        json.dumps(exercise.get("sub_parts", [])),
                        exercise.get("answer"),
                    ))

                # Insert figures
                for figure in data.get("figures", []):
                    cur.execute("""
                        INSERT INTO figures (chapter_id, figure_number, caption, image_path)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        chapter_id,
                        figure.get("number", ""),
                        figure.get("caption", ""),
                        figure.get("image_path"),
                    ))

                # Insert tables
                for table in data.get("tables", []):
                    cur.execute("""
                        INSERT INTO content_tables (chapter_id, table_number, title, headers, rows)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        chapter_id,
                        table.get("number", ""),
                        table.get("title", ""),
                        table.get("headers", []),
                        json.dumps(table.get("rows", [])),
                    ))

                return chapter_id

    def get_by_book_code(self, book_code: str) -> Optional[dict]:
        """Get chapter by book code."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM chapters WHERE book_code = %s
                """, (book_code,))
                row = cur.fetchone()
                if row:
                    return dict(row)
        return None

    def get_all(self, subject: str = None, class_: int = None) -> list[dict]:
        """Get all chapters, optionally filtered."""
        with get_db() as conn:
            with conn.cursor() as cur:
                query = "SELECT id, book_code, subject, class, chapter_number, title, statistics, created_at FROM chapters WHERE 1=1"
                params = []

                if subject:
                    query += " AND subject = %s"
                    params.append(subject)
                if class_:
                    query += " AND class = %s"
                    params.append(class_)

                query += " ORDER BY subject, class, chapter_number"
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Full-text search across sections."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        c.book_code,
                        c.title as chapter_title,
                        s.section_number,
                        s.title as section_title,
                        ts_headline('english', s.content, plainto_tsquery('english', %s),
                            'MaxWords=50, MinWords=20') as snippet,
                        ts_rank(to_tsvector('english', s.content), plainto_tsquery('english', %s)) as rank
                    FROM sections s
                    JOIN chapters c ON s.chapter_id = c.id
                    WHERE to_tsvector('english', s.content) @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                """, (query, query, query, limit))
                return [dict(row) for row in cur.fetchall()]

    def delete(self, book_code: str) -> bool:
        """Delete chapter by book code."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chapters WHERE book_code = %s RETURNING id", (book_code,))
                return cur.fetchone() is not None

    def get_statistics(self) -> dict:
        """Get overall statistics."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) as total_chapters,
                        COUNT(DISTINCT subject) as subjects,
                        (SELECT COUNT(*) FROM sections) as total_sections,
                        (SELECT COUNT(*) FROM examples) as total_examples,
                        (SELECT COUNT(*) FROM exercises) as total_exercises,
                        (SELECT COUNT(*) FROM figures) as total_figures
                    FROM chapters
                """)
                return dict(cur.fetchone())
