"""Database connection and initialization."""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/ncert_extractor"
)


def get_connection():
    """Get a new database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    schema = """
    -- Enable pgvector extension for semantic search
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Chapters table
    CREATE TABLE IF NOT EXISTS chapters (
        id SERIAL PRIMARY KEY,
        book_code VARCHAR(20) UNIQUE NOT NULL,
        subject VARCHAR(50) NOT NULL,
        class INTEGER NOT NULL,
        chapter_number INTEGER,
        title TEXT NOT NULL,
        content JSONB,
        summary TEXT[],
        statistics JSONB,
        embedding vector(1536),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Sections table
    CREATE TABLE IF NOT EXISTS sections (
        id SERIAL PRIMARY KEY,
        chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
        section_number VARCHAR(10) NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        equations JSONB,
        embedding vector(1536),
        UNIQUE(chapter_id, section_number)
    );

    -- Examples table
    CREATE TABLE IF NOT EXISTS examples (
        id SERIAL PRIMARY KEY,
        chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
        section_id INTEGER REFERENCES sections(id) ON DELETE SET NULL,
        number VARCHAR(10) NOT NULL,
        problem TEXT NOT NULL,
        solution TEXT,
        equations JSONB,
        UNIQUE(chapter_id, number)
    );

    -- Exercises table
    CREATE TABLE IF NOT EXISTS exercises (
        id SERIAL PRIMARY KEY,
        chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
        number VARCHAR(10) NOT NULL,
        text TEXT NOT NULL,
        sub_parts JSONB,
        answer TEXT,
        UNIQUE(chapter_id, number)
    );

    -- Figures table
    CREATE TABLE IF NOT EXISTS figures (
        id SERIAL PRIMARY KEY,
        chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
        figure_number VARCHAR(10) NOT NULL,
        caption TEXT,
        image_path TEXT,
        UNIQUE(chapter_id, figure_number)
    );

    -- Tables (from textbook)
    CREATE TABLE IF NOT EXISTS content_tables (
        id SERIAL PRIMARY KEY,
        chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
        table_number VARCHAR(10) NOT NULL,
        title TEXT,
        headers TEXT[],
        rows JSONB,
        UNIQUE(chapter_id, table_number)
    );

    -- Equations index for search
    CREATE TABLE IF NOT EXISTS equations (
        id SERIAL PRIMARY KEY,
        chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
        section_id INTEGER REFERENCES sections(id) ON DELETE SET NULL,
        latex TEXT NOT NULL,
        equation_type VARCHAR(20),
        description TEXT
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_chapters_subject ON chapters(subject);
    CREATE INDEX IF NOT EXISTS idx_chapters_class ON chapters(class);
    CREATE INDEX IF NOT EXISTS idx_chapters_book_code ON chapters(book_code);
    CREATE INDEX IF NOT EXISTS idx_sections_chapter ON sections(chapter_id);
    CREATE INDEX IF NOT EXISTS idx_exercises_chapter ON exercises(chapter_id);
    CREATE INDEX IF NOT EXISTS idx_chapters_content ON chapters USING GIN(content);

    -- Full-text search index
    CREATE INDEX IF NOT EXISTS idx_sections_content_fts
    ON sections USING GIN(to_tsvector('english', content));
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)

    print("Database initialized successfully!")
