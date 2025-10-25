#!/usr/bin/env python3
"""Entry point for provisioning the Echo Titan framework."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from echo_titan.generator import EchoTitanGenerator, GenerationPlan, build_arg_parser


def _relative_path(path: Path) -> Path:
    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    plan = GenerationPlan(
        base_dir=args.base_dir,
        puzzle_count=args.puzzles,
        doc_count=args.docs,
        test_count=args.tests,
    )
    EchoTitanGenerator(plan).generate()
    print(f"Echo Titan scaffold generated at {_relative_path(plan.base_dir)}")


if __name__ == "__main__":
    main()
