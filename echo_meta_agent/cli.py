"""Command line interface for Echo Meta Agent."""

from __future__ import annotations

import json
import shlex
from typing import Any

from .agent import EchoAgent
from .memory import find as memory_find
from .memory import last as memory_last
from .utils import parse_arguments

PROMPT = "echo> "


def _pretty_print(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _print_help() -> None:
    print(
        "Available commands:\n"
        "  help                     Show this message\n"
        "  plugins                  List discovered plugins\n"
        "  tools <plugin>           List tools for a plugin\n"
        "  call <plugin>.<tool> [args] Execute a tool\n"
        "  mem last [n]             Show last n memory entries\n"
        "  mem find \"query\"        Search memory for text\n"
        "  exit | quit              Exit the console"
    )


def main() -> None:
    agent = EchoAgent()
    print("Echo Meta Agent console. Type 'help' for commands.")
    while True:
        try:
            raw = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        command = raw.strip()
        if not command:
            continue
        if command in {"exit", "quit"}:
            break
        if command == "help":
            _print_help()
            continue

        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            print(f"Error parsing command: {exc}")
            continue

        verb = tokens[0]
        if verb == "plugins":
            _pretty_print(agent.registry.list_plugins())
        elif verb == "tools":
            if len(tokens) < 2:
                print("Usage: tools <plugin>")
                continue
            try:
                _pretty_print(agent.registry.list_tools(tokens[1]))
            except KeyError as exc:
                print(str(exc))
        elif verb == "call":
            if len(tokens) < 2:
                print("Usage: call <plugin>.<tool> [args]")
                continue
            target = tokens[1]
            if "." not in target:
                print("Expected <plugin>.<tool> format")
                continue
            plugin, tool = target.split(".", 1)
            args, kwargs = parse_arguments(tokens[2:])
            result = agent.execute(plugin, tool, *args, **kwargs)
            _pretty_print(result)
        elif verb == "mem":
            if len(tokens) < 2:
                print("Usage: mem <last|find> ...")
                continue
            action = tokens[1]
            if action == "last":
                n = 20
                if len(tokens) >= 3 and tokens[2].isdigit():
                    n = int(tokens[2])
                _pretty_print(memory_last(n))
            elif action == "find":
                if len(tokens) < 3:
                    print('Usage: mem find "query"')
                    continue
                query = tokens[2]
                _pretty_print(memory_find(query))
            else:
                print("Unknown mem action; use 'last' or 'find'.")
        else:
            response = agent.route(command)
            _pretty_print(response)

    print("Goodbye.")


if __name__ == "__main__":
    main()
