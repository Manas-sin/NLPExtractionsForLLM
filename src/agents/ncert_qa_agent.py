"""NCERT Q&A Agent using Google ADK 2.0.

This agent can:
1. Answer questions from NCERT content
2. Generate practice questions
3. Explain concepts with examples
4. Compare topics across chapters
"""

import json
import os
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from google.adk import Agent
from google.adk.tools import FunctionTool


class NCERTQAAgent:
    """Agent for Q&A on NCERT content."""

    def __init__(self, data_dir: Path = None, model: str = "gemini-2.0-flash"):
        self.data_dir = Path(data_dir) if data_dir else Path("data/extracted")
        self.model = model
        self.client = None
        self._content_cache = {}

    def _get_client(self):
        """Lazy load Genai client."""
        if self.client is None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def _load_chapter(self, book_code: str) -> Optional[dict]:
        """Load chapter content from JSON."""
        if book_code in self._content_cache:
            return self._content_cache[book_code]

        json_file = self.data_dir / book_code / "final_output.json"
        if not json_file.exists():
            return None

        content = json.loads(json_file.read_text())
        self._content_cache[book_code] = content
        return content

    def _get_chapter_context(self, book_code: str) -> str:
        """Get chapter content as context string."""
        chapter = self._load_chapter(book_code)
        if not chapter:
            return ""

        parts = [
            f"Subject: {chapter.get('subject', 'unknown')}",
            f"Chapter: {chapter.get('unit_title', book_code)}",
            "",
        ]

        for section in chapter.get("sections", []):
            parts.append(f"## {section.get('number', '')} {section.get('title', '')}")
            content = section.get("content", "")
            if content:
                parts.append(content[:1500])
            parts.append("")

        for example in chapter.get("examples", [])[:5]:
            parts.append(f"### Example {example.get('number', '')}")
            parts.append(f"Problem: {example.get('problem', '')[:500]}")
            parts.append(f"Solution: {example.get('solution', '')[:500]}")
            parts.append("")

        return "\n".join(parts)[:8000]

    def answer_question(self, question: str, book_code: str = None) -> dict:
        """Answer a question using NCERT content."""
        context = ""
        if book_code:
            context = self._get_chapter_context(book_code)

        prompt = f"""You are an expert NCERT teacher. Answer this question clearly and accurately.

{f"Context from {book_code}:" if context else ""}
{context}

Question: {question}

Provide:
1. A clear, concise answer
2. The relevant formula/equation if applicable (in LaTeX)
3. A simple example if helpful
4. Which chapter/section this topic is covered in

Format as JSON:
{{
  "answer": "...",
  "formula": "$...$" or null,
  "example": "..." or null,
  "source": "Chapter X.Y - Section Name" or null,
  "confidence": 0.0-1.0
}}"""

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(prompt)])]
        )

        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {"answer": text, "confidence": 0.5}

    def generate_questions(self, book_code: str, count: int = 5,
                           difficulty: str = "medium") -> list[dict]:
        """Generate practice questions from a chapter."""
        context = self._get_chapter_context(book_code)
        if not context:
            return []

        prompt = f"""Generate {count} {difficulty}-difficulty practice questions from this NCERT chapter content.

{context}

For each question provide:
- question: The question text
- type: mcq|short|numerical|conceptual
- answer: The correct answer
- explanation: Brief explanation
- marks: Expected marks (1-5)

Return as JSON array."""

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(prompt)])]
        )

        text = response.text
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return []

    def explain_concept(self, concept: str, book_code: str = None) -> dict:
        """Explain a concept in detail."""
        context = ""
        if book_code:
            context = self._get_chapter_context(book_code)

        prompt = f"""Explain this concept as an expert NCERT teacher would:

Concept: {concept}

{f"Context:" if context else ""}
{context[:4000]}

Provide:
1. Simple definition
2. Key points (bullet list)
3. Real-world example
4. Common misconceptions
5. Related formulas (LaTeX)
6. Practice tip

Format as JSON:
{{
  "definition": "...",
  "key_points": ["...", "..."],
  "example": "...",
  "misconceptions": ["...", "..."],
  "formulas": ["$...$"],
  "tip": "..."
}}"""

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(prompt)])]
        )

        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {"definition": text}

    def compare_topics(self, topic1: str, topic2: str) -> dict:
        """Compare two topics."""
        prompt = f"""Compare these two NCERT topics:

Topic 1: {topic1}
Topic 2: {topic2}

Provide a comparison as JSON:
{{
  "similarities": ["...", "..."],
  "differences": [
    {{"aspect": "...", "topic1": "...", "topic2": "..."}}
  ],
  "when_to_use": {{
    "topic1": "...",
    "topic2": "..."
  }},
  "common_confusion": "...",
  "memory_tip": "..."
}}"""

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(prompt)])]
        )

        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {"error": "Could not parse comparison"}


def create_qa_agent(data_dir: str = "data/extracted") -> Agent:
    """Create ADK agent with Q&A tools."""

    qa_agent = NCERTQAAgent(Path(data_dir))

    @FunctionTool
    def answer_question(question: str, book_code: str = "") -> str:
        """Answer a question from NCERT content."""
        result = qa_agent.answer_question(question, book_code or None)
        return json.dumps(result, indent=2)

    @FunctionTool
    def generate_practice_questions(book_code: str, count: int = 5, difficulty: str = "medium") -> str:
        """Generate practice questions from a chapter."""
        result = qa_agent.generate_questions(book_code, count, difficulty)
        return json.dumps(result, indent=2)

    @FunctionTool
    def explain_concept(concept: str, book_code: str = "") -> str:
        """Explain a concept in detail."""
        result = qa_agent.explain_concept(concept, book_code or None)
        return json.dumps(result, indent=2)

    @FunctionTool
    def compare_topics(topic1: str, topic2: str) -> str:
        """Compare two topics."""
        result = qa_agent.compare_topics(topic1, topic2)
        return json.dumps(result, indent=2)

    @FunctionTool
    def list_chapters() -> str:
        """List all available chapters."""
        chapters = []
        for chapter_dir in sorted(qa_agent.data_dir.iterdir()):
            if chapter_dir.is_dir():
                json_file = chapter_dir / "final_output.json"
                if json_file.exists():
                    data = json.loads(json_file.read_text())
                    chapters.append({
                        "code": chapter_dir.name,
                        "subject": data.get("subject", "unknown"),
                        "title": data.get("unit_title", chapter_dir.name),
                    })
        return json.dumps(chapters, indent=2)

    agent = Agent(
        name="ncert_qa_agent",
        model="gemini-2.0-flash",
        description="Answers questions and explains concepts from NCERT textbooks",
        instruction="""You are an expert NCERT teacher who helps students understand concepts.

Your capabilities:
1. Answer questions using chapter content
2. Generate practice questions
3. Explain concepts with examples
4. Compare related topics

When answering:
- Be clear and concise
- Use formulas in LaTeX when relevant
- Give real-world examples
- Mention the source chapter/section

Always encourage learning and provide helpful tips.""",
        tools=[
            answer_question,
            generate_practice_questions,
            explain_concept,
            compare_topics,
            list_chapters,
        ],
    )

    return agent
