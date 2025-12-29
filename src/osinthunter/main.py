"""Command-line runner for the OSINT Hunter MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

from .agent import OSINTAgent
from .models import ProblemInput


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the OSINT Hunter agent on a prompt")
    parser.add_argument("prompt", nargs="?", help="Problem text. If omitted, use --file")
    parser.add_argument("--file", type=Path, help="Path to a text file with the problem statement")
    parser.add_argument("--url", action="append", default=[], help="URL to include in the problem context")
    parser.add_argument("--image", action="append", default=[], help="Image path to include for image OSINT")
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt
    if args.file:
        return args.file.read_text(encoding="utf-8")
    raise SystemExit("Provide a prompt or --file")


def main() -> None:
    args = parse_args()
    text = load_text(args)

    agent = OSINTAgent()
    problem = ProblemInput(text=text, urls=args.url, image_paths=args.image)
    result = agent.run(problem)

    print("# Plan")
    for step in result.plan:
        print(f"- {step.title} [{step.tool}] :: {step.rationale}")

    print("\n# Evidence")
    for ev in result.evidence:
        print(f"- ({ev.confidence:.2f}) {ev.source}: {ev.fact}")

    if result.flag_candidates:
        print("\n# Flag candidates")
        for flag in result.flag_candidates:
            print(f"- {flag}")

    if result.notes:
        print("\n# Notes")
        print(result.notes)


if __name__ == "__main__":
    main()
