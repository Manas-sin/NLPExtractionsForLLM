#!/usr/bin/env python3
"""Run NCERT agents.

Usage:
    # Diagram analysis
    python scripts/run_agent.py diagram --image data/extracted/keph101/figures/fig_1_1.png
    python scripts/run_agent.py diagram --image fig.png --output svg
    python scripts/run_agent.py diagram --batch data/extracted/keph101/figures/

    # Q&A
    python scripts/run_agent.py qa --question "What is molarity?"
    python scripts/run_agent.py qa --question "What is Newton's first law?" --chapter keph104
    python scripts/run_agent.py qa --generate keph101 --count 5

    # Interactive mode
    python scripts/run_agent.py chat
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_diagram_agent(args):
    """Run diagram analysis agent."""
    from src.agents.ncert_diagram_agent import NCERTDiagramAgent

    agent = NCERTDiagramAgent()

    if args.batch:
        # Batch process directory
        output_dir = Path(args.output_dir) if args.output_dir else Path(args.batch) / "replicas"
        results = agent.batch_process(Path(args.batch), output_dir)

        print(f"\nProcessed {len(results)} diagrams:")
        for r in results:
            status = "✓" if r["status"] == "success" else "✗"
            print(f"  {status} {r['file']}: {r.get('diagram_type', r.get('error', ''))}")

        print(f"\nOutput saved to: {output_dir}")

    elif args.image:
        image_path = Path(args.image)

        if args.output == "analyze":
            print(f"Analyzing {image_path}...")
            analysis = agent.analyze_diagram(image_path)
            print(f"\nFigure: {analysis.figure_number}")
            print(f"Type: {analysis.diagram_type}")
            print(f"Caption: {analysis.caption}")
            print(f"Components: {len(analysis.components)}")
            for c in analysis.components[:10]:
                print(f"  - {c.type}: {c.content[:50]}")

        elif args.output in ("svg", "tikz", "mermaid"):
            print(f"Generating {args.output.upper()} replica...")
            code = agent.generate_replica(image_path, args.output)
            print(code)

            if args.save:
                out_file = image_path.with_suffix(f".{args.output}")
                out_file.write_text(code)
                print(f"\nSaved to: {out_file}")

        elif args.output == "compare":
            print("Generating SVG and comparing...")
            svg = agent.generate_replica(image_path, "svg")
            comparison = agent.compare_accuracy(image_path, svg)
            print(json.dumps(comparison, indent=2))


def run_qa_agent(args):
    """Run Q&A agent."""
    from src.agents.ncert_qa_agent import NCERTQAAgent

    agent = NCERTQAAgent(Path(args.data_dir) if args.data_dir else None)

    if args.question:
        print(f"Q: {args.question}")
        result = agent.answer_question(args.question, args.chapter)
        print(f"\nA: {result.get('answer', '')}")
        if result.get("formula"):
            print(f"\nFormula: {result['formula']}")
        if result.get("source"):
            print(f"\nSource: {result['source']}")

    elif args.explain:
        print(f"Explaining: {args.explain}")
        result = agent.explain_concept(args.explain, args.chapter)
        print(f"\nDefinition: {result.get('definition', '')}")
        print("\nKey Points:")
        for p in result.get("key_points", []):
            print(f"  • {p}")
        if result.get("formulas"):
            print("\nFormulas:")
            for f in result["formulas"]:
                print(f"  {f}")

    elif args.generate:
        print(f"Generating {args.count} questions from {args.generate}...")
        questions = agent.generate_questions(args.generate, args.count, args.difficulty)
        for i, q in enumerate(questions, 1):
            print(f"\n{i}. [{q.get('type', '?')}] {q.get('question', '')}")
            print(f"   Answer: {q.get('answer', '')}")

    elif args.compare:
        topics = args.compare.split(",")
        if len(topics) != 2:
            print("Error: Provide two topics separated by comma")
            return
        print(f"Comparing: {topics[0]} vs {topics[1]}")
        result = agent.compare_topics(topics[0].strip(), topics[1].strip())
        print(json.dumps(result, indent=2))

    elif args.list:
        from src.agents.ncert_qa_agent import NCERTQAAgent
        agent = NCERTQAAgent(Path(args.data_dir) if args.data_dir else None)
        print("Available chapters:")
        for chapter_dir in sorted(agent.data_dir.iterdir()):
            if chapter_dir.is_dir():
                json_file = chapter_dir / "final_output.json"
                if json_file.exists():
                    data = json.loads(json_file.read_text())
                    print(f"  {chapter_dir.name}: {data.get('unit_title', 'Unknown')}")


def run_chat(args):
    """Interactive chat mode."""
    from src.agents.ncert_qa_agent import NCERTQAAgent

    agent = NCERTQAAgent()
    print("NCERT Q&A Agent (type 'quit' to exit)")
    print("-" * 40)

    while True:
        try:
            question = input("\nYou: ").strip()
            if question.lower() in ("quit", "exit", "q"):
                break
            if not question:
                continue

            result = agent.answer_question(question)
            print(f"\nAgent: {result.get('answer', 'No answer')}")
            if result.get("formula"):
                print(f"\n  Formula: {result['formula']}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nGoodbye!")


def main():
    parser = argparse.ArgumentParser(description="Run NCERT agents")
    subparsers = parser.add_subparsers(dest="command", help="Agent to run")

    # Diagram agent
    diagram_parser = subparsers.add_parser("diagram", help="Diagram analysis agent")
    diagram_parser.add_argument("--image", "-i", help="Image to analyze")
    diagram_parser.add_argument("--batch", "-b", help="Directory for batch processing")
    diagram_parser.add_argument("--output", "-o", default="analyze",
                                choices=["analyze", "svg", "tikz", "mermaid", "compare"],
                                help="Output format")
    diagram_parser.add_argument("--output-dir", help="Output directory for batch")
    diagram_parser.add_argument("--save", "-s", action="store_true", help="Save output to file")

    # QA agent
    qa_parser = subparsers.add_parser("qa", help="Q&A agent")
    qa_parser.add_argument("--question", "-q", help="Question to answer")
    qa_parser.add_argument("--chapter", "-c", help="Chapter code (e.g., keph101)")
    qa_parser.add_argument("--explain", "-e", help="Concept to explain")
    qa_parser.add_argument("--generate", "-g", help="Generate questions from chapter")
    qa_parser.add_argument("--count", type=int, default=5, help="Number of questions")
    qa_parser.add_argument("--difficulty", default="medium",
                           choices=["easy", "medium", "hard"])
    qa_parser.add_argument("--compare", help="Compare two topics (comma-separated)")
    qa_parser.add_argument("--list", "-l", action="store_true", help="List chapters")
    qa_parser.add_argument("--data-dir", default="data/extracted", help="Data directory")

    # Chat mode
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")

    args = parser.parse_args()

    if args.command == "diagram":
        run_diagram_agent(args)
    elif args.command == "qa":
        run_qa_agent(args)
    elif args.command == "chat":
        run_chat(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
