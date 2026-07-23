"""Pydantic models for database entities."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Section(BaseModel):
    """Section model."""
    id: Optional[int] = None
    chapter_id: Optional[int] = None
    section_number: str
    title: str
    content: Optional[str] = None
    equations: Optional[list] = None


class Example(BaseModel):
    """Example model."""
    id: Optional[int] = None
    chapter_id: Optional[int] = None
    number: str
    problem: str
    solution: Optional[str] = None
    equations: Optional[list] = None


class Exercise(BaseModel):
    """Exercise model."""
    id: Optional[int] = None
    chapter_id: Optional[int] = None
    number: str
    text: str
    sub_parts: Optional[list] = None
    answer: Optional[str] = None


class Figure(BaseModel):
    """Figure model."""
    id: Optional[int] = None
    chapter_id: Optional[int] = None
    figure_number: str
    caption: Optional[str] = None
    image_path: Optional[str] = None


class ContentTable(BaseModel):
    """Table from textbook."""
    id: Optional[int] = None
    chapter_id: Optional[int] = None
    table_number: str
    title: Optional[str] = None
    headers: Optional[list] = None
    rows: Optional[list] = None


class Chapter(BaseModel):
    """Chapter model."""
    id: Optional[int] = None
    book_code: str
    subject: str
    class_: int
    chapter_number: Optional[int] = None
    title: str
    content: Optional[dict] = None
    summary: Optional[list] = None
    statistics: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        fields = {"class_": "class"}


class ChapterWithRelations(Chapter):
    """Chapter with all related data."""
    sections: list[Section] = []
    examples: list[Example] = []
    exercises: list[Exercise] = []
    figures: list[Figure] = []
    tables: list[ContentTable] = []
