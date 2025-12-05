"""Minimal JSONChain compiler to wire governance chain definitions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any


def load_ruleset(path: str | Path) -> Dict[str, Any]:
    rules_path = Path(path)
    with rules_path.open() as f:
        return json.load(f)


def compile_chain(ruleset: Dict[str, Any]) -> Dict[str, Any]:
    chain = ruleset.get("chain", {})
    links: List[Dict[str, str]] = chain.get("links", [])
    graph: Dict[str, List[str]] = {}
    constraints: Dict[str, List[str]] = {}

    for link in links:
        source = link["from"]
        target = link["to"]
        condition = link.get("condition", "always")

        graph.setdefault(source, []).append(target)
        constraints.setdefault(target, []).append(condition)

    return {
        "root": chain.get("root"),
        "graph": graph,
        "constraints": constraints,
        "emit": ruleset.get("compiler", {}).get("emit", []),
    }


def write_compiled(chain: Dict[str, Any], destination: str | Path) -> None:
    dest_path = Path(destination)
    dest_path.write_text(json.dumps(chain, indent=2))


def main() -> None:
    ruleset = load_ruleset("jsonchain_ruleset.json")
    compiled = compile_chain(ruleset)
    write_compiled(compiled, "jsonchain_compiled.json")


if __name__ == "__main__":
    main()
