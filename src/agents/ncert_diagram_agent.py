"""NCERT Diagram Analysis Agent using Google ADK 2.0.

This agent analyzes NCERT textbook diagrams and can:
1. Identify diagram components (labels, arrows, shapes)
2. Extract text from diagrams
3. Generate SVG/code replicas
4. Compare original vs extracted accuracy
"""

import base64
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from google import genai
from google.genai import types
from google.adk import Agent
from google.adk.tools import FunctionTool


@dataclass
class DiagramComponent:
    """A component in a diagram."""
    type: str  # label, arrow, shape, line, text
    content: str
    position: dict  # x, y, width, height (approximate)
    style: dict  # color, font, stroke


@dataclass
class DiagramAnalysis:
    """Complete analysis of a diagram."""
    figure_number: str
    caption: str
    diagram_type: str  # flowchart, circuit, anatomy, graph, etc.
    components: list[DiagramComponent]
    relationships: list[dict]  # connections between components
    svg_code: str
    tikz_code: str
    accuracy_score: float
    suggestions: list[str]


class NCERTDiagramAgent:
    """Agent for analyzing and replicating NCERT diagrams."""

    def __init__(self, model: str = "gemini-3.1-flash-lite"):
        self.model = model
        self.client = None

    def _get_client(self):
        """Lazy load Genai client."""
        if self.client is None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def analyze_diagram(self, image_path: Path) -> DiagramAnalysis:
        """Analyze a diagram image and extract components."""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        img_bytes = image_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()

        prompt = """Analyze this NCERT textbook diagram in detail.

Return a JSON object with:
{
  "figure_number": "e.g., 1.3",
  "caption": "diagram caption if visible",
  "diagram_type": "flowchart|circuit|anatomy|graph|vector|mechanical|chemical|other",
  "components": [
    {
      "type": "label|arrow|shape|line|text|image",
      "content": "text content or description",
      "position": {"x": 0-100, "y": 0-100, "width": 0-100, "height": 0-100},
      "style": {"color": "black", "font": "serif", "stroke": "solid"}
    }
  ],
  "relationships": [
    {"from": "component_index", "to": "component_index", "type": "arrow|line|contains"}
  ],
  "description": "What does this diagram show?"
}

Be precise about positions (as percentages of image size).
Identify ALL text labels, arrows, and shapes."""

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        types.Part.from_text(text=prompt),
                    ]
                )
            ]
        )

        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            data = {}

        components = [
            DiagramComponent(
                type=c.get("type", "unknown"),
                content=c.get("content", ""),
                position=c.get("position", {}),
                style=c.get("style", {}),
            )
            for c in data.get("components", [])
        ]

        svg_code = self._generate_svg(data, components)
        tikz_code = self._generate_tikz(data, components)

        return DiagramAnalysis(
            figure_number=data.get("figure_number", ""),
            caption=data.get("caption", ""),
            diagram_type=data.get("diagram_type", "other"),
            components=components,
            relationships=data.get("relationships", []),
            svg_code=svg_code,
            tikz_code=tikz_code,
            accuracy_score=0.0,
            suggestions=[],
        )

    def _generate_svg(self, data: dict, components: list[DiagramComponent]) -> str:
        """Generate SVG code from components."""
        svg_parts = ['<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">']
        svg_parts.append('  <style>')
        svg_parts.append('    text { font-family: serif; font-size: 3px; }')
        svg_parts.append('    .label { fill: #333; }')
        svg_parts.append('    .arrow { stroke: #333; stroke-width: 0.5; fill: none; marker-end: url(#arrowhead); }')
        svg_parts.append('    .shape { stroke: #333; stroke-width: 0.5; fill: none; }')
        svg_parts.append('  </style>')
        svg_parts.append('  <defs>')
        svg_parts.append('    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">')
        svg_parts.append('      <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>')
        svg_parts.append('    </marker>')
        svg_parts.append('  </defs>')

        for comp in components:
            pos = comp.position
            x = pos.get("x", 50)
            y = pos.get("y", 50)
            w = pos.get("width", 10)
            h = pos.get("height", 5)

            if comp.type == "text" or comp.type == "label":
                svg_parts.append(f'  <text x="{x}" y="{y}" class="label">{comp.content}</text>')
            elif comp.type == "arrow":
                svg_parts.append(f'  <line x1="{x}" y1="{y}" x2="{x+w}" y2="{y+h}" class="arrow"/>')
            elif comp.type == "shape":
                svg_parts.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" class="shape"/>')
            elif comp.type == "line":
                svg_parts.append(f'  <line x1="{x}" y1="{y}" x2="{x+w}" y2="{y+h}" class="shape"/>')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def _generate_tikz(self, data: dict, components: list[DiagramComponent]) -> str:
        """Generate TikZ code for LaTeX."""
        tikz_parts = [
            "\\begin{tikzpicture}[scale=0.1]",
            "  \\tikzstyle{label}=[font=\\small]",
            "  \\tikzstyle{arrow}=[->, >=stealth]",
        ]

        for comp in components:
            pos = comp.position
            x = pos.get("x", 50)
            y = 100 - pos.get("y", 50)  # TikZ y is inverted

            if comp.type == "text" or comp.type == "label":
                tikz_parts.append(f'  \\node[label] at ({x},{y}) {{{comp.content}}};')
            elif comp.type == "arrow":
                w = pos.get("width", 10)
                h = pos.get("height", 0)
                tikz_parts.append(f'  \\draw[arrow] ({x},{y}) -- ({x+w},{y-h});')
            elif comp.type == "shape":
                w = pos.get("width", 10)
                h = pos.get("height", 5)
                tikz_parts.append(f'  \\draw ({x},{y}) rectangle ({x+w},{y-h});')

        tikz_parts.append("\\end{tikzpicture}")
        return "\n".join(tikz_parts)

    def generate_replica(self, image_path: Path, output_format: str = "svg") -> str:
        """Generate a clean replica of the diagram."""
        image_path = Path(image_path)
        img_bytes = image_path.read_bytes()

        if output_format == "svg":
            prompt = """Create a clean, accurate SVG replica of this NCERT diagram.

Requirements:
1. Use proper SVG elements (rect, circle, line, path, text, polygon)
2. Include ALL text labels exactly as shown
3. Replicate arrows with proper arrowheads
4. Match colors and positions accurately
5. Use viewBox="0 0 400 300" for proper scaling
6. Include CSS styles for fonts and strokes

Return ONLY the SVG code, no explanation."""

        elif output_format == "tikz":
            prompt = """Create a clean, accurate TikZ (LaTeX) replica of this NCERT diagram.

Requirements:
1. Use proper TikZ commands (\\node, \\draw, \\path)
2. Include ALL text labels exactly as shown
3. Replicate arrows with proper styles
4. Use appropriate TikZ libraries (arrows, shapes, positioning)
5. Scale appropriately for A4 paper

Return ONLY the TikZ code wrapped in tikzpicture environment."""

        elif output_format == "mermaid":
            prompt = """Create a Mermaid diagram replica of this NCERT diagram.

Requirements:
1. Use appropriate Mermaid diagram type (flowchart, graph, etc.)
2. Include ALL text labels
3. Show relationships with proper arrows
4. Keep it as accurate as possible to the original

Return ONLY the Mermaid code starting with the diagram type."""

        else:
            raise ValueError(f"Unknown format: {output_format}")

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        types.Part.from_text(text=prompt),
                    ]
                )
            ]
        )

        return response.text

    def compare_accuracy(self, original_path: Path, replica_svg: str) -> dict:
        """Compare original diagram with generated replica."""
        original_path = Path(original_path)
        img_bytes = original_path.read_bytes()

        prompt = f"""Compare this original NCERT diagram with the SVG replica code below.

SVG Replica:
```svg
{replica_svg}
```

Evaluate on these criteria (score 1-10 each):
1. text_accuracy: Are all labels captured correctly?
2. layout_accuracy: Are positions and arrangements correct?
3. shape_accuracy: Are shapes (boxes, circles, arrows) correct?
4. relationship_accuracy: Are connections/arrows between elements correct?
5. style_accuracy: Are colors, fonts, line styles correct?

Also provide:
- missing_elements: List of elements in original but not in replica
- extra_elements: List of elements in replica but not in original
- suggestions: How to improve the replica

Return as JSON."""

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        types.Part.from_text(text=prompt),
                    ]
                )
            ]
        )

        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {"error": "Could not parse comparison"}

    def batch_process(self, figures_dir: Path, output_dir: Path) -> list[dict]:
        """Process all figures in a directory."""
        figures_dir = Path(figures_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for img_file in sorted(figures_dir.glob("*.png")):
            print(f"Processing {img_file.name}...")
            try:
                analysis = self.analyze_diagram(img_file)

                # Save SVG
                svg_file = output_dir / f"{img_file.stem}.svg"
                svg_file.write_text(analysis.svg_code)

                # Save TikZ
                tikz_file = output_dir / f"{img_file.stem}.tikz"
                tikz_file.write_text(analysis.tikz_code)

                # Save analysis
                analysis_file = output_dir / f"{img_file.stem}_analysis.json"
                analysis_dict = asdict(analysis)
                analysis_dict["components"] = [asdict(c) for c in analysis.components]
                analysis_file.write_text(json.dumps(analysis_dict, indent=2))

                results.append({
                    "file": img_file.name,
                    "status": "success",
                    "diagram_type": analysis.diagram_type,
                    "component_count": len(analysis.components),
                })
            except Exception as e:
                results.append({
                    "file": img_file.name,
                    "status": "error",
                    "error": str(e),
                })

        return results


def create_diagram_agent() -> Agent:
    """Create ADK agent with diagram tools."""

    diagram_agent = NCERTDiagramAgent()

    @FunctionTool
    def analyze_diagram(image_path: str) -> str:
        """Analyze a NCERT diagram and extract components."""
        result = diagram_agent.analyze_diagram(Path(image_path))
        return json.dumps(asdict(result), indent=2)

    @FunctionTool
    def generate_svg_replica(image_path: str) -> str:
        """Generate SVG replica of a diagram."""
        return diagram_agent.generate_replica(Path(image_path), "svg")

    @FunctionTool
    def generate_tikz_replica(image_path: str) -> str:
        """Generate TikZ/LaTeX replica of a diagram."""
        return diagram_agent.generate_replica(Path(image_path), "tikz")

    @FunctionTool
    def generate_mermaid_replica(image_path: str) -> str:
        """Generate Mermaid diagram replica."""
        return diagram_agent.generate_replica(Path(image_path), "mermaid")

    @FunctionTool
    def compare_diagrams(original_path: str, svg_code: str) -> str:
        """Compare original diagram with SVG replica."""
        result = diagram_agent.compare_accuracy(Path(original_path), svg_code)
        return json.dumps(result, indent=2)

    agent = Agent(
        name="ncert_diagram_agent",
        model="gemini-2.0-flash",
        description="Analyzes NCERT diagrams and creates accurate replicas",
        instruction="""You are an expert at analyzing educational diagrams from NCERT textbooks.

Your capabilities:
1. Analyze diagrams to identify all components (labels, arrows, shapes)
2. Generate SVG replicas that match the original
3. Generate TikZ code for LaTeX documents
4. Generate Mermaid diagrams for markdown
5. Compare replicas with originals for accuracy

When asked to process a diagram:
1. First analyze it to understand the structure
2. Generate the requested format (SVG/TikZ/Mermaid)
3. Compare with original if accuracy check is requested

Always aim for 100% text accuracy - every label must be captured exactly.""",
        tools=[
            analyze_diagram,
            generate_svg_replica,
            generate_tikz_replica,
            generate_mermaid_replica,
            compare_diagrams,
        ],
    )

    return agent
