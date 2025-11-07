"""Lightweight CLI for registering Echo vNext modules."""
from __future__ import annotations

import argparse
from pathlib import Path

from echo_module_registry import ModuleRecord, register_module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register an Echo vNext module")
    parser.add_argument("name", help="Unique module name")
    parser.add_argument("category", help="Module category such as 'services' or 'agents'")
    parser.add_argument("description", help="Human readable description")
    return parser


def main(argv: list[str] | None = None) -> ModuleRecord:
    parser = build_parser()
    args = parser.parse_args(argv)
    registry_path = Path(__file__).with_name("modules.json")
    record = register_module(
        args.name,
        args.description,
        args.category,
        registry_path=registry_path,
    )
    return record


if __name__ == "__main__":
    result = main()
    print(result)
